"""
前端消息返回模型
用于API接口返回给前端的消息格式定义
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FrontendMessageRole(str, Enum):
    """前端消息角色枚举"""
    
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    AGENT = "agent"


class TextContent(BaseModel):
    """文本内容模型"""
    
    content: str = Field(description="消息内容")
    reasoning_content: Optional[str] = Field(default="", description="思维链内容")


class ToolInfo(BaseModel):
    """工具信息模型"""
    
    tool_name: str = Field(description="工具名称")
    tool_arguments: str = Field(description="工具参数")
    tool_call_id: str = Field(description="工具调用ID")
    tool_result: str = Field(description="工具执行结果")
    tool_status: bool = Field(description="工具执行状态")
    completion_time: Optional[str] = Field(default=None, description="完成时间戳")
    execution_time: Optional[float] = Field(default=None, description="执行时长（秒）")


class SubAgentInfo(BaseModel):
    """子Agent信息模型"""
    
    agent_conversation_id: str = Field(description="Agent会话ID")
    agent_id: str = Field(description="Agent ID")
    agent_call_id: str = Field(description="Agent调用ID")
    agent_input: str = Field(description="Agent输入")
    agent_output: str = Field(description="Agent输出")
    agent_status: bool = Field(description="Agent执行状态")
    completion_time: Optional[str] = Field(default=None, description="完成时间戳")
    execution_time: Optional[float] = Field(default=None, description="执行时长（秒）")


class FrontendMessage(BaseModel):
    """前端消息模型"""
    
    round_id: str = Field(description="轮次ID")
    message_id: str = Field(description="消息ID")
    timestamp: str = Field(description="时间戳")
    role: FrontendMessageRole = Field(description="消息角色")
    
    # 文本内容（可选）
    text: Optional[TextContent] = Field(default=None, description="文本内容")
    
    # Token和模型信息（可选）
    token: Optional[int] = Field(default=None, description="Token数量")
    model: Optional[str] = Field(default=None, description="模型名称")
    
    # 工具信息（可选）
    tool: Optional[ToolInfo] = Field(default=None, description="工具信息")
    
    # 子Agent信息（可选）
    sub_agent: Optional[SubAgentInfo] = Field(default=None, description="子Agent信息")
    
    class Config:
        """Pydantic配置"""
        json_schema_extra = {
            "example": {
                "round_id": "round_001",
                "message_id": "msg_001",
                "timestamp": "2025-07-28 10:00:00",
                "role": "user",
                "text": {
                    "content": "你好",
                    "reasoning_content": ""
                },
                "token": 10,
                "model": "deepseek-chat"
            }
        }