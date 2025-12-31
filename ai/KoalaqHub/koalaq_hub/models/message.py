import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MessageType(Enum):
    """消息类型枚举"""

    CONTENT = "content"
    TOOL_CALL = "tool_call"  # 统一的工具调用类型（包含 MCP 和 Function Calling）
    TOOL_RESULT = "tool_result"  # Function Calling 模式的 tool 角色消息
    ERROR = "error"
    AGENT_START = "agent_start"  # 子 Agent 开始执行
    AGENT_END = "agent_end"  # 子 Agent 执行结束


@dataclass
class Attachment:
    """VL 附件数据类（图片等）

    用于存储消息中的附件信息，支持图片等多模态内容。

    Attributes:
        filename: 文件名（用于前端展示和从文件服务获取）
        data: base64 编码的文件数据（用于 LLM 调用）
        media_type: MIME 类型，如 "image/png", "image/jpeg"
    """
    filename: str
    data: str  # base64 编码
    media_type: str = "image/png"

    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {
            "filename": self.filename,
            "data": self.data,
            "media_type": self.media_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Attachment":
        """从字典创建"""
        return cls(
            filename=data.get("filename", ""),
            data=data.get("data", ""),
            media_type=data.get("media_type", "image/png")
        )

    def to_llm_format(self) -> Dict[str, Any]:
        """转换为 LLM VL API 格式"""
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{self.media_type};base64,{self.data}"
            }
        }


