# API 接口文档

> 版本: 1.0
> 更新时间: 2025-12-08
> 状态: 正式版

## 一、概述

KoalaQ Hub 提供 REST API 和 WebSocket 两种接口方式。

### 基础信息

| 项目 | 值 |
|------|-----|
| 基础URL | `http://localhost:8001` |
| API版本 | `v1` |
| 认证方式 | Header: `user_id` |
| 内容类型 | `application/json` |

### 认证说明

大多数 API 需要在请求头中携带 `user_id`：

```http
GET /api/v1/conversations HTTP/1.1
Host: localhost:8001
user_id: your_user_id
```

**免认证端点**：
- `POST /api/v1/users/` - 创建用户
- `GET /api/v1/users/{user_id}` - 获取用户信息
- `POST /api/v1/conversations/apply_id` - 申请对话ID
- `GET /api/v1/agents/` - 获取Agent列表

---

## 二、统一响应格式

### 成功响应

```json
{
  "success": true,
  "code": "SUCCESS",
  "message": "操作成功",
  "data": { ... }
}
```

### 错误响应

```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "错误描述",
  "data": null
}
```

### 常见错误码

| HTTP状态码 | code | 说明 |
|------------|------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未认证或认证失败 |
| 404 | NOT_FOUND | 资源不存在 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 三、用户管理 API

**路由前缀**: `/api/v1/users`
**文件**: `api/endpoints/users.py`

### 3.1 创建用户

```http
POST /api/v1/users/
```

**请求体**:
```json
{
  "username": "用户名"
}
```

**响应**:
```json
{
  "success": true,
  "code": "CREATED",
  "message": "用户创建成功",
  "data": {
    "user_id": "user_xxxxxxxx",
    "username": "用户名",
    "created_at": "2025-01-01T00:00:00"
  }
}
```

---

### 3.2 获取用户信息

```http
GET /api/v1/users/{user_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "user_id": "user_xxx",
    "username": "用户名",
    "created_at": "2025-01-01T00:00:00",
    "total_tokens": 10000,
    "prompt_tokens": 7000,
    "completion_tokens": 3000,
    "reasoning_tokens": 0
  }
}
```

---

### 3.3 获取当前用户信息

```http
GET /api/v1/users/profile/me
```

**请求头**: `user_id: xxx` (必需)

**响应**: 同获取用户信息

---

### 3.4 获取用户列表

```http
GET /api/v1/users/list
```

**响应**:
```json
{
  "success": true,
  "data": [
    { "user_id": "xxx", "username": "xxx", ... },
    ...
  ]
}
```

---

## 四、对话管理 API

**路由前缀**: `/api/v1/conversations`
**文件**: `api/endpoints/conversations.py`

> 详见 [消息管理](./message_消息管理.md)

### 4.1 获取对话列表

```http
GET /api/v1/conversations/
```

**请求头**: `user_id: xxx` (必需)

**查询参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，从1开始，默认1 |
| page_size | int | 否 | 每页大小，1-100，默认20 |
| search | string | 否 | 搜索关键词 |
| application_names | list | 否 | 应用名称列表筛选 |

