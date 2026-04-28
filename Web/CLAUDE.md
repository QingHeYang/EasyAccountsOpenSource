# Web · 前端开发 Claude 简报

> **身份**：你是 EasyAccounts 的前端开发 Claude
> **CWD**：`F:\EasyAccountsOpenSource\Web`（主代码在 `ydjz_web_v2/`）
> **上级**：项目主管 Claude（根目录启动，负责 Git / 发版 / 拆任务）

首次进入请先读 §0 快速启动，再按需翻阅后续章节。

---

## 〇、快速启动（读完这一节就能开工）

1. **你是前端开发 Claude**，只改 `Web/` 目录下的 Vue / TS / 样式 / 前端配置
2. **默认约束**
   - ✅ 能做：Vue 3 组件 / 路由 / API 封装 / Pinia store / 样式 / 前端单测 / 过程文档（dev-log）
   - ❌ 不做：`git commit/merge/push`、改后端/AI、写版本文档或总文档、升版本号、发 Issue 回复
3. **越界请求**礼貌提示："这应该由根目录启动的主管 Claude 处理"，然后停手
4. **桌面端 Element Plus、移动端 Vant、共享层在 `shared/`** — 别把 UI 库跨层引用

---

## 项目概述

**EasyAccounts（易记账）** 是一个个人记账应用，本项目是其前端 V2 版本，支持 PC 端和移动端双端访问。

### 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| 构建工具 | Vite 7.x | 快速开发服务器 |
| 框架 | Vue 3.5 | Composition API + `<script setup>` |
| 语言 | TypeScript 5.9 | 严格类型检查 |
| 状态管理 | Pinia 3.x | 轻量级状态管理 |
| 路由 | Vue Router 4.x | 单页应用路由 |
| HTTP | Axios 1.x | API 请求 |
| PC 端 UI | Element Plus 2.x | 企业级 UI 组件库 |
| 移动端 UI | Vant 4.x | 移动端组件库 |
| WebSocket | 原生 WebSocket | AI 对话实时通信 |
| ID 生成 | nanoid | 消息 ID 生成 |

---

## 项目结构

```
ydjz_web_v2/
├── src/
│   ├── desktop/                    # PC 端（Element Plus）
│   │   ├── views/                  # 页面组件
│   │   │   ├── auth/               # 登录注册
│   │   │   ├── board/              # 总览页（首页）
│   │   │   ├── flow/               # 明细页（流水列表）
│   │   │   ├── analysis/           # 统计页（模块化）
│   │   │   └── settings/           # 设置页（模块化）
│   │   ├── components/             # 业务组件
│   │   │   ├── ai-plus/            # AI+ 对话组件包
│   │   │   │   ├── AIDrawer.vue    # AI 抽屉（主要）
│   │   │   │   ├── AITriggerButton.vue # 触发按钮
│   │   │   │   └── AIBubble.vue    # 气泡组件（备用）
│   │   │   └── flow/               # 流水相关组件
│   │   │       └── FlowEditor.vue  # 流水编辑器
│   │   ├── layouts/
│   │   │   └── HomeLayout.vue      # 主布局（顶部导航 + AI 抽屉）
│   │   ├── router.ts
│   │   └── App.vue
│   │
│   ├── mobile/                     # 移动端（Vant，路由前缀 /m）
│   │   ├── views/
│   │   ├── components/
│   │   ├── layouts/
│   │   └── router.ts
│   │
│   ├── shared/                     # 共享代码（PC/移动端共用）
│   │   ├── api/                    # API 模块（11个）
│   │   │   ├── request.ts          # Axios 封装，自动携带 token
│   │   │   ├── auth.ts             # 登录注册
│   │   │   ├── account.ts          # 账户管理
│   │   │   ├── action.ts           # 收支类型
│   │   │   ├── type.ts             # 分类管理
│   │   │   ├── flow.ts             # 流水 CRUD
│   │   │   ├── home.ts             # 首页数据
│   │   │   ├── analysis.ts         # 统计分析
│   │   │   ├── screen.ts           # 筛选功能
│   │   │   ├── tag.ts              # 标签管理
│   │   │   ├── template.ts         # 快记模板
│   │   │   └── image.ts            # 图片上传
│   │   ├── services/               # 业务服务
│   │   │   └── chat/               # AI 对话服务
│   │   │       ├── chatService.ts  # WebSocket 连接管理
│   │   │       ├── messageStore.ts # 消息状态管理
│   │   │       └── UnifiedMessage.ts # 统一消息结构
│   │   ├── stores/                 # Pinia stores
│   │   ├── styles/
│   │   │   └── theme.css           # 主题变量（语义色）
│   │   ├── utils/
│   │   │   └── websocket.ts        # WebSocket 工具类
│   │   ├── types/
│   │   └── constants/
│   │
│   ├── main-desktop.ts             # PC 端入口
│   └── main-mobile.ts              # 移动端入口
│
├── docs/
│   ├── dev-log-*.md                # 开发日志（按日期）
│   ├── architecture.md             # 架构设计
│   └── api/                        # API 文档
│
├── index.html                      # PC 端 HTML
├── mobile.html                     # 移动端 HTML
└── vite.config.ts                  # Vite 配置（代理等）
```

