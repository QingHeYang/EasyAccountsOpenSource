# 打包指南

本文档说明 ydjz_web_v2 项目的环境配置、开发运行、测试和打包流程。

---

## 一、pnpm 包管理器

### 1.1 安装 pnpm

```bash
# 使用 npm 安装
npm install -g pnpm

# 或使用 corepack（Node.js 16.13+）
corepack enable
corepack prepare pnpm@latest --activate

# 验证安装
pnpm --version
```

### 1.2 常用命令

| 命令 | 说明 |
|------|------|
| `pnpm install` | 安装所有依赖 |
| `pnpm add <pkg>` | 添加生产依赖 |
| `pnpm add -D <pkg>` | 添加开发依赖 |
| `pnpm remove <pkg>` | 移除依赖 |
| `pnpm update` | 更新所有依赖 |
| `pnpm dev` | 启动开发服务器 |
| `pnpm build` | 构建生产版本 |
| `pnpm preview` | 预览构建结果 |

### 1.3 首次使用

```bash
cd Web/ydjz_web_v2

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

---

## 二、环境变量配置

### 2.1 配置文件

项目使用两个 `.env` 文件：

```
.env                 # 共享配置（所有环境）
.env.development     # 开发环境专用（Vite 代理目标）
```

#### `.env` - 共享配置

```bash
# 后端 API 基础路径
VITE_API_BASE_URL=/api
```

#### `.env.development` - 开发环境

```bash
# 后端服务地址（Vite 代理目标）
VITE_SERVER_TARGET=http://www.lllama.cn:10672

# AI 服务地址（Vite 代理目标）
VITE_AI_TARGET=http://localhost:8001
```

### 2.2 变量用途

| 变量 | 用途 | 使用位置 |
|------|------|----------|
| `VITE_API_BASE_URL` | 后端 API 请求的 baseURL | `main-*.ts` |
| `VITE_SERVER_TARGET` | 开发环境后端代理目标 | `vite.config.ts` |
| `VITE_AI_TARGET` | 开发环境 AI 服务代理目标 | `vite.config.ts` |

### 2.3 加载顺序

```
开发环境 (pnpm dev):
.env  →  .env.development
         (后者覆盖前者同名变量)

