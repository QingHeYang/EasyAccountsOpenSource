# AI 模块 CLAUDE.md

全部使用中文进行交互

## Claude 角色定义

**你是 AI 模块的开发 Claude**，负责：
- AI 服务端的功能开发和维护
- MCP 工具开发
- LLM 集成和优化
- 过程文档编写

> 项目主管 Claude 在上级目录，负责版本文档和跨模块协调。

## 项目概述

**项目名称**: KoalaqHub (EasyAccounts AI 服务)
**技术栈**: Python 3.10+ / FastAPI / MCP / SQLite
**端口**: 8001
**当前版本**: v2.6.0

核心功能：
- 智能财务管理 AI 服务
- MCP 工具协议支持（可被 Cherry Studio、Claude Desktop 等客户端调用）
- 多 LLM 平台支持
- 流式对话（WebSocket + SSE）
- Token 统计和对话总结

---

## 目录结构

```
ai/
├── KoalaqHub/                      # 主项目目录
│   ├── koalaq_hub/                 # 核心代码
│   │   ├── __main__.py             # 主程序入口
│   │   ├── api/                    # REST API 层
│   │   │   ├── fastapi_app.py      # FastAPI 应用
│   │   │   ├── endpoints/          # API 端点
│   │   │   └── models/             # 请求/响应模型
│   │   ├── config/                 # 配置管理
│   │   │   ├── settings.py         # 全局配置（从 .env）
│   │   │   ├── agent_builder.py    # Agent 构建器
│   │   │   └── llm_builder.py      # LLM 构建器
│   │   ├── core/                   # 核心业务逻辑
│   │   │   ├── agents/             # Agent 管理
│   │   │   ├── chat/               # 聊天处理器
│   │   │   ├── executor/           # 执行器
│   │   │   ├── llm/                # LLM 客户端
│   │   │   ├── tool/               # 工具系统（MCP + 内部）
│   │   │   └── prompt/             # 提示词管理
│   │   ├── database/               # 数据库层
│   │   ├── models/                 # 数据模型
│   │   ├── mcp/                    # MCP 服务器实现
│   │   │   └── easyaccounts_server.py
│   │   └── tools/                  # 内部工具系统
│   │       └── builtin/            # 内置工具
│   ├── resource/                   # 资源文件
│   │   ├── config/                 # 配置文件
│   │   │   ├── agent.ini           # Agent 配置
│   │   │   └── llm_config.ini      # LLM 配置
│   │   ├── prompts/                # 提示词
│   │   │   ├── functions/          # 功能提示词
│   │   │   └── layers/             # 分层提示词
│   │   ├── role/                   # 角色文件
│   │   └── database/               # SQLite 数据库
│   ├── docs/                       # 开发文档
│   │   └── dev-guide/              # 开发指南
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
├── Dockerfile
└── CLAUDE.md                       # 本文件
```

---

## 开发命令

```bash
# 进入项目目录
cd KoalaqHub

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 API_PORT, LLM_TIMEOUT 等

# 运行服务
python -m koalaq_hub

# Docker 构建
cd ..  # 回到 ai 目录
docker build -t easyaccounts-ai .
```

---

## 核心模块说明

### 1. Agent 系统

| 组件 | 位置 | 职责 |
|------|------|------|
| Agent 模型 | `models/agent.py` | Agent 实例定义 |
| Agent 构建器 | `config/agent_builder.py` | 从 INI 创建 Agent |
| Agent 注册表 | `core/agents/agent_registry.py` | Agent 实例管理和缓存 |
| Agent 执行器 | `core/agents/agent_executor.py` | 统一执行入口 |

### 2. 工具系统（双工具架构）

**MCP 工具** (`core/tool/mcp/`)
- `server_manager.py` - MCP 服务器管理器
- `mcp_tool_manager.py` - MCP 工具管理器
- `mcp_tool.py` - MCP 工具类

**内部工具** (`tools/`)
- `registry.py` - 工具注册表（单例）
- `executor.py` - 工具执行器
- `builtin/easy_accounts.py` - EasyAccounts 工具集

### 3. 聊天处理器

| 处理器 | 用途 |
|--------|------|
| `http_chat_processor.py` | HTTP 请求，阻塞式返回 |
| `websocket_chat_processor.py` | WebSocket，流式返回 |
| `internal_chat_processor.py` | Agent 间调用 |

