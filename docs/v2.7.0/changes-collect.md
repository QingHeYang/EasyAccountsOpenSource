# v2.7.0 · 发版条目收集本

> 创建时间：2026-04-28
> 用途：主管侧持续登记**值得写进 release notes** 的零碎条目（除主功能定时记账之外的修复 / 优化 / 工程项）
> 工作流：开发 Claude 在 dev-log 里写细节 → 主管在这里登记条目 → 发版前由主管整理为正式 release notes

---

## 🐛 Bug 修复

### B1 · Excel 生成超时死锁（上古 Bug）

| 项 | 内容 |
|---|---|
| **影响** | 生成 Excel（月度 / 筛选 / 分析）时偶发超时与死锁 |
| **存在时长** | 上古 Bug，长期挂着 |
| **用户感知** | 偶尔点了"导出 Excel"卡住、超时、报错 |
| **本次处理** | v2.7.0 修复 |
| **根因** | OSIV + 双 ORM（JPA + MyBatis）混用导致 Hikari 池等待超时 |
| **dev-log** | [`Server/docs/dev-log/dev-log-2026-04-28.md`](../../Server/docs/dev-log/dev-log-2026-04-28.md) §5 |
| **关联文件** | `Server/YD_JZ/src/main/java/com/deepblue/yd_jz/service/AutoExcelExecuteService.java`（+@Transactional） |

### B2 · 配置类项目（分类 / 收支 / 账户）路由栈管理

| 项 | 内容 |
|---|---|
| **影响** | 在设置页新增分类 / 收支 / 账户时，路由栈累积，导致用户**需要反复点返回**才能回到设置页 |
| **关联 Issue** | 与 GitHub #27（手机端分类多次添加后返回需点击多次）属同类问题 |
| **用户感知** | 体验断崖：明明只想加几个分类，却要返回很多次 |
| **本次处理** | v2.7.0 修复（前端路由栈管理统一收拾） |
| **dev-log** | ⏳ 待前端 Claude 在 `Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-XX.md` 中详细记录 |
| **关联文件** | `useSmartBack.ts` 等共享层路由处理逻辑 |

---

## ⚡ 性能 / 稳定性优化

### O1 · MySQL 连接池与缓冲区调优

| 项 | 内容 |
|---|---|
| **背景** | **上一次（v2.6.x）**对数据库做过的优化使运行期报错风险**急剧升高**（具体表现见 dev-log） |
| **本次动作** | 增大 MySQL 连接池、缓冲区等参数，回正运行期稳定性 |
| **代价** | 内存消耗有所增加 |
| **收益** | 用户使用期间报错风险显著降低 |
| **影响范围** | 部署运维感知：内存占用上升；用户感知：操作更流畅、报错更少 |
| **dev-log** | ⏳ 待开发 Claude 在 `Server/docs/dev-log/dev-log-2026-04-XX.md` 中记录调整前后参数对比与压测/观察数据 |
| **关联文件** | `Server/MySQL/my.cnf`（MySQL 配置） |

> 升级提示：用户升级 v2.7.0 时若部署在低内存机器（如 512M Raspberry Pi），需关注 MySQL 容器内存占用变化。

---

## ✨ 新功能（v2.7.0 内追加）

### N1 · 单日 / 月日支出统计（[Issue #33](https://github.com/QingHeYang/EasyAccounts/issues/33)）

| 项 | 内容 |
|---|---|
| **来源** | 用户反馈："想对每日花销严格管控，看单月日支出及变化" |
| **用户诉求** | 每天打开 App 一眼看到"今天 -¥XXX"，并能拉整月趋势 |
| **本次落地** | ① 明细页：日期行展示**当日支出总金额**<br>② 统计页：选定某月用**折线图**展示该月每日支出 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-28-part2.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-28-part2.md) |

### N2 · 明细抽屉图片上限 3 → 9 张

