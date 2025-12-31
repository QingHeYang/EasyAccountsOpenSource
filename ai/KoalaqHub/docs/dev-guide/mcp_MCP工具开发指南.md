# MCP 工具开发指南

> 版本: 1.0
> 更新时间: 2025-12-29
> 状态: 正式版

本文档介绍如何使用 `koalaq_hub.mcp` 模块开发 MCP (Model Context Protocol) 工具，供外部客户端（如 Cherry Studio、Claude Desktop 等）调用。

## 一、概述

### 什么是 MCP？

MCP (Model Context Protocol) 是一种标准协议，允许 AI 模型调用外部工具和服务。与内部工具不同，MCP 工具可以被任何支持 MCP 协议的客户端调用。

### 设计理念

```
MCP工具 = FastMCP框架 + @mcp.tool装饰器 + 工具函数
```

- **FastMCP**：Python MCP 服务器框架，简化工具开发
- **@mcp.tool**：装饰器，将函数注册为 MCP 工具
- **工具函数**：异步函数，实现具体业务逻辑

### 内部工具 vs MCP工具

| 特性 | 内部工具 | MCP工具 |
|------|----------|---------|
| 调用者 | KoalaqHub Agent | 外部MCP客户端 |
| 协议 | WebSocket/HTTP | MCP (SSE/HTTP) |
| 注册方式 | @register_tool + @tool | @mcp.tool |
| 上下文 | context字典 | FastMCP Context |
| 认证 | user_id请求头 | URL token参数 |

---

## 二、目录结构

```
koalaq_hub/mcp/
├── __init__.py              # 包入口
└── easyaccounts_server.py   # EasyAccounts MCP服务器
```

---

