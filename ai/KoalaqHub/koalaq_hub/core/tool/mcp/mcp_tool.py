"""
MCP工具类定义
独立的工具类文件，避免循环引用
"""

from typing import Any, Dict


class McpTool:
    """表示MCP工具及其属性和格式化"""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: Dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """为LLM格式化工具信息

        Returns:
            描述工具的格式化字符串
        """
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = f"- {param_name}: {param_info.get('description', 'No description')}"
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""Tool: {self.name}
            Description: {self.description}
            Arguments:
            {chr(10).join(args_desc)}
            """