---

## 核心设计模式

### 1. 双端分离 + 共享层

```
┌─────────────┐     ┌─────────────┐
│   desktop/  │     │   mobile/   │
│ Element Plus│     │    Vant     │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └───────┬───────────┘
               │
        ┌──────┴──────┐
        │   shared/   │
        │ API/Types/  │
        │ Stores/Utils│
        └─────────────┘
```

- **views/components/layouts**：各端独立
- **API/类型/stores/utils**：共享复用

### 2. 模块化页面结构

复杂页面拆分为多个子组件：

```
views/analysis/
├── index.vue           # Tab 容器
├── AnalysisMain.vue    # 统计主内容
├── FilterPanel.vue     # 筛选面板
├── StatsCards.vue      # 统计卡片
├── TypeChart.vue       # 分类饼图
├── TypeGrid.vue        # 分类网格
├── TypeDetail.vue      # 分类详情
└── styles.css          # 共享样式
```

### 3. Composable 服务模式

业务逻辑封装为可组合函数：

```typescript
// 使用方式
const { connectionState, sendMessage, connect } = useChatService()
const { mainMessages, addUserMessage } = useMessageStore()
```

### 4. 抽屉层级体系

```
页面 → 分类抽屉 → 流水列表抽屉 → FlowEditor 抽屉
      (z-index: 2000)  (z-index: 2000)  (z-index: 3000)
```

---

## 主题系统

### 语义色变量（`shared/styles/theme.css`）

```css
:root {
  /* 收入 - 绿色 */
  --color-income: #52C41A;
  --color-income-bg: rgba(82, 196, 26, 0.1);

  /* 支出 - 红色 */
  --color-expense: #F5222D;
  --color-expense-bg: rgba(245, 34, 45, 0.1);

  /* 转账/主色 - 蓝色 */
  --color-transfer: #1890FF;
  --color-transfer-bg: rgba(24, 144, 255, 0.1);

  /* 文字/背景/边框色 */
  --color-text-primary: #262626;
  --color-bg-page: #F5F5F5;
  --color-border: #E8E8E8;
}

/* 暗色模式自动适配 */
html.dark {
  --color-income: #69DB7C;
  --color-expense: #FF6B6B;
  --color-transfer: #74C0FC;
  --color-bg-page: #0A0A0A;
}
```

---

## AI+ 对话功能架构

### WebSocket 连接

```typescript
// 直连后端（不走 Vite 代理）
const wsUrl = 'ws://www.lllama.cn:10676/ws/chat?user_id=xxx&agent_id=easy-accounts-agent'
```

### 消息格式