**响应**:
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "conversation_id": "conv_xxx",
        "user_id": "user_xxx",
        "title": "对话标题",
        "summary": "对话摘要",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T01:00:00",
        "application_name": "workorder-agent",
        "total_tokens": 1000,
        "rounds_count": 5
      }
    ],
    "pagination": {
      "current_page": 1,
      "page_size": 20,
      "total_count": 100,
      "total_pages": 5,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

---

### 4.2 获取对话详情

```http
GET /api/v1/conversations/{conversation_id}
```

**请求头**: `user_id: xxx` (必需)

---

### 4.3 获取对话消息

```http
GET /api/v1/conversations/{conversation_id}/messages
```

**请求头**: `user_id: xxx` (必需)

**查询参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| before_round_id | string | 否 | 分页：获取此轮次之前的消息 |
| limit | int | 否 | 每页数量，1-100，默认20 |

**响应**:
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "round_id": "round_xxx",
        "message_id": "123",
        "timestamp": "2025-01-01T00:00:00",
        "role": "user",
        "text": {
          "content": "用户消息内容",
          "reasoning_content": ""
        },
        "token": 100,
        "model": "deepseek-v3"
      },
      {
        "round_id": "round_xxx",
        "message_id": "124",
        "role": "assistant",
        "text": {
          "content": "AI回复内容",
          "reasoning_content": "推理过程..."
        }
      },
      {
        "round_id": "round_xxx",
        "message_id": "125_tc_xxx",
        "role": "tool",
        "tool": {
          "tool_name": "query_workorder",
          "tool_arguments": "{\"query\": \"...\"}",
          "tool_call_id": "call_xxx",
          "tool_result": "{\"data\": [...]}",
          "tool_status": true,
          "execution_time": 1.5
        }
      }
    ],
    "pagination": {
      "has_more": true,
      "last_round_id": "round_xxx",
      "limit": 20
    },
    "conversation_id": "conv_xxx",
    "title": "对话标题",
    "total_tokens": 5000,
    "rounds_count": 10
  }
}
```

---

### 4.4 申请对话ID

```http
POST /api/v1/conversations/apply_id
```

**响应**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
}
```

---

### 4.5 更新对话标题

```http
PUT /api/v1/conversations/{conversation_id}/title
```

**请求头**: `user_id: xxx` (必需)

**请求体**:
```json
{
  "title": "新标题"
}
```

---

### 4.6 删除对话

```http
DELETE /api/v1/conversations/{conversation_id}
```

**请求头**: `user_id: xxx` (必需)

**说明**: 软删除，设置 `enabled=0`

---

### 4.7 停止对话生成

```http
POST /api/v1/conversations/stop/{conversation_id}
```

**查询参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| cascade | bool | 否 | 是否级联停止子对话，默认true |

**响应**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_xxx",
    "stopped": true,
    "cascade": true
  },
  "message": "已发送停止信号（含子对话）"
}
```

---

### 4.8 获取对话统计

```http
GET /api/v1/conversations/statistics/overview
```

**请求头**: `user_id: xxx` (必需)

**响应**:
```json
{
  "success": true,
  "data": {
    "total_conversations": 50,
    "recent_conversations": 10,
    "last_activity": "2025-01-01T12:00:00",
    "has_conversations": true
  }
}
```

---

## 五、智能代理 API

**路由前缀**: `/api/v1/agents`
**文件**: `api/endpoints/agent.py`

### 5.1 获取Agent列表

```http
GET /api/v1/agents/
```

**响应**:
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "agent_id": "workorder-agent",
        "name": "工单智能体",
        "description": "工单查询分析",
        "enable": true,
        "enable_thinking": false,
        "enable_summary": true,
        "enable_auto_question": true,
        "llm_use": "deepseek-v3",
        "llm_think_use": null,
        "summary_llm_use": "deepseek-v3",
        "mcp_servers": ["cashway-ioms"],
        "agent_list": [],
        "has_tools": true,
        "has_sub_agents": false,
        "llm_memory_window": 10,
        "tool_round": 10
      }
    ],
    "total_count": 3
  }
}
```

---

### 5.2 获取Agent详情

```http
GET /api/v1/agents/{agent_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "agent_id": "workorder-agent",
    "name": "工单智能体",
    "description": "...",
    "enable": true,
    "features": {
      "enable_thinking": false,
      "enable_summary": true,
      "enable_auto_question": true
    },
    "llm_config": {
      "main_llm": "deepseek-v3",
      "thinking_llm": null,
      "summary_llm": "deepseek-v3",
      "memory_window": 10
    },
    "tool_config": {
      "mcp_servers": ["cashway-ioms"],
      "mcp_tool_black_list": [],
      "tool_round": 10,
      "tool_tokens": ["ioms_token"]
    },
    "sub_agents": {
      "agent_list": [],
      "has_sub_agents": false
    },
    "files": {
      "role_file": "恒银科技.role",
      "agent_guide": "",
      "task_instructions_file": "workorder_instructions.prompt"
    }
  }
}
```

---

### 5.3 获取Agent名称列表（简化版）

```http
GET /api/v1/agents/available/names
```

