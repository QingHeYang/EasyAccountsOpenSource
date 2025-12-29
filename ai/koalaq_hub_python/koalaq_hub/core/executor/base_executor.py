"""
基础执行器 - 定义执行器的通用接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..logging_utils import ManagerLogger


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseExecutor(ABC):
    """执行器基类"""
    
    def __init__(self):
        self.logger = ManagerLogger(self.__class__.__name__)
        
    @abstractmethod
    async def execute(self, call: Any, context: Dict[str, Any]) -> ExecutionResult:
        """
        执行调用
        
        Args:
            call: 要执行的调用（ToolCall或AgentCall）
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass
    
    
    def _create_success_result(self, result: Any, metadata: Dict[str, Any] = None) -> ExecutionResult:
        """创建成功结果"""
        return ExecutionResult(
            success=True,
            result=result,
            metadata=metadata or {}
        )
    
    def _create_error_result(self, error: str, metadata: Dict[str, Any] = None) -> ExecutionResult:
        """创建错误结果"""
        return ExecutionResult(
            success=False,
            result=None,
            error=error,
            metadata=metadata or {}
        )
    
    async def validate_context(self, context: Dict[str, Any]) -> bool:
        """
        验证执行上下文
        
        Args:
            context: 执行上下文
            
        Returns:
            bool: 上下文是否有效
        """
        required_fields = ["user_id", "conversation_id"]
        return all(field in context for field in required_fields)