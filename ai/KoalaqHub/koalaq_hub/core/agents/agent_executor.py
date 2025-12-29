"""
Agent 执行器 - 管理 Agent 的执行流程
作为 ChatManager 的替代品，专门用于 Agent 执行
"""

from typing import Any, Dict, List, Optional, Union

from ...config.agent_builder import agent_builder
from ...database.repository_adapter import RepositoryAdapter
from ...models.agent import Agent

# from ..prompt_manager import PromptManager  # 不再需要
from ..auto_question_manager import AutoQuestionManager
from ..chat import HttpChatProcessor, InternalChatProcessor, WebSocketChatProcessor
from ..executor import SubAgentExecutor
from ..history_manager import HistoryManager
from ..logging_utils import ManagerLogger
from ..summary_manager import SummaryManager
from ..tool.mcp.mcp_tool_manager import ToolManager
from ..tool.mcp.server_manager import ServerManager
from .agent_registry import AgentRegistry


class AgentExecutor:
    """Agent 执行器 - 统一管理 Agent 的执行"""
    
    def __init__(self, 
                 agent_registry: AgentRegistry,
                 repository_adapter: RepositoryAdapter,
                 summary_manager: SummaryManager,
                 server_manager: ServerManager,
                 function_prompt_assembler,
                 websocket_handler=None):
        """初始化 Agent 执行器
        
        Args:
            agent_registry: Agent 注册表
            repository_adapter: 数据库适配器
            summary_manager: 总结管理器
            server_manager: MCP 服务器管理器
            function_prompt_assembler: 功能提示词组装器
            websocket_handler: WebSocket 处理器（可选）
        """
        self.agent_registry = agent_registry
        self.repository_adapter = repository_adapter
        self.summary_manager = summary_manager
        self.server_manager = server_manager
        self.function_prompt_assembler = function_prompt_assembler
        self.websocket_handler = websocket_handler
        
        # 初始化日志记录器
        self.logger = ManagerLogger("AgentExecutor")
        
        # 创建共享的管理器实例
        self.tool_manager = ToolManager(server_manager, websocket_handler)
        self.auto_question_manager = AutoQuestionManager(
            repository_adapter, self.tool_manager, function_prompt_assembler
        )
        self.history_manager = HistoryManager(
            repository_adapter, summary_manager, 
            self.auto_question_manager, self.tool_manager
        )
        
        # 创建共享的 SubAgentExecutor 实例（避免循环依赖和重复创建）

        self.sub_agent_executor = SubAgentExecutor(
            agent_excutor=self,  # 传递自己
            agent_builder=agent_builder,
            agent_registry=agent_registry,
            repository_adapter=repository_adapter
        )
        
        # 设置 summary_manager 的 websocket_handler
        self.summary_manager.set_websocket_handler(websocket_handler)

        # 活跃处理器追踪（用于停止机制）
        # Key: conversation_id, Value: ChatProcessor 实例
        self.active_processors: Dict[str, Any] = {}

    def _create_websocket_processor(self) -> WebSocketChatProcessor:
        """创建新的 WebSocket 处理器实例"""
        return WebSocketChatProcessor(
            self.history_manager,
            self.tool_manager,
            self.summary_manager,
            self.websocket_handler,
            server_manager=self.server_manager,
            repository_adapter=self.repository_adapter,
            sub_agent_executor=self.sub_agent_executor
        )

    def _create_http_processor(self) -> HttpChatProcessor:
        """创建新的 HTTP 处理器实例"""
        return HttpChatProcessor(
            self.history_manager,
            self.tool_manager,
            self.summary_manager,
            server_manager=self.server_manager,
            repository_adapter=self.repository_adapter,
            sub_agent_executor=self.sub_agent_executor
        )
    
    async def execute(self,
                      agent: Agent,
                      message: str,
                      conversation_id: str,
                      user_id: str,
                      source: str = "internal",
                      parent_conversation_id: Optional[str] = None,
                      **kwargs) -> Union[List[Dict[str, Any]], None]:
        """执行 Agent
        
        Args:
            agent: Agent 实例
            message: 要处理的消息
            conversation_id: 对话 ID
            user_id: 用户 ID
            source: 执行来源 ("http", "websocket", "internal")
            parent_conversation_id: 父对话 ID（用于 Agent 调用链）
            **kwargs: 其他参数
            
        Returns:
            HTTP/内部调用返回响应列表，WebSocket 返回 None
        """
        # 验证 Agent
        if not agent:
            error_msg = "Agent 实例不能为空"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if not agent.is_ready():
            error_msg = f"Agent 未就绪: {agent.agent_id}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        self.logger.info("开始执行 Agent", {
            "agent_id": agent.agent_id,
            "agent_name": agent.name,
            "source": source,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "message_length": len(message),
            "parent_conversation_id": parent_conversation_id
        })
        
        # 如果系统提示词为空，则组装（非WebSocket来源需要在这里组装）
        if not agent.system_prompt:
            system_prompt = await self.agent_registry.build_system_prompt(agent, user_id, conversation_id)
            agent.system_prompt = system_prompt
            self.logger.info("组装系统提示词", {
                "agent_id": agent.agent_id,
                "prompt_length": len(system_prompt),
                "source": source
            })
        
        # 设置递归深度
        recursion_depth = agent.tool_round

        # 根据来源创建处理器
        processor = None

        if source == "http":
            processor = self._create_http_processor()
        elif source == "websocket":
            if not self.websocket_handler:
                error_msg = "WebSocket 处理器未初始化"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            processor = self._create_websocket_processor()
        elif source == "internal":
            # 内部调用 - 创建 InternalChatProcessor
            processor = InternalChatProcessor(
                self.history_manager,
                self.tool_manager,
                self.summary_manager,
                self.websocket_handler,
                server_manager=self.server_manager,
                repository_adapter=self.repository_adapter,
                sub_agent_executor=self.sub_agent_executor,
                parent_conversation_id=parent_conversation_id
            )
        else:
            error_msg = f"不支持的执行来源: {source}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        # 注册到活跃处理器（执行前）
        self.active_processors[conversation_id] = processor
        self.logger.debug("注册活跃处理器", {
            "conversation_id": conversation_id,
            "source": source,
            "active_count": len(self.active_processors)
        })

        try:
            # 执行处理
            return await processor.process_message(
                agent=agent,
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                recursion_depth=recursion_depth,
                parent_conversation_id=parent_conversation_id if source == "internal" else None,
                **kwargs
            )
        finally:
            # 从活跃处理器移除（执行后）
            self.active_processors.pop(conversation_id, None)
            self.logger.debug("移除活跃处理器", {
                "conversation_id": conversation_id,
                "active_count": len(self.active_processors)
            })

    async def stop(self, conversation_id: str, cascade: bool = True) -> bool:
        """
        停止指定会话的 Agent 执行

        根据 conversation_id 从 active_processors 中找到对应的 Processor，
        并调用其 stop() 方法停止 LLM 生成。

        Args:
            conversation_id: 要停止的会话 ID
            cascade: 是否级联停止子对话（默认 True）
                     当为 True 时，会同时停止所有 {conversation_id}_sub_* 的子对话

        Returns:
            bool: 是否成功找到并停止了会话（主对话或任意子对话）

        注意：
        - 此方法是异步的，需要使用 await 调用
        - 如果 conversation_id 不存在，方法会返回 False
        - 级联停止会查找并停止所有子Agent对话
        """
        self.logger.info("收到停止Agent执行请求", {
            "conversation_id": conversation_id,
            "cascade": cascade
        })

        stopped_any = False

        # 1. 停止主对话
        processor = self.active_processors.get(conversation_id)
        if processor:
            try:
                await processor.stop()
                self.logger.info("成功停止主对话Agent执行", {"conversation_id": conversation_id})
                stopped_any = True
            except Exception as e:
                self.logger.error(f"停止主对话Agent执行时出错: {e}", extra_data={"conversation_id": conversation_id})

        # 2. 级联停止子对话
        if cascade:
            sub_prefix = f"{conversation_id}_sub_"
            sub_conversation_ids = [
                cid for cid in self.active_processors.keys()
                if cid.startswith(sub_prefix)
            ]

            if sub_conversation_ids:
                self.logger.info("发现子对话，准备级联停止", {
                    "main_conversation_id": conversation_id,
                    "sub_conversation_count": len(sub_conversation_ids),
                    "sub_conversation_ids": sub_conversation_ids
                })

                for sub_cid in sub_conversation_ids:
                    sub_processor = self.active_processors.get(sub_cid)
                    if sub_processor:
                        try:
                            await sub_processor.stop()
                            self.logger.info("成功停止子对话Agent执行", {
                                "sub_conversation_id": sub_cid,
                                "parent_conversation_id": conversation_id
                            })
                            stopped_any = True
                        except Exception as e:
                            self.logger.error(f"停止子对话Agent执行时出错: {e}", extra_data={
                                "sub_conversation_id": sub_cid,
                                "parent_conversation_id": conversation_id
                            })

        if not stopped_any:
            self.logger.warning("没有找到正在执行的任务", {"conversation_id": conversation_id})

        return stopped_any
