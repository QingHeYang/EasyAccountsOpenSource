# EasyAccounts 路线图 — v2.6.x / v2.7

> 整理时间：2026-04-21
> 最近更新：2026-04-28（v2.7.0 进入收尾）
> 数据来源：GitHub Issues（[仓库地址](https://github.com/QingHeYang/EasyAccounts/issues)）
> 状态：v2.6.1 已发布；v2.7.0 主线 + 大部分连带项**已完成**，剩 AI 三件套由用户审计

---

## 一、Bug 列表（待修复）

| # | 标题 | 模块 | 优先级 | 状态 | 备注 |
|---|------|------|--------|------|------|
| [#23](https://github.com/QingHeYang/EasyAccounts/issues/23) | 外网无法访问 AI 助手 | Server / Web | 🔴 高 | ⏳ **待修** | `user_id` header 被外层 nginx 丢弃（下划线问题）。计划改走 URL query 参数 |
| [#27](https://github.com/QingHeYang/EasyAccounts/issues/27) | 手机端分类多次添加后返回需点击多次 | Web（移动端） | 🟡 中 | ✅ **已修** | useSmartBack.replaceAfterSubmit 共享 API + 5 个 *Add 页面接入（v2.7.0-config-ui） |
| [#28](https://github.com/QingHeYang/EasyAccounts/issues/28) | 内部转账：总金额不计入，分账单明细疑似也不计入 | Server | 🟡 中 | 待确认 | 需先确认是预期行为还是 bug |
| [#29](https://github.com/QingHeYang/EasyAccounts/issues/29) | AI 报错不展示错误信息 | Web / AI | 🔴 高 | ✅ **已修** | AI 工具失败结构化错误 + 借机修了 5 个连锁稳定性问题（流式/历史/DS-R1/httpx/.env） |
| [#31](https://github.com/QingHeYang/EasyAccounts/issues/31) | AI 使用智谱 GLM-4.6V-FlashX 时重复记账 | AI | 🔴 高 | ❌ **不做** | 评估后判定不在 AI 端硬拦：重复参数不一定是 bug（用户可能买两杯同价咖啡），属 LLM 判断力问题 |

---

## 二、需求列表（v2.7.0 范围 + 远期）

| # | 标题 | 模块 | 优先级 | 状态 | 备注 |
|---|------|------|--------|------|------|
| — | **定时记账**（每月订阅/房贷/水电等重复支出） | Server / Web | 🔴 高 | ✅ **已完成** | v2.7.0 主线，全套落地（双端 + AI 邮件提醒 + 通知中心 + 执行记录） |
| [#33](https://github.com/QingHeYang/EasyAccounts/issues/33) | 单日总支出、单月日支出统计 | Web / Server | 🟡 中 | ✅ **已完成** | 明细页当日合计 + 统计页月度日支出折线图 |
| [#32](https://github.com/QingHeYang/EasyAccounts/issues/32) | 增加删除回收站 | Server / Web | 🔴 高 | ❌ **取消** | 用户决定硬删够用，不做软删除回收站 |
| [#26](https://github.com/QingHeYang/EasyAccounts/issues/26) | 授权设备记住密码 | Web / Server | 🟡 中 | ❌ **取消** | 已被 v2.7.0 鉴权过期时间 UI 化覆盖（用户自配长过期时间） |
| [#15](https://github.com/QingHeYang/EasyAccounts/issues/15) / [#7](https://github.com/QingHeYang/EasyAccounts/issues/7) | 账本导入（CSV / 支付宝 / 微信 / 银行） | AI / Skills | 🟢 观察 | **交由 AI 接管**，不做原生导入功能。通过 AI Skill + Excel 处理能力间接支持 |
| [#11](https://github.com/QingHeYang/EasyAccounts/issues/11) | 群晖 DSM 7.0+ 部署教程 | 文档 | 🟢 低 | 待整理 | #23 已证实群晖可跑，整理教程即可 |
| [#10](https://github.com/QingHeYang/EasyAccounts/issues/10) | 支持 sqlite3 | Server | 🟢 低 | ❌ **取消** | 数据安全风险（SQLite 升级跨版本不够鲁棒），不做 |

---

## 二·B、v2.7.0 额外完成（非 issue 但实质做了）

| 主题 | 类型 | 说明 |
|---|---|---|
| **配置 UI 化** | ✨ 新功能 | 邮件 SMTP / 备份 cron / 鉴权 / 通知 全部从 env 下沉到 `app_config` 表，UI 可改且热生效 |
| **WebHook 模块物理移除** | 🏗 架构 | 邮件能力内聚到 Server，废弃 `WebHook/` 容器 |
| **自动月度 Excel 生成** | ✨ 新功能 | 配合定时记账配套的自动报表导出 |
| **Excel 死锁修复** | 🐛 上古 Bug | OSIV + 双 ORM 混用导致 Hikari 池等待超时 |
| **MySQL 调优** | ⚡ 性能 | my.cnf + Hikari 三项加固，回正 v2.6.x 一次数据库优化导致的报错风险 |
| **HTML 邮件模板** | ✨ 体验 | 8 封邮件全 HTML，品牌头部 + logo + 字段表 |

---

## 三、版本规划建议

### 🎯 v2.6.x（维护版本，小修小补）

**主题**：基础 Bug 修复 + 文档补充

| 类型 | 条目 | Issue |
|------|------|-------|
| Bug | 手机端分类返回路由栈修复 | #27 |
| Bug | 内部转账总金额计入逻辑确认 | #28 |
| 文档 | 群晖 DSM 部署教程 | #11 |

> AI 相关的 Bug（#23/#29/#31）集中在 v2.7 一起处理，因为届时要配合定时记账改动 AI 模块。

### 🚀 v2.7（主版本，已实质完成）

**主题**：定时记账 + 配置 UI 化 + 用户体验打磨

| 类型 | 条目 | Issue | 状态 |
|------|------|-------|------|
| 大功能 | **定时记账**：每月订阅、房贷、水电等周期性自动生成 | — | ✅ |
| 大功能 | **配置 UI 化**：邮件 / 备份 / 鉴权 / 通知全部从 env 下沉到 UI | — | ✅ |
| 大功能 | **自动月度 Excel** 生成 | — | ✅ |
| 架构 | **WebHook 容器废弃**，邮件能力内聚到 Server | — | ✅ |
| 统计 | 单日/单月日支出统计与折线图 | #33 | ✅ |
| Bug | 路由栈管理修复（手机端分类返回） | #27 | ✅ |
| Bug | Excel 生成超时死锁修复（上古 Bug） | — | ✅ |
| 性能 | MySQL 连接池 + 缓冲区调优 | — | ✅ |
| AI 修复 | AI 错误提示完善（工具失败结构化错误 + 5 个连锁稳定性问题）| #29 | ✅ |
| AI 修复 | AI 重复记账防护 | #31 | ❌ 评估不做（属 LLM 判断力，不在 AI 端硬拦）|
| AI 修复 | 外网 AI 访问根治 | #23 | ⏳ 待修（user_id 改走 URL query）|
| AI 安全 | 删除回收站 | #32 | ❌ 取消（硬删够用） |
| 登录 | 授权设备记住密码 | #26 | ❌ 取消（已被鉴权 UI 化覆盖） |

> **说明 1**：账单导入（支付宝/微信/银行）**不作为原生功能**开发，后续交由 **AI + Excel Skill** 接管。
> **说明 2**：AI 三件套审计结果 —— #29 已修 / #31 评估不做（属 LLM 判断力） / #23 待修。

### 🔮 v2.8.0 候选（已立项 plan，待开工）

- **多账本**（钱迹模式：账户共享、其他隔离）→ `docs/v2.8.0/plan-multi-book.md`
- **自定义查询条件 / 快速筛选**（用户保存常用筛选）→ `docs/v2.8.0/plan-saved-filter.md`

### 🔮 远期候选 / 已弃置

- ❌ SQLite 支持（#10）—— **明确不做**：跨版本数据安全风险
- ❌ 家庭协作 —— **明确不做**：每笔流水加用户字段改造太重
- ❌ 多币种 —— **明确不做**：用户无反馈
- ❌ 预算与超支提醒 —— **明确不做**：超了拦截/不拦截两难，本质是心理安慰
- ❌ 账单到期提醒 —— **明确不做**：跟项目定位不符
- 群晖 DSM 部署教程（#11）—— 文档类，待整理

---

## 四、规律观察

### 1. 账单导入交由 AI 接管

Issue #15 + #7 是**导入需求**，但经评估**不作为原生功能**开发。原因：

- 各家账单格式千差万别（支付宝/微信/招行/工行/农行…），原生解析维护成本极高
- AI + Excel Skill 组合已经能覆盖：用户把账单导出为 Excel/CSV，让 AI 读取后调用 `batch_add_flow` 批量入账
- skills/easyaccounts 已具备这个能力，只需把流程写进使用文档

**后续动作**：在 `skills/easyaccounts/README.md` 里增加"账单导入实战"章节，给出支付宝、微信的导出指引与示例对话。

### 2. AI 相关 Bug 集中在 harrisyi 一位用户

Issue #29/#31/#32 都来自同一个深度 AI 用户 harrisyi。说明：
- AI 记账功能已经被认真使用起来了
- 但稳定性/容错还需要打磨
- 这个用户值得作为 AI 功能的种子用户持续沟通

### 3. 外网部署是共性痛点

Issue #23（外网 AI）+ #26（记住密码）+ #11（群晖教程）都源自外网部署场景。这类用户基数不小，建议 v2.6.x 集中处理。

---

## 五、进度追踪

合并/发布时请回头更新本文档的状态栏。每个版本发布后，把已完成条目从这里移到对应的 `version/x.x.x.json` 里作为归档。

### v2.7.0 发版前最后一公里

- [x] AI 三件套审计：#29 已修 / #31 评估不做 / #23 待修
- [ ] **#23 user_id 改走 URL query**（剩下唯一 AI 端待修项）
- [ ] 联调抽测（前端建规则 → 等执行 → 看记录全流程）
- [ ] 邮件抽测（在配过 SMTP 的环境下走一次）
- [ ] `docs/v2.7.0/release-v2.7.0.md` 版本总文档（主管整理）
- [ ] 各端 dev-guide 残留 WebHook 引用清理（各端 Claude）
- [x] `changes-collect.md` 把 dev-log 路径补回链接
- [ ] 抬升镜像版本号 + Tag + 镜像构建上传
- [ ] 发布 Release Notes
