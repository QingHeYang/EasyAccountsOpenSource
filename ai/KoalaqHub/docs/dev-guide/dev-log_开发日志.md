# 开发日志

记录开发过程中遇到的重要问题和解决方案。

---

## 2024-12-30: Vite 代理 SSE (Server-Sent Events) 超时问题

### 问题描述

在开发环境中，需要通过 Vite 开发服务器代理 MCP SSE 连接到后端 FastAPI 服务：

- **直连后端** (localhost:8001): `/sse` 和 `/mcp` 均正常工作
- **通过 Vite 代理** (localhost:5173): `/mcp` (streamable-http) 正常，但 `/sse` 约30秒后超时 (32001 request timeout)

### 根本原因

1. **http-proxy 默认超时**: node-http-proxy 默认2分钟超时，但 Vite/Node.js 的 socket 默认超时更短
2. **SSE 是长连接**: SSE 需要保持连接打开，直到客户端断开或服务器关闭
3. **中间件缓冲**: 某些中间件（如压缩、CORS）可能会缓冲 SSE 响应

### 解决方案

在 `vite.config.ts` 中使用原生 `http-proxy` 并正确配置 SSE 支持：

```typescript
import httpProxy from 'http-proxy'

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'sse-proxy-middleware',
      configureServer(server) {
        const proxy = httpProxy.createProxyServer({
          target: 'http://localhost:8001',
          changeOrigin: true,
          selfHandleResponse: false,
          // 关键配置：完全禁用超时
          proxyTimeout: 0,
          timeout: 0,
          xfwd: false,
        })

        // 关键：在 proxyReq 事件中设置 socket 选项
        proxy.on('proxyReq', (proxyReq, req, res) => {
          if (req.url?.startsWith('/sse')) {
            // 禁用所有超时
            req.socket?.setTimeout(0)
            req.socket?.setNoDelay(true)
            req.socket?.setKeepAlive(true, 0)

            // 响应 socket 也需要设置
            if (res.socket) {
              res.socket.setTimeout(0)
              res.socket.setNoDelay(true)
              res.socket.setKeepAlive(true, 0)
            }

            // 设置 SSE 请求头
            proxyReq.setHeader('Accept', 'text/event-stream')
            proxyReq.setHeader('Cache-Control', 'no-cache')
            proxyReq.setHeader('Connection', 'keep-alive')
          }
        })

        // 确保 SSE 响应头正确
        proxy.on('proxyRes', (proxyRes, req, res) => {
          if (req.url?.startsWith('/sse')) {
            res.setHeader('Content-Type', 'text/event-stream')
            res.setHeader('Cache-Control', 'no-cache, no-transform')
            res.setHeader('Connection', 'keep-alive')
            res.setHeader('X-Accel-Buffering', 'no')  // 告诉 nginx 等代理不要缓冲
          }
        })

        server.middlewares.use((req, res, next) => {
          if (req.url?.startsWith('/sse') || req.url?.startsWith('/mcp') || req.url?.startsWith('/messages')) {
            return proxy.web(req, res)
          }
          next()
        })
      },
    },
  ],
})
```

### 关键点

1. **`proxyTimeout: 0` 和 `timeout: 0`**: 禁用 http-proxy 的超时
2. **`socket.setTimeout(0)`**: 禁用 Node.js socket 超时（这是最关键的！）
3. **`socket.setNoDelay(true)`**: 禁用 Nagle 算法，确保数据立即发送
4. **`socket.setKeepAlive(true, 0)`**: 启用 TCP keep-alive
5. **`X-Accel-Buffering: no`**: 告诉上游代理（如 nginx）不要缓冲响应

### 后端配套（FastAPI）

确保后端使用**纯 ASGI 中间件**而不是 `@app.middleware("http")`，因为后者基于 `BaseHTTPMiddleware`，不兼容 SSE 流式响应：

```python
# 错误方式（会导致 SSE 失败）
@app.middleware("http")
async def auth_middleware(request, call_next):
    response = await call_next(request)  # 这会缓冲整个响应
    return response

# 正确方式
class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # 直接传递，不缓冲
        await self.app(scope, receive, send)

app.add_middleware(AuthMiddleware)
```

### 参考资料

- [GitHub: How to enable SSE in Vite dev Server - Discussion #10851](https://github.com/vitejs/vite/discussions/10851)
- [GitHub: Server-sent events not working - node-http-proxy Issue #921](https://github.com/http-party/node-http-proxy/issues/921)
- [GitHub: SSE close event not forwarded - Vite Issue #13522](https://github.com/vitejs/vite/issues/13522)

### 验证成功

```
[MCP Proxy] -> GET /sse?token=xxx
[MCP Proxy] <- 200 /sse?token=xxx Content-Type: text/event-stream; charset=utf-8
[MCP Proxy] -> POST /messages/?session_id=xxx
[MCP Proxy] <- 202 /messages/?session_id=xxx Content-Type: undefined
```

SSE 连接保持稳定，消息交互正常。

---