### 4. LLM 集成

- `core/llm/enhanced_llm_client.py` - 增强 LLM 客户端
- 支持流式输出、Function Calling、思考模式
- 多平台支持：OpenAI、DuckDuckGo、Tongyi 等

### 5. MCP 服务器

`mcp/easyaccounts_server.py` - 暴露给外部 MCP 客户端的服务

提供的工具：
- `accounts` - 查询账户
- `flows` - 查询流水
- `add_flow` - 添加流水（支持图片附件）
- `update_flow` - 更新流水（支持图片附件）
- `types` - 查询分类
- `year_statistics` - 年度统计
- `make_excel` - 生成 Excel 报表
- `current_date` - 当前日期

---

## 配置文件说明

### .env（环境变量）
```bash
API_PORT=8001
API_HOST=0.0.0.0
LLM_TIMEOUT=60
DATABASE_NAME=system.db
```

### agent.ini（Agent 配置）
```ini
[easy-accounts-agent]
id = 2
name = easy-accounts
llm_use = easy-accounts
enable_summary = false
enable_thinking = false
tool_round = 8
mcp_servers = []
inner_tools = ["accounts", "types", "flows", "add_flow", "update_flow", "make_excel"]
task_instructions_file = easy_accounts_instructions.prompt
```

### llm_config.ini（LLM 配置）
```ini
[easy-accounts]
api_key = <配置>
url = <配置>
model = <配置>
temperature = 0.7
platform = user_input
```

---

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/chat/chat` | POST | HTTP 聊天 |
| `/api/v1/agents/` | GET | Agent 列表 |
| `/ws/chat` | WebSocket | 流式聊天 |
| `/api/v1/conversations/` | GET | 会话列表 |
| `/api/v1/users/` | GET | 用户列表 |
| `/api/v1/config/` | GET | 配置信息 |
| `/health` | GET | 健康检查 |
| `/mcp` `/sse` | SSE | MCP 服务 |

---

## 开发指南

### 添加新的 MCP 工具

1. 在 `mcp/easyaccounts_server.py` 中添加工具函数
2. 使用 `@mcp.tool()` 装饰器
3. 定义参数类型和返回值
4. 参考已有工具如 `flows`、`add_flow`

### 添加新的内部工具

1. 在 `tools/builtin/` 下创建工具文件
2. 继承 `BaseTool` 基类
3. 实现 `execute` 方法
4. 在 `tools/__init__.py` 中注册

### 修改提示词

- 功能提示词：`resource/prompts/functions/`
- 角色提示词：`resource/prompts/layers/role/`
- 任务提示词：`resource/prompts/layers/task/`

### 开发文档

详细的开发指南在 `docs/dev-guide/` 目录：
- `agent_运行流程.md`
- `mcp_MCP工具开发指南.md`
- `llm_运行流程.md`
- `websocket_运行流程.md`
- `tool_执行流程.md`
- `function_功能模块开发.md`

---

## 重要注意事项

1. **Python 版本**: 需要 Python 3.10+
2. **依赖安装**: 使用虚拟环境，避免依赖冲突
3. **配置优先**: 修改配置前先复制 `.env.example`
4. **数据库**: SQLite 存储在 `resource/database/system.db`
5. **日志**: 使用 `colorlog` 和 `rich` 输出彩色日志
6. **异步**: 大量使用 `asyncio`，注意异步上下文
7. **Token 统计**: 所有 token 使用都会被跟踪

---

## 设计模式

| 模式 | 使用位置 |
|------|----------|
| Builder | AgentBuilder, LLMBuilder |
| Registry | ToolRegistry, AgentRegistry |
| Factory | DatabaseFactory |
| Adapter | RepositoryAdapter |
| Strategy | 聊天处理器（HTTP/WebSocket/内部） |
| Singleton | Configuration, ToolRegistry |

---

## 过程文档规则

开发过程中，需要在 `docs/` 目录下编写过程文档：
- 新功能开发：记录设计思路和实现细节
- Bug 修复：记录问题原因和解决方案
- 重构：记录重构目标和变更内容

文档命名格式：`{类型}_{功能名称}.md`
