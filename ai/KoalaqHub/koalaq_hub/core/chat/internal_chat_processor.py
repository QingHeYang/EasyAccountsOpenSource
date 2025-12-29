"""
内部聊天处理器 - 用于Agent内部调用，既能返回结果又能发送WebSocket消息
"""

from typing import Any, Dict, List, Optional

from ...models.agent import Agent
from ..executor import ToolExecutor as MCPToolExecutor
from ..history_manager import HistoryManager
from ..llm.enhanced_llm_client import EnhancedLLMClient
from ..summary_manager import SummaryManager
from ..tool.mcp.mcp_tool_manager import ToolManager
from ..websocket_handler import AgentMessage, MessageBuilder, WebSocketHandler, WebSocketMessage
from .base_chat_processor import BaseChatProcessor


class InternalChatProcessor(BaseChatProcessor):
    """内部聊天处理器 - 结合HTTP的返回值和WebSocket的实时消息"""
    
    def __init__(self, history_manager: HistoryManager, tool_manager: ToolManager, 
                 summary_manager: SummaryManager, websocket_handler: Optional[WebSocketHandler] = None,
                 server_manager=None, repository_adapter=None, 
                 sub_agent_executor=None,
                 parent_conversation_id: str = None):
        """初始化内部聊天处理器
        
        Args:
            history_manager: 历史记录管理器
            tool_manager: 工具管理器
            summary_manager: 总结管理器
            websocket_handler: WebSocket处理器（可选，用于发送消息到父会话）
            server_manager: MCP服务器管理器（可选）
            repository_adapter: 数据库适配器（可选）
            sub_agent_executor: 子Agent执行器（注入）
            parent_conversation_id: 父会话ID（用于WebSocket消息路由）
        """
        super().__init__(history_manager, tool_manager, summary_manager)
        self.websocket_handler = websocket_handler
        self.agent = None
        self.parent_conversation_id = parent_conversation_id
        self.message_box: Dict[str, WebSocketMessage] = {}  # 使用字典存储不同类型的消息

        # 创建一个包装的WebSocketHandler用于路由消息到父会话
        self._wrapped_websocket_handler = None

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
        """调用LLM - 使用阻塞式调用获取完整结果"""
        llm_client = EnhancedLLMClient.create_from_agent(agent)
        # 使用明确的参数传递工具配置
        return await llm_client.block(
            messages=messages, 
            conversation_id=conversation_id,
            tools=agent.tool_list,  # 可能为空列表或None
            tool_choice="auto"  # 让模型自动决定是否使用工具
        )

    
    async def send_message(self, conversation_id: str, message: WebSocketMessage):
        """发送消息 - 既收集结果又通过WebSocket发送"""
        # 设置agent信息
        agent = AgentMessage(
            agent_id=self.agent.agent_id,
            agent_conversation_id=conversation_id
        )
        message.agent = agent
        message.conversation_id = self.parent_conversation_id
        
        # 如果需要，通过WebSocket发送
        if self.agent.websocket_mode:
            await self.websocket_handler.send_message(self.parent_conversation_id, message)
        
        # 存储消息到message_box，使用消息类型作为key
        message_type = message.type
        self.message_box[message_type] = message
        
        # 记录收集的消息
        self.logger.debug("收集消息到message_box", {
            "type": message_type,
            "conversation_id": conversation_id,
            "text_length": len(message.text) if message.text else 0,
            "has_object": bool(message.object),
            "total_types": len(self.message_box)
        })
    
    def get_result(self):
        """获取处理结果 - 返回message_box"""
        # 注意：这个方法必须是同步的，因为父类中的调用是同步的
        # 返回整个message_box，让调用方根据需要提取消息
        return self.message_box
    
    async def process_message(self,
                              agent: Agent,
                              message: str, 
                              user_id: str, 
                              conversation_id: str, 
                              recursion_depth: int = None,
                              parent_conversation_id: str = None,
                              **kwargs) -> List[Dict[str, Any]]:  # fmt: skip
        """处理内部消息
        
        Args:
            message: 用户消息
            user_id: 用户ID
            conversation_id: 会话ID（子会话）
            parent_conversation_id: 父会话ID（可选，用于WebSocket消息路由）
            **kwargs: 其他参数
            
        Returns:
            处理结果列表
        """

        self.agent = agent
        
        # 判断是否是工具调用递归（通过 is_call_tool 参数）
        is_call_tool = kwargs.get('is_call_tool', False)
        
        self.logger.info("开始处理内部消息", {
            "conversation_id": conversation_id, 
            "parent_conversation_id": self.parent_conversation_id,
            "user_id": user_id, 
            "message_length": len(message),
            "is_call_tool": is_call_tool
        })
        
        # 只在初始调用时发送 start 消息，工具调用递归时不发送
        if not is_call_tool:
            # 传递任务文本（message 参数即为任务内容）
            message_obj = MessageBuilder.create_agent_start_message(
                conversation_id, 
                agent_id=self.agent.agent_id,
                task=message  # 添加任务文本
            )
            await self.send_message(conversation_id, message_obj)
        
        # 调用父类的公共处理逻辑
        await super().process_message(
            agent=agent,
            recursion_depth=recursion_depth, 
            message=message, 
            user_id=user_id, 
            conversation_id=conversation_id, 
            **kwargs
        )
        
        # 完全移除 agent_complete 消息的发送
        # 原因：complete 消息在多次工具调用时会重复发送，造成混乱
        
        self.logger.info("内部聊天处理器完成消息处理", {
            "conversation_id": conversation_id,
            "parent_conversation_id": self.parent_conversation_id,
            "message_types": list(self.message_box.keys()),
            "total_types": len(self.message_box),
            "is_call_tool": is_call_tool
        })
        
        # 返回message_box（供 SubAgentExecutor 提取结果）
        return self.message_box