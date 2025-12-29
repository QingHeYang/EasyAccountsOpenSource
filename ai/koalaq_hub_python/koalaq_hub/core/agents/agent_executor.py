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
        
        # 预创建的处理器实例（可复用）
        self.http_processor = None
        self.websocket_processor = None
        
        # 初始化处理器
        self._init_processors()
        
    def _init_processors(self):
        """初始化处理器实例"""
        # HTTP 处理器 - 可以复用，因为每次调用都会清空 http_content
        self.http_processor = HttpChatProcessor(
            self.history_manager,
            self.tool_manager,
            self.summary_manager,
            server_manager=self.server_manager,
            repository_adapter=self.repository_adapter,
            sub_agent_executor=self.sub_agent_executor  # 传递共享的 SubAgentExecutor
        )
        
        # WebSocket 处理器 - 可以复用，因为状态都在 websocket_handler 中
        if self.websocket_handler:
            self.websocket_processor = WebSocketChatProcessor(
                self.history_manager,
                self.tool_manager,
                self.summary_manager,
                self.websocket_handler,
                server_manager=self.server_manager,
                repository_adapter=self.repository_adapter,
                sub_agent_executor=self.sub_agent_executor  # 传递共享的 SubAgentExecutor
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
            system_prompt = self.agent_registry.build_system_prompt(agent, user_id, conversation_id)
            agent.system_prompt = system_prompt
            self.logger.info("组装系统提示词", {
                "agent_id": agent.agent_id,
                "prompt_length": len(system_prompt),
                "source": source
            })
        
        # 设置递归深度
        recursion_depth = agent.tool_round
        
        # 根据来源选择处理器
        if source == "http":
            # HTTP 处理器可以复用，但需要清空之前的内容
            self.http_processor.http_content = []
            return await self.http_processor.process_message(
                agent=agent,
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                recursion_depth=recursion_depth,
                **kwargs
            )
            
        elif source == "websocket":
            if not self.websocket_processor:
                error_msg = "WebSocket 处理器未初始化"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
                
            return await self.websocket_processor.process_message(
                agent=agent,
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                recursion_depth=recursion_depth,
                **kwargs
            )
            
        elif source == "internal":
            # 内部调用 - 每次都创建新的处理器实例
            # 因为需要特定的 parent_conversation_id
            internal_processor = InternalChatProcessor(
                self.history_manager,
                self.tool_manager,
                self.summary_manager,
                self.websocket_handler,
                server_manager=self.server_manager,
                repository_adapter=self.repository_adapter,
                sub_agent_executor=self.sub_agent_executor,  # 传递共享的 SubAgentExecutor
                parent_conversation_id=parent_conversation_id
            )
            
            return await internal_processor.process_message(
                agent=agent,
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                recursion_depth=recursion_depth,
                parent_conversation_id=parent_conversation_id,
                **kwargs
            )
            
        else:
            error_msg = f"不支持的执行来源: {source}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
