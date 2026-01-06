# EasyAccounts AI 服务

EasyAccounts 的 AI 服务端，基于 KoalaqHub 框架，提供智能记账对话能力。

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 运行时 | Python | 3.10+ |
| Web 框架 | FastAPI | 0.110+ |
| 异步服务器 | Uvicorn | 0.32+ |
| WebSocket | websockets | 12.0+ |
| HTTP 客户端 | httpx | 0.25+ |
| 数据库 | SQLite (aiosqlite) | - |
| LLM 集成 | OpenAI SDK | 1.12+ |
| MCP 协议 | mcp + fastmcp | 1.0+ / 2.0+ |

---

## 项目结构

```
KoalaqHub/
├── koalaq_hub/                     # 核心代码
│   ├── api/                        # API 层
│   │   └── endpoints/              # HTTP/WebSocket 端点
│   │       ├── chat.py             # HTTP 对话接口
│   │       └── websocket.py        # WebSocket 对话接口
│   ├── config/                     # 配置模块
│   │   ├── settings.py             # 全局配置
│   │   └── agent_builder.py        # Agent 配置加载
│   ├── core/                       # 核心模块
│   │   ├── agents/                 # Agent 系统
│   │   │   ├── agent_registry.py   # Agent 注册表
│   │   │   └── agent_executor.py   # Agent 执行器
│   │   ├── llm/                    # LLM 集成
│   │   │   ├── llm_builder.py      # LLM 构建器
│   │   │   └── enhanced_llm_client.py  # 增强 LLM 客户端
│   │   ├── prompt/                 # 提示词系统
│   │   │   └── system_prompt_assembler.py
│   │   └── chat/                   # 对话处理
│   │       └── chat_processor.py
│   ├── database/                   # 数据库层
│   │   ├── repositories/           # 数据仓库
│   │   └── repository_adapter.py   # 仓库适配器
│   ├── mcp/                        # MCP 服务
│   │   └── server.py               # MCP 服务器
│   ├── models/                     # 数据模型
│   │   ├── agent.py                # Agent 模型
│   │   └── llm.py                  # LLM 模型
│   ├── tools/                      # 工具系统
│   │   ├── base.py                 # 工具基类
│   │   ├── registry.py             # 工具注册表
│   │   └── builtin/                # 内置工具
│   │       └── easy_accounts.py    # EasyAccounts 工具集
│   └── __main__.py                 # 入口文件
│
├── resource/                       # 资源文件
│   ├── config/                     # 配置文件
│   │   ├── agent.ini               # Agent 配置
│   │   └── llm_config.ini          # LLM 配置
│   ├── prompts/                    # 提示词
│   │   ├── layers/                 # 分层提示词
│   │   │   ├── task/               # 任务指导
│   │   │   └── role/               # 角色模板
│   │   └── functions/              # 功能型提示词
│   ├── role/                       # 角色定义
│   │   └── 小易.role
│   └── database/                   # SQLite 数据库
│
├── docs/                           # 文档
│   ├── dev-log/                    # 开发日志
│   └── dev-guide/                  # 开发指南
│
├── .env.example                    # 环境变量模板
├── requirements.txt                # Python 依赖
└── Dockerfile                      # Docker 构建文件
```

---

## 环境配置

### 1. 安装依赖

```bash
cd ai/KoalaqHub

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境变量

复制样例文件并修改：

```bash
cp .env.example .env
```

编辑 `.env`，配置 LLM：

```bash
# LLM 配置（必填）
LLM_EASY_ACCOUNTS_API_KEY=your_api_key
LLM_EASY_ACCOUNTS_URL=https://api.openai.com/v1
LLM_EASY_ACCOUNTS_MODEL=gpt-4o-mini

# EasyAccounts 后端地址
EASYACCOUNTS_URL=http://localhost:8081
```

### 3. 支持的 LLM 平台

| 平台 | URL | 说明 |
|------|-----|------|
| OpenAI | https://api.openai.com/v1 | 官方 API |
| 智谱 AI | https://open.bigmodel.cn/api/paas/v4 | GLM-4 系列 |
| 月之暗面 | https://api.moonshot.cn/v1 | Kimi 系列 |
| DeepSeek | https://api.deepseek.com/v1 | DeepSeek 系列 |
| 硅基流动 | https://api.siliconflow.cn/v1 | 多模型聚合 |

> 任何兼容 OpenAI API 格式的服务都可以使用。

---

## 开发调试

### 启动服务

```bash
cd ai/KoalaqHub
python -m koalaq_hub
```

服务启动后：
- HTTP API：http://localhost:8001
- WebSocket：ws://localhost:8001/ws/{agent_id}
- 健康检查：http://localhost:8001/health

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/ws/{agent_id}` | WebSocket | 对话连接 |
| `/ai/agents` | GET | 获取 Agent 列表 |
| `/ai/conversations` | GET | 获取会话列表 |
| `/sse` | GET | MCP SSE 端点 |
| `/mcp` | POST | MCP HTTP 端点 |

