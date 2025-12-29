"""
基础解析器类 - 定义解析器的通用接口和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

from ..logging_utils import ManagerLogger


class CallType(Enum):
    """调用类型枚举"""
    TOOL = "tool"           # 工具调用
    AGENT = "agent"         # Agent调用（可以是单个或多个）


@dataclass
class ParseResult:
    """解析结果基类"""
    call_type: CallType
    raw_content: str  # 原始内容
    position: Tuple[int, int]  # 在原文中的位置 (start, end)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "call_type": self.call_type.value,
            "raw_content": self.raw_content,
            "position": self.position
        }


class BaseParser(ABC):
    """解析器基类"""
    
    def __init__(self):
        self.logger = ManagerLogger(self.__class__.__name__)
    
    @abstractmethod
    def parse(self, content: str) -> Tuple[str, List[ParseResult], bool]:
        """
        解析内容，提取调用信息
        
        Args:
            content: 需要解析的内容
            
        Returns:
            Tuple[str, List[ParseResult], bool]: 
            - 清理后的内容（移除已解析的部分）
            - 解析结果列表
            - 是否包含可解析内容
        """
        pass
    
    @abstractmethod
    def can_parse(self, content: str) -> bool:
        """
        快速检查是否包含可解析的内容
        
        Args:
            content: 需要检查的内容
            
        Returns:
            bool: 是否包含可解析内容
        """
        pass
    
    def validate_result(self, result: ParseResult) -> bool:
        """
        验证解析结果是否有效
        
        Args:
            result: 解析结果
            
        Returns:
            bool: 是否有效
        """
        return result is not None and result.raw_content
    
    def remove_parsed_content(self, content: str, results: List[ParseResult]) -> str:
        """
        从原内容中移除已解析的部分
        
        Args:
            content: 原始内容
            results: 解析结果列表
            
        Returns:
            str: 清理后的内容
        """
        if not results:
            return content
            
        # 按位置排序（从后往前删除，避免位置偏移）
        sorted_results = sorted(results, key=lambda r: r.position[0], reverse=True)
        
        cleaned_content = content
        for result in sorted_results:
            start, end = result.position
            cleaned_content = cleaned_content[:start] + cleaned_content[end:]
            
        return cleaned_content.strip()