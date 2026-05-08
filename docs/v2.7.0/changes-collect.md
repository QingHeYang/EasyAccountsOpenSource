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

### N3 · 版本升级庆祝动画

| 项 | 内容 |
|---|---|
| **用户感知** | 升级到新版本后**首次打开** Board 总览页，会有礼花/动画庆祝当前版本号；后续打开不再触发 |
| **触发逻辑** | 基于 `versionCode` 比对，每个用户每次升级仅触发一次（localStorage 存 `lastSeenVersionCode`）|
| **范围** | 双端（PC + 移动）Board 页面 |
| **依赖** | 新增 `canvas-confetti` 礼花动画库 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md) §9 |

### N4 · 移动端 FlowAdd 金额 + 收支合体卡（chip 直选 + 渐变联动）

| 项 | 内容 |
|---|---|
| **用户感知** | 移动端记账时选收支类型不再点弹窗，**直接在表单里 chip 选择** |
| **细节** | ① 顺序：支出 → 收入 → 转账（按使用频次）<br>② "不计入"项目分组折叠，默认收起<br>③ 选中后卡片背景按收支类型渐变（绿/红/蓝）<br>④ 默认选第一个支出<br>⑤ 大字号金额 + 横线分隔 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md) §4 |

### N5 · 移动端 Analysis 筛选面板重构

| 项 | 内容 |
|---|---|
| **用户感知** | 移动端"统计"页筛选从底部弹层改为**顶部 fixed 折叠面板**，所有时间相关筛选集中：快捷选项 / 自定义起止 / 选项开关 |
| **细节** | ① 开始/结束日期拆成两个独立 picker<br>② 快捷选项支持横向滑动<br>③ 头部按钮有非默认筛选时显示红点提示 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md) §3 |

### N6 · 定时记账开始日期最早明天（双端业务校验补齐）

| 项 | 内容 |
|---|---|
| **背景** | 用户新建定时记账时如果选今天但已经过了 runTime（执行时分），首日就不触发，歧义大 |
| **修复** | 双端 datepicker + 校验：开始日期最早只能选**明天**<br>移动端 `ScheduledFlowAdd` + PC 端 `ScheduledFlowManager` 一起改 |
| **附带** | ScheduledFlowAdd 接入 TypePicker，**移动端 4 个分类选择入口全部统一**（接续 E4）|
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md) §5, §6 |

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

### B8 · toast 全局体验优化 + 修 9 处全局 fail toast 被秒关 bug

| 项 | 内容 |
|---|---|
| **现象** | 业务调用失败后看不到错误 toast：5 个系统设置子页 + ScheduledFlowAdd 4 处 catch 块写了 `closeToast()`，把全局 fail toast 也一起关了 |
| **修复** | 9 处 catch 内不再 `closeToast`，让全局 onError 弹的 fail toast 自然显示 |
| **附带优化** | 长文本（>20 字）走横长条 toast，宽度 88%，duration 按字数线性；短文本走 fail 方形 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md) §4 |

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
| **附带修复** | 全局 fail toast 被 closeToast 秒关的 bug |
| **PC 端外观** | 外观设置 emoji 对齐移动端（☀️ / 🌙 / ⚙️） |
| **用户感知** | 移动端打开页面有明确"加载中"反馈；网络异常时也能看出是失败而不是空账本 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md) §1, §2, §3 |

### E4 · 移动端分类选择器抽象重构