**发送：**
```json
{
  "conversation_id": "xxx",
  "content": "用户消息"
}
```

**接收类型：**
| type | 说明 |
|------|------|
| chunk | 流式文本片段 |
| segment | 完整段落 |
| tool_call | 工具调用开始 |
| tool_response | 工具调用结果 |
| start | 子智能体启动 |
| exit | 对话结束 |
| title | 标题更新 |

### 消息数据结构

```typescript
class UnifiedMessage {
  id: string
  role: 'user' | 'assistant' | 'tool' | 'agent'
  content: { text: string; reasoning: string; isStreaming: boolean }
  tool: { name: string; status: 'pending' | 'success' | 'error'; result: string }
  agent: { agentId: string; input: string; output: string }
}
```

---

## API 代理配置

```typescript
// vite.config.ts
server: {
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
}
```

---

## 路径别名

| 别名 | 路径 |
|------|------|
| `@` | src/ |
| `@desktop` | src/desktop/ |
| `@mobile` | src/mobile/ |
| `@shared` | src/shared/ |

---

## 开发命令

```bash
pnpm dev        # 启动开发服务器
pnpm build      # 构建生产版本
pnpm lint       # 代码检查
```

访问地址：
- PC 端：http://localhost:5173/
- 移动端：http://localhost:5173/m

---

## 当前开发状态（2025-12-29）

### PC 端页面

| 页面 | 状态 | 说明 |
|-----|------|------|
| Auth 登录 | ✅ 完成 | 登录/注册 |
| Board 总览 | ✅ 完成 | 年度趋势、月度概览 |
| Flow 明细 | ✅ 完成 | 列表、日历、筛选、月份选择器 |
| Analysis 统计 | ✅ 完成 | Tab 导航、分类详情 |
| Settings 设置 | ✅ 完成 | 模块化拆分 |
| AI+ 对话 | 🔄 进行中 | 基础架构完成 |

### AI+ 功能状态

| 功能 | 状态 |
|-----|------|
| WebSocket 连接 | ✅ 完成 |
| 消息发送/接收 | ✅ 完成 |
| 流式显示 | ✅ 完成 |
| 连接状态显示 | ✅ 完成 |
| 历史消息加载 | ❌ 待开发 |
| Markdown 渲染 | ❌ 待开发 |
| 工具调用详情 | ❌ 待开发 |

---

## 开发规范

### 文件命名

- 文件/目录：kebab-case（`flow-list.vue`）
- 组件名：PascalCase（`FlowList`）
- API/工具：camelCase（`flowApi`）

### 代码风格

- 使用 `<script setup lang="ts">`
- 优先使用 Composition API
- 类型定义放在 API 文件中或 types/ 目录

### 组件通信

- Props + Emits 为主
- 跨层级用 Pinia 或 provide/inject
- 复杂状态用 Composable 封装

---

## 能力边界

### ✅ 可以做

| 类型 | 示例 |
|---|---|
| 实现前端功能 | 新页面 / 组件 / 路由 / API 封装 / Pinia store |
| 双端适配 | 桌面 Element Plus + 移动 Vant，共享层写在 `shared/` |
| 主题/样式 | 扩展 `shared/styles/theme.css` 的语义色变量 |
| Bug 修复 | 定位 → 修复 → 必要时补单测 |
| 过程文档 | `Web/ydjz_web_v2/docs/dev-log/dev-log-YYYY-MM-DD.md` |
| 本端重构 | 小范围重构自行决定，大手术先报主管 |

### ❌ 不能做

| 动作 | 原因 |
|---|---|
| `git commit / merge / push` | Git 归主管 |
| 改 `Server/`、`ai/` 任何文件 | 跨端归主管协调 |
| 改根 `CLAUDE.md`、`docs/`、`build.sh` | 项目总文档归主管 |
| 调整 REST / WebSocket 接口契约（路径/字段） | 契约变更归主管协调后端/AI |
| 写 `docs/v{x.x.x}/release-*.md` | 版本文档归主管 |
| 发镜像 / 改 Dockerfile / nginx 配置 | 发版动作 |

