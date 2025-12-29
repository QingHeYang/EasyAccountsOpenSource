"""
LLM 模型定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from ..config.settings import config


@dataclass
class LLM:
    """LLM 模型

    表示一个 LLM 配置实例，包含所有必要的连接和参数信息

    字段来源：
    - 数据库字段：llm_id, llm_config_name, platform, model, api_key, url, temperature, top_p, max_tokens, description
    - 运行时字段：timeout (from .env), think, think_max_tokens (from ini, 不入库)
    """

    # === 数据库字段（持久化） ===
    llm_id: str  # UUID 唯一标识符
    llm_config_name: str  # 配置名称（ini section 名，用于查找）
    api_key: str  # API 密钥
    url: str  # API URL
    model: str  # 模型名称
    platform: str  # 平台名称

    # 可选数据库字段
    temperature: float = 0.7  # 温度参数
    top_p: float = 1.0  # Top-p 参数
    max_tokens: int = 4096  # 最大 token 数
    description: str = ""  # LLM 描述

    # === 运行时字段（不入库） ===
    timeout: float = field(default_factory=lambda: config.llm_timeout)  # 超时时间，从 .env 读取
    think: bool = False  # 是否支持思维链
    think_max_tokens: int = 0  # 思维链最大 token 数

    # 时间字段
    created_at: Optional[datetime] = field(default_factory=datetime.now)

    @property
    def name(self) -> str:
        """兼容旧代码，name 等同于 llm_config_name"""
        return self.llm_config_name

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
        return f"LLM({self.llm_id}: {self.llm_config_name}, model={self.model}, platform={self.platform})"

    def __repr__(self) -> str:
        """详细表示"""
        return (
            f"LLM(llm_id='{self.llm_id}', llm_config_name='{self.llm_config_name}', "
            f"model='{self.model}', platform='{self.platform}', "
            f"url='{self.url}')"
        )