# Tool 执行流程

本文档描述 KoalaQ Hub 工具系统的完整架构和执行流程。

## 快速索引

- 内部工具开发 → 第二节
- MCP工具配置 → 第三节
- 工具执行流程 → 第四节
- 文件位置索引 → 第七节

---

## 一、工具系统架构

### 1.1 两类工具

```
┌─────────────────────────────────────────────────────────────┐
│                       工具类型                               │
├──────────────────────────┬──────────────────────────────────┤
│      内部工具             │           MCP工具                 │
│   (Internal Tools)       │        (MCP Tools)               │
├──────────────────────────┼──────────────────────────────────┤
│ • 代码内定义              │ • 外部MCP服务器提供               │
│ • 装饰器注册              │ • SSE协议连接                    │
│ • 同进程执行              │ • 按需连接（用完即关）            │
├──────────────────────────┼──────────────────────────────────┤
│ 示例:                    │ 示例:                            │
│ • get_time (获取时间)     │ • query_device (设备查询)        │
│ • call_agent (调用子Agent)│ • query_history_workorder       │
│                          │ • create_excel_report            │
└──────────────────────────┴──────────────────────────────────┘
```

### 1.2 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                        工具注册                              │
├─────────────────────────────────────────────────────────────┤
│  ToolRegistry              ServerManager                    │
│  ├─ 单例模式               ├─ MCP服务器实例管理              │
│  ├─ 装饰器注册内部工具      ├─ 配置文件加载                   │
│  └─ name→tool映射          └─ 工具→服务器映射                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        工具绑定                              │
├─────────────────────────────────────────────────────────────┤
│  AgentToolBinder                                            │
│  ├─ 根据agent.inner_tools配置绑定内部工具                    │
│  ├─ 根据agent.agent_list动态构建call_agent工具              │
│  └─ 输出Function Calling格式                                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        工具执行                              │
├─────────────────────────────────────────────────────────────┤
│  ToolExecutor (内部)       McpToolExecutor (MCP)            │
│  ├─ JSON参数解析           ├─ 获取服务器映射                 │
│  ├─ 参数验证               ├─ 按需SSE连接                    │
│  └─ 调用tool.execute()     └─ 超时控制                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、内部工具系统

### 2.1 目录结构

```
koalaq_hub/tools/
├── __init__.py          # 导出register_builtin_tools()
├── base.py              # BaseTool基类、@tool装饰器、ToolParam
├── registry.py          # ToolRegistry单例、@register_tool装饰器
├── binder.py            # AgentToolBinder（工具绑定到Agent）
├── executor.py          # ToolExecutor（内部工具执行）
└── builtin/             # 内置工具目录
    ├── __init__.py      # 导出并注册内置工具
    ├── get_time.py      # 时间查询工具
    └── call_agent.py    # 调用子Agent工具
```

### 2.2 工具定义方式

```python
# 文件: koalaq_hub/tools/builtin/get_time.py

from typing import Any, Dict
from ..base import BaseTool, ToolParam, tool
from ..registry import register_tool

@register_tool                    # 注册到全局Registry
@tool(
    name="get_time",
    description="获取当前的日期、时间、星期几和时区信息",
    parameters=[
        ToolParam(
            name="timezone",
            param_type="string",
            description="时区名称，如 'Asia/Shanghai'",
            required=False
        )
    ]
)
class GetTimeTool(BaseTool):
    """获取时间的内部工具"""

    async def execute(self, arguments: Dict[str, Any],
                      context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工具逻辑

        Args:
            arguments: LLM传入的参数 {"timezone": "Asia/Shanghai"}
            context: 执行上下文 {"user_id", "conversation_id", "agent", ...}

        Returns:
            {"success": True, "result": "..."}
            或 {"success": False, "error": "..."}
        """
        timezone = arguments.get("timezone")
        # ... 业务逻辑 ...
        return self._success(result="当前时间是...")
```

### 2.3 工具注册流程

```
应用启动
    ↓
__main__.py: register_builtin_tools()
    ↓
koalaq_hub/tools/__init__.py
    ↓
from .builtin import get_time, call_agent
    ↓
@register_tool 装饰器执行
    ↓
ToolRegistry.register(tool_instance)
    ↓
存储到 _tools: Dict[name, BaseTool]
```

