import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    {
      name: 'mobile-html-middleware',
      configureServer(server) {
        server.middlewares.use((req, res, next) => {
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
        target: 'http://www.lllama.cn:10680',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/ai-api/, ''),
      },
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
