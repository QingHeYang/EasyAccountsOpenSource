"""
Agent调用数据类
用于在系统内传递Agent调用信息
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AgentCall:
    """Agent调用信息"""
    agent_id: str
    task: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "agent_id": self.agent_id,
            "task": self.task,
            "context": self.context
        }