### 2.4 Agent绑定配置

```ini
# resource/config/agent.ini

[workorder-agent]
# 指定该Agent可用的内部工具
inner_tools = ["get_time"]

# 指定可调用的子Agent（自动生成call_agent工具）
agent_list = ["sub-agent-1", "sub-agent-2"]
```

### 2.5 工具绑定流程

```
AgentRegistry.build_tools_list(agent)
    ↓
AgentToolBinder.get_tools_for_agent(agent)
    │
    ├─ 遍历 agent.inner_tools
    │      ↓
    │  ToolRegistry.get_tool_definition(name)
    │      ↓
    │  转换为 Function Calling 格式
    │
    └─ 检查 agent.agent_list
           ↓
       动态构建 call_agent 工具
       (enum 填充为可调用的agent_id列表)
    ↓
返回 tools: List[Dict]  # OpenAI Function Calling格式
```

### 2.6 内部工具执行流程

```
LLM返回 tool_calls
    ↓
BaseChatProcessor._execute_tool_calls()
    ↓
判断: is_inner_tool(tool_name)?
    ↓ Yes
ToolExecutor.execute(tool_name, arguments, context)
    │
    ├─ JSON解析arguments（如果是字符串）
    │
    ├─ ToolRegistry.get(tool_name)
    │
    ├─ tool.validate_arguments(arguments)
    │
    └─ tool.execute(arguments, context)
           ↓
       返回 {"success": True, "result": "..."}
```

---

## 三、MCP工具系统

### 3.1 目录结构

```
koalaq_hub/core/tool/mcp/
├── __init__.py
├── server_manager.py    # MCP服务器管理
├── server_simple.py     # 按需连接的服务器封装
├── mcp_tool.py          # McpTool数据类
└── mcp_tool_manager.py  # 工具筛选和黑名单

resource/mcp/
├── cashway-ioms.json           # 实际配置（被.gitignore忽略）
└── cashway-ioms.example.json   # 配置模板
```

### 3.2 MCP配置文件格式

```json
// resource/mcp/cashway-ioms.json
{
    "mcpServers": {
        "cashway-ioms": {
            "url": "http://192.168.30.202:3002/sse",
            "timeout": 60,
            "description": "恒银科技IOMS MCP服务器"
        }
    }
}
```

### 3.3 Agent配置MCP

```ini
# resource/config/agent.ini

[workorder-agent]
# MCP服务器列表（对应resource/mcp/下的json文件名）
mcp_servers = ["cashway-ioms"]

# 工具黑名单（禁止使用的工具）
mcp_tool_black_list = ["dangerous_tool"]
```

### 3.4 MCP初始化流程

```
应用启动 (__main__.py)
    ↓
ServerManager()
    ↓
initialize_all_servers()
    │
    ├─ 扫描 resource/mcp/*.json
    │  （跳过 *.example.json）
    │
    ├─ 解析配置文件
    │
    └─ 创建 SimpleServer 实例（不建立连接）
    ↓
refresh_tool_mapping()
    │
    ├─ 连接所有服务器
    │
    ├─ 获取工具列表
    │
    └─ 构建 tool_name → server_name 映射
    ↓
日志: "MCP工具加载完成，共 X 个工具"
```

### 3.5 SimpleServer 连接模式

```python
# 按需连接模式（非长连接）

async def execute_tool(self, tool_name: str, arguments: dict):
    """每次调用都创建新连接"""

    # 建立SSE连接
    async with sse_client(url=self.url, timeout=self.timeout) as transport:
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 执行工具
            result = await session.call_tool(tool_name, arguments)

            return result
    # 离开with块，连接自动关闭
```

**连接时序:**
```
工具调用1 ──→ SSE连接 ──→ 执行 ──→ 关闭
工具调用2 ──→ SSE连接 ──→ 执行 ──→ 关闭
```

### 3.6 MCP工具执行流程

