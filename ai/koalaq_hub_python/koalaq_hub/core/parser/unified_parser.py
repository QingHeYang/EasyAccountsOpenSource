"""
统一解析器 - 协调工具和Agent解析，作为解析器的统一入口
"""

from typing import Dict, List, Tuple

from ..logging_utils import ManagerLogger
from .agent_parser import AgentCall, AgentParser
from .base_parser import CallType, ParseResult
from .tool_parser import ToolCall, ToolParser


class UnifiedParser:
    """统一解析器 - 整合工具和Agent调用的解析"""
    
    def __init__(self):
        self.logger = ManagerLogger("UnifiedParser")
        
        # 初始化子解析器
        self.tool_parser = ToolParser()
        self.agent_parser = AgentParser()
        
        # 解析器优先级（可配置）
        self.parsers = [
            self.tool_parser,
            self.agent_parser
        ]
    
    def parse_response(self, content: str) -> Tuple[str, List[ParseResult], Dict[str, int]]:
        """
        解析响应内容，提取所有调用
        
        Args:
            content: 需要解析的内容
            
        Returns:
            Tuple[str, List[ParseResult], Dict[str, int]]:
            - 清理后的内容
            - 所有解析结果
            - 各类型调用的统计
        """
        all_results = []
        stats = {
            "tool": 0,
            "agent": 0
        }
        
        # 逐个解析器处理
        current_content = content
        for parser in self.parsers:
            if parser.can_parse(current_content):
                cleaned_content, results, has_results = parser.parse(current_content)
                
                if has_results:
                    all_results.extend(results)
                    current_content = cleaned_content
                    
                    # 统计各类型数量
                    for result in results:
                        stats[result.call_type.value] = stats.get(result.call_type.value, 0) + 1
        
        # 日志记录
        self.logger.info(
            "解析完成",
            extra_data={
                "total": len(all_results),
                "stats": stats
            }
        )
        
        return current_content, all_results, stats
    
    def has_any_calls(self, content: str) -> bool:
        """快速检查是否包含任何调用"""
        return any(parser.can_parse(content) for parser in self.parsers)
    
    def group_by_type(self, results: List[ParseResult]) -> Dict[CallType, List[ParseResult]]:
        """按类型分组解析结果"""
        grouped = {}
        
        for result in results:
            if result.call_type not in grouped:
                grouped[result.call_type] = []
            grouped[result.call_type].append(result)
        
        return grouped
    
    def extract_tool_calls(self, results: List[ParseResult]) -> List[ToolCall]:
        """提取所有工具调用"""
        return [r for r in results if isinstance(r, ToolCall)]
    
    def extract_agent_calls(self, results: List[ParseResult]) -> List[AgentCall]:
        """提取所有Agent调用"""
        return [r for r in results if isinstance(r, AgentCall)]
    
    def format_for_display(self, results: List[ParseResult]) -> str:
        """格式化解析结果用于显示"""
        if not results:
            return "无调用"
        
        lines = []
        grouped = self.group_by_type(results)
        
        for call_type, items in grouped.items():
            lines.append(f"\n{call_type.value.upper()} 调用 ({len(items)} 个):")
            
            for item in items:
                if isinstance(item, ToolCall):
                    lines.append(f"  - 工具: {item.tool_name}")
                    if item.arguments:
                        lines.append(f"    参数: {item.arguments}")
                        
                elif isinstance(item, AgentCall):
                    lines.append(f"  - Agent: {item.agent_id}")
                    lines.append(f"    任务: {item.task}")
        
        return "\n".join(lines)
    
    def validate_calls(self, results: List[ParseResult], available_tools: List[str] = None, 
                      available_agents: List[str] = None) -> Tuple[List[ParseResult], List[str]]:
        """
        验证调用的有效性
        
        Args:
            results: 解析结果
            available_tools: 可用工具列表
            available_agents: 可用Agent列表
            
        Returns:
            Tuple[List[ParseResult], List[str]]: (有效的调用, 错误信息列表)
        """
        valid_results = []
        errors = []
        
        for result in results:
            if isinstance(result, ToolCall):
                if available_tools and result.tool_name not in available_tools:
                    errors.append(f"工具 '{result.tool_name}' 不可用")
                else:
                    valid_results.append(result)
                    
            elif isinstance(result, AgentCall):
                if available_agents and result.agent_id not in available_agents:
                    errors.append(f"Agent '{result.agent_id}' 不可用")
                else:
                    valid_results.append(result)
            
            else:
                valid_results.append(result)
        
        return valid_results, errors