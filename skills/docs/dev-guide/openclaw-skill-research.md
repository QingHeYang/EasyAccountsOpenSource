# OpenClaw Skill 技术调研报告

> 调研日期：2026-04-01

## 一、OpenClaw 平台概述

OpenClaw 是 2026 年初爆发的开源个人 AI 助手平台，定位为"本地优先"的 AI 代理框架。

- **多渠道接入**：WhatsApp、Telegram、Slack、Discord、Signal、iMessage 等
- **多 LLM 支持**：25+ 提供商（Anthropic、OpenAI 等），一行配置切换
- **本地运行**：数据在自己机器上，不依赖第三方 SaaS
- **GitHub Stars**：250,000+
- **GitHub 仓库**：`github.com/openclaw/openclaw`
- **吉祥物**：太空龙虾 🦞

---

## 二、Skills 系统规范

### 2.1 目录结构

```
my-skill/
├── SKILL.md          # 必需 - YAML 元数据 + Markdown 指令
├── scripts/          # 可选 - 可执行脚本（bash 为主）
└── references/       # 可选 - 补充文档
```

### 2.2 SKILL.md 格式

```markdown
---
name: my-skill-name
description: 简短描述
metadata:
  openclaw:
    os: ["darwin", "linux", "win32"]
    emoji: "🦞"
    homepage: "https://example.com"
    requires:
      bins: ["curl", "jq"]
      env: ["MY_API_KEY"]
    primaryEnv: "MY_API_KEY"
---

## 指令部分（Markdown）

告诉 AI 代理如何执行任务的步骤说明。
可用 {baseDir} 引用 skill 所在目录路径。
```

### 2.3 关键字段

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 唯一标识符（snake_case） |
| `description` | 是 | 一行描述 |
| `requires.bins` | 否 | PATH 中必须存在的命令 |
| `requires.env` | 否 | 必须存在的环境变量 |
| `os` | 否 | 平台限制：darwin/linux/win32 |
| `primaryEnv` | 否 | 主要凭证环境变量 |
| `user-invocable` | 否 | 是否暴露为斜杠命令（默认 true） |

### 2.4 Skills 加载优先级（高→低）

1. `<workspace>/skills` — 工作区级
2. `<workspace>/.agents/skills` — 项目代理级
3. `~/.agents/skills` — 个人跨机器级
4. `~/.openclaw/skills` — 受管理/本地级
5. 内置 Skills（随安装包分发）
6. `skills.load.extraDirs` 配置目录

### 2.5 约束

- SKILL.md body 建议 500 行 / 5000 词以内
- 最大打包体积 50MB
- 每个 skill 约消耗 24 tokens 基础开销

---

## 三、社区实现模式调研

### 3.1 三种主流实现模式

| 模式 | 适用场景 | 代表案例 |
|------|----------|----------|
| **A. 内联 curl 示例** | 操作简单、参数少 | Trello、Notion |
| **B. helper 脚本** | 操作多、参数复杂 | GitLab（`scripts/gitlab_api.sh`） |
| **C. 混合** | 简单操作内联，复杂操作用脚本 | 大部分社区 skill |

**核心结论：社区压倒性地使用 bash + curl + jq，不使用 Python。**

Skill 不像 MCP 那样定义离散的工具 schema，而是在 SKILL.md 里用 markdown 写每个操作的 curl 示例，AI 模型读指令后自己构造命令执行。

### 3.2 认证管理模式

| 方式 | 说明 | 适用场景 |
|------|------|----------|
| **环境变量** | `requires.env` 声明，用户配置在 `~/.openclaw/.env` | 静态 API Key（Notion、Trello） |
| **配置文件** | 如 `~/.config/gitlab/api_token` | 文件级 token |
| **OAuth/登录** | 委托 CLI 工具处理刷新 | Twitter/X（xurl） |

- 环境变量在整个 shell 会话中持久存在，不需要跨脚本传递
- **安全规则**：永远不要把 token 打印到 LLM 上下文中

### 3.3 多操作组织方式

Skill 不定义离散的 tool schema，而是用两种方式组织多操作：

1. **Markdown 分节**：每个操作一个 `##` 标题 + curl 示例（Trello、Notion 用法）
2. **Helper 脚本**：`scripts/` 下放命名脚本，SKILL.md 指导 agent 调用对应脚本

### 3.4 参考案例

**Trello Skill（API wrapper，7+ 操作）：**
- `requires.bins: [jq]`
- `requires.env: [TRELLO_API_KEY, TRELLO_TOKEN]`
- 每个操作（list boards、create card、move card 等）一个 section + curl 示例

**Notion Skill（API wrapper，8+ 操作）：**
- `requires.env: [NOTION_API_KEY]`
- Bearer token 认证
- 操作：search、retrieve、create、update、query databases、append blocks