| 项 | 内容 |
|---|---|
| **来源** | 用户反馈"3 张不够用" |
| **用户感知** | 编辑流水时可贴更多图片（购物小票多张 / 出行多张），PC 端 3×3 网格展示 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-28-part3.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-28-part3.md) §2 |

---

## 🐛 Bug 修复（续登）

### B3 · AI 报错不展示错误信息（[Issue #29](https://github.com/QingHeYang/EasyAccounts/issues/29)）

| 项 | 内容 |
|---|---|
| **影响** | AI 工具调用失败时前端无任何提示，用户看着对话卡住或者突然不动，无从排查 |
| **本次处理** | AI 端工具失败从裸字符串升级为结构化错误（错误码 / 用户可读消息 / 提示 / 是否可重试），前端 / LLM 都能消费 |
| **dev-log** | [`ai/KoalaqHub/docs/dev-log/dev-log-2026-04-29.md`](../../ai/KoalaqHub/docs/dev-log/dev-log-2026-04-29.md) Part 2 |

### B4 · 删流水后图片留孤儿

| 项 | 内容 |
|---|---|
| **影响** | 删流水后 `flow_image` 表关联和磁盘 `/Ledger/images/` 文件都不清理，长期会撑爆数据库和磁盘 |
| **存在时长** | 早期版本累积，跨版本残留 |
| **本次处理** | v2.7.0 修复（删 / 编辑流水都补上图片清理；并对历史孤儿数据做迁移清理） |
| **dev-log** | [`Server/docs/dev-log/dev-log-2026-04-29.md`](../../Server/docs/dev-log/dev-log-2026-04-29.md) §2 |

### B5 · 图片下载接口路径穿越漏洞

| 项 | 内容 |
|---|---|
| **影响** | `GET /image/{fileName}` 缺少 fileName 校验，理论上恶意 URL 可以读取服务器任意文件 |
| **风险等级** | 🔴 安全 |
| **本次处理** | v2.7.0 修复（fileName 严格校验） |
| **dev-log** | [`Server/docs/dev-log/dev-log-2026-04-29.md`](../../Server/docs/dev-log/dev-log-2026-04-29.md) §3 |

### B6 · 邮件配置 SMTP 输入框暗黑模式样式异常

| 项 | 内容 |
|---|---|
| **影响** | PC 端"系统设置 → 邮件 → 编辑"对话框暗黑模式下，input 内框超出外框 + 左右不充满 |
| **本次处理** | input 高度策略改用 Element Plus 标准变量，避免手撕样式与暗黑模式冲突 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-28-part3.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-04-28-part3.md) §1 |

---

## 🏗 架构 / 工程改进

### E1 · AI 提示词与工具描述全面对齐后端业务语义

| 项 | 内容 |
|---|---|
| **背景** | LLM 调后端工具准确率不高，根因是 AI 端工具描述与后端实际行为有偏差（约 9 处事实错误） |
| **本次重构** | ① 后端落盘《AI 工具调用 · 后端 API 业务语义说明》（约 585 行，给 AI 端参考）<br>② AI 端重写内部工具 `*_DESC` + ToolParam description<br>③ AI 端重写 MCP `@mcp.tool` 函数 docstring<br>④ AI 端重写任务级提示词 `easy_accounts_instructions_inner.prompt` |
| **用户感知** | 间接提升 —— AI 工具调用更准确，少误用接口 |
| **关联文档** | [`Server/docs/feature-guide/ai-api-business-guide.md`](../../Server/docs/feature-guide/ai-api-business-guide.md) |
| **dev-log** | [`Server/docs/dev-log/dev-log-2026-04-29.md`](../../Server/docs/dev-log/dev-log-2026-04-29.md) §1<br>[`ai/KoalaqHub/docs/dev-log/dev-log-2026-04-29.md`](../../ai/KoalaqHub/docs/dev-log/dev-log-2026-04-29.md) Part 1 |

### E2 · AI 端连锁稳定性修复（流式 / 历史 / DS-R1 / httpx / .env）

