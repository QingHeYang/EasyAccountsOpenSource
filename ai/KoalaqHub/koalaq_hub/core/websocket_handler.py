import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, Optional

from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from .logging_utils import ManagerLogger


class MessageType(Enum):
    """WebSocket消息类型枚举 - 统一消息类型，通过agent字段区分来源"""

    # 核心消息类型
    CHUNK = "chunk"  # 流式文本块
    SEGMENT = "segment"  # 完整响应片段
    TOOL_CALL = "tool_call"  # 工具调用
    TOOL_RESPONSE = "tool_response"  # 工具响应
    
    # 状态消息
    START = "start"  # 开始处理（可用于agent开始）
    COMPLETE = "complete"  # 处理完成
    EXIT = "exit"  # 退出
    ERROR = "error"  # 错误
    
    # 特殊功能消息
    TITLE = "title"  # 标题生成
    QUESTION = "question"  # 问题建议

    
@dataclass
class AgentMessage:
    """子agent消息数据类"""
    agent_id: str
    agent_conversation_id: str

@dataclass
class WebSocketMessage:
    """WebSocket消息数据类"""

    conversation_id: str
    is_finish: bool
    type: str
    text: str
    object: dict
    status: bool = True
    agent: AgentMessage = None

    def to_json(self):
        """转换为JSON字符串"""
        return json.dumps(asdict(self), ensure_ascii=False)



class MessageBuilder:
    """WebSocket消息构建器，提供统一的消息创建接口"""

    @staticmethod
    def create_message(
        conversation_id: str,
        message_type: MessageType,
        text: str = "",
        is_finish: bool = False,
        object: dict = None,
        status: bool = True,
        agent: AgentMessage = None
    ) -> WebSocketMessage:
        """创建统一格式的消息
        
        Args:
            conversation_id: 会话ID
            message_type: 消息类型
            text: 文本内容
            is_finish: 是否结束
            object: 附加对象数据
            status: 状态（成功/失败）
            agent: Agent信息（如果是子agent发送的消息）
        """
        return WebSocketMessage(
            conversation_id=conversation_id,
            is_finish=is_finish,
            type=message_type.value,
            text=text,
            object=object or {},
            status=status,
            agent=agent
        )
    
    @staticmethod
    def create_chunk_message(conversation_id: str, text: str, content_type: str = "content", agent: AgentMessage = None) -> WebSocketMessage:
        """创建流式响应文本块消息"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.CHUNK,
            text=text,
            is_finish=False,
            object={"content_type": content_type},
            agent=agent
        )

    @staticmethod
    def create_segment_message(conversation_id: str, text: str, reasoning_content: str = "", agent: AgentMessage = None) -> WebSocketMessage:
        """创建完整响应片段消息"""
        segment_object = {}
        if reasoning_content:
            segment_object["reasoning_content"] = reasoning_content
            
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.SEGMENT,
            text=text,
            is_finish=True,
            object=segment_object,
            agent=agent
        )

    @staticmethod
    def create_tool_call_message(conversation_id: str, tool_name: str, tool_call_id: str, tool_arguments: str, agent: AgentMessage = None) -> WebSocketMessage:
        """创建工具调用通知消息"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.TOOL_CALL,
            text=tool_name,
            is_finish=True,
            object={"tool_call_id": tool_call_id, "tool_name": tool_name,"tool_arguments": tool_arguments},
            agent=agent
        )

    @staticmethod
    def create_tool_response_message(conversation_id: str, tool_response, tool_name: str, tool_call_id: str, status: bool, agent: AgentMessage = None, error_object: Optional[dict] = None) -> WebSocketMessage:
        """创建工具执行结果消息

        Args:
            tool_response: 给 LLM 看的执行结果（字符串或 dict）
            error_object: 失败时附带的结构化错误，前端据此渲染错误 UI / 重试按钮。
                          字段：code / message / hint / retryable / metadata
        """
        obj: dict = {
            "tool_call_id": tool_call_id,
            "tool_name": tool_name,
            "tool_response": tool_response,
        }
        if error_object:
            obj["error_object"] = error_object
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.TOOL_RESPONSE,
            text=tool_name,
            is_finish=True,
            object=obj,
            status=status,
            agent=agent
        )

    @staticmethod
    def create_title_message(conversation_id: str, title: str) -> WebSocketMessage:
        """创建对话标题生成消息"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.TITLE,
            text=title,
            is_finish=True,
            object={"title": title}
        )

    @staticmethod
    def create_question_message(conversation_id: str, questions: list) -> WebSocketMessage:
        """创建自动问题建议消息"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.QUESTION,
            text="",
            is_finish=True,
            object={"questions": questions}
        )

    @staticmethod
    def create_exit_message(conversation_id: str, agent: AgentMessage = None) -> WebSocketMessage:
        """创建退出消息"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.EXIT,
            text="",
            is_finish=True,
            object={"exit": True},
            agent=agent
        )

    @staticmethod
    def create_error_message(conversation_id: str, error_message: str, agent: AgentMessage = None) -> WebSocketMessage:
        """创建错误消息"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.ERROR,
            text=error_message,
            is_finish=True,
            object={"error": True, "message": error_message},
            status=False,
            agent=agent
        )
    
    @staticmethod
    def create_agent_start_message(conversation_id: str, agent_id: str, task: str = None, agent: AgentMessage = None) -> WebSocketMessage:
        """创建开始消息（用于agent开始执行）
        
        Args:
            conversation_id: 会话ID
            agent_id: Agent ID
            task: 任务文本（可选）
            agent: Agent消息对象
        """
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.START,
            text=task or agent_id,  # 优先使用任务文本，没有则使用agent_id
            is_finish=True,
            object={"agent_id": agent_id, "task": task} if task else {"agent_id": agent_id},
            agent=agent
        )
    
    @staticmethod
    def create_agent_complete_message(conversation_id: str,agent: AgentMessage = None) -> WebSocketMessage:
        """创建完成消息（用于agent执行完成）"""
        return MessageBuilder.create_message(
            conversation_id=conversation_id,
            message_type=MessageType.COMPLETE,
            text="",
            is_finish=True,
            object={"complete": True},
            agent=agent
        )

