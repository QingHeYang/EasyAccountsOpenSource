"""
HTTP聊天处理器 - 处理HTTP请求的聊天逻辑
"""

from typing import Any, Dict, List

from ...models.agent import Agent
from ..executor import ToolExecutor as MCPToolExecutor
from ..history_manager import HistoryManager
from ..llm.enhanced_llm_client import EnhancedLLMClient
from ..summary_manager import SummaryManager
from ..tool.mcp.mcp_tool_manager import ToolManager
from ..websocket_handler import WebSocketMessage
from .base_chat_processor import BaseChatProcessor


class HttpChatProcessor(BaseChatProcessor):
    """HTTP聊天处理器 - 使用阻塞式LLM调用，收集响应到http_content"""

    def __init__(self, history_manager: HistoryManager, tool_manager: ToolManager, 
                 summary_manager: SummaryManager, server_manager=None, 
                 repository_adapter=None, sub_agent_executor=None):
        """初始化HTTP聊天处理器

        Args:
            history_manager: 历史记录管理器
            tool_manager: 工具管理器
            summary_manager: 总结管理器
            server_manager: MCP服务器管理器（可选）
            repository_adapter: 数据库适配器（可选）
            sub_agent_executor: 子Agent执行器（注入）
        """
        super().__init__(history_manager, tool_manager, summary_manager)
        self.http_content: List[Dict[str, Any]] = []

        # 初始化MCP工具执行器
        if server_manager:
            self.mcp_tool_executor = MCPToolExecutor(
                server_manager=server_manager,
                tool_manager=self.tool_manager
            )

        # 使用注入的 SubAgentExecutor
        self.agent_executor = sub_agent_executor
        # 注：内部工具执行器在基类中已初始化为全局单例

    async def call_llm(self, agent: Agent, messages: list, conversation_id: str):
        """调用LLM - HTTP使用阻塞式调用"""
        llm_client = EnhancedLLMClient.create_from_agent(agent)
        # 使用明确的参数传递工具配置
        return await llm_client.block(
            messages=messages, 
            conversation_id=conversation_id,
            tools=agent.tool_list,  # 可能为空列表或None
            tool_choice="auto"  # 让模型自动决定是否使用工具
        )

    async def send_message(self, conversation_id: str, message: WebSocketMessage):
        """发送消息 - HTTP收集到http_content列表"""
        if message.get("type") != "exit":
            self.http_content.append(message)
            self.logger.info("当前http_content 字典length", {"conversation_id": conversation_id, "length": len(self.http_content)})

    def get_result(self):
        """获取处理结果 - HTTP返回收集的内容列表"""
        return self.http_content

    async def process_message(self,
                              agent: Agent,
                              message: str, 
                              user_id: str, 
                              conversation_id: str, 
                              recursion_depth: int = None, 
                              **kwargs) -> List[Dict[str, Any]]:  # fmt: skip
        """处理HTTP消息

        Args:
            message: 用户消息
            user_id: 用户ID
            conversation_id: 会话ID
            **kwargs: 其他参数

        Returns:
            HTTP响应内容列表
        """

        self.logger.info("开始处理HTTP消息", {"conversation_id": conversation_id, "user_id": user_id, "message_length": len(message)})

        # 调用父类的公共处理逻辑
        result = await super().process_message(agent=agent,recursion_depth=recursion_depth, message=message, user_id=user_id, conversation_id=conversation_id, **kwargs)

        return result