| 项 | 内容 |
|---|---|
| **影响** | 借 #29 主线修复时排查出多个稳定性问题：流式累积残缺 tool_call、历史污染回放、DS-R1 reasoning_content 协议、httpx timeout / 代理误判、.env 加载顺序 |
| **本次处理** | 一并修复，AI 端整体抗压能力显著提升 |
| **dev-log** | [`ai/KoalaqHub/docs/dev-log/dev-log-2026-04-29.md`](../../ai/KoalaqHub/docs/dev-log/dev-log-2026-04-29.md) Part 3 |

### E3 · 公告系统抽离重构 + 移动端加载体验改进

| 项 | 内容 |
|---|---|
| **公告系统重构** | ① 抽出 `useNotice.ts` 双端共享 composable（拉取 / 已读管理 / Markdown 渲染 / localStorage 持久化）<br>② 抽出 `NoticeCard.vue` 双端各自的卡片组件（含折叠/展开逻辑）<br>③ `NoticeDrawer.vue`（桌面）和 `NoticePopup.vue`（移动端）大幅瘦身（共 -300+ 行） |
| **移动端加载体验** | Board / Analysis / Flow / AnalysisType 4 个核心页加载流程统一：<br>① 加载中 `showLoadingToast` 提示<br>② 失败时清空数据 + 标记 `loadFailed`，让空态显示"加载失败"占位（不再误导用户以为"没数据"） |
| **用户感知** | 移动端打开页面有明确"加载中"反馈；网络异常时也能看出是失败而不是空账本 |
| **dev-log** | ⏳ 待 Web Claude 补 |

---

### B7 · 外网无法访问 AI 助手（[Issue #23](https://github.com/QingHeYang/EasyAccounts/issues/23)）—— ✅ 文档级解决

| 项 | 内容 |
|---|---|
| **现象** | 用户在自家 nginx 反代后访问 EasyAccounts，AI 助手"连接失败" |
| **根因（彻底定位）** | **不是 user_id header / 下划线问题**，而是用户自己的反代 nginx 没配 WebSocket Upgrade 三件套（`proxy_http_version 1.1` + `Upgrade` + `Connection`），WebSocket 握手永远失败 |
| **诊断曲折记录** | 之前主管两次给出错误诊断（怀疑过 nginx 下划线、AI 中间件挡 WebSocket），最终核查代码确认：项目代码 + 内置 nginx 配置全部正确，问题 100% 在用户的反代配置上 |
| **解决方案** | **不改代码**，新增 [`docs/deployment-reverse-proxy.md`](./deployment-reverse-proxy.md) 完整反向代理部署指南：含 nginx HTTP/HTTPS 模板、Caddy / Apache 模板、5 类常见坑、自查 checklist、排查步骤 |
| **关联动作** | 在 issue #23 重新回复用户，撤回旧诊断，给完整模板 |
| **dev-log** | 不涉及代码，无 dev-log |

---

## 📌 待登记位

后续其他零碎修复 / 优化 / 工程项请追加到下方对应小节，发版前由主管整理。

### 🐛 Bug 修复
- _待登记_

### ⚡ 性能 / 稳定性优化
- _待登记_

### ✨ 工程改进
- _待登记_

---

## 📚 与现有 plan 文档的关系

本文档**仅收集 plan 之外的零碎事项**。已有 plan 的主功能不在此重复登记：

- 定时记账主功能 → `docs/v2.7.0/plan-scheduled-flow.md`
- 配置 UI 化（邮件 + 备份 cron） → `docs/v2.7.0/plan-config-ui.md`
- 前端任务包 → `docs/v2.7.0/tasks-web.md`

发版前主管整理 release notes 时，把本文档 + 三份 plan 的"已完成"内容合并成对外公告。

---

## 🔒 文档边界

- 本文档由项目主管 Claude 维护
- 各端 Claude 写好 dev-log 后，主管把对应 dev-log 路径补回本文档"dev-log"行
- 主管不在这里写技术细节，只登记"值得告诉用户"的条目