@dataclass
class Message:
    """对话消息数据类

    表示对话中的一条消息，包含角色、内容、时间戳、会话ID、轮次ID和类型等信息。

    使用示例:
        # 创建普通内容消息
        msg = Message.create_content("user", "你好", "conv_001", "round_001")

        # 创建工具调用消息
        tool_msg = Message.create_tool_call("assistant", tool_data, "conv_001", "round_001")

        # 创建工具响应消息
        response_msg = Message.create_tool_response("assistant", response_data, "conv_001", "round_001")

        # 转换为字典（用于LLM交互）
        msg_dict = msg.to_dict()

        # 从字典创建消息
        msg = Message.from_dict({"role": "assistant", "content": "回复", "timestamp": "2024-01-20 10:00:00"})
    """

    role: str
    content: str
    timestamp: str
    round_id: str
    type: MessageType
    tool_success: bool = False
    reasoning_content: str = ""
    # Function Calling 相关字段
    tool_call_ids: str = ""  # 多个 tool_call_id 用 | 分隔
    tool_call_raw: str = ""  # tool_calls 的原始 JSON 字符串
    # Agent 相关字段
    agent_id: Optional[str] = None  # 子 Agent 的 ID
    # 新增字段
    tool_name: Optional[str] = None  # 工具名称（用于 TOOL_RESPONSE 类型）
    sub_conversation_id: Optional[str] = None  # 子会话 ID（用于 SUB_AGENT 类型）
    # 数据库相关字段
    message_id: Optional[int] = None  # 消息 ID（从数据库加载时会有）
    # Token 和模型信息
    total_tokens: Optional[int] = None  # 总 Token 数
    model: Optional[str] = None  # 模型名称
    # VL 附件（图片等）
    attachments: Optional[List[Attachment]] = None

    @property
    def tool_calls(self) -> Optional[List[Dict[str, Any]]]:
        """获取工具调用列表（从 tool_call_raw 解析）"""
        if self.tool_call_raw:
            try:
                return json.loads(self.tool_call_raw)
            except (json.JSONDecodeError, ValueError):
                return None
        return None
    
    @property
    def tool_call_id(self) -> Optional[str]:
        """获取单个 tool_call_id（用于 TOOL_RESULT 类型）"""
        # 对于 TOOL_RESULT 类型，tool_call_ids 应该只包含一个 ID
        if self.tool_call_ids:
            # 如果包含多个（用 | 分隔），返回第一个
            return self.tool_call_ids.split('|')[0]
        return None

    @classmethod
    def create_user_message(cls, content: str, round_id: str,
                           timestamp: Optional[str] = None,
                           attachments: Optional[List[Dict[str, Any]]] = None) -> "Message":
        """创建用户消息

        Args:
            content: 消息内容
            round_id: 轮次ID
            timestamp: 时间戳，如果为None则使用当前时间
            attachments: VL 附件列表（可选）

        Returns:
            Message实例
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            role="user",
            content=content,
            timestamp=timestamp,
            round_id=round_id,
            type=MessageType.CONTENT,
            attachments=attachments
        )

    @classmethod
    def create_assistant_message(cls, content: str, round_id: str, 
                                tool_calls: Optional[List[Dict[str, Any]]] = None,
                                reasoning_content: str = "", 
                                is_agent: bool = False,
                                agent_id: Optional[str] = None,
                                timestamp: Optional[str] = None) -> "Message":
        """创建助手消息
        
        Args:
            content: 消息内容
            round_id: 轮次ID
            tool_calls: 工具调用列表（可选）
            reasoning_content: 思维链内容（可选）
            is_agent: 是否是 Agent 调用
            agent_id: Agent ID（当 is_agent 为 True 时使用）
            timestamp: 时间戳
            
        Returns:
            Message实例
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 如果有 tool_calls，提取 tool_call_ids 并序列化
        if tool_calls:
            # 根据 is_agent 决定消息类型
            message_type = MessageType.AGENT_START if is_agent else MessageType.TOOL_CALL
            
            tool_call_ids = [tc["id"] for tc in tool_calls if "id" in tc]
            return cls(
                role="assistant",
                content=content or "",
                timestamp=timestamp,
                round_id=round_id,
                type=message_type,
                tool_call_ids="|".join(tool_call_ids),
                tool_call_raw=json.dumps(tool_calls, ensure_ascii=False),
                reasoning_content=reasoning_content,
                agent_id=agent_id
            )
        else:
            # 普通助手消息
            return cls(
                role="assistant",
                content=content,
                timestamp=timestamp,
                round_id=round_id,
                type=MessageType.CONTENT,
                reasoning_content=reasoning_content
            )
    
    @classmethod
    def create_tool_message(cls, tool_call_id: str, result: str, round_id: str,
                           success: bool = True, tool_name: Optional[str] = None,
                           timestamp: Optional[str] = None) -> "Message":
        """创建工具结果消息
        
        Args:
            tool_call_id: 工具调用ID
            result: 执行结果
            round_id: 轮次ID
            success: 执行是否成功
            tool_name: 工具名称
            timestamp: 时间戳
            
        Returns:
            Message实例
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            role="tool",
            content=result,
            timestamp=timestamp,
            round_id=round_id,
            type=MessageType.TOOL_RESULT,
            tool_call_ids=tool_call_id,  # 单个 tool_call_id
            tool_success=success,
            tool_name=tool_name
        )
    
    @classmethod
    def create_error_message(cls, error_message: str, round_id: str, timestamp: Optional[str] = None) -> "Message":
        """创建错误消息
        
        Args:
            error_message: 错误信息
            round_id: 轮次ID
            timestamp: 时间戳
            
        Returns:
            Message实例
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            role="error", 
            content=error_message, 
            timestamp=timestamp, 
            round_id=round_id, 
            type=MessageType.ERROR
        )
    
    @classmethod
    def create_sub_agent_message(cls, content: str, round_id: str, agent_id: str, 
                                sub_conversation_id: Optional[str] = None,
                                tool_call_id: Optional[str] = None,
                                timestamp: Optional[str] = None) -> "Message":
        """创建子 Agent 结束消息
        
        Args:
            content: 消息内容
            round_id: 轮次ID
            agent_id: 子 Agent 的 ID
            sub_conversation_id: 子会话 ID
            tool_call_id: 工具调用ID（当通过 Function Calling 调用时）
            timestamp: 时间戳，如果为None则使用当前时间
            
        Returns:
            Message实例
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return cls(
            role="tool",  # 使用 tool 角色（因为是 Function Calling 的响应）
            content=content,
            timestamp=timestamp,
            round_id=round_id,
            type=MessageType.AGENT_END,
            tool_call_ids=tool_call_id,  # 添加 tool_call_id
            agent_id=agent_id,
            sub_conversation_id=sub_conversation_id
        )

    def to_llm_content(self):
        """转换为 LLM API 需要的 content 格式

        如果有附件，返回 VL 格式的数组；否则返回纯文本字符串。

        Returns:
            str 或 List[Dict]: LLM content 格式
        """
        if not self.attachments:
            return self.content

        # VL 格式：content 是数组
        result = []

        # 先添加图片
        for att in self.attachments:
            result.append(att.to_llm_format())

        # 再添加文本
        if self.content:
            result.append({"type": "text", "text": self.content})

        return result

    def to_dict(self) -> dict:
        """转换为字典格式（用于LLM交互或存储）"""
        result = {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "round_id": self.round_id,
            "type": self.type.value,
            "tool_success": self.tool_success,
            "reasoning_content": self.reasoning_content,
            "tool_call_ids": self.tool_call_ids,
            "tool_call_raw": self.tool_call_raw,
        }
        if self.message_id is not None:
            result["message_id"] = self.message_id
        if self.agent_id:
            result["agent_id"] = self.agent_id
        if self.tool_name:
            result["tool_name"] = self.tool_name
        if self.sub_conversation_id:
            result["sub_conversation_id"] = self.sub_conversation_id
        if self.total_tokens is not None:
            result["total_tokens"] = self.total_tokens
        if self.model:
            result["model"] = self.model
        if self.attachments:
            result["attachments"] = [att.to_dict() for att in self.attachments]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """从字典创建消息实例"""
        # 处理 attachments 反序列化
        attachments_data = data.get("attachments")
        attachments = None
        if attachments_data:
            attachments = [Attachment.from_dict(att) for att in attachments_data]

        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            round_id=data.get("round_id", ""),
            type=MessageType(data.get("type", "content")),
            tool_success=data.get("tool_success", False),
            reasoning_content=data.get("reasoning_content", ""),
            tool_call_ids=data.get("tool_call_ids", ""),
            tool_call_raw=data.get("tool_call_raw", ""),
            agent_id=data.get("agent_id"),
            tool_name=data.get("tool_name"),
            sub_conversation_id=data.get("sub_conversation_id"),
            message_id=data.get("message_id"),
            total_tokens=data.get("total_tokens"),
            model=data.get("model"),
            attachments=attachments,
        )
    
