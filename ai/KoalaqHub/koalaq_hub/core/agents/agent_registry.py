"""
Agent 注册表
负责缓存 AgentConfig 和管理用户级别的 Agent 实例
"""

import asyncio
from typing import Dict, List, Optional

from ...config.agent_builder import AgentConfig, agent_builder
from ...config.settings import config
from ...database.repository_adapter import RepositoryAdapter
from ...models.agent import Agent
from ..llm_manager import LLMManager
from ..logging_utils import ManagerLogger
from ..prompt.system_prompt_assembler import SystemPromptAssembler
from ..tool import ToolConverter
from ..tool.mcp.mcp_tool_manager import ToolManager
from ...tools import agent_tool_binder


class AgentRegistry:
    """Agent 注册表 - 缓存配置和管理用户级别的 Agent"""

    def __init__(
        self,
        tool_manager: Optional[ToolManager] = None,
        repository_adapter: Optional[RepositoryAdapter] = None,
        llm_manager: Optional[LLMManager] = None,
        cache_timeout_minutes: int = 30,
    ):
        """初始化 Agent 注册表

        Args:
            tool_manager: 工具管理器（可选，用于生成系统提示词）
            repository_adapter: 数据库适配器（可选，用于获取历史上下文）
            llm_manager: LLM 管理器（必需，用于获取 LLM 配置）
            cache_timeout_minutes: Agent缓存超时时间（分钟），默认30分钟
        """
        self.logger = ManagerLogger("AgentRegistry")

        # AgentConfig 缓存（保留配置缓存，只是不缓存实例）
        self._configs: Dict[str, AgentConfig] = {}

        # 线程安全锁
        self._lock = asyncio.Lock()

        # 依赖服务
        self.tool_manager = tool_manager
        self.repository_adapter = repository_adapter
        self.llm_manager = llm_manager

        # 内部工具绑定器（使用全局单例）
        self.agent_tool_binder = agent_tool_binder

        # 提示词组装器（如果有依赖服务才创建）
        self.system_prompt_assembler = None
        if tool_manager and repository_adapter:
            self.system_prompt_assembler = SystemPromptAssembler(repository_adapter, tool_manager)
            
        # 定期清理任务
        self._cleanup_task = None
        
    async def initialize(self):
        """初始化注册表，缓存所有配置"""
        self.logger.info("开始初始化 Agent 注册表")
        
        # 获取所有配置的 Agent
        all_agent_configs = agent_builder.get_all_agents()
        
        # 缓存所有配置
        for agent_id, config in all_agent_configs.items():
            self._configs[agent_id] = config
            
        self.logger.info(f"缓存了 {len(self._configs)} 个 Agent 配置")
        
        # 统计启用的 Agent 数量
        enabled_count = sum(1 for config in self._configs.values() if config.enable)
        self.logger.info(f"共有 {enabled_count} 个 Agent 已启用")
        
        # 启动定期清理任务
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self.logger.info("启动了定期清理任务（不再缓存 Agent 实例）")
    
    
    def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取 Agent 配置
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentConfig 实例，不存在返回 None
        """
        return self._configs.get(agent_id)
    
    
    def create_agent_from_config(self, agent_id: str) -> Optional['Agent']:
        """基于配置创建 Agent 实例
        
        Args:
            agent_id: Agent ID
            
        Returns:
            新创建的 Agent 实例
        """

        
        config = self.get_agent_config(agent_id)
        if not config:
            self.logger.error(f"找不到 Agent 配置: {agent_id}")
            return None
        
        if not config.enable:
            self.logger.warning(f"Agent {agent_id} 未启用")
            return None
        
        # 获取 LLM 对象
        main_llm = None
        if config.llm_use:
            main_llm = self.llm_manager.get_llm(config.llm_use)
            if not main_llm:
                self.logger.error(f"找不到 LLM 配置: {config.llm_use}")
                return None
        
        think_llm = None
        if config.enable_thinking and config.llm_think_use:
            think_llm = self.llm_manager.get_llm(config.llm_think_use)
            if not think_llm:
                self.logger.warning(f"找不到思考 LLM 配置: {config.llm_think_use}")
        
        summary_llm = None
        if config.enable_summary and config.summary_llm_use:
            summary_llm = self.llm_manager.get_llm(config.summary_llm_use)
            if not summary_llm:
                self.logger.warning(f"找不到总结 LLM 配置: {config.summary_llm_use}")
        
        # 如果没有指定summary_llm，使用main_llm
        if not summary_llm:
            summary_llm = main_llm
        
        # 创建 Agent 实例，复制配置值而不是引用
        agent = Agent(
            agent_id=agent_id,
            name=config.name,
            description=config.description,
            # 复制配置值
            enable=config.enable,
            # system_prompt_file=config.system_prompt_file,  # 已废弃
            role_file=config.role_file,
            role_context=config.role_context,
            llm_use=config.llm_use,
            llm_think_use=config.llm_think_use,
            summary_llm_use=config.summary_llm_use,
            enable_summary=config.enable_summary,
            enable_thinking=config.enable_thinking,
            enable_auto_question=config.enable_auto_question,
            llm_memory_window=config.llm_memory_window,
            tool_round=config.tool_round,
            mcp_servers=list(config.mcp_servers),  # 复制列表
            mcp_tool_black_list=list(config.mcp_tool_black_list),  # 复制列表
            tool_tokens=dict(config.tool_tokens),  # 复制字典
            agent_guide=config.agent_guide,  # Agent指南文件名
            agent_list=list(config.agent_list),  # 复制子Agent列表
            inner_tools=list(config.inner_tools),  # 复制内部工具列表
            task_instructions_file=config.task_instructions_file,
            # LLM 对象
            main_llm=main_llm,
            think_llm=think_llm,
            summary_llm=summary_llm,
        )
        
        # 构建子Agent的使用提示词
        if agent.agent_list:
            sub_prompts = []
            for sub_agent_id in agent.agent_list:
                sub_config = agent_builder.get_agent(sub_agent_id)
                if sub_config and sub_config.agent_guide_context:
                    sub_prompts.append(f"### {sub_agent_id}\n{sub_config.agent_guide_context}")
            
            if sub_prompts:
                agent.agent_sub_prompt = "\n".join(sub_prompts)
                self.logger.info("构建子Agent提示词", {
                    "agent_id": agent_id,
                    "sub_agents": agent.agent_list,
                    "prompt_length": len(agent.agent_sub_prompt)
                })
        
        return agent
    
    async def get_or_create_user_agent(self, user_id: str, agent_id: str) -> Optional['Agent']:
        """创建用户的 Agent 实例
        
        注意：每次调用都会创建新的 Agent 实例，不再缓存
        WebSocket 断开后 Agent 会被自动回收
        
        Args:
            user_id: 用户 ID
            agent_id: 应用名称（Agent ID）
            
        Returns:
            新创建的 Agent 实例
        """
        # 直接创建新的 Agent 实例，不再缓存
        agent = self.create_agent_from_config(agent_id)
        if not agent:
            return None
            
        self.logger.info("创建新的 Agent 实例（不缓存）", {
            "user_id": user_id,
            "agent_id": agent_id,
            "agent_name": agent.name
        })
        
        return agent
    
    def build_sub_agent(self, agent_id: str) -> Optional['Agent']:
        """创建简化的子Agent实例，用于内部调用
        
        子Agent特点：
        - 不需要总结功能
        - 不需要思考功能  
        - 不需要自动问题生成
        - 不纳入管理系统
        - 使用完即销毁
        
        Args:
            agent_id: 原始Agent ID
            
        Returns:
            简化的 Agent 实例，如果失败返回 None
        """
        config = self.get_agent_config(agent_id)
        if not config:
            self.logger.error(f"找不到 Agent 配置: {agent_id}")
            return None
        
        if not config.enable:
            self.logger.warning(f"Agent {agent_id} 未启用")
            return None
        
        # 只获取主 LLM，不需要思考和总结 LLM
        main_llm = None
        if config.llm_use:
            main_llm = self.llm_manager.get_llm(config.llm_use)
            if not main_llm:
                self.logger.error(f"找不到 LLM 配置: {config.llm_use}")
                return None
        
        # 创建简化的 SubAgent 实例
        sub_agent = Agent(
            agent_id=f"sub_{agent_id}",  # 添加前缀区分
            name=f"Sub-{config.name}",  # 添加前缀区分
            description=config.description,
            
            # 基础配置
            enable=True,
            role_file=config.role_file,
            role_context=config.role_context,
            llm_use=config.llm_use,
            
            # 简化配置：禁用不必要的功能
            llm_think_use=None,
            summary_llm_use=None,
            enable_summary=False,  # 不需要总结
            enable_thinking=False,  # 不需要思考
            enable_auto_question=False,  # 不需要自动问题
            
            # 内存和工具配置
            llm_memory_window=config.llm_memory_window,
            tool_round=min(config.tool_round, 3),  # 限制工具调用轮次，防止过深递归
            mcp_servers=list(config.mcp_servers),
            mcp_tool_black_list=list(config.mcp_tool_black_list),
            tool_tokens=dict(config.tool_tokens),
            agent_guide=config.agent_guide,
            agent_list=[],  # 子Agent不能再调用其他Agent，避免无限递归
            inner_tools=list(config.inner_tools),  # 复制内部工具列表
            task_instructions_file=config.task_instructions_file,
            
            # LLM 对象：只设置主 LLM
            main_llm=main_llm,
            think_llm=None,  # 不需要思考
            summary_llm=None,  # 不需要总结
            sub_agent_mode=True,
        )
        
        self.logger.debug("SubAgent创建完成", {
            "sub_agent_id": sub_agent.agent_id,
            "original_agent_id": agent_id, 
            "agent_name": sub_agent.name,
            "tool_round": sub_agent.tool_round
        })
        
        return sub_agent
    
    async def build_tools_list(self, agent: Agent) -> None:
        """为Agent构建Function Calling工具列表

        Args:
            agent: Agent实例
        """
        tools = []

        # 1. 获取MCP工具列表（异步获取）
        if self.tool_manager:
            mcp_tools = await self.tool_manager.get_tools_for_application(agent)
            # 转换为Function Calling格式
            tools.extend(ToolConverter.mcp_list_to_function_format(mcp_tools))

        # 2. 获取内部工具列表（如call_agent）
        if self.agent_tool_binder:
            inner_tools = self.agent_tool_binder.get_tools_for_agent(agent)
            tools.extend(inner_tools)

        # 将工具列表存储到agent对象中
        agent.tool_list = tools

        self.logger.info("构建Function Calling工具列表", {
            "agent_id": agent.agent_id,
            "tool_count": len(agent.tool_list),
        })

    async def build_system_prompt(self, agent: Agent, user_id: str, conversation_id: str) -> str:
        """为Agent构建系统提示词，同时构建Function Calling工具列表

        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID

        Returns:
            组装好的系统提示词
        """
        # 构建Function Calling工具列表（异步）
        await self.build_tools_list(agent)

        # 构建系统提示词
        if self.system_prompt_assembler:
            return self.system_prompt_assembler.assemble(agent, user_id, conversation_id)
        else:
            # 如果没有组装器，返回简单的默认提示词
            self.logger.warning("没有系统提示词组装器，使用默认提示词")
            return f"你是{agent.name}，{agent.description}"
    
    async def mark_agent_disconnected(self, user_id: str, agent_id: str) -> bool:
        """标记用户的 Agent 为断开状态（WebSocket 断开时调用）
        
        由于不再缓存 Agent，这个方法只记录日志
        
        Args:
            user_id: 用户 ID
            agent_id: 应用名称（Agent ID）
            
        Returns:
            始终返回 True
        """
        self.logger.info("Agent 已断开连接（无需清理，因为不再缓存）", {
            "user_id": user_id,
            "agent_id": agent_id
        })
        return True
    
    async def remove_user_agent(self, user_id: str, agent_id: str) -> bool:
        """移除用户的 Agent 实例
        
        由于不再缓存 Agent，这个方法只记录日志
        
        Args:
            user_id: 用户 ID
            agent_id: 应用名称（Agent ID）
            
        Returns:
            始终返回 True
        """
        self.logger.info("Agent 移除请求（无需操作，因为不再缓存）", {
            "user_id": user_id,
            "agent_id": agent_id
        })
        return True
    
    def get_user_agents_count(self) -> int:
        """获取当前活跃的用户 Agent 数量
        
        由于不再缓存，始终返回 0
        """
        return 0
    
    def get_user_agents_info(self) -> List[Dict[str, str]]:
        """获取所有用户 Agent 的信息（用于调试和监控）
        
        由于不再缓存，始终返回空列表
        """
        return []
    
    def list_agents(self) -> List[str]:
        """列出所有 Agent ID"""
        return list(self._configs.keys())
    
    def list_enabled_agents(self) -> List[str]:
        """列出所有启用的 Agent ID"""
        return [
            agent_id 
            for agent_id, config in self._configs.items() 
            if config.enable
        ]
    
    def reload_config(self, agent_id: str) -> bool:
        """重新加载指定 Agent 的配置
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功
        """
        # 从 agent_builder 重新获取配置
        new_config = agent_builder.get_agent(agent_id)
        if not new_config:
            return False
        
        # 更新缓存
        self._configs[agent_id] = new_config
        
        # 记录配置更新
        self.logger.info("重新加载Agent配置", {
            "agent_id": agent_id,
            "enabled": new_config.enable
        })
        
        return True
    
    async def _periodic_cleanup(self):
        """定期清理任务
        
        由于不再缓存 Agent，这个任务只是保持兼容性
        """
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟执行一次（减少频率）
                # 不再执行任何清理操作
                self.logger.debug("定期清理任务运行中（无操作）")
            except asyncio.CancelledError:
                self.logger.info("定期清理任务被取消")
                break
            except Exception as e:
                self.logger.error(f"定期清理任务出错: {e}")
                await asyncio.sleep(300)
    
    async def shutdown(self):
        """关闭注册表，清理资源"""
        self.logger.info("关闭 Agent 注册表")
        
        # 取消定期清理任务
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # 清理配置缓存
        self._configs.clear()


# 全局 Agent 注册表实例（将在应用启动时初始化）
agent_registry: Optional[AgentRegistry] = None