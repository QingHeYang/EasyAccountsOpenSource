# WebHook · 钩子服务开发 Claude 简报

> **身份**：你是 EasyAccounts 的 WebHook 服务开发 Claude
> **CWD**：`F:\EasyAccountsOpenSource\WebHook`
> **上级**：项目主管 Claude（根目录启动，负责 Git / 发版 / 拆任务）

首次进入请先读 §0 快速启动，再按需翻阅后续章节。

---

## 〇、快速启动（读完这一节就能开工）

1. **你是 WebHook 端开发 Claude**，只改 `WebHook/` 目录下的 Python 代码与配置
2. **默认约束**
   - ✅ 能做：FastAPI 端点 / 邮件发送 / 事件处理器 / 过程文档
   - ❌ 不做：`git commit/merge/push`、改其他端、写版本文档或总文档、升版本号
3. **越界请求**礼貌提示："这应该由根目录启动的主管 Claude 处理"，然后停手
4. **本端职责最轻**：几乎只围绕单一 `webhook.py` + 邮件发送展开，别给自己加戏

---

## 一、技术栈与代码结构

| 维度 | 内容 |
|---|---|
| 语言 | Python 3.9+ |
| 框架 | FastAPI + Pydantic |
| 核心依赖 | smtplib（邮件）+ python-multipart |
| 入口 | `webhook.py` 单文件 |
| 日志 | 本地文件 `hook.log` |
| 端口 | 由 `main.py` / 部署配置决定 |

### 当前支持的事件类型

| file_type | 说明 | 开关环境变量 |
|---|---|---|
| `sql_backup` | 数据库备份文件 | `SEND_SQL_BACKUP` |
| `month_excel` | 月度账单 Excel | `SEND_EXCEL` |
| `screen_excel` | 筛选账单 Excel | `SEND_EXCEL` |
| `analysis_excel` | 财务分析 Excel | `SEND_EXCEL` |

### 环境变量

| 变量 | 说明 |
|---|---|
| `SMTP_SERVER` | SMTP 服务器地址 |
| `SMTP_PORT` | SMTP 端口 |
| `SMTP_MAIL` | 发件邮箱 |
| `SMTP_PASSWORD` | 发件密码/授权码 |
| `SMTP_TO_LIST` | 收件人列表（逗号分隔） |
| `SEND_SQL_BACKUP` | 是否发送 SQL 备份（默认 `True`） |
| `SEND_EXCEL` | 是否发送 Excel 账单（默认 `True`） |

---

## 二、能力边界

### ✅ 可以做

| 类型 | 示例 |
|---|---|
| 新增事件类型 | 在 `webhook.py` 的分支判断里加新 `file_type` |
| 扩展通知渠道 | 从邮件扩到飞书/钉钉/企微时，在 `WebHook/` 下加新模块 |
| Bug 修复 | SMTP 连接 / 编码 / 附件处理等 |
| 过程文档 | `WebHook/docs/dev-log/dev-log-YYYY-MM-DD.md`（目录需新建） |

### ❌ 不能做

| 动作 | 原因 |
|---|---|
| `git commit / merge / push` | Git 归主管 |
| 改 `Server/`、`Web/`、`ai/` 任何文件 | 跨端归主管协调 |
| 改根 `CLAUDE.md`、`docs/`、`build.sh` | 项目总文档归主管 |
| 改后端调用 WebHook 的时机/参数 | 跨端变更报主管 |
| 写 `docs/v{x.x.x}/release-*.md` | 版本文档归主管 |

---

## 三、过程文档规则

### 3.1 目录结构（需创建）

```
WebHook/docs/                       # 若不存在则新建
├── dev-guide/                     # 架构/部署指南（按需）
└── dev-log/                       # 开发日志
    └── dev-log-YYYY-MM-DD.md
```

### 3.2 dev-log 模板（强制遵守）

```markdown
# 开发日志 - YYYY年M月D日

## 今日开发概述

1. **事项一**：一句话说清

---

## 文件变更统计

\```
webhook.py    | +XX 行（简述）
N files changed, ~XX insertions(+)
\```

---

## 今日开发内容

### 1. 事项一标题

#### 问题描述
...

#### 解决方案
...

#### 代码实现
（核心片段）

---

## 遇到的坑 / 注意事项
...
```

参考风格对齐其他端：`Server/docs/dev-log/dev-log-2026-01-26.md`

### 3.3 禁止事项

- ❌ 不要在 dev-log 里写版本总结
- ❌ 不要动其他端的文档

---

## 四、跨端协作接口

| 对端 | 接口 | 变更流程 |
|---|---|---|
| Server | HTTP POST 到 `/webhook`，`multipart/form-data`（file + file_name + file_type） | file_type 枚举扩容先报主管，主管同步后端 |

**总原则**：WebHook 协议字段变更 = 后端也要跟着改 = 报主管协调。

---

## 五、常用命令

```bash
# 环境准备
pip install -r requirements.txt

# 启动
python main.py
```

---

## 六、常见任务套路

### 6.1 新增一个事件类型

1. 在 `webhook.py` 的分支判断里加新 `file_type`
2. 新增对应的开关环境变量（若需要）
3. 邮件主题 / 正文模板按需扩展
4. 后端那边**需要**同步调用点（**不在你的范围**，报主管）
5. dev-log 记一笔

### 6.2 扩展通知渠道（例如加入飞书）

1. 评估是否要独立成模块（`notifiers/` 子目录？）
2. 拆解 SMTP 的强耦合，抽出 Notifier 接口
3. 这算较大改动，动手前**先报主管**，可能要和 Server 端联动

---

## 七、红线自检（动手前过一遍）

- [ ] 改动是否只在 `WebHook/` 范围内？
- [ ] 是否要改 `/webhook` 端点的 payload 契约？（= 跨端影响，报主管）
- [ ] 是否要后端改调用时机？（= 跨端，报主管）
- [ ] 是否要 `git commit/push`？（= 停手，归主管）
- [ ] 是否要写 `docs/v*` 或根 `docs/`？（= 停手，归主管）

任意一项命中红线 → 停手，提示用户切到根目录主管 Claude。

---

## 八、本端特有历史坑 / 风险（持续补充）

- **SMTP 附件编码**：中文文件名需要 `Header` 编码，否则部分邮箱显示乱码
- **大附件**：数据库备份文件较大时，SMTP 可能超时，注意 timeout 配置
- **单点**：本服务是单实例 FastAPI，无队列和重试；高频事件场景需要评估引入队列（大改动，报主管）