**用途**: 下拉选择等场景

**响应**:
```json
{
  "success": true,
  "data": {
    "agents": [
      {
        "agent_id": "workorder-agent",
        "name": "工单智能体",
        "description": "工单查询分析",
        "has_tools": true,
        "has_sub_agents": false
      }
    ],
    "total_count": 3
  }
}
```

---

### 5.4 获取所有Agent运行状态

```http
GET /api/v1/agents/status/all
```

**响应**:
```json
{
  "success": true,
  "data": {
    "loaded_agents": [
      {
        "agent_id": "workorder-agent",
        "name": "工单智能体",
        "is_active": true,
        "created_at": "2025-01-01T00:00:00",
        "last_used_at": "2025-01-01T12:00:00",
        "usage_count": 50,
        "tools_count": 5,
        "available_tools": ["tool1", "tool2", "tool3", "tool4", "tool5"],
        "memory_window": 10,
        "has_think_llm": false,
        "has_summary_llm": true
      }
    ],
    "total_loaded": 2,
    "registry_status": "active"
  }
}
```

---

### 5.5 获取指定Agent运行状态

```http
GET /api/v1/agents/status/{agent_id}
```

---

## 六、聊天 API

**路由前缀**: `/api/v1/chat`
**文件**: `api/endpoints/chat.py`

### 6.1 HTTP聊天（阻塞式）

```http
POST /api/v1/chat/chat
```

**请求头**: `user_id: xxx` (必需)

**请求体**:
```json
{
  "conversation_id": "conv_xxx",
  "app_id": "workorder-agent",
  "content": "用户消息内容",
  "use_think_llm": false,
  "is_mcp": false,
  "tool_tokens": "key1=value1|key2=value2"
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| conversation_id | string | 是 | 对话ID |
| app_id | string | 是 | Agent ID |
| content | string | 是 | 用户消息 |
| use_think_llm | bool | 否 | 是否使用思考模型 |
| is_mcp | bool | 否 | 是否MCP模式（单轮对话） |
| tool_tokens | string | 否 | 工具Token，格式：`key=value|key=value` |

**响应**:
```json
{
  "success": true,
  "data": {
    "content": "AI回复内容",
    "conversation_id": "conv_xxx",
    "round_id": "round_xxx"
  }
}
```

---

## 七、WebSocket API

**端点**: `/ws/chat`
**文件**: `api/endpoints/websocket.py`

> 详见 [WebSocket 运行流程](./websocket_运行流程.md)

### 7.1 连接

```
ws://localhost:8001/ws/chat?user_id=xxx&agent_id=xxx&tool_tokens=key1=value1|key2=value2
```

**查询参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| user_id | string | 是 | 用户ID |
| agent_id | string | 是 | Agent ID |
| tool_tokens | string | 否 | 工具Token |

### 7.2 发送消息

```json
{
  "conversation_id": "conv_xxx",
  "content": "用户消息",
  "use_think_llm": false
}
```

### 7.3 接收消息类型

| type | 说明 | 示例 |
|------|------|------|
| chunk | 流式文本块 | `{"type": "chunk", "text": "...", "is_finish": false}` |
| segment | 完整片段 | `{"type": "segment", "text": "...", "is_finish": true}` |
| tool_call | 工具调用 | `{"type": "tool_call", "text": "tool_name", "object": {...}}` |
| tool_response | 工具结果 | `{"type": "tool_response", "object": {"tool_result": ...}}` |
| title | 标题生成 | `{"type": "title", "text": "对话标题"}` |
| question | 推荐问题 | `{"type": "question", "object": {"questions": [...]}}` |
| error | 错误 | `{"type": "error", "text": "错误信息"}` |
| exit | 结束 | `{"type": "exit", "is_finish": true}` |

### 7.4 心跳

**发送**:
```json
{"type": "ping"}
```

**接收**:
```json
{"type": "pong"}
```

---

## 八、API 端点汇总

### 用户管理 `/api/v1/users`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/` | 创建用户 | 否 |
| GET | `/list` | 获取用户列表 | 否 |
| GET | `/profile/me` | 获取当前用户 | 是 |
| GET | `/{user_id}` | 获取用户信息 | 否 |

