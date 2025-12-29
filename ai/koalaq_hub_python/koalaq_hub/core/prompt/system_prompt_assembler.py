"""
系统提示词组装器
负责按照分层架构组装完整的系统提示词
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List

from ...config.settings import config
from ...database.repository_adapter import RepositoryAdapter
from ...models.agent import Agent
from ..logging_utils import ManagerLogger
from ..tool.mcp.mcp_tool_manager import ToolManager


class SystemPromptAssembler:
    """系统提示词组装器"""
    
    def __init__(self, repository_adapter: RepositoryAdapter, tool_manager: ToolManager):
        """初始化
        
        Args:
            repository_adapter: 数据库适配器，用于获取历史上下文
            tool_manager: 工具管理器，用于获取工具描述
        """
        self.repository_adapter = repository_adapter
        self.tool_manager = tool_manager
        self.logger = ManagerLogger("SystemPromptAssembler")
        
        # 提示词目录
        self.prompts_dir = config.prompts_dir
        self.layers_dir = self.prompts_dir / "layers"
        
    def assemble(self, agent: Agent, user_id: str, conversation_id: str) -> str:
        """组装完整的系统提示词
        
        Args:
            agent: Agent实例
            user_id: 用户ID
            conversation_id: 会话ID
            
        Returns:
            组装好的系统提示词
        """
        sections = []
        
        # 1. 任务层（最高优先级）
        if agent.task_instructions_file:
            task_content = self._load_task_layer(agent)
            if task_content:
                sections.append(f"<task>\n【重要指导】\n{task_content}\n</task>")
        
        # 2. 角色层（身份定位，提前到基础层之前）
        role_content = self._build_role_layer(agent)
        if role_content:
            sections.append(f"<role>\n{role_content}\n</role>")
        
        # 3. 基础层
        base_sections = self._load_base_layer(agent)
        if base_sections:
            base_content = "\n\n".join(base_sections)
            sections.append(f"<base>\n{base_content}\n</base>")
        
        # 4. 能力层
        capability_content = self._build_capability_layer(agent)
        if capability_content:
            sections.append(f"<capability>\n{capability_content}\n</capability>")
        
        # 5. 上下文层
        context_content = self._build_context_layer(user_id, conversation_id)
        if context_content:
            sections.append(f"<context>\n{context_content}\n</context>")
        
        # 6. 如果有任务指导，结尾再次强调
        if agent.task_instructions_file:
            sections.append("\n【请务必遵守上述重要指导】")
        
        # 组装最终结果
        result = "\n\n".join(filter(None, sections))
        
        # 保存到文件（调试用）
        #self._save_to_file(agent, result, sections)
        
        self.logger.info("系统提示词组装完成", {
            "agent_id": agent.agent_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "prompt_length": len(result),
            "sections_count": len(sections)
        })
        
        return result
    
    def _load_task_layer(self, agent: Agent) -> str:
        """加载任务层提示词"""
        task_path = self.layers_dir / "task" / agent.task_instructions_file
        if task_path.exists():
            try:
                with open(task_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                self.logger.error(f"加载任务指导文件失败: {e}")
        return ""
    
    def _load_base_layer(self, agent: Agent) -> List[str]:
        """加载基础层模块"""
        sections = []
        
        # 加载base_modules中指定的模块
        for module_name in agent.base_modules:
            content = self._load_base_module(module_name)
            if content:
                sections.append(content)
        
        # 如果Agent可以调用其他Agent，自动加载时间处理规则
        if agent.agent_list:
            time_content = self._load_base_module("time_handling")
            if time_content:
                sections.append(time_content)
        
        # 处理ReAct模式
        if agent.enable_react_mode:
            react_file = f"react/react_mode_{agent.react_style}.prompt"
            if agent.react_style == "verbose":
                react_file = "react/react_mode.prompt"
            
            react_content = self._load_base_module(react_file)
            if react_content:
                sections.append(react_content)
        
        return sections
    
    def _load_base_module(self, module_name: str) -> str:
        """加载基础层的单个模块"""
        content = ""
        tag_name = ""
        
        # 尝试直接路径
        module_path = self.layers_dir / "base" / f"{module_name}.prompt"
        if module_path.exists():
            try:
                with open(module_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                tag_name = self._get_xml_tag_name(module_name)
            except Exception as e:
                self.logger.error(f"加载基础模块失败 {module_name}: {e}")
                return ""
        
        # 尝试子目录路径（如 format/format_rules.prompt）
        if not content:
            for subdir in ["format", "communication", "react", "safety"]:
                subdir_path = self.layers_dir / "base" / subdir / f"{module_name}.prompt"
                if subdir_path.exists():
                    try:
                        with open(subdir_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        tag_name = self._get_xml_tag_name(module_name)
                    except Exception as e:
                        self.logger.error(f"加载基础模块失败 {module_name}: {e}")
                        return ""
                    break
        
        # 如果已经包含路径分隔符，直接使用
        if not content and "/" in module_name:
            full_path = self.layers_dir / "base" / module_name
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 从路径中提取模块名
                    module_base_name = module_name.split("/")[-1].replace(".prompt", "")
                    tag_name = self._get_xml_tag_name(module_base_name)
                except Exception as e:
                    self.logger.error(f"加载基础模块失败 {module_name}: {e}")
        
        # 如果有内容，包裹XML标签
        if content and tag_name:
            return f"<{tag_name}>\n{content}\n</{tag_name}>"
        
        return content
    
    def _get_xml_tag_name(self, module_name: str) -> str:
        """根据模块名生成XML标签名
        
        例如:
        - format_rules -> format-rules
        - communication_style -> communication-style
        - safety_rules -> safety-rules
        - react_mode -> react-mode
        - react_mode_hidden -> react-mode-hidden
        """
        # 移除常见后缀
        name = module_name.replace(".prompt", "")
        # 将下划线转换为连字符
        tag_name = name.replace("_", "-")
        return tag_name
    
    def _build_role_layer(self, agent: Agent) -> str:
        """构建角色层提示词"""
        if not agent.role_context:
            return ""
        
        # 解析role_context (JSON格式)
        try:
            role_dict = json.loads(agent.role_context)
        except:
            self.logger.error("解析角色配置失败")
            return ""
        
        # 查找合适的角色模板
        role_template_path = None
        
        # 1. 尝试特定角色文件
        if agent.role_file:
            role_name = agent.role_file.replace('.role', '')
            specific_path = self.layers_dir / "role" / f"{role_name}.prompt"
            if specific_path.exists():
                role_template_path = specific_path
        
        # 2. 尝试通用模板
        if not role_template_path:
            # 优先使用compact版本（精简）
            compact_path = self.layers_dir / "role" / "compact.prompt"
            if compact_path.exists():
                role_template_path = compact_path
            else:
                # 使用default版本
                default_path = self.layers_dir / "role" / "default.prompt"
                if default_path.exists():
                    role_template_path = default_path
        
        if not role_template_path:
            return ""
        
        # 读取模板并替换占位符
        try:
            with open(role_template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # 替换占位符
            result = template
            for key, value in role_dict.items():
                result = result.replace(f"{{{key}}}", str(value))
            
            return result
        except Exception as e:
            self.logger.error(f"构建角色层失败: {e}")
            return ""
    
    def _build_capability_layer(self, agent: Agent) -> str:
        """构建能力层提示词"""
        sections = []
        
        if config.tool_mode == "function_calling":
            tool_guide_filename = "tool_usage_guide_function_calling.prompt"
        
        # 加载工具使用指南
        tool_guide_path = self.layers_dir / "capability" / "tools" / tool_guide_filename
        if tool_guide_path.exists():
            try:
                with open(tool_guide_path, 'r', encoding='utf-8') as f:
                    tool_guide_content = f.read()
                    sections.append(f"<tool-usage-guide>\n{tool_guide_content}\n</tool-usage-guide>")
            except Exception as e:
                self.logger.error(f"加载工具指南失败: {e}")
            
        return "\n\n".join(sections) if sections else ""
    
    def _format_agent_capabilities(self, agent_sub_prompt: str) -> str:
        """格式化Agent能力描述，为每个agent的yaml定义添加代码块
        
        Args:
            agent_sub_prompt: 包含agent能力描述的原始文本
            
        Returns:
            格式化后的文本，每个agent的yaml定义都包裹在```yaml代码块中
        """
        # 首先检查是否是从文件加载的agent列表
        return agent_sub_prompt
    
    def _load_agent_yaml(self, agent_id: str) -> str:
        """加载指定agent的yaml定义文件
        
        Args:
            agent_id: agent的ID
            
        Returns:
            yaml文件内容，如果文件不存在则返回空字符串
        """
        agents_dir = Path(config.project_root) / "resource" / "agents"
        yaml_path = agents_dir / f"{agent_id}.yaml"
        
        if yaml_path.exists():
            try:
                with open(yaml_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.error(f"加载Agent YAML文件失败 {agent_id}: {e}")
        
        return ""
    
    def _build_context_layer(self, user_id: str, conversation_id: str) -> str:
        """构建上下文层（历史信息）"""
        if not self.repository_adapter:
            return ""
        
        parts = []
        
        try:
            # 获取会话信息
            conversation = self.repository_adapter.get_conversation_recorder(user_id, conversation_id)
            
            # 1. 当前会话总结
            if conversation and conversation.summary:
                parts.append(f"【当前会话总结】\n{conversation.summary}")
            
            # 2. 最近快照
            recent_snapshots = self.repository_adapter.get_recent_snapshots(conversation_id, limit=2)
            if recent_snapshots:
                for i, snapshot in enumerate(recent_snapshots, 1):
                    parts.append(f"【快照{i}】\n{snapshot['context_summary']}")
                    
        except Exception as e:
            self.logger.error(f"获取历史上下文失败: {e}")
        
        return "\n\n".join(parts) if parts else ""
    
    def _save_to_file(self, agent: Agent, prompt: str, sections: List[str]) -> None:
        """保存组装好的提示词到文件（调试用）
        
        Args:
            agent: Agent实例
            prompt: 组装好的完整提示词
            sections: 各个部分的列表
        """
        try:
            # 创建runtime目录
            runtime_dir = Path(config.project_root) / "runtime"
            runtime_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}-{agent.agent_id}.md"
            filepath = runtime_dir / filename
            
            # 构建文件内容
            content = []
            content.append("# 系统提示词组装结果")
            content.append(f"\n**Agent**: {agent.name} ({agent.agent_id})")
            content.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            content.append(f"**总长度**: {len(prompt)} 字符")
            content.append(f"**组件数量**: {len(sections)} 个\n")
            
            # 添加统计信息
            content.append("## 各层统计")
            layer_stats = {
                "任务层": 0,
                "基础层": 0,
                "角色层": 0,
                "能力层": 0,
                "上下文层": 0
            }
            
            for section in sections:
                if "【重要指导】" in section:
                    layer_stats["任务层"] = len(section)
                elif "【角色定位】" in section:
                    layer_stats["角色层"] = len(section)
                elif "格式规范" in section or "交流风格规范" in section or "安全和隐私规范" in section or "ReAct" in section:
                    layer_stats["基础层"] += len(section)
                elif "## 可用工具" in section or "## 可用的子Agent" in section:
                    layer_stats["能力层"] = len(section)
                elif "【当前会话总结】" in section or "【快照" in section:
                    layer_stats["上下文层"] = len(section)
            
            for layer, length in layer_stats.items():
                if length > 0:
                    content.append(f"- {layer}: {length} 字符")
            
            # 添加配置信息
            content.append("\n## 配置信息")
            content.append(f"- ReAct模式: {'启用' if agent.enable_react_mode else '禁用'} ({agent.react_style})")
            content.append(f"- 基础模块: {', '.join(agent.base_modules)}")
            content.append(f"- 任务指导文件: {agent.task_instructions_file or '无'}")
            
            # 添加完整内容
            content.append("\n---\n")
            content.append(prompt)
            
            # 写入文件
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            
            self.logger.debug(f"提示词已保存到: {filepath}")
            
        except Exception as e:
            self.logger.error(f"保存提示词到文件失败: {e}")