### 调试技巧

**1. 查看日志**

服务运行时会输出详细日志：
```
2026-01-06 10:00:00 - INFO - 用户消息: 记一笔午餐 20 元
2026-01-06 10:00:01 - INFO - 工具调用: current_date
2026-01-06 10:00:01 - INFO - 工具调用: accounts
2026-01-06 10:00:02 - INFO - 工具调用: types
2026-01-06 10:00:03 - INFO - 工具调用: add_flow
```

**2. 滚动日志（Docker 环境）**

配置 `LOG_DIR` 环境变量启用文件日志：
```bash
LOG_DIR=/app/logs
```

日志文件按日期滚动：`koalaq_20260106.log`

**3. WebSocket 测试**

使用 [websocat](https://github.com/vi/websocat) 或浏览器控制台：
```javascript
const ws = new WebSocket('ws://localhost:8001/ws/easy-accounts-agent');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.send(JSON.stringify({ message: '记一笔午餐20元' }));
```

---

## Docker 部署

### 构建镜像

```bash
cd ai
docker build -t easyaccounts-ai .
```

### Docker Compose

```yaml
services:
  ai:
    image: easyaccounts-ai
    ports:
      - "8001:8001"
    environment:
      - LLM_EASY_ACCOUNTS_API_KEY=your_api_key
      - LLM_EASY_ACCOUNTS_URL=https://api.openai.com/v1
      - LLM_EASY_ACCOUNTS_MODEL=gpt-4o-mini
      - EASYACCOUNTS_URL=http://server:8081
      - LOG_DIR=/app/logs
    volumes:
      - ./AI/database:/app/koalaq_hub_python/resource/database
      - ./AI/logs:/app/logs
      - ./AI/小易.role:/app/koalaq_hub_python/resource/role/小易.role
      - ./AI/task.prompt:/app/koalaq_hub_python/resource/prompts/layers/task/easy_accounts_instructions.prompt
    depends_on:
      - server
```

### 可映射的配置文件

| 宿主机路径 | 容器路径 | 说明 |
|-----------|---------|------|
| `./AI/database` | `/app/.../resource/database` | SQLite 数据库 |
| `./AI/logs` | `/app/logs` | 日志目录 |
| `./AI/小易.role` | `/app/.../resource/role/小易.role` | 角色定义 |
| `./AI/task.prompt` | `/app/.../layers/task/easy_accounts_instructions.prompt` | 用户自定义指导 |

---

## 内置工具

EasyAccounts Agent 内置以下工具：

| 工具 | 功能 | 说明 |
|------|------|------|
| `current_date` | 获取当前日期 | 返回 yyyy-MM-dd 格式 |
| `accounts` | 查询账户 | 返回账户列表和余额 |
| `types` | 获取分类 | 返回分类层级结构 |
| `year_statistics` | 年度统计 | 按月份的收支统计 |
| `flows` | 查询流水 | 支持多条件筛选 |
| `get_flow` | 获取流水详情 | 根据 ID 查询单条 |
| `add_flow` | 添加流水 | 记账 |
| `update_flow` | 更新流水 | 修改已有记录 |
| `make_excel` | 导出 Excel | 生成报表文件 |

---

## MCP 服务

KoalaqHub 支持作为 MCP 服务器，可被 Cherry Studio、Claude Desktop 等客户端调用。

### 启用 MCP

在 `.env` 中配置：
```bash
MCP_SERVER_ENABLED=true
MCP_TRANSPORT_MODE=sse  # 或 streamable-http
```

### 连接地址

| 模式 | 地址 |
|------|------|
| SSE | `http://localhost:8001/sse?token=<token>` |
| HTTP | `http://localhost:8001/mcp?token=<token>` |

> Token 从 Agent 的 `tool_tokens` 配置获取。

---

## 提示词系统

### 分层架构

```
<task>    任务层 - Agent 专属指导（工具使用规则）
<role>    角色层 - 身份定位（性格、语气）
<context> 上下文层 - 历史信息（会话总结）
```

### 任务指导多文件

`task_instructions_file` 支持数组格式，按顺序加载：

```ini
# agent.ini
task_instructions_file = ["easy_accounts_instructions_inner.prompt", "easy_accounts_instructions.prompt"]
```

- `*_inner.prompt` - 内部核心指导（开发者维护）
- `*.prompt` - 用户自定义指导（可通过 Docker 映射）

---

## 相关文档

| 文档 | 路径 |
|------|------|
| 提示词组装流程 | `docs/dev-guide/system_提示词组装使用流程.md` |
| 开发日志 | `docs/dev-log/` |
