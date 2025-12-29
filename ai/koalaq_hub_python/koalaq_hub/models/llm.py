"""
LLM 模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class LLM:
    """LLM 模型
    
    表示一个 LLM 配置实例，包含所有必要的连接和参数信息
    """
    
    # 必需字段（无默认值）
    llm_id: str  # LLM 唯一标识符
    name: str  # LLM 名称
    api_key: str  # API 密钥
    url: str  # API URL
    model: str  # 模型名称
    platform: str  # 平台名称
    
    # 可选字段（有默认值）
    description: str = ""  # LLM 描述
    temperature: float = 0.7  # 温度参数
    top_p: float = 1.0  # Top-p 参数
    timeout: float = 120.0  # 超时时间（秒）
    max_tokens: int = 4096  # 最大 token 数
    think: bool = False  # 是否支持思维链
    think_max_tokens: int = 0  # 思维链最大 token 数
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    
    def to_llm_config(self) -> Dict[str, Any]:
        """转换为 LLMClient 需要的配置格式
        
        Returns:
            包含 LLM 配置的字典
        """
        return {
            "api_key": self.api_key,
            "url": self.url,
            "model": self.model,
            "platform": self.platform,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "timeout": self.timeout,
            "max_tokens": self.max_tokens,
            "think": self.think,
            "think_max_tokens": self.think_max_tokens,
            "description": self.description
        }
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"LLM({self.llm_id}: {self.name}, model={self.model}, platform={self.platform})"
    
    def __repr__(self) -> str:
        """详细表示"""
        return (
            f"LLM(llm_id='{self.llm_id}', name='{self.name}', "
            f"model='{self.model}', platform='{self.platform}', "
            f"url='{self.url}')"
        )