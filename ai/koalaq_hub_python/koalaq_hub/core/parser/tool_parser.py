"""
工具解析器 - 从现有的tool_manager中迁移并优化工具解析逻辑
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .base_parser import BaseParser, CallType, ParseResult


@dataclass
class ToolCall(ParseResult):
    """工具调用结果"""
    tool_name: str
    arguments: Dict[str, Any]
    
    def __init__(self, tool_name: str, arguments: Dict[str, Any], 
                 raw_content: str, position: Tuple[int, int]):
        super().__init__(
            call_type=CallType.TOOL,
            raw_content=raw_content,
            position=position
        )
        self.tool_name = tool_name
        self.arguments = arguments
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base_dict = super().to_dict()
        base_dict.update({
            "tool": self.tool_name,
            "arguments": self.arguments
        })
        return base_dict


class ToolParser(BaseParser):
    """工具调用解析器"""
    
    def __init__(self):
        super().__init__()
        # 预编译正则表达式以提高性能
        self._code_block_pattern = re.compile(r"```tool\s*\n(.*?)\n```", re.DOTALL)
        self._json_pattern = re.compile(r'\{[^{}]*"tool"[^{}]*"arguments"[^{}]*\}')
    
    def parse(self, content: str) -> Tuple[str, List[ToolCall], bool]:
        """
        解析工具调用
        
        支持的格式：
        1. ```tool 代码块
        2. JSON格式: {"tool": "name", "arguments": {...}}
        3. 嵌套JSON格式（手工匹配大括号）
        """
        tools_found = []
        
        # 尝试不同的解析方式
        parsers = [
            self._parse_code_block_tool,
            self._parse_json_tool,
            self._parse_inline_json_tool,
        ]
        
        for parser in parsers:
            found_tools = parser(content)
            if found_tools:
                tools_found.extend(found_tools)
                # 找到一种格式就停止，避免重复解析
                break
        
        # 清理已解析的内容
        cleaned_content = self.remove_parsed_content(content, tools_found) if tools_found else content
        
        self.logger.info(f"解析到 {len(tools_found)} 个工具调用")
        return cleaned_content, tools_found, len(tools_found) > 0
    
    def can_parse(self, content: str) -> bool:
        """快速检查是否包含工具调用"""
        # 检查常见的工具调用标记
        return any([
            "```tool" in content,
            '"tool"' in content and '"arguments"' in content,
            '{"tool"' in content
        ])
    
    def _parse_code_block_tool(self, content: str) -> List[ToolCall]:
        """解析 ```tool 代码块格式"""
        tools = []
        
        for match in self._code_block_pattern.finditer(content):
            try:
                tool_data = json.loads(match.group(1).strip())
                
                # 处理嵌套的JSON字符串
                if isinstance(tool_data, str):
                    tool_data = json.loads(tool_data)
                
                if self._validate_tool_data(tool_data):
                    tools.append(ToolCall(
                        tool_name=tool_data["tool"],
                        arguments=tool_data.get("arguments", {}),
                        raw_content=match.group(0),
                        position=(match.start(), match.end())
                    ))
            except json.JSONDecodeError as e:
                self.logger.debug(f"代码块工具解析失败: {e}")
        
        return tools
    
    def _parse_json_tool(self, content: str) -> List[ToolCall]:
        """解析JSON格式的工具调用"""
        tools = []
        
        for match in self._json_pattern.finditer(content):
            try:
                tool_data = json.loads(match.group(0))
                
                if self._validate_tool_data(tool_data):
                    tools.append(ToolCall(
                        tool_name=tool_data["tool"],
                        arguments=tool_data.get("arguments", {}),
                        raw_content=match.group(0),
                        position=(match.start(), match.end())
                    ))
            except json.JSONDecodeError:
                self.logger.debug("JSON工具解析失败")
        
        return tools
    
    def _parse_inline_json_tool(self, content: str) -> List[ToolCall]:
        """解析嵌套JSON格式（手工匹配大括号）"""
        tools = []
        stack = []
        
        for i, c in enumerate(content):
            if c == "{":
                stack.append(i)
            elif c == "}" and stack:
                start = stack.pop()
                segment = content[start : i + 1]
                
                # 快速检查是否可能是工具调用
                if '"tool"' in segment and '"arguments"' in segment:
                    try:
                        tool_data = json.loads(segment)
                        
                        if self._validate_tool_data(tool_data):
                            tools.append(ToolCall(
                                tool_name=tool_data["tool"],
                                arguments=tool_data.get("arguments", {}),
                                raw_content=segment,
                                position=(start, i + 1)
                            ))
                    except json.JSONDecodeError:
                        continue
        
        return tools
    
    def _validate_tool_data(self, data: Any) -> bool:
        """验证工具数据格式"""
        if not isinstance(data, dict):
            return False
        
        # 必须包含tool字段
        if "tool" not in data:
            return False
        
        # tool名称必须是字符串
        if not isinstance(data["tool"], str):
            return False
        
        # arguments必须是字典（如果存在）
        if "arguments" in data and not isinstance(data.get("arguments"), dict):
            return False
        
        return True