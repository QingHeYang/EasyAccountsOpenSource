# EasyAccounts Web 前端

EasyAccounts 的 Web 前端项目，支持桌面端和移动端双端访问。

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 构建工具 | Vite | 7.x |
| 框架 | Vue | 3.5 |
| 语言 | TypeScript | 5.9 |
| 状态管理 | Pinia | 3.x |
| 路由 | Vue Router | 4.x |
| HTTP 客户端 | Axios | 1.x |
| 桌面端 UI | Element Plus | 2.x |
| 移动端 UI | Vant | 4.x |
| 图表 | ECharts + vue-echarts | 6.x |
| Markdown | markdown-it | 14.x |

---

## 项目结构

```
ydjz_web_v2/
├── src/
│   ├── desktop/                    # 桌面端（Element Plus）
│   │   ├── views/                  # 页面组件
│   │   │   ├── auth/               # 登录注册
│   │   │   ├── board/              # 总览页
│   │   │   ├── flow/               # 明细页
│   │   │   ├── analysis/           # 统计页
│   │   │   └── settings/           # 设置页
│   │   ├── components/             # 业务组件
│   │   │   ├── ai-plus/            # AI+ 对话组件
│   │   │   └── flow/               # 流水相关组件
│   │   ├── layouts/
│   │   │   └── HomeLayout.vue      # 主布局
│   │   ├── router.ts               # 桌面端路由
│   │   └── App.vue
│   │
│   ├── mobile/                     # 移动端（Vant）
│   │   ├── views/                  # 页面组件
│   │   ├── components/             # 业务组件
│   │   ├── layouts/
│   │   │   └── HomeLayout.vue      # 主布局
│   │   └── router.ts               # 移动端路由（前缀 /m）
│   │
│   ├── shared/                     # 共享代码
│   │   ├── api/                    # API 模块
│   │   │   ├── request.ts          # Axios 封装
│   │   │   ├── ai-request.ts       # AI 请求封装
│   │   │   ├── auth.ts             # 认证 API
│   │   │   ├── account.ts          # 账户 API
│   │   │   ├── flow.ts             # 流水 API
│   │   │   ├── type.ts             # 分类 API
│   │   │   ├── home.ts             # 首页 API
│   │   │   ├── analysis.ts         # 统计 API
│   │   │   └── ai.ts               # AI API
│   │   ├── stores/                 # Pinia stores
│   │   ├── composables/            # 组合式函数
│   │   ├── services/               # 业务服务
│   │   │   └── chat/               # AI 对话服务
│   │   ├── styles/
│   │   │   └── theme.css           # 主题变量
│   │   ├── types/                  # 类型定义
│   │   └── utils/                  # 工具函数
│   │
│   ├── main-desktop.ts             # 桌面端入口
│   └── main-mobile.ts              # 移动端入口
│
├── index.html                      # 桌面端 HTML
├── mobile.html                     # 移动端 HTML
├── vite.config.ts                  # Vite 配置
├── tsconfig.json                   # TypeScript 配置
└── package.json
```

### 路径别名

| 别名 | 路径 |
|------|------|
| `@` | src/ |
| `@desktop` | src/desktop/ |
| `@mobile` | src/mobile/ |
| `@shared` | src/shared/ |

---

## 环境配置

### 1. 安装依赖

```bash
cd Web/ydjz_web_v2
pnpm install
```

> 推荐使用 pnpm，也可以使用 npm 或 yarn

### 2. 环境变量

复制样例文件并修改：

```bash
cp .env.development.example .env.development
```

编辑 `.env.development`：

```bash
# 后端 API 服务地址
VITE_SERVER_TARGET=http://localhost:8081

# AI 服务地址
VITE_AI_TARGET=http://localhost:8001
```

> 如果连接远程服务，将地址改为对应的服务器地址即可。

### 3. 代理配置

开发服务器自动代理以下路径：

| 路径 | 目标 | 说明 |
|------|------|------|
| `/api/*` | VITE_SERVER_TARGET | 后端 API |
| `/ai/*` | VITE_AI_TARGET | AI API |
| `/ws/*` | VITE_AI_TARGET | WebSocket（AI 对话） |
| `/sse`, `/mcp`, `/messages` | VITE_AI_TARGET | MCP/SSE 长连接 |

---

## 开发调试

### 启动开发服务器

```bash
pnpm dev
```

访问地址：
- 桌面端：http://localhost:5173/
- 移动端：http://localhost:5173/m

### 类型检查

```bash
# 仅检查，不编译
npx vue-tsc --noEmit

# 或在构建前自动检查
pnpm build
```

### 调试技巧

**1. Vue DevTools**