| 项 | 内容 |
|---|---|
| **背景** | 移动端记账（FlowAdd / TemplateAdd）和统计（AnalysisType）原本各自实现一套分类选择 UI，逻辑重复且维护负担大 |
| **重构** | ① 新增 `mobile/components/flow/TypePicker.vue` —— 记账场景，**全展开网格视图替代 cascader**，self-contained（按 actionId 自拉、loading/empty/error 状态、竞态守卫）<br>② 新增 `mobile/components/analysis/StatTypePicker.vue` —— 统计场景，**全部分类（不按 action 过滤）+ 一级标题旁 action 标签 + 父级聚合"全部" chip**<br>③ FlowAdd / TemplateAdd / **ScheduledFlowAdd**（v2.7.0 末期补）接入 TypePicker，移除原生 vant cascader 代码<br>④ AnalysisType 接入 StatTypePicker，删除 -288 行原地分类树管理逻辑<br>⑤ flowAddState 清理废弃的 `cascaderValue` 状态字段 |
| **附带修复** | 父级聚合下同月既有收入又有支出时传 `3`（全部）而不是只看支出。**双端同时修**：移动端 `AnalysisType.chooseHandle` + PC 端 `TypeDetail.onMonthItemClick` |
| **用户感知** | 移动端选择分类的体验在 4 处页面统一一致；网格视图比 cascader 更直观 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-05.md) §6, §7, §8<br>[`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md) §6 |

### E5 · 图标库统一切到 Lucide

| 项 | 内容 |
|---|---|
| **背景** | 双端图标来自 Element Plus / Vant / 手写 SVG / emoji 多个来源，风格 / stroke 重量 / 颜色机制不一致 |
| **本次重构** | 装 `lucide-vue-next`，把所有"语义化业务图标"切到 Lucide：<br>① 双端导航 / 通知 / 设置主页 / 系统设置子页 / 系统设置抽屉 Section header / 主题选项 / 定时记账执行记录 全部替换<br>② Element Plus 仅保留状态符号（CircleCheckFilled 等填充态）+ 导航箭头<br>③ Vant 仅保留小型导航类图标 |
| **配套规范** | 新增 `Web/ydjz_web_v2/docs/dev-guide/icon_图标使用规范.md`：<br>① 图标库选型 / 统一参数 / 命名约定<br>② 双端通用语义对照表<br>③ 新增页面接入清单<br>④ 特殊场景注意（el-button 不支持 :icon=Lucide / van-cell 同理 / 垂直对齐 display:block / `:has()` 浏览器要求） |
| **用户感知** | 双端图标观感统一，尤其暗黑模式下不再有"有的图标偏黑、有的偏灰"的零碎感 |
| **dev-log** | [`Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md`](../../Web/ydjz_web_v2/docs/dev-log/dev-log-2026-05-08.md) §1, §2 |

---

### B7 · 外网无法访问 AI 助手（[Issue #23](https://github.com/QingHeYang/EasyAccounts/issues/23)）—— ✅ 文档级解决

| 项 | 内容 |
|---|---|
| **现象** | 用户在自家 nginx 反代后访问 EasyAccounts，AI 助手"连接失败" |
| **根因（彻底定位）** | **不是 user_id header / 下划线问题**，而是用户自己的反代 nginx 没配 WebSocket Upgrade 三件套（`proxy_http_version 1.1` + `Upgrade` + `Connection`），WebSocket 握手永远失败 |
| **诊断曲折记录** | 之前主管两次给出错误诊断（怀疑过 nginx 下划线、AI 中间件挡 WebSocket），最终核查代码确认：项目代码 + 内置 nginx 配置全部正确，问题 100% 在用户的反代配置上 |
| **解决方案** | **不改代码**，在 issue #23 评论区直接给用户完整 nginx 反代配置模板（重点：WebSocket Upgrade 三件套 `proxy_http_version 1.1` + `Upgrade` + `Connection`）|
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

## 📚 与主功能的关系

本文档登记**v2.7.0 全部用户可感知的变更**，包括主功能与零碎修复。
plan 类讨论过程产物不在 docs/ 中，发版前主管将本文档整理成对外 release notes。

主功能（已落地）：
- **定时记账**（v2.7.0 主线）—— 5 态规则、不补漏、信息记录、信息提醒
- **配置 UI 化**（邮件 SMTP + 备份 cron + 鉴权 + 自动 Excel）
- **WebHook 容器废弃**（邮件能力内聚到 Server）
- **自动月度 Excel 生成**

主功能 + 本文档全部条目汇成 release notes。

---

## 🔒 文档边界

- 本文档由项目主管 Claude 维护
- 各端 Claude 写好 dev-log 后，主管把对应 dev-log 路径补回本文档"dev-log"行
- 主管不在这里写技术细节，只登记"值得告诉用户"的条目
