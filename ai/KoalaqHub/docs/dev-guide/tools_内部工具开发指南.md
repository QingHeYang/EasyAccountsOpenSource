# 内部工具开发指南

本文档介绍如何使用 `koalaq_hub.tools` 模块开发内部工具。

## 目录结构

```
koalaq_hub/tools/
├── __init__.py           # 包入口，导出公共接口
├── base.py               # 工具基类、参数定义、装饰器
├── registry.py           # 工具注册表（单例模式）
├── binder.py             # Agent-工具绑定器
├── executor.py           # 工具执行器
└── builtin/              # 内置工具目录
    ├── __init__.py       # 内置工具注册入口
    └── call_agent.py     # call_agent 工具示例
```

## 快速开始

### 1. 创建一个简单的内部工具

在 `tools/builtin/` 目录下创建新文件，例如 `my_tool.py`：

```python
from ..base import BaseTool, ToolParam, tool
from ..registry import register_tool


@register_tool
@tool(
    name="my_tool",
    description="这是我的工具，用于执行某个操作",
    parameters=[
        ToolParam(
            name="message",
            param_type="string",
            description="要处理的消息内容",
            required=True
        ),
        ToolParam(
            name="count",
            param_type="number",
            description="重复次数",
            required=False,
            default=1
        )
    ]
)
class MyTool(BaseTool):
    """我的工具实现"""

    async def execute(self, arguments: dict, context: dict) -> dict:
        """执行工具逻辑

        Args:
            arguments: LLM传入的参数
            context: 执行上下文

        Returns:
            执行结果字典
        """
        message = arguments.get("message")
        count = arguments.get("count", 1)

        # 执行业务逻辑
        result = message * count

        # 返回成功结果
        return self._success(result=result)
```

### 2. 注册工具

在 `tools/builtin/__init__.py` 中导入你的工具：

```python
def register_builtin_tools():
    """注册所有内置工具"""
    from . import call_agent
    from . import my_tool  # 添加这一行
```

### 3. 绑定到 Agent

如果工具需要根据 Agent 配置动态启用，修改 `tools/binder.py` 中的 `get_tools_for_agent` 方法。

## 核心概念

### ToolParam - 参数定义

```python
ToolParam(
    name="param_name",           # 参数名称
    param_type="string",         # 类型: string, number, boolean, object, array
    description="参数描述",       # 参数说明
    required=True,               # 是否必填
    enum=["opt1", "opt2"],       # 可选：枚举值列表
    default=None                 # 可选：默认值
)
```

### @tool 装饰器

```python
@tool(
    name="tool_name",            # 工具名称（LLM调用时使用）
    description="工具描述",       # 工具功能说明
    parameters=[...]             # 参数列表
)
```

### @register_tool 装饰器

自动将工具注册到全局 `ToolRegistry`，使其可被系统发现和调用。

### BaseTool 基类

所有内部工具必须继承 `BaseTool` 并实现 `execute` 方法：

```python
class BaseTool(ABC):
    # 类属性（由 @tool 装饰器设置）
    name: str
    description: str
    parameters: List[ToolParam]

    # 必须实现的方法
    async def execute(self, arguments: dict, context: dict) -> dict:
        pass

    # 辅助方法
    def _success(self, result, metadata=None) -> dict  # 创建成功响应
    def _error(self, error, metadata=None) -> dict     # 创建错误响应
    def validate_arguments(self, arguments) -> str     # 验证参数
```

## 执行上下文 (context)

`execute` 方法接收的 `context` 包含以下信息：

| 字段 | 类型 | 说明 |
|------|------|------|
| `conversation_id` | str | 当前会话ID |
| `user_id` | str | 用户ID |
| `agent` | Agent | 当前Agent实例 |
| `round_id` | str | 当前轮次ID |
| `recursion_depth` | int | 剩余递归深度 |
| `tool_timeout` | int | 工具执行超时时间 |
| `sub_agent_executor` | SubAgentExecutor | 子Agent执行器（如需调用其他Agent） |

## 返回值格式

### 成功响应

```python
return self._success(
    result="执行结果内容",           # 这个会返回给 LLM
    metadata={"extra_info": "..."}   # 这个不会返回给 LLM
)
# 返回: {"success": True, "result": "...", "metadata": {...}}
```