安装 [Vue DevTools](https://devtools.vuejs.org/) 浏览器扩展，可以：
- 查看组件树和状态
- 检查 Pinia store
- 追踪路由变化

**2. 网络请求调试**

打开浏览器开发者工具 → Network 面板：
- 筛选 `XHR/Fetch` 查看 API 请求
- 筛选 `WS` 查看 WebSocket 消息

**3. 代理日志**

开发服务器会输出代理日志：
```
[MCP Proxy] -> GET /sse
[MCP Proxy] <- 200 /sse Content-Type: text/event-stream
```

**4. 移动端调试**

- 使用 Chrome DevTools 的设备模拟模式
- 或在同一局域网内用手机访问 `http://<电脑IP>:5173/m`

---

## 打包构建

### 构建命令

```bash
pnpm build
```

构建产物输出到 `dist/` 目录：
```
dist/
├── index.html          # 桌面端入口
├── mobile.html         # 移动端入口
└── assets/             # 静态资源（JS/CSS/图片）
```

### Docker 构建

项目根目录提供了 Dockerfile：

```bash
cd Web
docker build -t easyaccounts-web .
```

Dockerfile 使用 nginx 作为静态服务器，配置文件位于 `nginx/` 目录。

### 构建优化

Vite 构建时会自动：
- Tree-shaking 移除未使用代码
- 代码分割（按路由懒加载）
- 资源压缩（JS/CSS 压缩）
- 静态资源哈希（缓存优化）

---

## 主题系统

项目使用 CSS 变量实现主题切换，支持浅色/深色/跟随系统。

主题变量定义在 `src/shared/styles/theme.css`：

```css
:root {
  /* 语义色 */
  --color-income: #52C41A;      /* 收入 - 绿色 */
  --color-expense: #F5222D;     /* 支出 - 红色 */
  --color-transfer: #1890FF;    /* 转账/主色 - 蓝色 */

  /* 文字/背景/边框 */
  --color-text-primary: #262626;
  --color-bg-page: #F5F5F5;
  --color-border: #E8E8E8;
}

html.dark {
  --color-income: #69DB7C;
  --color-expense: #FF6B6B;
  --color-transfer: #74C0FC;
  --color-bg-page: #0A0A0A;
}
```

---

## NGINX 代理配置

生产环境使用 NGINX 作为静态服务器和反向代理，配置文件位于 `nginx/default.conf`。

### 代理路由表

| 路径 | 目标服务 | 说明 |
|------|----------|------|
| `/` | 静态文件 | 前端页面，自动检测设备类型 |
| `/api/*` | `server:8081` | 后端 API |
| `/ai/*` | `ai:8001` | AI HTTP API |
| `/ws/*` | `ai:8001` | AI WebSocket（对话） |
| `/sse` | `ai:8001` | SSE 长连接 |
| `/mcp` | `ai:8001` | MCP 协议 |
| `/messages` | `ai:8001` | MCP 消息 |
| `/resources/*` | 静态文件 | 用户上传资源 |

### 移动端自动识别

NGINX 根据 User-Agent 自动选择入口文件：

```nginx
set $entry_file "index.html";
if ($http_user_agent ~* "(Android|iPhone|iPad|Mobile)") {
    set $entry_file "mobile.html";
}

location / {
    try_files $uri $uri/ /$entry_file;
}
```

### SSE/WebSocket 配置要点

**WebSocket（AI 对话）：**

```nginx
location /ws/ {
    proxy_pass http://ai:8001/ws/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;  # 1小时
}
```

**SSE（Server-Sent Events）：**

```nginx
location /sse {
    proxy_pass http://ai:8001/sse;

    # 关键：禁用缓冲
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
    proxy_set_header X-Accel-Buffering no;

    # SSE 不使用 upgrade
    proxy_set_header Connection "";

    proxy_read_timeout 86400s;  # 24小时
}
```

### 自定义请求头

项目使用 `user_id` 请求头传递用户标识，需要开启下划线支持：

```nginx
underscores_in_headers on;

location /ws/ {
    proxy_pass_request_headers on;
    proxy_set_header user_id $http_user_id;
}
```

### Docker Compose 示例

```yaml
services:
  web:
    image: easyaccounts-web
    ports:
      - "80:80"
    depends_on:
      - server
      - ai

  server:
    image: easyaccounts-server
    expose:
      - "8081"

  ai:
    image: easyaccounts-ai
    expose:
      - "8001"
```

> 注意：NGINX 配置中的 `server:8081` 和 `ai:8001` 是 Docker 内部网络地址，需要确保服务名称与 docker-compose.yml 中定义的一致。

---

## 相关文档

各端架构指南、开发日志、专项设计已迁移到独立的 Devlog 仓库（不在开源源码仓库中）。开源用户可参考：

- [GitBook 用户文档](https://mercys-organization-2.gitbook.io/easyaccounts/)
- [部署仓库](https://github.com/QingHeYang/EasyAccounts)
