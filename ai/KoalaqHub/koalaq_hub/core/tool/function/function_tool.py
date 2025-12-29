"""
Function Calling 工具类定义
基于 OpenAI Function Calling 标准的工具表示
"""

from typing import Any, Dict, Optional


class FunctionTool:
    """表示 Function Calling 格式的工具"""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        strict: Optional[bool] = None
    ):
        """
        初始化 Function Tool
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 参数 schema，遵循 JSON Schema 规范
            strict: 是否严格模式（部分平台支持）
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {
            "type": "object",
            "properties": {},
            "required": []
        }
        self.strict = strict
    
    def to_openai_format(self) -> Dict[str, Any]:
        """
        转换为 OpenAI Function Calling 格式
        
        Returns:
            符合 OpenAI API 的工具定义
        """
        function_def = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
        
        # 部分平台支持 strict 参数
        if self.strict is not None:
            function_def["strict"] = self.strict
            
        return {
            "type": "function",
            "function": function_def
        }
