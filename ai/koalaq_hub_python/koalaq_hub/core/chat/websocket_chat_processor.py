"""
WebSocket聊天处理器 - 处理WebSocket请求的聊天逻辑
"""

from ...models.agent import Agent
from ..executor import ToolExecutor
from ..executor.inner_tool_executor import InnerToolExecutor
from ..history_manager import HistoryManager
from ..llm.enhanced_llm_client import EnhancedLLMClient, OutputType
from ..summary_manager import SummaryManager
from ..tool.mcp.mcp_tool_manager import ToolManager
from ..websocket_handler import WebSocketHandler, WebSocketMessage
from .base_chat_processor import BaseChatProcessor


class WebSocketChatProcessor(BaseChatProcessor):
    """WebSocket聊天处理器 - 使用流式LLM调用，实时发送消息"""

    def __init__(self, history_manager: HistoryManager, tool_manager: ToolManager, 
                 summary_manager: SummaryManager, websocket_handler: WebSocketHandler,
                 server_manager=None, repository_adapter=None, 
                 sub_agent_executor=None):
        """初始化WebSocket聊天处理器

        Args:
            history_manager: 历史记录管理器
            tool_manager: 工具管理器
            summary_manager: 总结管理器
            websocket_handler: WebSocket处理器
            server_manager: MCP服务器管理器（可选）
            repository_adapter: 数据库适配器（可选）
            sub_agent_executor: 子Agent执行器（注入）
        """
        super().__init__(history_manager, tool_manager, summary_manager)
        self.websocket_handler = websocket_handler
        
        # 初始化执行器
        if server_manager:
            # 传递 tool_manager 给 ToolExecutor
            self.tool_executor = ToolExecutor(
                server_manager=server_manager,
                tool_manager=self.tool_manager
            )
        
        # 使用注入的 SubAgentExecutor
        self.agent_executor = sub_agent_executor
        
        # 初始化内部工具执行器
        if sub_agent_executor:
            self.inner_tool_executor = InnerToolExecutor(sub_agent_executor)

    async def call_llm(self, agent: Agent, messages: list, conversation_id: str):
        """调用LLM - WebSocket使用流式调用"""
        llm_client = EnhancedLLMClient.create_from_agent(agent)
        # 使用明确的参数传递工具配置
        return await llm_client.stream(
            messages=messages,
            conversation_id=conversation_id,
            output_type=OutputType.WEBSOCKET,
            websocket_handler=self.websocket_handler,
            tools=agent.tool_list,  # 可能为空列表或None
            tool_choice="auto"  # 让模型自动决定是否使用工具
        )

    async def send_message(self, conversation_id: str, message: WebSocketMessage):
        """发送消息 - WebSocket实时发送"""
        await self.websocket_handler.send_message(conversation_id, message)
        # 修复：正确获取消息类型
        message_type = getattr(message, 'type', 'unknown') if hasattr(message, 'type') else message.get('type', 'unknown') if isinstance(message, dict) else 'unknown'
        self.logger.debug("WebSocket消息已发送", {"conversation_id": conversation_id, "message_type": message_type})

    def get_result(self):
        """获取处理结果 - WebSocket返回None"""
        return None

    def _get_websocket_handler(self):
        """获取WebSocket处理器 - 重写基类方法"""
        return self.websocket_handler

    async def process_message(self, agent: Agent,message: str, 
                              user_id: str, 
                              conversation_id: str, 
                              recursion_depth: int = None, 
                              **kwargs) -> None:  # fmt: skip
        """处理WebSocket消息

        Args:
            message: 用户消息
            user_id: 用户ID
            conversation_id: 会话ID
            **kwargs: 其他参数

        Returns:
            None (WebSocket实时发送，无需返回内容)
        """
        self.logger.info("开始处理WebSocket消息", {"conversation_id": conversation_id, "user_id": user_id, "message_length": len(message)})

        # 调用父类的公共处理逻辑
        result = await super().process_message(agent=agent,recursion_depth=recursion_depth, message=message, user_id=user_id, conversation_id=conversation_id, **kwargs)

        self.logger.info("WebSocket消息处理完成", {"conversation_id": conversation_id})

        return result