## 三、架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                       外部 MCP 客户端                                │
│         Cherry Studio / Claude Desktop / 其他MCP客户端              │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ SSE/HTTP
                                  │ /sse?token=xxx 或 /mcp?token=xxx
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI 应用                                 │
├─────────────────────────────────────────────────────────────────────┤
│  认证中间件                                                          │
│  ├─→ 检测 /sse 或 /mcp 路径                                         │
│  ├─→ 提取 URL token 参数                                            │
│  └─→ 调用 set_global_token() 保存                                   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastMCP 服务器                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │                    MCP Server Instance                   │       │
│  │                                                          │       │
│  │  @mcp.tool                                               │       │
│  │  async def accounts(ctx: Context) -> str                 │       │
│  │                                                          │       │
│  │  @mcp.tool                                               │       │
│  │  async def flows(ctx: Context, ...) -> str               │       │
│  │                                                          │       │
│  │  @mcp.tool                                               │       │
│  │  async def add_flow(ctx: Context, ...) -> str            │       │
│  │                                                          │       │
│  └─────────────────────────────────────────────────────────┘       │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      EasyAccounts 后端                               │
│                    (http://xxx:port/api/...)                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、快速开始

### 4.1 创建一个简单的 MCP 工具

```python
from fastmcp import Context, FastMCP

# 创建MCP服务器实例
mcp = FastMCP(
    name="MyService",
    instructions="我的服务描述"
)

@mcp.tool
async def hello_world(ctx: Context, name: str) -> str:
    """向用户问好。

    这是一个简单的示例工具，展示MCP工具的基本结构。

    Args:
        name: 用户名称，必填

    Returns:
        问候语
    """
    return f"Hello, {name}!"
```

### 4.2 带复杂参数的工具

```python
@mcp.tool
async def query_data(
    ctx: Context,
    start_date: str,
    end_date: str = None,
    limit: int = 100,
    tags: list[str] = None
) -> str:
    """查询数据记录。

    支持日期范围、数量限制和标签过滤。

    Args:
        start_date: 开始日期，格式yyyy-MM-dd，必填
        end_date: 结束日期，格式yyyy-MM-dd，可选
        limit: 返回数量上限，默认100
        tags: 标签列表，可选

    Returns:
        JSON格式的查询结果
    """
    import json

    result = {
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
        "tags": tags or [],
        "data": []
    }

    return json.dumps(result, ensure_ascii=False)
```

---

## 五、核心概念

### 5.1 FastMCP Context

`Context` 是 FastMCP 提供的上下文对象，包含请求相关信息：

```python
from fastmcp import Context
from fastmcp.server.dependencies import get_http_headers, get_http_request

@mcp.tool
async def my_tool(ctx: Context) -> str:
    # 获取HTTP请求对象
    request = get_http_request()

    # 获取HTTP Headers
    headers = get_http_headers()

    # 获取URL参数
    if request:
        token = request.query_params.get('token')

    return "result"
```

### 5.2 参数类型支持

FastMCP 支持以下参数类型：

| Python类型 | JSON Schema类型 | 示例 |
|-----------|----------------|------|
| `str` | string | `name: str` |
| `int` | integer | `count: int` |
| `float` | number | `amount: float` |
| `bool` | boolean | `enabled: bool` |
| `list[T]` | array | `tags: list[str]` |
| `Optional[T]` | nullable | `note: str = None` |

### 5.3 文档字符串规范

工具的 docstring 会自动提取为 MCP 工具描述，格式要求：

```python
@mcp.tool
async def example_tool(ctx: Context, param1: str, param2: int = 10) -> str:
    """工具简短描述（第一行，会作为工具名称后的说明）。

    详细说明段落。可以包含使用场景、注意事项等。
    这里的内容会展示在工具详情中。

    Args:
        param1: 参数1说明，必填
        param2: 参数2说明，默认值10

    Returns:
        返回值说明
    """
```

**重要**：工具描述的质量直接影响 LLM 调用工具的准确性！

---

## 六、Token 认证机制

### 6.1 全局 Token 存储

由于 SSE 连接时 token 在 URL 参数中，但工具调用通过单独的 POST 请求，需要全局存储 token：

```python
# 全局token存储（单用户模式）
_global_token: Optional[str] = None

def set_global_token(token: str) -> None:
    """设置全局token（由中间件调用）"""
    global _global_token
    _global_token = token

def get_global_token() -> Optional[str]:
    """获取全局token"""
    return _global_token
```

### 6.2 中间件集成

在 `fastapi_app.py` 的认证中间件中提取 token：

```python
# 白名单前缀
whitelist_prefixes = [
    "/mcp",       # MCP服务器
    "/sse",       # MCP SSE端点
    "/messages",  # MCP消息端点
    "/.well-known",
    "/register",
]

# 检测SSE连接并保存token
if request.url.path.startswith("/sse"):
    token = request.query_params.get("token")
    if token:
        set_global_token(token)
```

### 6.3 工具中获取 Token

```python
def get_token_from_context(ctx: Context) -> Optional[str]:
    """从MCP Context中获取token

    优先级：
    1. 全局token（SSE连接时设置）
    2. HTTP请求URL参数
    3. HTTP Headers
    """
    # 优先使用全局token
    token = get_global_token()
    if token:
        return token

    # Fallback: 从HTTP请求获取
    request = get_http_request()
    if request:
        token = request.query_params.get('token')

    # Fallback: 从Headers获取
    if not token:
        headers = get_http_headers()
        if headers:
            token = headers.get('authorization')
            if token and token.startswith('Bearer '):
                token = token[7:]

    return token
```

---

## 七、HTTP 客户端封装

### 7.1 创建 API 客户端

```python
class EasyAccountsClient:
    """EasyAccounts API 客户端"""

    def __init__(self, auth_token: Optional[str] = None):
        self.base_url = config.easyaccounts_url
        self.auth_token = auth_token

    def _build_headers(self, content_type: Optional[str] = None) -> dict:
        headers = {}
        if self.auth_token:
            headers["authorization"] = self.auth_token
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _handle_auth_error(self) -> dict:
        return {
            "error": "认证失败",
            "status": 401,
            "message": "请确保MCP连接URL中包含有效的token参数"
        }
```

### 7.2 在工具中使用客户端

```python
def _get_client(ctx: Context) -> EasyAccountsClient:
    """从Context获取客户端"""
    token = get_token_from_context(ctx)
    return EasyAccountsClient(auth_token=token)

@mcp.tool
async def accounts(ctx: Context) -> str:
    """查询账户列表"""
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/account/getAccount"

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                url,
                headers=client._build_headers()
            )

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error())

            return json.dumps(response.json(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"获取失败: {str(e)}"})
```

---

## 八、完整工具示例

### 8.1 查询工具示例

```python
@mcp.tool
async def flows(
    ctx: Context,
    handle: int,
    accountId: int = None,
    startDate: str = None,
    endDate: str = None,
    note: str = None,
    types: list[int] = None,
    orderBy: int = None
) -> str:
    """根据条件查询流水记录。

    支持多种查询条件组合：日期范围、账户、分类、关键字等。

    使用场景：
    1. 查询某段时间的收支情况
    2. 查询特定分类的流水
    3. 按关键字搜索

    Args:
        handle: 收支类型：0=收入，1=支出，2=内部转账，3=全部。必填
        accountId: 账户ID，可选。使用accounts工具获取
        startDate: 开始日期，格式yyyy-MM-dd
        endDate: 结束日期，格式yyyy-MM-dd
        note: 备注关键字，模糊查询
        types: 分类ID列表。使用types工具获取
        orderBy: 排序方式：0=金额升序，1=金额降序，2=时间排序

    Returns:
        流水列表和收支汇总
    """
    try:
        # 参数验证
        if handle is None:
            return json.dumps({"error": "缺少必要参数: handle"})
        if int(handle) > 3 or int(handle) < 0:
            return json.dumps({"error": "handle参数错误"})

        client = _get_client(ctx)
        url = f"{client.base_url}/screen/getFlowByScreen"

        # 构建请求体
        payload = {
            "accountId": accountId,
            "chooseHandle": handle,
            "startDate": startDate,
            "endDate": endDate,
            "note": note,
            "types": types,
        }
        # 移除None值
        payload = {k: v for k, v in payload.items() if v is not None}

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            if response.status_code == 401:
                return json.dumps(client._handle_auth_error())

            # 处理响应数据
            data = response.json().get("data", {})

            # 格式化输出
            result = {
                "summary": f"收入={data.get('totalIn')}, 支出={data.get('totalOut')}",
                "flows": data.get("flows", [])
            }

            return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"})
```

### 8.2 写入工具示例

```python
@mcp.tool
async def add_flow(
    ctx: Context,
    accountId: int,
    typeId: int,
    actionId: int,
    money: str,
    fDate: str,
    note: str = None
) -> str:
    """添加一条流水记录。

    使用前请先：
    1. 用accounts获取账户ID
    2. 用types获取分类ID和actionId
    3. 用current_date获取日期

    Args:
        accountId: 账户ID，必填
        typeId: 分类ID，必填
        actionId: 收支动作ID，必填
        money: 金额，格式如'100.00'
        fDate: 流水日期，格式yyyy-MM-dd
        note: 备注，可选

    Returns:
        添加结果
    """
    try:
        client = _get_client(ctx)
        url = f"{client.base_url}/flow/addFlow"

        payload = {
            "accountId": accountId,
            "typeId": typeId,
            "actionId": actionId,
            "money": money,
            "fDate": fDate,
            "from": "mcp"
        }
        if note:
            payload["note"] = note

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(
                url,
                headers=client._build_headers(content_type="application/json"),
                json=payload
            )

            if response.status_code == 200:
                return json.dumps({
                    "success": True,
                    "message": "添加成功",
                    "data": response.json()
                })
            elif response.status_code == 401:
                return json.dumps(client._handle_auth_error())
            else:
                return json.dumps({"error": "添加失败"})

    except Exception as e:
        return json.dumps({"error": f"添加失败: {str(e)}"})
```

---

## 九、MCP 服务器配置

### 9.1 环境变量

在 `.env` 文件中配置：

```ini
# ===== MCP 服务器配置 =====
# 是否启用MCP服务器 (true/false)
MCP_SERVER_ENABLED=true

# MCP传输模式: sse 或 streamable-http
# - sse: Server-Sent Events，兼容性好，适合大多数客户端
# - streamable-http: 更高效，适合支持该协议的客户端
MCP_TRANSPORT_MODE=sse

# MCP连接地址:
# - SSE模式: http://{host}:{API_PORT}/sse?token=<your_token>
# - HTTP模式: http://{host}:{API_PORT}/mcp?token=<your_token>
```

### 9.2 传输模式选择

| 模式 | 端点 | 兼容性 | 性能 |
|------|------|--------|------|
| SSE | `/sse?token=xxx` | 高（Cherry Studio、Claude Desktop） | 一般 |
| Streamable HTTP | `/mcp?token=xxx` | 较低（需客户端支持） | 高 |

### 9.3 创建 MCP 应用

```python
def create_mcp_app(transport_mode: str = "sse"):
    """创建MCP ASGI应用"""
    if transport_mode == "streamable-http":
        return mcp.http_app(transport="streamable-http")
    else:
        return mcp.http_app(transport="sse")
```

---

## 十、集成到 FastAPI

### 10.1 挂载 MCP 服务器

在 `FastAPIServer.__init__` 中：

```python
def __init__(self, ...):
    # 创建MCP应用（需在FastAPI创建前）
    self.mcp_app = self._create_mcp_app()

    # 创建FastAPI，传入MCP的lifespan
    if self.mcp_app:
        self.app = FastAPI(
            title="KoalaQ Hub API",
            lifespan=self.mcp_app.lifespan  # 重要！
        )
    else:
        self.app = FastAPI(title="KoalaQ Hub API")

    # ... 其他配置

    # 挂载MCP服务器
    self._mount_mcp_server()

def _mount_mcp_server(self):
    """挂载MCP服务器到FastAPI"""
    if self.mcp_app:
        self.app.mount("/", self.mcp_app)
```

**重要**：必须将 `mcp_app.lifespan` 传递给 FastAPI，否则会出现 "Task group is not initialized" 错误！

---

## 十一、工具描述最佳实践

### 11.1 描述结构

```python
@mcp.tool
async def my_tool(ctx: Context, ...) -> str:
    """[简短描述：做什么，一句话]。

    [详细说明]
    [使用场景]
    [依赖说明：需要先调用哪些工具]
    [注意事项]

    Args:
        param1: [说明]，[必填/可选]。[如何获取]
        param2: [说明]，[格式要求]

    Returns:
        [返回内容说明]
    """
```

### 11.2 好的描述示例

```python
@mcp.tool
async def flows(ctx: Context, handle: int, ...) -> str:
    """根据条件查询流水记录。支持多种查询条件组合：日期范围、账户、分类、关键字等。返回符合条件的流水列表和收支汇总。

    使用场景：1.查询某段时间的收支情况 2.查询特定分类的流水 3.按关键字搜索 4.分析支出占比
    遇到无法确定的需求时，请先查询types、accounts工具获取必要的ID。

    Args:
        handle: 收支类型：0=收入，1=支出，2=内部转账，3=全部。必填
        accountId: 账户ID，可选。使用accounts工具获取
        startDate: 开始日期，格式yyyy-MM-dd
        ...
    """
```

### 11.3 描述要点

1. **第一行要完整**：LLM 主要看第一行决定是否使用工具
2. **说明参数来源**：如 "使用accounts工具获取"
3. **说明格式要求**：如 "格式yyyy-MM-dd"
4. **说明依赖关系**：如 "使用前请先调用current_date"
5. **说明使用场景**：帮助 LLM 判断何时使用

---

## 十二、现有工具清单

| 工具名 | 功能 | 必填参数 | 依赖工具 |
|--------|------|----------|----------|
| `accounts` | 查询账户列表 | 无 | 无 |
| `types` | 获取分类信息 | 无 | 无 |
| `current_date` | 获取当前日期 | 无 | 无 |
| `year_statistics` | 年度统计 | year | current_date |
| `flows` | 查询流水 | handle | accounts, types |
| `add_flow` | 添加流水 | accountId, typeId, actionId, money, fDate | accounts, types, current_date |
| `update_flow` | 更新流水 | flowId, accountId, typeId, actionId, money, fDate | flows, accounts, types |
| `make_excel` | 生成Excel报表 | excelName, handle | accounts, types |

---

## 十三、调试与测试

### 13.1 查看已注册工具

```python
from koalaq_hub.mcp.easyaccounts_server import mcp

# 获取所有工具
tools = mcp.list_tools()
for tool in tools:
    print(f"工具: {tool.name}")
    print(f"描述: {tool.description}")
    print(f"参数: {tool.parameters}")
```

### 13.2 使用 MCP 客户端测试

使用 Cherry Studio 或其他 MCP 客户端：

1. 添加 MCP 服务器连接：`http://localhost:8001/sse?token=your_token`
2. 查看可用工具列表
3. 测试工具调用

### 13.3 日志调试

```python
from koalaq_hub.core.logging_utils import ManagerLogger

logger = ManagerLogger("MCPServer")

@mcp.tool
async def my_tool(ctx: Context) -> str:
    logger.info("工具被调用")
    logger.debug("调试信息", {"param": "value"})
    # ...
```

---

## 十四、新增 MCP 工具指南

### 14.1 步骤总览

```
1. 在 easyaccounts_server.py 中添加工具函数
2. 使用 @mcp.tool 装饰器注册
3. 编写完整的 docstring
4. 测试工具功能
```

### 14.2 详细步骤

#### 步骤 1：添加工具函数

**文件**: `koalaq_hub/mcp/easyaccounts_server.py`

```python
@mcp.tool
async def my_new_tool(
    ctx: Context,
    required_param: str,
    optional_param: int = 10
) -> str:
    """工具描述。

    详细说明...

    Args:
        required_param: 参数说明，必填
        optional_param: 参数说明，默认10

    Returns:
        返回值说明
    """
    try:
        client = _get_client(ctx)
        # 实现业务逻辑
        result = {"data": "..."}
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})
```

#### 步骤 2：更新工具清单

在本文档第十二节添加新工具信息。

#### 步骤 3：测试

1. 重启 KoalaqHub 服务
2. 使用 MCP 客户端连接
3. 验证工具在列表中显示
4. 测试工具调用

---

## 十五、常见问题

### Q1: 工具调用时 token 为 None

**原因**：SSE 连接的 token 没有正确保存到全局变量

**解决**：
1. 确认中间件白名单包含 `/sse`
2. 确认 `set_global_token` 被正确调用
3. 检查日志确认 token 提取

### Q2: 出现 "Task group is not initialized" 错误

**原因**：FastAPI 没有使用 MCP 应用的 lifespan

**解决**：
```python
self.app = FastAPI(
    lifespan=self.mcp_app.lifespan  # 必须传入
)
```

### Q3: 客户端连接返回 400 Bad Request

**原因**：传输模式不匹配（客户端用 SSE，服务器用 Streamable HTTP）

**解决**：
```ini
# .env
MCP_TRANSPORT_MODE=sse
```

### Q4: 工具不在列表中显示

**原因**：
1. 工具函数没有 `@mcp.tool` 装饰器
2. 服务器没有重启

**解决**：
1. 确认装饰器正确添加
2. 重启服务

---

## 十六、文件位置索引

| 类型 | 文件路径 |
|------|----------|
| MCP 服务器 | `koalaq_hub/mcp/easyaccounts_server.py` |
| FastAPI 集成 | `koalaq_hub/api/fastapi_app.py` |
| 配置文件 | `.env` |
| 依赖声明 | `requirements.txt` (fastmcp>=2.0.0) |