```
LLM返回 tool_calls
    ↓
BaseChatProcessor._execute_tool_calls()
    ↓
判断: is_inner_tool(tool_name)?
    ↓ No (MCP工具)
McpToolExecutor.execute_batch(tool_calls, context)
    │
    ├─ 获取 tool_server_mapping
    │
    ├─ 查找 server = servers[server_name]
    │
    └─ server.execute_tool(tool_name, arguments)
           │
           ├─ 建立SSE连接
           ├─ session.call_tool()
           └─ 关闭连接
    ↓
返回结果给LLM
```

---

## 四、工具执行总流程

### 4.1 完整时序图

```
User          LLM           ChatProcessor      ToolExecutor    McpExecutor    MCP Server
 │             │                 │                  │              │              │
 │──message───>│                 │                  │              │              │
 │             │                 │                  │              │              │
 │             │<──tool_calls────│                  │              │              │
 │             │                 │                  │              │              │
 │             │                 │──分类判断────────>│              │              │
 │             │                 │  is_inner_tool?  │              │              │
 │             │                 │                  │              │              │
 │             │                 │   [内部工具]      │              │              │
 │             │                 │──────────────────>│              │              │
 │             │                 │                  │──execute()   │              │
 │             │                 │<──result─────────│              │              │
 │             │                 │                  │              │              │
 │             │                 │   [MCP工具]       │              │              │
 │             │                 │─────────────────────────────────>│              │
 │             │                 │                  │              │──SSE连接────>│
 │             │                 │                  │              │<──工具结果───│
 │             │                 │<─────────────────────────result─│              │
 │             │                 │                  │              │              │
 │             │                 │──存储结果到历史    │              │              │
 │             │                 │──发送tool_response│              │              │
 │             │                 │                  │              │              │
 │             │                 │   [递归调用LLM]   │              │              │
 │             │<────────────────│                  │              │              │
 │             │                 │                  │              │              │
```

### 4.2 工具分类判断

```python
# koalaq_hub/core/chat/base_chat_processor.py

for tc in tool_calls_list:
    tool_name = tc["function"]["name"]

    if self.inner_tool_executor.is_inner_tool(tool_name):
        # 内部工具 → ToolExecutor
        inner_tool_calls.append(tc)
    else:
        # MCP工具 → McpToolExecutor
        mcp_tool_calls.append(tc)
```

### 4.3 执行上下文

```python
execution_context = {
    "user_id": "user_xxx",
    "conversation_id": "conv_xxx",
    "round_id": "round_xxx",
    "agent": Agent,              # 当前Agent实例
    "recursion_depth": 10,       # 剩余工具调用次数
    "tool_timeout": 60,          # 工具执行超时（秒）
    "sub_agent_executor": ...,   # 用于call_agent
}
```

---

## 五、特殊工具: call_agent

### 5.1 工具定义

```python
# koalaq_hub/tools/builtin/call_agent.py

@register_tool
@tool(
    name="call_agent",
    description="调用其他智能助手来协助完成特定任务",
    parameters=[
        ToolParam(name="agent_id", param_type="string",
                  description="要调用的智能助手ID", required=True,
                  enum=[]),  # 动态填充
        ToolParam(name="task", param_type="string",
                  description="任务描述", required=True),
        ToolParam(name="context", param_type="object",
                  description="上下文信息", required=False),
    ]
)
class CallAgentTool(BaseTool):
    async def execute(self, arguments, context):
        sub_agent_executor = context.get("sub_agent_executor")
        agent_call = AgentCall(
            agent_id=arguments["agent_id"],
            task=arguments["task"],
            context=arguments.get("context", {})
        )
        result = await sub_agent_executor.execute(agent_call, context)
        return self._success(result=result.result)
```

### 5.2 动态enum填充

```python
# koalaq_hub/tools/binder.py

def get_tools_for_agent(self, agent: Agent) -> List[Dict]:
    tools = []

    # 处理call_agent（动态设置可调用的agent列表）
    if agent.agent_list:
        call_agent_def = self.get_tool_definition("call_agent")
        # 填充enum
        call_agent_def["function"]["parameters"]["properties"]["agent_id"]["enum"] = agent.agent_list
        tools.append(call_agent_def)

    return tools
```

### 5.3 子Agent执行流程

