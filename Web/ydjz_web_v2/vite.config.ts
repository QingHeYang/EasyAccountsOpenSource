import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import httpProxy from 'http-proxy'

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'sse-proxy-middleware',
      configureServer(server) {
        // 创建原生 http-proxy 实例（SSE需要特殊配置）
        const proxy = httpProxy.createProxyServer({
          target: 'http://192.168.50.231:8001',
          changeOrigin: true,
          // SSE 关键配置
          selfHandleResponse: false,
          // 完全禁用超时（SSE是长连接）
          proxyTimeout: 0,
          timeout: 0,
          // 禁用 X-Forwarded 头（避免干扰）
          xfwd: false,
        })

        // 请求发送前：设置SSE必要的请求头
        proxy.on('proxyReq', (proxyReq, req, res) => {
          console.log('[MCP Proxy] ->', req.method, req.url)

          // MCP 客户端不经过 Axios，需要手动添加 user_id
          if (!proxyReq.getHeader('user_id')) {
            proxyReq.setHeader('user_id', 'user_67ce21d6-a11c-4340-851b-7a8949906aa3')
          }

          // SSE 关键：在请求级别禁用socket超时
          if (req.url?.startsWith('/sse')) {
            // 禁用所有超时
            req.socket?.setTimeout(0)
            req.socket?.setNoDelay(true)
            req.socket?.setKeepAlive(true, 0)

            // 响应socket也需要设置
            if (res.socket) {
              res.socket.setTimeout(0)
              res.socket.setNoDelay(true)
              res.socket.setKeepAlive(true, 0)
            }

            // 设置请求头，告诉服务器这是SSE请求
            proxyReq.setHeader('Accept', 'text/event-stream')
            proxyReq.setHeader('Cache-Control', 'no-cache')
            proxyReq.setHeader('Connection', 'keep-alive')
          }
        })

        // 响应返回时：确保SSE响应头正确
        proxy.on('proxyRes', (proxyRes, req, res) => {
          console.log('[MCP Proxy] <-', proxyRes.statusCode, req.url, 'Content-Type:', proxyRes.headers['content-type'])

          if (req.url?.startsWith('/sse')) {
            // 强制设置SSE响应头，防止代理缓冲
            // 这些头会覆盖上游响应
            res.setHeader('Content-Type', 'text/event-stream')
            res.setHeader('Cache-Control', 'no-cache, no-transform')
            res.setHeader('Connection', 'keep-alive')
            res.setHeader('X-Accel-Buffering', 'no')  // 告诉nginx等代理不要缓冲
          }
        })

        proxy.on('error', (err, req, res) => {
          console.error('[MCP Proxy] Error:', err.message, req.url)
          // 防止连接挂起
          if (res && !res.headersSent) {
            res.writeHead(502, { 'Content-Type': 'text/plain' })
            res.end('Proxy Error: ' + err.message)
          }
        })

        // 在 Vite 中间件链的最前面插入
        server.middlewares.use((req, res, next) => {
          // MCP/SSE 路径使用自定义代理
          if (req.url?.startsWith('/sse') || req.url?.startsWith('/mcp') || req.url?.startsWith('/messages')) {
            return proxy.web(req, res)
          }
          // /m 或 /m/xxx 路径使用 mobile.html
          if (req.url?.startsWith('/m')) {
            req.url = '/mobile.html'
          }
          next()
        })
      },
    },
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@desktop': resolve(__dirname, 'src/desktop'),
      '@mobile': resolve(__dirname, 'src/mobile'),
      '@shared': resolve(__dirname, 'src/shared'),
    },
  },
  server: {
    host: true, // 允许局域网访问
    proxy: {
      '/api': {
        target: 'http://www.lllama.cn:10672',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ai-api': {
        target: 'http://192.168.50.231:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ai-api/, ''),
      },
      // 注意: /sse, /mcp, /messages 在 configureServer 中间件中处理
    },
  },
  build: {
    rollupOptions: {
      input: {
        desktop: resolve(__dirname, 'index.html'),
        mobile: resolve(__dirname, 'mobile.html'),
      },
    },
  },
})
