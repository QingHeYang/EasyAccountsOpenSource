import datetime
from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    user_id: str
    username: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    extra_data: Optional[str] = None
    total_tokens: Optional[int] = 0
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    reasoning_tokens: Optional[int] = 0

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "username": self.username,
            "created_at": self.created_at,
            "extra_data": self.extra_data,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Conversation(BaseModel):
    conversation_id: str
    user_id: str
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: str
    updated_at: str
    tags: Optional[str] = None
    total_tokens: Optional[int] = 0
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    reasoning_tokens: Optional[int] = 0
    rounds_count: Optional[int] = 0
    application_name: Optional[str] = None
    is_agent_call: Optional[int] = 0
    parent_conversation_id: Optional[str] = None
    def to_dict(self):
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "rounds_count": self.rounds_count,
            "application_name": self.application_name,
            "is_agent_call": self.is_agent_call,
            "parent_conversation_id": self.parent_conversation_id,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Round(BaseModel):
    round_id: str
    conversation_id: str
    summary: Optional[str] = None
    created_at: str
    user_rating: Optional[int] = None
    extra_data: Optional[str] = None
    total_tokens: Optional[int] = 0
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    reasoning_tokens: Optional[int] = 0
    execution_time: Optional[float] = None

    def to_dict(self):
        return {
            "round_id": self.round_id,
            "conversation_id": self.conversation_id,
            "summary": self.summary,
            "created_at": self.created_at,
            "user_rating": self.user_rating,
            "extra_data": self.extra_data,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "execution_time": self.execution_time,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class SummarySnapshot(BaseModel):
    snapshot_id: int
    conversation_id: str
    based_on_round_id: str
    context_summary: str
    created_at: str

    def to_dict(self):
        return {
            "snapshot_id": self.snapshot_id,
            "conversation_id": self.conversation_id,
            "based_on_round_id": self.based_on_round_id,
            "context_summary": self.context_summary,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class Model(BaseModel):
    """模型统计数据模型"""

    model_id: Optional[int] = None
    platform: str  # 平台名称 (deepseek, tongyi, siliconflow等)
    model: str  # 模型名称 (deepseek-chat, qwen-plus等)
    total_tokens: int = 0  # 累计使用的token数量
    prompt_tokens: int = 0  # 累计使用的提示token数量
    completion_tokens: int = 0  # 累计使用的完成token数量
    reasoning_tokens: int = 0  # 累计使用的推理token数量
    request_count: int = 0  # 请求次数
    success_count: int = 0  # 成功次数
    error_count: int = 0  # 错误次数
    avg_response_time: float = 0  # 平均响应时间
    created_at: str
    updated_at: str

    def to_dict(self):
        return {
            "model_id": self.model_id,
            "platform": self.platform,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_response_time": self.avg_response_time,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class SummaryLog(BaseModel):
    """总结日志数据模型"""

    log_id: Optional[int] = None
    summary_content: str
    summary_result: Optional[str] = None
    status: str  # 'pending', 'success', 'failed'
    conversation_id: Optional[str] = None
    round_id: Optional[str] = None
    snapshot_id: Optional[int] = None
    platform: Optional[str] = None  # 平台名称
    model: Optional[str] = None  # 模型名称
    created_at: str
    updated_at: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    total_tokens: Optional[int] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    reasoning_tokens: Optional[int] = None

    def to_dict(self):
        return {
            "log_id": self.log_id,
            "summary_content": self.summary_content,
            "summary_result": self.summary_result,
            "status": self.status,
            "conversation_id": self.conversation_id,
            "round_id": self.round_id,
            "snapshot_id": self.snapshot_id,
            "platform": self.platform,
            "model": self.model,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "reasoning_tokens": self.reasoning_tokens,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