生产环境 (pnpm build):
.env  →  (无 .env.production，直接使用 .env)
```

---

## 三、请求路径与代理

### 3.1 统一路径前缀

前端代码使用固定的路径前缀，由代理层转发：

| 路径前缀 | 用途 | 代码位置 |
|----------|------|----------|
| `/api` | 后端业务 API | `request.ts` |
| `/ai-api` | AI HTTP API | `ai-request.ts` |
| `/ws` | AI WebSocket | `chatService.ts` |
| `/sse` | AI SSE | MCP 客户端 |
| `/mcp` | AI MCP | MCP 客户端 |

### 3.2 开发环境 vs 生产环境

```
┌─────────────────────────────────────────────────────────────────────┐
│                        开发环境                                      │
│                                                                     │
│  浏览器请求: GET http://localhost:5173/api/flow/list               │
│                          │                                          │
│                          ▼                                          │
│                  Vite Dev Server                                    │
│                  读取 .env.development                               │
│                  VITE_SERVER_TARGET=http://xxx                      │
│                          │                                          │
│                          ▼                                          │
│                  代理到后端服务器                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        生产环境                                      │
│                                                                     │
│  浏览器请求: GET http://your-domain.com/api/flow/list              │
│                          │                                          │
│                          ▼                                          │
│                  Nginx（静态文件 + 代理）                            │
│                  location /api/ { proxy_pass http://server:8081 }  │
│                          │                                          │
│                          ▼                                          │
│                  代理到后端服务器                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**关键点**：
- 开发时 Vite 做代理
- 打包后 Vite 不存在，由 Nginx 做代理
- 前端代码只用路径前缀（如 `/api`），不关心实际服务器地址

---

## 四、开发运行

### 4.1 启动开发服务器

```bash
cd Web/ydjz_web_v2

# 安装依赖（首次或依赖更新后）
pnpm install

# 启动开发服务器
pnpm dev
```

### 4.2 访问地址

| 端 | 地址 |
|----|------|
| PC 端 | http://localhost:5173/ |
| 移动端 | http://localhost:5173/m |
| 局域网 | http://你的IP:5173/ |

### 4.3 修改代理目标

编辑 `.env.development`：

```bash
# 修改后端服务地址
VITE_SERVER_TARGET=http://192.168.1.100:8081

# 修改 AI 服务地址
VITE_AI_TARGET=http://192.168.1.100:8001
```

**注意**：修改后需重启开发服务器。

### 4.4 开发服务器代理表

| 路径 | 目标 | 说明 |
|------|------|------|
| `/api/*` | `VITE_SERVER_TARGET` | 后端 API |
| `/ai-api/*` | `VITE_AI_TARGET` | AI HTTP API |
| `/ws/*` | `VITE_AI_TARGET` | AI WebSocket |
| `/sse/*` | `VITE_AI_TARGET` | AI SSE |
| `/mcp/*` | `VITE_AI_TARGET` | AI MCP |
| `/messages/*` | `VITE_AI_TARGET` | AI Messages |

---

## 五、构建打包

### 5.1 构建命令

```bash
cd Web/ydjz_web_v2

# 生产构建
pnpm build
```

构建过程：
1. `vue-tsc -b` - TypeScript 类型检查
2. `vite build` - Vite 构建

### 5.2 构建产物

```
dist/
├── index.html          # PC 端入口
├── mobile.html         # 移动端入口
├── assets/             # 静态资源（JS/CSS/图片）
│   ├── desktop-xxx.js
│   ├── mobile-xxx.js
│   └── ...
├── favicon.ico
└── ...
```

### 5.3 预览构建结果

```bash
# 本地预览（注意：API 请求不会被代理）
pnpm preview

# 访问 http://localhost:4173/
```

---

## 六、部署配置

### 6.1 Nginx 配置

构建产物需配合 Nginx 部署，关键配置：

```nginx
# 静态文件
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /$entry_file;
}

# 后端 API 代理
location /api/ {
    proxy_pass http://server:8081/;
}

# AI 服务代理
location /ai-api/ {
    proxy_pass http://ai:8001/;
}

location /ws/ {
    proxy_pass http://ai:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}

location /sse/ {
    proxy_pass http://ai:8001/sse/;
    proxy_buffering off;
}

location /mcp/ {
    proxy_pass http://ai:8001/mcp/;
    proxy_buffering off;
}
```

### 6.2 Docker 部署

```dockerfile
FROM nginx:latest
COPY dist/ /usr/share/nginx/html/
COPY nginx/default.conf /etc/nginx/conf.d/default.conf
```

---

## 七、环境变量使用示例

### 7.1 在前端代码中

```typescript
// 访问 VITE_API_BASE_URL
import.meta.env.VITE_API_BASE_URL  // '/api'
```

### 7.2 在 vite.config.ts 中

```typescript
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const aiTarget = env.VITE_AI_TARGET || 'http://localhost:8001'
  const serverTarget = env.VITE_SERVER_TARGET || 'http://localhost:8081'

  return {
    server: {
      proxy: {
        '/api': { target: serverTarget },
        '/ai-api': { target: aiTarget },
      }
    }
  }
})
```

---

## 八、常见问题

### 8.1 修改环境变量后不生效

**解决**：重启开发服务器。

```bash
# Ctrl+C 停止后重新启动
pnpm dev
```

### 8.2 打包后 API 请求 404

**原因**：生产环境没有 Vite 代理，需要 Nginx 配置。

**解决**：检查 `nginx/default.conf` 代理配置是否正确。

### 8.3 TypeScript 类型错误

新增环境变量后需更新 `src/env.d.ts`：

```typescript
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_NEW_VAR: string  // 新增
}
```

### 8.4 pnpm 安装失败

```bash
# 清除缓存
pnpm store prune

# 删除 node_modules 重新安装
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

---

## 九、命令速查表

| 命令 | 说明 |
|------|------|
| `pnpm install` | 安装依赖 |
| `pnpm dev` | 启动开发服务器 |
| `pnpm build` | 生产构建 |
| `pnpm preview` | 预览构建结果 |

---

## 十、相关文件

| 文件 | 说明 |
|------|------|
| `.env` | 共享环境变量 |
| `.env.development` | 开发环境变量（代理目标） |
| `vite.config.ts` | Vite 配置（含代理规则） |
| `src/env.d.ts` | 环境变量类型定义 |
| `package.json` | 项目脚本和依赖 |
| `nginx/default.conf` | Nginx 生产代理配置 |