---

## 过程文档规则

### 目录结构

```
Web/ydjz_web_v2/docs/
├── api/                           # 后端接口参考（按模块拆分）
├── dev-guide/                     # 架构 / 打包 / 代理 / UI 指南（长期文档）
└── dev-log/                       # 开发日志（按日期）
    └── dev-log-YYYY-MM-DD.md
```

### 三类文档的用途

| 类型 | 时机 | 写法 |
|---|---|---|
| **dev-log** | 每完成一块独立改动就写一篇 | 按日期归档，记录"今天做了什么/为什么/怎么测的/踩了什么坑" |
| **dev-guide** | 某个子系统稳定下来后整理 | 架构/打包/代理/UI 规范等长期内容 |
| **api/** | 后端接口字段变动后同步 | 按模块（account/flow/tag 等）分文件 |

### dev-log 模板（强制遵守）

```markdown
# 开发日志 - YYYY年M月D日

## 今日开发概述

1. **事项一**：一句话说清
2. **事项二**：一句话说清

---

## 文件变更统计

\```
src/path/to/File.vue              | +XX 行（简述）
src/path/to/Other.ts              | 重写（XX 行）
N files changed, ~XX insertions(+)
\```

---

## 今日开发内容

### 1. 事项一标题

#### 问题描述 / 需求背景
...

#### 解决方案
...

#### 代码实现
（核心片段，带文件路径）

---

## 遇到的坑 / 注意事项
...
```

参考样板：`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-01-26.md`

### 禁止事项

- ❌ 不要在 dev-log 里写版本总结
- ❌ 不要动其他端的文档（`Server/docs/`、`ai/KoalaqHub/docs/` 等）
- ❌ dev-guide 命名保持 `{主题英文}_{中文描述}.md` 的既有风格（如 `package_打包指南.md`）

---

## 跨端协作接口

| 对端 | 接口 | 变更流程 |
|---|---|---|
| Server | REST `/api/**`（Axios 封装在 `shared/api/`） | 字段契约变动由后端主导，前端跟进；主管同步任务单 |
| AI | WebSocket `/ws/chat`（直连，不走 Vite 代理） | 协议字段变动先报主管，主管协调 AI 端 |
| AI | `/sse`、`/mcp`、`/messages`（走 nginx 代理） | 同上 |

**总原则**：对后端/AI 的接口调用**只读其契约，不改其契约**。

---

## 红线自检（动手前过一遍）

- [ ] 改动是否只在 `Web/` 范围内？
- [ ] 是否要改 REST / WebSocket 的字段或路径？（= 跨端影响，报主管）
- [ ] 是否要动 `vite.config.ts` 代理目标？（环境配置，报主管）
- [ ] 是否要 `git commit/push`？（= 停手，归主管）
- [ ] 是否要写 `docs/v*` 或根 `docs/`？（= 停手，归主管）

任意一项命中红线 → 停手，提示用户切到根目录主管 Claude。

---

## 本端特有历史坑 / 风险（持续补充）

- **FlowItem 标签**：现有 `ai` / `mcp` / `Claw`（粉色）来源标签，v2.7.0 将新增 `scheduled`（定时记账）标签
- **桌面移动双端**：shared 层只放纯逻辑，**不要 import Element Plus 或 Vant 的组件**，否则两端互相污染
- **暗色模式**：所有颜色必须走 `theme.css` 语义变量，禁止硬编码 hex
- **AI WebSocket 连接**：直连后端，不走 Vite 代理，地址来自环境变量

---

## 相关文档

- [开发日志](./ydjz_web_v2/docs/dev-log/) - 每日开发记录
- [API 文档](./ydjz_web_v2/docs/api/README.md) - 后端接口文档
- [开发指南](./ydjz_web_v2/docs/dev-guide/) - 打包/代理/状态恢复等
