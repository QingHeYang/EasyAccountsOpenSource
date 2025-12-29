"""
工具格式转换器
在 MCP 工具和 Function Calling 工具之间进行转换
"""

import json
from typing import Any, Dict, List, Optional

from .function.function_tool import FunctionTool
from .mcp.mcp_tool import McpTool


class ToolConverter:
    """MCP Tool 和 Function Tool 之间的转换器"""
    
    @staticmethod
    def mcp_to_function(mcp_tool: McpTool) -> FunctionTool:
        """
        将 MCP 工具转换为 Function Calling 格式
        
        Args:
            mcp_tool: MCP 工具实例
            
        Returns:
            FunctionTool 实例
        """
        return FunctionTool(
            name=mcp_tool.name,
            description=mcp_tool.description,
            parameters=mcp_tool.input_schema
        )
    
    @staticmethod
    def function_to_mcp(function_tool: FunctionTool) -> McpTool:
        """
        将 Function Tool 转换为 MCP 格式
        
        Args:
            function_tool: Function Tool 实例
            
        Returns:
            McpTool 实例
        """
        return McpTool(
            name=function_tool.name,
            description=function_tool.description,
            input_schema=function_tool.parameters
        )
    
    @staticmethod
    def mcp_list_to_function_format(mcp_tools: List[McpTool]) -> List[Dict[str, Any]]:
        """
        将 MCP 工具列表转换为 OpenAI API 的 tools 参数格式
        
        Args:
            mcp_tools: MCP 工具列表
            
        Returns:
            符合 OpenAI API 的 tools 参数
        """
        return [
            ToolConverter.mcp_to_function(tool).to_openai_format()
            for tool in mcp_tools
        ]
    
    @staticmethod
    def parse_function_call(
        tool_call: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析 Function Calling 响应中的工具调用
        
        Args:
            tool_call: OpenAI API 返回的 tool_call 对象
            
        Returns:
            包含工具名称和参数的字典
        """
        function = tool_call.get("function", {})
        
        # 解析参数（可能是 JSON 字符串）
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                # 如果解析失败，保持原始字符串
                pass
        
        return {
            "tool_name": function.get("name"),
            "arguments": arguments,
            "call_id": tool_call.get("id")  # 保留调用 ID 用于关联响应
        }
    
    @staticmethod
    def parse_function_calls(
        message: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        从消息中提取所有工具调用
        
        Args:
            message: LLM 响应消息
            
        Returns:
            工具调用列表
        """
        tool_calls = message.get("tool_calls", [])
        if not tool_calls:
            return []
        
        return [
            ToolConverter.parse_function_call(call)
            for call in tool_calls
        ]
    
    @staticmethod
    def format_tool_response(
        tool_name: str,
        result: Any,
        call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        格式化工具执行结果为 Function Calling 响应格式
        
        Args:
            tool_name: 工具名称
            result: 执行结果
            call_id: 调用 ID（如果有）
            
        Returns:
            符合 OpenAI API 的工具响应消息
        """
        response = {
            "role": "tool",
            "content": str(result)
        }
        
        # 新版 API 需要 tool_call_id
        if call_id:
            response["tool_call_id"] = call_id
        else:
            # 兼容旧版，使用 name 字段
            response["name"] = tool_name
            
        return response
    
    @staticmethod
    def convert_mcp_response_to_text(
        tool_name: str,
        result: Any
    ) -> str:
        """
        将 MCP 工具执行结果转换为文本格式（用于非 Function Calling 场景）
        
        Args:
            tool_name: 工具名称
            result: 执行结果
            
        Returns:
            格式化的文本结果
        """
        return f"工具 {tool_name} 执行结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}"
    
    @staticmethod
    def function_calls_to_mcp_format(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将 Function Calling 格式的工具调用转换为 MCP 执行格式
        
        Args:
            tool_calls: LLM 返回的 tool_calls 列表
            
        Returns:
            转换后的 MCP 格式列表，每个元素包含：
            - tool_call_id: 工具调用ID
            - tool_name: 工具名称
            - arguments: 参数字典
        """
        mcp_calls = []
        
        for tool_call in tool_calls:
            # 获取 function 信息
            function = tool_call.get("function", {})
            
            # 解析参数
            arguments = function.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            
            mcp_calls.append({
                "tool_call_id": tool_call.get("id"),
                "tool_name": function.get("name"),
                "arguments": arguments
            })
        
        return mcp_calls