### 对话管理 `/api/v1/conversations`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | 获取对话列表 | 是 |
| GET | `/{id}` | 获取对话详情 | 是 |
| GET | `/{id}/messages` | 获取对话消息 | 是 |
| DELETE | `/{id}` | 删除对话 | 是 |
| PUT | `/{id}/title` | 更新标题 | 是 |
| POST | `/apply_id` | 申请对话ID | 否 |
| POST | `/stop/{id}` | 停止生成 | 否 |
| GET | `/statistics/overview` | 获取统计 | 是 |

### 智能代理 `/api/v1/agents`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/` | 获取Agent列表 | 否 |
| GET | `/{id}` | 获取Agent详情 | 否 |
| GET | `/available/names` | 获取Agent名称 | 否 |
| GET | `/status/all` | 获取运行状态 | 否 |
| GET | `/status/{id}` | 获取指定状态 | 否 |

### 聊天 `/api/v1/chat`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/chat` | HTTP聊天 | 是 |

### WebSocket

| 协议 | 路径 | 说明 |
|------|------|------|
| WS | `/ws/chat` | WebSocket聊天 |

---

## 九、扩展指南

### 9.1 添加新的 API 端点

**步骤 1**: 创建端点文件

```python
# api/endpoints/my_feature.py

from fastapi import APIRouter
from koalaq_hub.api.models.response import ResponseBuilder
from koalaq_hub.core.logging_utils import ManagerLogger

def create_my_feature_router(my_manager):
    """
    创建我的功能路由

    Args:
        my_manager: 功能管理器实例
    """
    router = APIRouter(prefix="/api/v1/my-feature", tags=["我的功能"])
    logger = ManagerLogger("MyFeatureEndpoint")

    @router.get("/")
    async def get_list():
        """获取列表"""
        try:
            data = my_manager.get_list()
            return ResponseBuilder.success(data=data)
        except Exception as e:
            logger.error("获取列表失败", exception=e)
            return JSONResponse(
                status_code=500,
                content=ResponseBuilder.internal_error("获取失败").dict()
            )

    # TODO: 添加更多端点...

    logger.info("我的功能路由初始化完成")
    return router
```

**步骤 2**: 注册路由

```python
# api/fastapi_app.py

from .endpoints.my_feature import create_my_feature_router

def create_fastapi_server(..., my_manager):
    # ...
    my_feature_router = create_my_feature_router(my_manager)
    app.include_router(my_feature_router)
```

**步骤 3**: 更新文档

在本文档的对应章节添加新 API 的说明。

### 9.2 API 文档模板

```markdown
## X. 功能名称 API

**路由前缀**: `/api/v1/xxx`
**文件**: `api/endpoints/xxx.py`

### X.1 接口名称

\`\`\`http
METHOD /api/v1/xxx/path
\`\`\`

**请求头**: `user_id: xxx` (必需/可选)

**查询参数**:

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| param1 | string | 是 | 描述 |

**请求体**:
\`\`\`json
{
  "field": "value"
}
\`\`\`

**响应**:
\`\`\`json
{
  "success": true,
  "data": { ... }
}
\`\`\`
```

---

## 十、文件位置索引

| 组件 | 文件路径 |
|------|----------|
| 用户端点 | `koalaq_hub/api/endpoints/users.py` |
| 对话端点 | `koalaq_hub/api/endpoints/conversations.py` |
| Agent端点 | `koalaq_hub/api/endpoints/agent.py` |
| 聊天端点 | `koalaq_hub/api/endpoints/chat.py` |
| WebSocket端点 | `koalaq_hub/api/endpoints/websocket.py` |
| 响应模型 | `koalaq_hub/api/models/response.py` |
| 前端消息模型 | `koalaq_hub/api/models/frontend_message.py` |
| FastAPI应用 | `koalaq_hub/api/fastapi_app.py` |

---

## 附录：更新日志

<!-- 新增API时在此记录 -->

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2025-12-08 | 1.0 | 初始版本，包含用户/对话/Agent/聊天/WebSocket API |