```
call_agent调用
    ↓
SubAgentExecutor.execute(agent_call, context)
    │
    ├─ 检查调用深度（max_call_depth=5）
    │
    ├─ 检查循环调用（防止A→B→A）
    │
    ├─ 创建子会话ID: conv_xxx_sub_abc123
    │
    ├─ AgentRegistry.build_sub_agent(agent_id)
    │      │
    │      └─ 简化配置:
    │         • enable_summary = False
    │         • enable_thinking = False
    │         • agent_list = []  # 防止再调用
    │         • tool_round = min(原值, 3)
    │
    └─ AgentExecutor.execute(sub_agent, message, ...)
           ↓
       返回子Agent响应
```

---

## 六、递归深度与调用栈

### 6.1 工具调用次数限制

```ini
# agent.ini
[workorder-agent]
tool_round = 10   # 单轮对话最多调用10次工具
```

```python
# 每次工具调用后递减
recursion_depth = recursion_depth - 1

if recursion_depth <= 0:
    return "工具调用额度已用完"
```

### 6.2 调用栈管理（防循环）

```python
# SubAgentExecutor

_call_stacks = {
    "conv_xxx": ["agent-a", "agent-b"]  # 当前调用栈
}

def _check_call_depth(self, conversation_id, agent_id):
    stack = self._call_stacks.get(conversation_id, [])

    # 深度检查
    if len(stack) >= self.max_call_depth:
        return False

    # 循环调用检查
    if agent_id in stack:
        return False

    return True
```

---

## 七、文件位置索引

### 7.1 内部工具相关

| 文件 | 路径 | 说明 |
|------|------|------|
| BaseTool | `koalaq_hub/tools/base.py` | 工具基类、@tool装饰器 |
| ToolRegistry | `koalaq_hub/tools/registry.py` | 工具注册表单例 |
| AgentToolBinder | `koalaq_hub/tools/binder.py` | Agent工具绑定 |
| ToolExecutor | `koalaq_hub/tools/executor.py` | 内部工具执行器 |
| GetTimeTool | `koalaq_hub/tools/builtin/get_time.py` | 时间查询工具 |
| CallAgentTool | `koalaq_hub/tools/builtin/call_agent.py` | 子Agent调用工具 |

### 7.2 MCP工具相关

| 文件 | 路径 | 说明 |
|------|------|------|
| ServerManager | `koalaq_hub/core/tool/mcp/server_manager.py` | MCP服务器管理 |
| SimpleServer | `koalaq_hub/core/tool/mcp/server_simple.py` | 按需连接封装 |
| ToolManager | `koalaq_hub/core/tool/mcp/mcp_tool_manager.py` | 工具筛选、黑名单 |
| McpTool | `koalaq_hub/core/tool/mcp/mcp_tool.py` | MCP工具数据类 |
| McpToolExecutor | `koalaq_hub/core/executor/tool_executor.py` | MCP工具执行器 |

### 7.3 执行流程相关

| 文件 | 路径 | 说明 |
|------|------|------|
| BaseChatProcessor | `koalaq_hub/core/chat/base_chat_processor.py` | 工具调用编排 |
| SubAgentExecutor | `koalaq_hub/core/executor/sub_agent_executor.py` | 子Agent执行 |
| ToolConverter | `koalaq_hub/core/tool/converter.py` | 格式转换 |

### 7.4 配置文件

| 文件 | 路径 | 说明 |
|------|------|------|
| Agent配置 | `resource/config/agent.ini` | inner_tools、mcp_servers配置 |
| MCP配置 | `resource/mcp/*.json` | MCP服务器地址配置 |

---

## 八、配置速查

### 8.1 给Agent添加内部工具

```ini
# resource/config/agent.ini
[my-agent]
inner_tools = ["get_time", "my_new_tool"]
```

### 8.2 给Agent添加MCP工具

```ini
# resource/config/agent.ini
[my-agent]
mcp_servers = ["cashway-ioms", "another-mcp"]
```

### 8.3 添加新的MCP服务器

```json
// resource/mcp/new-server.json
{
    "mcpServers": {
        "new-server": {
            "url": "http://xxx:3002/sse",
            "timeout": 60
        }
    }
}
```

### 8.4 开发新的内部工具

参考文档: [内部工具开发指南](./tools_内部工具开发指南.md)

---

> 文档版本: 3.0
> 更新时间: 2024-12
