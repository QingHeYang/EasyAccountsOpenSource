# 项目代理图鉴

本文档详细说明 EasyAccounts Web 项目的代理架构，包括浏览器端和 AI IDE 端的请求流程。

---

## 一、整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  客户端层                                        │
│                                                                                 │
│   ┌───────────────────────────────┐    ┌───────────────────────────────────┐   │
│   │         浏览器端               │    │          AI IDE 端                 │   │
│   │                               │    │                                   │   │
│   │  ┌─────────┐ ┌─────────────┐  │    │  ┌─────────┐ ┌─────────────────┐  │   │
│   │  │ PC 端   │ │  移动端      │  │    │  │ Cursor  │ │  Cherry Studio  │  │   │
│   │  │ Vue     │ │  Vue        │  │    │  ├─────────┤ ├─────────────────┤  │   │
│   │  └────┬────┘ └──────┬──────┘  │    │  │ Cline   │ │  Claude Code    │  │   │
│   │       │             │         │    │  └────┬────┘ └────────┬────────┘  │   │
│   │       └──────┬──────┘         │    │       └───────┬───────┘           │   │
│   │              │                │    │               │                   │   │
│   │   HTTP / WebSocket            │    │         SSE / MCP                 │   │
│   │   /api  /ai-api  /ws          │    │        /sse  /mcp  /messages      │   │
│   └──────────────┼────────────────┘    └───────────────┼───────────────────┘   │
│                  │                                     │                        │
└──────────────────┼─────────────────────────────────────┼────────────────────────┘
                   │                                     │
                   ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              代理层                                              │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │  开发环境: Vite Dev Server (localhost:5173)                              │   │
