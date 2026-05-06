"""
工具基类和装饰器
提供工具定义的基础设施
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from .error_codes import E_INTERNAL, ToolError, make_error


@dataclass
class ToolParam:
    """工具参数定义"""
    name: str
    param_type: str  # string, number, boolean, object, array
    description: str
    required: bool = True
    enum: Optional[List[str]] = None  # 可选的枚举值列表
    default: Any = None
    items: Optional[Dict[str, Any]] = None  # array 类型的元素定义，如 {"type": "integer"}

    def to_schema(self) -> Dict[str, Any]:
        """转换为JSON Schema格式"""
        schema = {
            "type": self.param_type,
            "description": self.description
        }
        if self.enum:
            schema["enum"] = self.enum
        if self.param_type == "object":
            schema["additionalProperties"] = True
        if self.param_type == "array":
            # array 类型必须有 items 定义，否则部分模型会报错
            schema["items"] = self.items or {"type": "string"}
        return schema


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParam] = field(default_factory=list)
    tool_class: Optional[Type['BaseTool']] = None

    def to_function_calling_format(self, **dynamic_params) -> Dict[str, Any]:
        """转换为Function Calling格式

        Args:
            **dynamic_params: 动态参数，用于覆盖参数定义
                例如: agent_id_enum=["agent1", "agent2"] 会设置agent_id参数的enum值

        Returns:
            Function Calling格式的工具定义
        """
        properties = {}
        required = []

        for param in self.parameters:
            # 检查是否有动态参数覆盖
            enum_key = f"{param.name}_enum"
            param_schema = param.to_schema()

            if enum_key in dynamic_params:
                param_schema["enum"] = dynamic_params[enum_key]

            properties[param.name] = param_schema
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class BaseTool(ABC):
    """工具基类 - 所有内部工具都应继承此类"""

    # 子类需要设置的类属性
    name: str = ""
    description: str = ""
    parameters: List[ToolParam] = []

    def __init__(self):
        """初始化工具"""
        self._definition: Optional[ToolDefinition] = None

    @property
    def definition(self) -> ToolDefinition:
        """获取工具定义"""
        if self._definition is None:
            self._definition = ToolDefinition(
                name=self.name,
                description=self.description,
                parameters=self.parameters,
                tool_class=self.__class__
            )
        return self._definition

    @abstractmethod
    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具

        Args:
            arguments: LLM传入的工具参数
            context: 执行上下文，包含：
                - conversation_id: 会话ID
                - user_id: 用户ID
                - agent: 当前Agent实例
                - 其他可能的上下文信息

        Returns:
            执行结果字典，包含：
                - success: bool - 是否成功
                - result: Any - 执行结果（成功时）
                - error: str - 错误信息（失败时）
                - metadata: dict - 额外元数据（可选）
        """
        pass

    def validate_arguments(self, arguments: Dict[str, Any]) -> Optional[str]:
        """验证参数

        Args:
            arguments: 待验证的参数

        Returns:
            错误信息，如果验证通过则返回None
        """
        for param in self.parameters:
            if param.required and param.name not in arguments:
                return f"缺少必要参数: {param.name}"

            if param.name in arguments and param.enum:
                value = arguments[param.name]
                if value not in param.enum:
                    return f"参数 {param.name} 的值 '{value}' 不在允许的范围内: {param.enum}"

        return None

    def _success(self, result: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创建成功响应"""
        response = {
            "success": True,
            "result": result
        }
        if metadata:
            response["metadata"] = metadata
        return response

    def _error(
        self,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        *,
        code: Optional[str] = None,
        message: Optional[str] = None,
        hint: Optional[str] = None,
        retryable: Optional[bool] = None,
        error_obj: Optional[ToolError] = None,
    ) -> Dict[str, Any]:
        """创建结构化错误响应。

        三种调用方式（优先级递减）：

        1) 直接传 ToolError 对象：
           ``self._error(error_obj=ToolError(...))``
        2) 用 code + 可选 message/hint/retryable 构造：
           ``self._error(code=E_TYPE_DISABLED)``
           ``self._error(code=E_NETWORK, message="无法连接", hint="稍后再试")``
        3) 旧风格的纯字符串（兼容历史代码，会被包成 E_INTERNAL）：
           ``self._error(error="something failed")``

        返回字典字段：
          - ``success: False``
          - ``error: <给 LLM 看的字符串，含 message + hint>``
          - ``error_object: <ToolError dict，传到前端做结构化展示>``
          - ``metadata: <可选，调试信息>``
        """
        # 1. 直接对象优先
        if error_obj is not None:
            err = error_obj
        # 2. 显式 code
        elif code is not None:
            err = make_error(code, message=message, hint=hint, retryable=retryable, metadata=metadata)
        # 3. 旧风格字符串
        else:
            err = make_error(
                E_INTERNAL,
                message=error or "操作失败",
                hint="请告知用户具体情况，或联系开发者排查。",
                retryable=False,
                metadata=metadata,
            )

        # 给 LLM 看的字符串：拼 message + hint，方便模型据此自我修复
        llm_text = err.message
        if err.hint:
            llm_text = f"{llm_text}（{err.hint}）"

        response: Dict[str, Any] = {
            "success": False,
            "error": llm_text,
            "error_object": err.to_dict(),
        }
        if err.metadata:
            response["metadata"] = err.metadata
        return response


def tool(name: str, description: str, parameters: Optional[List[ToolParam]] = None):
    """工具装饰器 - 用于快速定义工具

    使用方式:
    ```python
    @tool(
        name="my_tool",
        description="我的工具描述",
        parameters=[
            ToolParam(name="arg1", param_type="string", description="参数1"),
        ]
    )
    class MyTool(BaseTool):
        async def execute(self, arguments, context):
            return self._success(result="done")
    ```
    """
    def decorator(cls: Type[BaseTool]) -> Type[BaseTool]:
        cls.name = name
        cls.description = description
        cls.parameters = parameters or []
        return cls
    return decorator