**GitLab Skill（社区，5+ 操作 + helper 脚本）：**
- Token 存储在 `~/.config/gitlab/api_token`
- `scripts/gitlab_api.sh` 封装所有 API 调用

---

## 四、ClawHub 发布规范

### 4.1 ClawHub 概述

ClawHub（`clawhub.ai`）是 OpenClaw 的官方技能注册表和市场。

- 13,700+ 第三方 Skills
- 支持语义搜索（向量 + 自然语言）
- GitHub 仓库：`github.com/openclaw/clawhub`
- 技术栈：TanStack Start + Convex + OpenAI embeddings

### 4.2 发布流程

```bash
# 认证
clawhub login

# 发布
clawhub skill publish <path>

# 其他管理命令
clawhub search [query]
clawhub install <slug>
clawhub inspect <slug>
clawhub list
clawhub skill rename <slug> <new-slug>
clawhub delete <slug>
```

### 4.3 安全注意事项

- 每个发布的 skill 生成 SHA-256 哈希并与 VirusTotal 比对
- 使用 Gemini 驱动的 Code Insight 分析可疑内容
- 历史事件：**ClawHavoc** 恶意攻击，数百个钓鱼 skills 上传

---

## 五、EasyAccounts Skill 设计方案

### 5.1 特殊性分析

我们的场景与常见 skill 不同：

1. **动态认证**：不是静态 API Key，需要 login 接口获取 token
2. **调用链依赖**：添加流水前必须 accounts → types → 可能 actions
3. **业务规则复杂**：typeId vs actionId 区分、分类可用性规则等
4. **写操作**：add_flow、update_flow 有特殊标记（🦞OpenClaw记账/更新）

### 5.2 最终方案：模式 C（混合）

```
easyaccounts/
├── SKILL.md              # 元数据 + 操作指南 + 简单操作的 curl 示例
└── scripts/
    ├── login.sh          # 登录获取 token
    ├── api.sh            # 通用 API 调用封装（读 token、处理 401）
    ├── add_flow.sh       # 添加流水（复杂 JSON 构造 + 🦞标记）
    ├── update_flow.sh    # 更新流水（复杂 JSON 构造 + 🦞标记）
    └── query_flows.sh    # 查询流水（多参数构造）
```

### 5.3 工具清单（11 个操作）

| 操作 | 实现方式 | API 端点 | 方法 |
|------|----------|----------|------|
| login | `scripts/login.sh` | `/auth/login` | POST |
| current_date | 内联（`date`命令） | 无 | - |
| accounts | 内联 curl | `/account/getAccount` | GET |
| types | 内联 curl | `/type/getType` | GET |
| actions | 内联 curl | `/action/getAction` | GET |
| year_statistics | 内联 curl | `/home/getHomeInfoV2/{year}` | GET |
| flows | `scripts/query_flows.sh` | `/screen/getFlowByScreen` | POST |
| get_flow | 内联 curl | `/flow/getFlow/{flowId}` | GET |
| add_flow | `scripts/add_flow.sh` | `/flow/addFlow` | POST |
| update_flow | `scripts/update_flow.sh` | `/flow/updateFlow/{flowId}` | PUT |
| make_excel | `scripts/query_flows.sh` 复用 | `/screen/makeExcel` | POST |

### 5.4 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `EASYACCOUNTS_URL` | 是 | 服务地址，如 `http://localhost:8081` |
| `EASYACCOUNTS_USERNAME` | 否 | 用户名（也可交互输入） |
| `EASYACCOUNTS_PASSWORD` | 否 | 密码（也可交互输入） |

### 5.5 Token 管理

- login 成功后存储到 `~/.easyaccounts_token`
- 后续所有 curl 从该文件读取，放入 `Authorization` header
- 遇到 401 时提示重新 login

### 5.6 来源标记

| 场景 | 字段 | 值 |
|------|------|-----|
| 添加流水备注 | note 追加 | `🦞OpenClaw记账` |
| 更新流水备注 | note 追加 | `🦞OpenClaw更新` |
| 来源字段 | from | `🦞` |

### 5.7 依赖声明

```yaml
requires:
  bins: [curl, jq]
```

---

## 六、OpenClaw vs Claude Code 关系

| 维度 | OpenClaw | Claude Code |
|------|----------|-------------|
| 定位 | 通用 AI 助手/管理者 | 编码 AI 代理 |
| 开发者 | 社区开源 | Anthropic 官方 |
| Skills 市场 | ClawHub，13,700+ | 本地 slash commands |
| 运行方式 | 后台自动化 | 终端交互式 |

两者可配合使用，社区插件 `openclaw-claude-code` 可将 Claude Code 作为 OpenClaw 的编码引擎。