│   │  生产环境: Nginx (Docker 容器: web:80)                                   │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│   路由规则:                                                                      │
│   ┌──────────────┬───────────────────┬────────────────────┬──────────────────┐  │
│   │ 请求路径      │ 开发环境目标        │ 生产环境目标        │ 客户端            │  │
│   ├──────────────┼───────────────────┼────────────────────┼──────────────────┤  │
│   │ /api/*       │ lllama.cn:10672   │ server:8081        │ 浏览器           │  │
│   │ /ai-api/*    │ localhost:8001    │ ai:8001            │ 浏览器           │  │
│   │ /ws/*        │ localhost:8001    │ ai:8001            │ 浏览器           │  │
│   │ /sse/*       │ localhost:8001    │ ai:8001            │ 浏览器 + AI IDE  │  │
│   │ /mcp/*       │ localhost:8001    │ ai:8001            │ 浏览器 + AI IDE  │  │
│   │ /messages/*  │ localhost:8001    │ ai:8001            │ 浏览器 + AI IDE  │  │
│   └──────────────┴───────────────────┴────────────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘
                   │                                     │
                   ▼                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              服务层                                              │
│                                                                                 │
│   ┌─────────────────────────┐    ┌─────────────────────────────────────────┐   │
│   │   EasyAccounts 后端      │    │              AI 服务                    │   │
│   │   (server:8081)         │    │            (ai:8001)                    │   │
│   │                         │    │                                         │   │
│   │   Spring Boot           │    │   ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│   │   ┌─────────────────┐   │    │   │  HTTP   │ │WebSocket│ │   SSE   │   │   │
│   │   │ 账户/流水/分析   │   │    │   │/api/v1/*│ │/ws/chat │ │ /sse/*  │   │   │
│   │   │ 用户认证        │   │    │   └─────────┘ └─────────┘ └─────────┘   │   │
│   │   │ 数据导出        │   │    │                                         │   │
│   │   └─────────────────┘   │    │   ┌─────────┐ ┌─────────────────────┐   │   │
│   │                         │    │   │   MCP   │ │     Messages        │   │   │
│   │   MySQL 数据库           │    │   │ /mcp/*  │ │    /messages/*      │   │   │
│   │                         │    │   └─────────┘ └─────────────────────┘   │   │
│   └─────────────────────────┘    └─────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、客户端类型说明

### 2.1 浏览器端

浏览器端是用户通过网页访问 EasyAccounts 的主要方式，支持 PC 端和移动端。

| 协议 | 路径前缀 | 用途 |
|------|----------|------|
| HTTP | `/api/*` | 后端业务 API（账户、流水、分析等） |
| HTTP | `/ai-api/*` | AI 服务 HTTP API |
| WebSocket | `/ws/*` | AI 实时聊天 |
| SSE | `/sse/*` | AI 流式响应 |
| MCP | `/mcp/*` | AI 工具调用 |

### 2.2 AI IDE 端

除了浏览器，AI IDE 和工具也会直接连接 AI 服务，使用 SSE 和 MCP 协议。

| 客户端 | 连接方式 | 说明 |
|--------|----------|------|
| **Cursor** | SSE + MCP | AI 代码编辑器，通过 MCP 调用工具 |
| **Cline** | SSE + MCP | VS Code AI 插件 |
| **Cherry Studio** | SSE + MCP | AI 对话工具 |
| **Claude Code** | SSE + MCP | Claude 官方 CLI 工具 |
| **其他 MCP 客户端** | SSE + MCP | 任何支持 MCP 协议的客户端 |

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AI IDE 连接流程                               │
│                                                                     │
│   Cursor / Cline / Cherry Studio                                   │
│           │                                                         │
│           ▼                                                         │
│   配置 MCP Server URL                                               │
│   例如: https://your-domain.com/mcp                                 │
│           │                                                         │
│           ▼                                                         │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │                    Nginx 代理                              │    │
│   │                                                           │    │
│   │   location /mcp/ {                                        │    │
│   │       proxy_pass http://ai:8001/mcp/;                     │    │
│   │       proxy_buffering off;      # 禁用缓冲                 │    │
│   │       proxy_read_timeout 86400s; # 24小时超时              │    │
│   │   }                                                       │    │
│   └───────────────────────────────────────────────────────────┘    │
│           │                                                         │
│           ▼                                                         │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │                    AI 服务 (ai:8001)                       │    │
│   │                                                           │    │
│   │   处理 MCP 请求:                                           │    │
│   │   - tools/list: 返回可用工具列表                            │    │
│   │   - tools/call: 执行工具调用                                │    │
│   │   - 返回 SSE 流式响应                                       │    │
│   └───────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 三、协议详解

### 3.1 HTTP（普通请求）

最基础的请求-响应模式，用于后端业务 API。

```
请求流程:
┌────────────┐     ┌────────────┐     ┌────────────┐
│   浏览器    │────▶│   代理层    │────▶│   后端服务  │
│            │◀────│            │◀────│            │
└────────────┘     └────────────┘     └────────────┘
     请求              转发              处理
     响应              返回              响应
```

**前端代码示例：**
```typescript
// src/shared/api/flow.ts
export const flowApi = {
  getFlowList: (params: FlowParams) =>
    getRequest().get<ApiResponse<FlowListResult>>('/flow/list', { params })
}
```

**代理配置：**
```nginx
# Nginx
location /api/ {
    proxy_pass http://server:8081/;
}
```

### 3.2 WebSocket（双向通信）

用于 AI 实时聊天，支持双向消息推送。

```
连接流程:
┌────────────┐     ┌────────────┐     ┌────────────┐
│   浏览器    │────▶│   代理层    │────▶│   AI 服务   │
│            │     │            │     │            │
│  WebSocket │◀───▶│  Upgrade   │◀───▶│  WebSocket │
│   Client   │     │  Protocol  │     │   Server   │
└────────────┘     └────────────┘     └────────────┘
```

**前端代码示例：**
```typescript
// src/shared/services/chat/chatService.ts
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const baseUrl = `${protocol}//${window.location.host}`
const wsUrl = `${baseUrl}/ws/chat?user_id=${userId}&agent_id=${agentId}`
this.ws = new WebSocket(wsUrl)
```

**代理配置：**
```nginx
# Nginx
location /ws/ {
    proxy_pass http://ai:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
}
```

### 3.3 SSE（Server-Sent Events）

服务端向客户端单向推送事件流，用于 AI 流式响应。

```
连接流程:
┌────────────┐     ┌────────────┐     ┌────────────┐
│ 浏览器/IDE  │────▶│   代理层    │────▶│   AI 服务   │
│            │     │            │     │            │
│ EventSource│◀────│ 禁用缓冲    │◀────│  事件流     │
│            │     │ 长连接      │     │  推送      │
└────────────┘     └────────────┘     └────────────┘
                        │
                        ▼
                 关键配置:
                 - proxy_buffering off
                 - chunked_transfer_encoding off
                 - proxy_read_timeout 86400s
```

**代理配置（关键）：**
```nginx
# Nginx - SSE 必须禁用缓冲
location /sse/ {
    proxy_pass http://ai:8001/sse/;
    proxy_http_version 1.1;

    # SSE 关键配置：禁用缓冲
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;

    # SSE 连接头（不是 WebSocket 的 upgrade）
    proxy_set_header Connection "";

    # 防止 nginx 缓冲响应
    proxy_set_header X-Accel-Buffering no;

    # SSE 长连接超时（24小时）
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
}
```

### 3.4 MCP（Model Context Protocol）

AI 工具调用协议，基于 JSON-RPC，支持 HTTP 和 SSE 两种传输方式。

```
MCP 架构:
┌─────────────────────────────────────────────────────────────────────┐
│                          MCP 客户端                                  │
│                                                                     │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                │
│   │   Cursor    │  │   Cline     │  │Cherry Studio│                │
│   └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                │
│          │                │                │                        │
│          └────────────────┼────────────────┘                        │
│                           │                                         │
│                           ▼                                         │
│                    MCP 请求 (JSON-RPC)                              │
│                    ┌─────────────────────────────────────┐          │
│                    │ POST /mcp                           │          │
│                    │ Content-Type: application/json      │          │
│                    │ Accept: application/json,           │          │
│                    │         text/event-stream           │          │
│                    │                                     │          │
│                    │ {                                   │          │
│                    │   "jsonrpc": "2.0",                 │          │
│                    │   "method": "tools/call",           │          │
│                    │   "params": {                       │          │
│                    │     "name": "add_flow",             │          │
│                    │     "arguments": { ... }            │          │
│                    │   }                                 │          │
│                    │ }                                   │          │
│                    └─────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          Nginx 代理                                  │
│                                                                     │
│   location /mcp/ {                                                  │
│       proxy_pass http://ai:8001/mcp/;                               │
│       proxy_buffering off;                                          │
│       proxy_set_header Accept "application/json, text/event-stream";│
│       proxy_read_timeout 86400s;                                    │
│   }                                                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MCP 服务端 (ai:8001)                        │
│                                                                     │
│   处理请求:                                                          │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │ 1. 解析 JSON-RPC 请求                                        │   │
│   │ 2. 调用对应工具（如 add_flow）                                 │   │
│   │ 3. 返回响应:                                                  │   │
│   │    - JSON 响应（普通结果）                                     │   │
│   │    - SSE 流（流式结果）                                        │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   可用工具示例:                                                      │
│   - add_flow: 添加流水记录                                          │
│   - get_accounts: 获取账户列表                                      │
│   - get_analysis: 获取分析数据                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、开发环境 vs 生产环境

### 4.1 环境对比

```
┌─────────────────────────────────────────────────────────────────────┐
│                          开发环境                                    │
│                                                                     │
│   浏览器/IDE ──▶ Vite (localhost:5173) ──▶ 远程服务器               │
│                        │                                            │
│                        ├── /api/*      → www.lllama.cn:10672       │
│                        ├── /ai-api/*   → localhost:8001            │
│                        ├── /ws/*       → localhost:8001            │
│                        ├── /sse/*      → localhost:8001            │
│                        ├── /mcp/*      → localhost:8001            │
│                        └── /messages/* → localhost:8001            │
│                                                                     │
│   配置文件: .env.development                                        │
│   VITE_SERVER_TARGET=http://www.lllama.cn:10672                    │
│   VITE_AI_TARGET=http://localhost:8001                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          生产环境 (Docker)                           │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │                    Docker Network (网桥)                     │   │
│   │                                                             │   │
│   │   浏览器/IDE ──▶ Nginx (web:80)                             │   │
│   │                        │                                    │   │
│   │                        ├── /api/*      → server:8081       │   │
│   │                        ├── /ai-api/*   → ai:8001           │   │
│   │                        ├── /ws/*       → ai:8001           │   │
│   │                        ├── /sse/*      → ai:8001           │   │
│   │                        ├── /mcp/*      → ai:8001           │   │
│   │                        └── /messages/* → ai:8001           │   │
│   │                                                             │   │
│   │   容器互相通过服务名访问（Docker DNS）                         │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│   配置文件: nginx/default.conf                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 配置文件位置

| 环境 | 配置文件 | 说明 |
|------|----------|------|
| 开发 | `ydjz_web_v2/.env` | 共享环境变量 |
| 开发 | `ydjz_web_v2/.env.development` | 开发环境代理目标 |
| 开发 | `ydjz_web_v2/vite.config.ts` | Vite 代理配置 |
| 生产 | `ydjz_web_v2/.env.production` | 生产环境变量 |
| 生产 | `nginx/default.conf` | Nginx 代理配置 |

---

## 五、协议对比总结

| 协议 | 连接方式 | 数据方向 | 代理关键配置 | 客户端 | 用途 |
|------|----------|----------|--------------|--------|------|
| **HTTP** | 短连接 | 请求-响应 | `proxy_pass` | 浏览器 | 业务 API |
| **WebSocket** | 长连接 | 双向 | `Upgrade: websocket` | 浏览器 | 实时聊天 |
| **SSE** | 长连接 | 服务端→客户端 | `proxy_buffering off` | 浏览器 + AI IDE | 流式响应 |
| **MCP** | HTTP/SSE | 双向（RPC） | `Accept: json+sse` | 浏览器 + AI IDE | 工具调用 |

---

## 六、代理工作原理

### 6.1 为什么需要代理？

1. **解决跨域问题**：浏览器同源策略限制，前端无法直接请求不同域的后端
2. **统一入口**：所有请求通过同一域名，简化配置
3. **安全隔离**：后端服务不直接暴露给外网
4. **负载均衡**：生产环境可配置多个后端实例

### 6.2 代理如何工作？

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        浏览器发起请求                                     │
│                                                                          │
│  const response = await axios.get('/api/flow/list')                     │
│                                                                          │
│  实际发送: GET http://localhost:5173/api/flow/list                       │
│            ─────────────────────────────────────────                     │
│            协议  │  主机:端口        │ 路径                               │
│            http  │  localhost:5173  │ /api/flow/list                    │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      代理层处理                                           │
│                                                                          │
│  1. 检查路径是否匹配代理规则                                               │
│     /api/* ✓ 匹配                                                        │
│                                                                          │
│  2. 读取代理配置                                                          │
│     target: 'http://server:8081'                                        │
│     rewrite: 去掉 /api 前缀                                              │
│                                                                          │
│  3. 重写请求                                                              │
│     原始: /api/flow/list                                                 │
│     重写: /flow/list                                                     │
│                                                                          │
│  4. 转发到目标服务器                                                       │
│     GET http://server:8081/flow/list                                    │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        后端服务器响应                                     │
│                                                                          │
│  Spring Boot 处理 /flow/list                                             │
│  返回 JSON: { "code": 0, "data": [...] }                                │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      代理返回响应给浏览器                                  │
│                                                                          │
│  代理将后端响应原样返回给浏览器                                            │
│  浏览器认为响应来自 localhost:5173（同源）                                 │
│  ──────────────────────────────────                                      │
│  跨域问题解决！                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 七、AI IDE 配置示例

### 7.1 Cursor 配置

在 Cursor 设置中添加 MCP Server：

```json
{
  "mcpServers": {
    "easyaccounts": {
      "url": "https://your-domain.com/mcp",
      "headers": {
        "user_id": "your-user-id"
      }
    }
  }
}
```

### 7.2 Claude Code 配置

在 `~/.claude.json` 中添加：

```json
{
  "mcpServers": {
    "easyaccounts": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://your-domain.com/sse"],
      "env": {
        "USER_ID": "your-user-id"
      }
    }
  }
}
```

### 7.3 Cherry Studio 配置

在设置中添加 MCP 服务器：
- URL: `https://your-domain.com/mcp`
- Headers: `user_id: your-user-id`

---

## 八、故障排查

### 8.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| SSE 连接立即断开 | Nginx 缓冲未关闭 | 添加 `proxy_buffering off` |
| WebSocket 连接失败 | 缺少 Upgrade 头 | 添加 `proxy_set_header Upgrade` |
| MCP 返回 406 错误 | Accept 头不正确 | 添加 `Accept: application/json, text/event-stream` |
| 请求超时 | 超时时间太短 | 增加 `proxy_read_timeout` |
| user_id 丢失 | 下划线头被过滤 | 添加 `underscores_in_headers on` |

### 8.2 调试命令

```bash
# 测试 SSE 连接
curl -N -H "Accept: text/event-stream" https://your-domain.com/sse/test

# 测试 MCP 连接
curl -X POST https://your-domain.com/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

# 测试 WebSocket（需要 wscat）
wscat -c wss://your-domain.com/ws/chat?user_id=test
```

---

## 九、相关文件

| 文件 | 说明 |
|------|------|
| `vite.config.ts` | Vite 开发环境代理配置 |
| `.env` | 共享环境变量 |
| `.env.development` | 开发环境代理目标 |
| `.env.production` | 生产环境变量 |
| `nginx/default.conf` | Nginx 生产环境代理配置 |
| `src/shared/api/request.ts` | 后端 API 请求封装 |
| `src/shared/api/ai-request.ts` | AI 服务请求封装 |
| `src/shared/services/chat/chatService.ts` | WebSocket 聊天服务 |