class WebSocketHandler:
    """处理WebSocket连接和消息"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # 初始化日志记录器
        self.logger = ManagerLogger("WebSocketHandler")

    async def connect(self, websocket: WebSocket, conversation_id: str):
        """建立WebSocket连接

        注意：此方法假设WebSocket连接已经在调用方被接受
        """
        self.active_connections[conversation_id] = websocket
        self.logger.info("WebSocket连接已建立", {"conversation_id": conversation_id})

    async def disconnect(self, conversation_id: str):
        """断开WebSocket连接"""
        if conversation_id in self.active_connections:
            #await self.active_connections[conversation_id].close()
            del self.active_connections[conversation_id]
            self.logger.info("WebSocket连接已断开", {"conversation_id": conversation_id})

    async def send_message(self, conversation_id: str, message):
        """发送消息到WebSocket客户端"""
        if conversation_id in self.active_connections:
            try:
                # 如果传入的是WebSocketMessage对象，自动转为json
                if isinstance(message, WebSocketMessage):
                    await self.active_connections[conversation_id].send_text(message.to_json())
                else:
                    await self.active_connections[conversation_id].send_text(message)
            except Exception as e:
                self.logger.error("发送消息失败，清理连接", exception=e, extra_data={"conversation_id": conversation_id})
                await self.disconnect(conversation_id)
                # 重新抛出异常，让调用方知道发送失败
        else:
            self.logger.warning("WebSocket连接不存在，无法发送消息", extra_data={"conversation_id": conversation_id})
            # 抛出异常表示连接不存在
            raise ConnectionError(f"WebSocket连接不存在: {conversation_id}")

    async def receive_message(self, conversation_id: str) -> Optional[str]:
        """从WebSocket客户端接收消息"""
        if conversation_id in self.active_connections:
            try:
                message = await self.active_connections[conversation_id].receive_text()
                self.logger.debug("接收到消息", {"conversation_id": conversation_id, "message": message})
                return message
            except Exception as e:
                self.logger.error("接收消息失败", exception=e, extra_data={"conversation_id": conversation_id})
                await self.disconnect(conversation_id)
        return None

    def is_connected(self, conversation_id: str) -> bool:
        """检查WebSocket连接是否仍然活跃
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            bool: 连接是否活跃
        """
        if conversation_id not in self.active_connections:
            return False
        
        # 检查WebSocket连接的实际状态
        websocket = self.active_connections[conversation_id]
        try:
            # 检查WebSocket的client_state是否为CONNECTED
            if websocket.client_state == WebSocketState.CONNECTED:
                return True
            else:
                # 连接已断开，主动清理
                self.logger.info("检测到WebSocket连接已断开，主动清理", {"conversation_id": conversation_id})
                # 异步清理连接（注意：这里不能用await，所以只清理字典）
                del self.active_connections[conversation_id]
                return False
        except Exception as e:
            # 检查连接状态时出错，认为连接已断开
            self.logger.debug("检查连接状态时出错，认为连接已断开", extra_data={"conversation_id": conversation_id, "error": str(e)})
            # 清理连接
            del self.active_connections[conversation_id]
            return False
    

    async def start_server(self):
        """启动WebSocket服务器

        注意：这个方法实际上不需要做任何事情，因为WebSocket服务器的启动
        是由FastAPI框架处理的。这个方法仅用于保持接口兼容性。
        """
        self.logger.info("WebSocket服务器已准备就绪")