### 错误响应

```python
return self._error(
    error="错误描述",                # 这个会返回给 LLM
    metadata={"error_code": 500}     # 这个不会返回给 LLM
)
# 返回: {"success": False, "error": "...", "metadata": {...}}
```

### 关于 metadata

**重要：`metadata` 不会返回给 LLM！**

在批量执行时，只有 `result`（成功）或 `error`（失败）会被转成字符串返回给 LLM。

`metadata` 的用途：
- 供调用方（如 `BaseChatProcessor`）做额外处理
- 例如 `call_agent` 的 `sub_conversation_id` 用于存储到历史记录
- 日志记录、调试信息等

## 完整示例：数据库查询工具

```python
from ..base import BaseTool, ToolParam, tool
from ..registry import register_tool


@register_tool
@tool(
    name="query_database",
    description="查询数据库中的用户信息",
    parameters=[
        ToolParam(
            name="user_id",
            param_type="string",
            description="要查询的用户ID",
            required=True
        ),
        ToolParam(
            name="fields",
            param_type="array",
            description="要返回的字段列表",
            required=False
        )
    ]
)
class QueryDatabaseTool(BaseTool):
    """数据库查询工具"""

    async def execute(self, arguments: dict, context: dict) -> dict:
        user_id = arguments.get("user_id")
        fields = arguments.get("fields", ["name", "email"])

        # 从上下文获取数据库连接（如果需要）
        # db = context.get("database")

        try:
            # 模拟数据库查询
            user_data = {
                "user_id": user_id,
                "name": "张三",
                "email": "zhangsan@example.com"
            }

            # 过滤字段
            result = {k: v for k, v in user_data.items() if k in fields}

            return self._success(
                result=result,
                metadata={"query_fields": fields}
            )

        except Exception as e:
            return self._error(
                error=f"数据库查询失败: {str(e)}",
                metadata={"user_id": user_id}
            )
```

## 动态参数示例：带枚举的工具

参考 `call_agent` 的实现，枚举值可以在绑定时动态设置：

```python
# tools/builtin/select_model.py
@register_tool
@tool(
    name="select_model",
    description="选择要使用的模型",
    parameters=[
        ToolParam(
            name="model_id",
            param_type="string",
            description="模型ID",
            required=True,
            enum=[]  # 空列表，由 Binder 动态填充
        )
    ]
)
class SelectModelTool(BaseTool):
    async def execute(self, arguments: dict, context: dict) -> dict:
        model_id = arguments.get("model_id")
        return self._success(result=f"已选择模型: {model_id}")
```

```python
# tools/binder.py
def get_tools_for_agent(self, agent: Agent) -> List[Dict]:
    tools = []

    # 动态设置枚举值
    if agent.available_models:
        tool = self.registry.get("select_model")
        if tool:
            tools.append(tool.definition.to_function_calling_format(
                model_id_enum=agent.available_models
            ))

    return tools
```

## 调试与测试

### 手动测试工具

```python
from koalaq_hub.tools import tool_registry, tool_executor

# 检查工具是否已注册
print(tool_registry.list_tools())

# 获取工具定义
tool = tool_registry.get("my_tool")
print(tool.definition.to_function_calling_format())

# 手动执行工具
result = await tool_executor.execute(
    tool_name="my_tool",
    arguments={"message": "Hello", "count": 3},
    context={"conversation_id": "test", "user_id": "test_user"}
)
print(result)
```

### 检查工具是否为内部工具

```python
from koalaq_hub.tools import tool_executor

is_inner = tool_executor.is_inner_tool("my_tool")  # True
is_inner = tool_executor.is_inner_tool("mcp_tool")  # False
```

## 最佳实践

1. **命名规范**：工具名使用小写字母和下划线，如 `query_user`、`send_email`
2. **参数验证**：使用 `ToolParam` 的 `required` 和 `enum` 进行基础验证
3. **错误处理**：使用 try-catch 捕获异常，返回 `_error()` 而非抛出异常
4. **日志记录**：重要操作使用 `self.logger` 记录日志
5. **异步操作**：`execute` 是异步方法，可使用 `await` 调用其他异步函数
6. **上下文隔离**：不要修改 `context` 中的对象，避免副作用
