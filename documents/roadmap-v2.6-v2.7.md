# EasyAccounts 路线图 — v2.6.x / v2.7

> 整理时间：2026-04-21
> 数据来源：GitHub Issues（[仓库地址](https://github.com/QingHeYang/EasyAccounts/issues)）
> 状态：v2.6.1 已发布，v2.6.x 维护中，v2.7 规划中

---

## 一、Bug 列表（待修复）

| # | 标题 | 模块 | 优先级 | 状态 | 备注 |
|---|------|------|--------|------|------|
| [#23](https://github.com/QingHeYang/EasyAccounts/issues/23) | 外网无法访问 AI 助手 | Server / Web | 🔴 高 | 已定位 | `user_id` header 被外层 nginx 丢弃（下划线问题）。已给用户 workaround，待版本根治（改用 URL query 参数） |
| [#27](https://github.com/QingHeYang/EasyAccounts/issues/27) | 手机端分类多次添加后返回需点击多次 | Web（移动端） | 🟡 中 | 待修 | 路由栈累积问题，应一次返回到设置页 |
| [#28](https://github.com/QingHeYang/EasyAccounts/issues/28) | 内部转账：总金额不计入，分账单明细疑似也不计入 | Server | 🟡 中 | 待确认 | 需先确认是预期行为还是 bug |
| [#29](https://github.com/QingHeYang/EasyAccounts/issues/29) | AI 报错不展示错误信息 | Web / AI | 🔴 高 | 待修 | AI 操作失败时前端无提示，用户无从排查 |
| [#31](https://github.com/QingHeYang/EasyAccounts/issues/31) | AI 使用智谱 GLM-4.6V-FlashX 时重复记账 | AI | 🔴 高 | 待修 | LLM 模型兼容性/重复调用问题，需要排查工具调用去重 |

---

## 二、需求列表（待实现）

| # | 标题 | 模块 | 优先级 | 备注 |
|---|------|------|--------|------|
| — | **定时记账**（每月订阅/房贷/水电等重复支出） | Server / Web | 🔴 高 | v2.7 主线功能，参考历史 #13 诉求 |
| [#32](https://github.com/QingHeYang/EasyAccounts/issues/32) | 增加删除回收站 | Server / Web | 🔴 高 | 配合 AI 记账防误删，AI 安全专项 |
| [#33](https://github.com/QingHeYang/EasyAccounts/issues/33) | 单日总支出、单月日支出统计 | Web / Server | 🟡 中 | 明细页日总支出 + 统计页日支出折线图 |
| [#26](https://github.com/QingHeYang/EasyAccounts/issues/26) | 授权设备记住密码 | Web / Server | 🟡 中 | 公网映射场景刚需，关联 #23 那批用户 |
| [#15](https://github.com/QingHeYang/EasyAccounts/issues/15) / [#7](https://github.com/QingHeYang/EasyAccounts/issues/7) | 账本导入（CSV / 支付宝 / 微信 / 银行） | AI / Skills | 🟢 观察 | **交由 AI 接管**，不做原生导入功能。通过 AI Skill + Excel 处理能力间接支持 |
| [#11](https://github.com/QingHeYang/EasyAccounts/issues/11) | 群晖 DSM 7.0+ 部署教程 | 文档 | 🟢 低 | #23 已证实群晖可跑，整理教程即可 |
| [#10](https://github.com/QingHeYang/EasyAccounts/issues/10) | 支持 sqlite3 | Server | 🟢 低 | 去 MySQL 依赖，改动大，可作为长期选项 |

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

### 🚀 v2.7（主版本，中期规划）

**主题**：定时记账 + AI 修复与增强

| 类型 | 条目 | Issue |
|------|------|-------|
| 大功能 | **定时记账**：每月订阅、房贷、水电等固定支出的周期性自动生成 | — |
| AI 修复 | AI 错误提示完善（前端展示失败原因） | #29 |
| AI 修复 | AI 重复记账防护（工具调用去重） | #31 |
| AI 修复 | 外网 AI 访问根治（user_id 改 URL query 参数） | #23 |
| AI 安全 | 删除回收站（流水软删除 + 恢复） | #32 |
| 统计 | 单日/单月日支出统计与折线图 | #33 |
| 登录 | 授权设备记住密码（token 长期化） | #26 |

> **说明**：账单导入（支付宝/微信/银行）**不作为原生功能**开发，后续交由 **AI + Excel Skill** 接管。用户可把账单导出成 Excel/CSV，让 AI 解析后批量记账。

### 🔮 远期候选（暂不排期）

- SQLite 支持（#10）——改动大，需评估价值
- 多账本 / 家庭协作（曾有用户提出 #21/#22，已关闭但可长期考虑）
- 多币种支持（来自问卷反馈）
- 预算与超支提醒（来自问卷反馈）
- 账单到期提醒（来自问卷反馈）

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
