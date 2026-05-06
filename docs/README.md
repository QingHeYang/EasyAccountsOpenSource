# EasyAccounts · 主管文档索引

> 本目录由项目主管 Claude 维护。各端开发文档在各自目录下，见末尾索引。

---

## 📚 主管侧文档（本目录）

### 角色与协作

| 文件 | 用途 |
|---|---|
| [`dev-claude-template.md`](./dev-claude-template.md) | 各端开发 Claude 的角色模板（实例化后落地为 `{模块}/CLAUDE.md`） |
| `../CLAUDE.md` | 项目主管 Claude 的角色定义（仓库根） |

### 路线图与跨版本规划

| 文件 | 用途 |
|---|---|
| [`roadmap-v2.6-v2.7.md`](./roadmap-v2.6-v2.7.md) | v2.6.x / v2.7.0 路线图（issue + 需求 + 状态总览） |

### 版本归档

每个版本目录下只保留**长期价值的过程文档**与**发版结果**。

> 产品 plan / 任务拆分 / 讨论草稿等**讨论过程产物不进 docs/**，全程在对话和 commit message 里完成。

#### v2.7.0（发版前收尾）

| 文件 | 类型 | 说明 |
|---|---|---|
| [`v2.7.0/changes-collect.md`](./v2.7.0/changes-collect.md) | 变更收集 | plan 之外的零碎修复 / 优化 / 新功能登记，发版前整理为 release notes |

---

## 🗺 全项目文档索引

### 各端开发 Claude 简报（CWD 启动后看的角色定义）

| 端 | 路径 |
|---|---|
| Server | [`../Server/CLAUDE.md`](../Server/CLAUDE.md) |
| Web | [`../Web/CLAUDE.md`](../Web/CLAUDE.md) |
| AI | [`../ai/CLAUDE.md`](../ai/CLAUDE.md) |

### 各端过程文档

| 端 | dev-guide（架构指南） | dev-log（开发日志） | 其他 |
|---|---|---|---|
| Server | [`../Server/docs/dev-guide/`](../Server/docs/dev-guide/) | [`../Server/docs/dev-log/`](../Server/docs/dev-log/) | [`../Server/docs/feature-guide/`](../Server/docs/feature-guide/) 专项特性记录 |
| Web | [`../Web/ydjz_web_v2/docs/dev-guide/`](../Web/ydjz_web_v2/docs/dev-guide/) | [`../Web/ydjz_web_v2/docs/dev-log/`](../Web/ydjz_web_v2/docs/dev-log/) | [`../Web/ydjz_web_v2/docs/api/`](../Web/ydjz_web_v2/docs/api/) 后端接口参考 |
| AI | [`../ai/KoalaqHub/docs/dev-guide/`](../ai/KoalaqHub/docs/dev-guide/) | [`../ai/KoalaqHub/docs/dev-log/`](../ai/KoalaqHub/docs/dev-log/) | — |

---

## 📝 文档分工原则

| 文档类型 | 谁写 | 谁维护 |
|---|---|---|
| 主管级 plan / roadmap / changes-collect / 任务包 | 项目主管 Claude | 主管 |
| 版本总文档 / Release Notes | 主管 | 主管 |
| 各端 dev-log（开发日志，按日期） | 各端 Claude | 各端 |
| 各端 dev-guide（架构指南，长期） | 各端 Claude | 各端 |
| 各端 feature-guide（专项特性）| 各端 Claude | 各端 |

**红线**：
- 主管**不**写代码、schema、技术方案、各端的过程文档
- 各端 Claude **不**改主管的 plan / roadmap、Git 提交、跨端协调

---

## 🔍 怎么找信息

| 想知道 | 看哪儿 |
|---|---|
| 当前版本要做什么 | `roadmap-v2.6-v2.7.md` 状态栏 + `v2.x.x/plan-*.md` |
| 某个功能的产品规则 | 对应的 `v2.x.x/plan-*.md` |
| 某个功能的技术方案 | 对应端的 `docs/feature-guide/*-design.md` |
| 某天具体改了什么 | 对应端的 `docs/dev-log/dev-log-YYYY-MM-DD.md` |
| 某个子系统怎么工作 | 对应端的 `docs/dev-guide/{topic}_*.md` |
| 即将发版的 release notes 素材 | `v2.x.x/changes-collect.md` + 各 plan 已完成内容 |
