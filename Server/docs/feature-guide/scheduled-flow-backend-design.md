# 定时记账 · 后端技术方案（v2.7.0）

本文档是**后端技术方案草案**，用于提交给项目主管 Review。产品需求见根目录 `docs/v2.7.0/plan-scheduled-flow.md`，本文档**不重复产品语义**，只回答「后端怎么实现」。

---

## 概览

| 项目 | 内容 |
|------|------|
| **分支** | `2.7.0`（或在其上拉 feature 分支，待主管定粒度） |
| **产品文档** | `docs/v2.7.0/plan-scheduled-flow.md`（v3 产品需求最终版） |
| **本文档作者** | 后端开发 Claude |
| **状态** | 🟡 方案草案，**尚未动代码**，待主管 Review |
| **涉及模块** | Server |

---

## 与产品需求的关键对齐

这部分**不是**重写产品需求，而是把会影响后端实现的关键约束提炼出来，作为后面所有技术选择的根据：

| 产品原则 | 后端含义 |
|---|---|
| 定时记账与快记模板独立共存，不互转 | **新建独立数据表**，不复用 `flow_template` |
| 五态状态机 | 后端只管**合法状态转移 + 字段合法性校验**；"必须编辑过才能点开始"属前端 UX，后端不实现标记位 |
| 任何错过都不补（停机 / HH:mm 已过一律跳过） | 启动补偿**只推进游标，不执行**；调度循环对"已过"直接跳过 |
| 不提供立即执行一次 | **后端不实现** `run-now` 接口 |
| 账户停用、分类停用/归档触发规则失效 | 在现有 AccountService / TypeService 的停用路径接切面式调用 |
| 每次执行写一条信息记录 | 新建执行日志表，成功/失败各一条 |
| 事前提醒 = 信息通知 + 可选邮件 | 新建信息通知表；邮件复用 WebHook |
| AI 端本版本不做 | 不预留 AI 端接口，不做工具层 |

---

## 一、数据模型

### 1.1 新建表一览

| 表 | 用途 | 估算行数 |
|---|---|---|
| `scheduled_flow_rule` | 定时记账规则本体 | 个位数 ~ 百级 |
| `scheduled_flow_log` | 每次执行的事后记录 | 与规则数 × 周期累积 |
| `user_notice` | 站内信息通知（事前提醒及未来其它通知通用） | 低频累积 |
| `app_config` | 全局应用配置（提醒前 N 天 + 提醒时间） | 1 ~ 少量 key |

> **为什么不复用云端公告 `NoticeService`**：现有 `NoticeService` 从 OSS 拉云端 JSON，是"面向全部用户的单向广播"；这里需要的是**本地数据库生成、可读写、可删除**的用户级通知，语义完全不同。

### 1.2 `scheduled_flow_rule` 表

```
┌─ 基础标识
│  id                 INT PK AI
│  name               VARCHAR(50) NOT NULL       -- 规则名
│  create_time        DATETIME NOT NULL          -- 创建时间
│
├─ 记账完整字段（与 Flow 对齐，生成流水时原样写入）
│  money              VARCHAR(20) NOT NULL       -- 金额，字符串，与 flow.money 一致
│  type_id            INT NOT NULL
│  action_id          INT NOT NULL
│  account_id         INT NOT NULL
│  account_to_id      INT NULL                   -- 转账时必填
│  note               VARCHAR(200)
│
├─ 周期配置
│  cycle_type         TINYINT NOT NULL           -- 1=每日 2=每周 3=每月 4=每年
│  cycle_dates        VARCHAR(255)               -- JSON 字符串，见 §1.3
│  run_time           VARCHAR(8) NOT NULL        -- HH:mm:ss，默认 ss=00
│
├─ 起止与状态
│  start_date         DATE NOT NULL              -- 必须 ≥ 创建时的 today+1
│  end_date           DATE NULL                  -- NULL 表示永久
│  is_permanent       TINYINT(1) NOT NULL        -- 冗余字段，由产品需求要求显式存
│  status             TINYINT NOT NULL           -- 1~5 见 §3
│
├─ 调度游标
│  next_run_date      DATE NULL                  -- 下次执行日
│  last_run_date      DATE NULL                  -- 上次执行日
│
└─ 提醒配置（per 规则）
   reminder_enabled   TINYINT(1) NOT NULL DEFAULT 0
   email_enabled      TINYINT(1) NOT NULL DEFAULT 0
```

### 1.3 `cycle_dates` 字段编码

统一用 JSON 字符串，按 `cycle_type` 不同解释：

| cycle_type | cycle_dates 示例 | 解释 |
|---|---|---|
| 1 每日 | `null` 或 `"[]"` | 无需选 |
| 2 每周 | `"[1,4]"` | 周一 + 周四（1~7，ISO 标准） |
| 3 每月 | `"[1,15,31]"` | 每月 1/15/31 号（31 号遇 2 月回退月末） |
| 4 每年 | `"[\"03-01\",\"10-01\"]"` | 每年 3-1 + 10-1（`"02-30"` 回退 2 月末） |

**选择 JSON 字符串的理由**：
- 避免再拉一张 `scheduled_flow_rule_date` 关联表，表数量可控
- 多选集合整体覆盖写，不做增量，JSON 天然表达
- 查询侧不需要 SQL 层索引（调度只读 `next_run_date`，不按具体日期过滤）

> ⚠️ Review 点 R1：是否接受 JSON 字符串方案？若希望规范化关联表，成本多一张 `scheduled_flow_rule_date`。

### 1.4 `scheduled_flow_log` 表

```
id                  INT PK AI
rule_id             INT NOT NULL                -- 关联规则
execute_time        DATETIME NOT NULL           -- 执行时刻
success             TINYINT(1) NOT NULL         -- 0/1
flow_id             INT NULL                    -- 成功时指向生成的 flow.id
fail_category       TINYINT NULL                -- 1=主数据类 2=其他类
fail_reason         VARCHAR(500) NULL           -- 失败原因文本
```

索引：`(rule_id, execute_time DESC)`，用于规则详情页按时间倒序翻历史。

### 1.5 `user_notice` 表

```
id                  INT PK AI
type                TINYINT NOT NULL           -- 1=定时记账事前提醒（预留扩展）
title               VARCHAR(100) NOT NULL
content             VARCHAR(500) NOT NULL
related_rule_id     INT NULL                    -- 事前提醒时指向规则
related_run_date    DATE NULL                   -- 事前提醒时指向预计执行日
is_read             TINYINT(1) NOT NULL DEFAULT 0
create_time         DATETIME NOT NULL
```

**后补需求兼容**：「执行过后自动删除对应事前提醒」实现方式 —— 调度执行生成流水成功后，根据 `rule_id + run_date` 删除匹配的 `user_notice`。

### 1.6 `app_config` 表

按 `domain` 区分业务域的 k-v 表，未来其他模块的全局配置也走这张表：

```
id            INT PK AI
domain        VARCHAR(50)  NOT NULL       -- 业务域，例：scheduled_flow
config_key    VARCHAR(50)  NOT NULL
config_value  VARCHAR(255) NOT NULL
updated_at    DATETIME     NOT NULL
UNIQUE KEY uk_app_config_domain_key (domain, config_key)
```

本期写入：
- `domain=scheduled_flow, config_key=remind_before_days, config_value=1`（1~5）
- `domain=scheduled_flow, config_key=remind_time, config_value=09:00`

### 1.7 现有 `flow` 表不改结构

- 定时记账生成的流水，**不新增列**，通过 `flow.from` 写一个专属枚举字符串（取值待定，见 Review 点 R3）来区分
- 备注里在尾部追加可视化标记，例如 `【定时】`，保持 UI 可识别
- 不加 `source_rule_id` 外键（前期不做流水 → 规则反向追溯；若未来需要可在后续版本扩字段）

> ⚠️ Review 点 R3：`Flow.from` 用什么字面值？候选：`scheduled` / `auto` / `SCHEDULED`。现有已用枚举：`ai` / `mcp` / `Claw`。建议保持小写英文短词 → **`scheduled`**。
>
> ⚠️ Review 点 R4：`Flow.from` 在 DB 的实际列名存疑（文档说 `from_source`，Bean 叫 `from`），动手前需要 grep `FlowSelectProvider` / `FlowDao` / v2.5.0 changelog 确认，若是 `from_source` 也不改，只确认语义。

### 1.8 Liquibase 新增文件

- 新建：`db/changelog/yd_jz_2.7.0.yaml`
- 在 `db.changelog-master.yaml` 追加 include
- changeset 命名遵循现有惯例：`2.7.0-create-scheduled-flow-rule` / `2.7.0-create-scheduled-flow-log` / `2.7.0-create-user-notice` / `2.7.0-create-app-config` / `2.7.0-seed-app-config-defaults`
- author: `claude`，每个 changeset 带 `remarks`

---

## 二、接口清单

全部接口路径前缀 `/scheduledFlow`，错误码沿用 `BusinessException + ErrorCode`。请求/响应字段命名驼峰。

### 2.1 规则 CRUD

| 方法 | 路径 | 说明 | 副作用 |
|---|---|---|---|
| POST | `/scheduledFlow/rule` | 新建规则 | 落库 status=未开始 |
| PUT | `/scheduledFlow/rule/{id}` | 修改规则 | 原样覆盖；状态允许时重算 next_run_date |
| DELETE | `/scheduledFlow/rule/{id}` | 删除规则 | 级联删其 `scheduled_flow_log` 和未读 `user_notice` |
| GET | `/scheduledFlow/rule/{id}` | 单个详情 | — |
| GET | `/scheduledFlow/rule/list` | 全部规则（分页可选） | — |

> ⚠️ Review 点 R5：规则删除时**级联删日志**还是**保留日志**？产品未明。倾向级联删（避免孤儿数据），但保留日志可追溯。

### 2.2 状态操作

| 方法 | 路径 | 说明 | 合法的前置状态 |
|---|---|---|---|
| POST | `/scheduledFlow/rule/{id}/start` | 点"开始" | 未开始 / 暂停 / 完成 / 失效 |
| POST | `/scheduledFlow/rule/{id}/pause` | 点"暂停" | 开始 |

`start` 接口后端逻辑：
1. 读规则，校验当前状态在允许集内
2. 按当前规则字段重算 `next_run_date`（§4.3 计算器）
3. 字段合法性校验：
   - `next_run_date` 能算出来且 ≤ `end_date`（或 `end_date` 为 NULL）
   - 引用的账户未停用、分类未停用/归档
4. 校验失败 → 抛业务异常（前端负责引导用户补齐字段再重试）
5. 校验通过 → 写回 `status=开始`

> 前端的"必须先编辑字段再点开始"是 UX 约束，由前端实现。后端只认字段合法性——用户不改任何字段就从"完成/失效"点开始，会被第 3 步自然拦下来。

**不提供** `run-now`、`enable/disable`、`/log/clear` 等接口。

### 2.3 预览

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/scheduledFlow/rule/{id}/preview` | 未来一轮执行日期列表（每月=下月；每年=下一年；每日/每周返回空） |

### 2.4 执行记录

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/scheduledFlow/log/list?ruleId=&page=&size=` | 执行历史分页查询；`ruleId` 可选 |

### 2.5 全局提醒配置

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/scheduledFlow/config/reminder` | 返回 `{ remindBeforeDays, remindTime }` |
| PUT | `/scheduledFlow/config/reminder` | 更新两个字段；`remindBeforeDays` 校验 1~5 |

### 2.6 信息通知（用户级）

通知是通用机制，不放到 `/scheduledFlow` 下。建议独立新控制器 `/notice`：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/notice/list?isRead=` | 按已读状态过滤 |
| PUT | `/notice/{id}/read` | 单条标记已读 |
| PUT | `/notice/markAllRead` | 全部已读 |
| DELETE | `/notice/{id}` | 删除单条 |

> ⚠️ Review 点 R6：通知接口放 `/notice` 还是放 `/home/notice`？现有 `HomeController` 已有 `/home/getNotices` 走云端公告，命名有歧义风险。建议独立 `/notice`。

### 2.7 跨端契约汇总（前端 + WebHook）

按 CLAUDE.md §4，以下对前端契约**增量**需要主管先跟前端对齐：

- 全部 §2.1 ~ §2.6 接口（全新）
- `GET /flow/getFlow/{id}` 响应里 `from="scheduled"` 的新值（前端流水标签要新增）
- `FlowAddRequestDto.from` 继续允许任意字符串，不收紧

对 WebHook 契约**增量**：
- 邮件发送调用约定（复用现有 `FileMakeWebHook` 还是新起 `EmailWebHook`，看现有能力，动手前再敲定）

---

## 三、状态机

### 3.1 五态 + 合法转移

后端只关心**合法的状态转移**和**字段合法性校验**。"必须先编辑才能重新开始"之类 UX 规则归前端。

```
未开始 ── sys ──► 开始 ◄─── user(start) ─── 暂停
                    │   ◄─── user(start) ─── 完成
            user    │   ◄─── user(start) ─── 失效
         (pause)    │
                    ├── sys ──► 完成（到达 end_date）
                    └── sys ──► 失效（主数据事件）

图例:
  sys    = 系统自动转换（调度器/启动补偿）
  user   = 用户通过 §2.2 接口触发
```

### 3.2 转移矩阵

| 源 \ 目标 | 开始 | 暂停 | 完成 | 失效 |
|---|---|---|---|---|
| 未开始 | sys（到开始日期）/ user(start) | — | — | — |
| 开始 | — | user(pause) | sys（到 end_date） | sys/主数据事件 |
| 暂停 | user(start) | — | — | — |
| 完成 | user(start) | — | — | — |
| 失效 | user(start) | — | — | — |

其他组合一律 `BusinessException(ILLEGAL_STATE_TRANSITION)`。

`user(start)` 额外要求**字段合法**（见 §2.2），校验失败抛异常而不是转移状态。

### 3.3 集中实现位置

新建 `ScheduledFlowRuleStateMachine`（utility 性质，无状态），唯一一个方法：

```
void transit(ScheduledFlowRule rule, RuleStateEvent event)
```

所有改状态的路径（user API / 调度器 / 补偿 / 主数据事件）必须调它，**不允许 Service 直接 set status**。

---

## 四、调度与执行

### 4.1 调度入口总览

参考现有 `SQLBackUpTask` 套路，新增两个定时任务类：

| Bean | cron | 职责 |
|---|---|---|
| `ScheduledFlowExecuteTask` | `0 * * * * ?`（每分钟 0 秒） | 扫规则，执行到点的记账 |
| `ReminderDispatchTask` | `0 * * * * ?`（每分钟 0 秒） | 扫规则，按全局提醒时间发站内/邮件提醒 |
| `StartupCompensation` | `@PostConstruct` 或 `ApplicationReadyEvent` | 启动时清理过期游标 |

> ⚠️ Review 点 R8：cron 频率。分钟级最划算（HH:mm 粒度）。每秒扫没必要；每 5 分钟会让 HH:mm 延迟明显。建议 1 分钟。

### 4.2 执行任务核心循环

```
findRules(status=开始, next_run_date<=today)
    ↓ for each rule
    是否到点? (now.time >= rule.run_time 且 与上次执行不是同一分钟)
        ↓ 否 → skip
        ↓ 是
    try:
        生成流水 (复用 FlowService 的 setNewFlow 核心逻辑)
        flow.from = "scheduled"
        flow.note = rule.note + "【定时】"
        写 scheduled_flow_log(success=1, flow_id=新 id)
        删除匹配的 user_notice(related_rule_id, related_run_date=today)
    catch 主数据类异常:  (账户停用 / 分类停用/归档)
        写 scheduled_flow_log(success=0, fail_category=1, fail_reason=...)
        stateMachine.transit(rule, INVALIDATE)
    catch 其他异常:
        写 scheduled_flow_log(success=0, fail_category=2, fail_reason=...)
        状态不变

    推进 next_run_date = 计算器(rule, from=today+1)
    若 next_run_date > end_date: stateMachine.transit(rule, COMPLETE)
    保存 rule
```

关键点：
- **幂等保护**：规则表加 `last_run_date` 字段；如果 `last_run_date == today` 且 `last_run_time_min == 当前分钟`，本次跳过。防止单分钟内多次触发（多实例不考虑，部署单实例）
- **事务边界**：每个规则独立事务，一条规则失败不影响其它规则
- **并发**：`@Scheduled` 默认单线程，本项目用户并发低，不做分布式锁；多实例部署不支持（声明在运维文档）

### 4.3 周期计算器 `CycleCalculator`

独立工具类，无 Spring 依赖，便于单元测试。签名：

```
LocalDate nextRunDate(CycleType type, List<Integer|String> dates, LocalDate from)
List<LocalDate> previewNextCycle(CycleType type, List<Integer|String> dates, LocalDate anchor)
```

**月末回退规则**：
- 每月 31 号 → 2 月 → 当月最后一天（28/29）；4/6/9/11 月 → 30
- 每年 2-30 → 2 月最后一天；4-31 → 4-30

**预览语义**：
- 每月：anchor 所在月的**下一个月**的所有选中日期（经月末回退）
- 每年：anchor 所在年的**下一年**的所有选中 MM-DD（经月末回退）
- 每日 / 每周：返回空列表

### 4.4 启动补偿（不补执行）

```
findRules(status=开始)
    ↓
    若 next_run_date < today:
        next_run_date = 计算器(rule, from=today)
        保存（不触发执行，不写日志）
    若 next_run_date = today 且 now.time > rule.run_time:
        next_run_date = 计算器(rule, from=today+1)
        保存
    若 next_run_date = today 且 now.time ≤ rule.run_time:
        保持，由 §4.2 执行任务接管
```

### 4.5 主数据失效事件挂钩

现有代码 `AccountService.disable(id)` / `TypeService.disable(id)` / `TypeService.archive(id, true)` 要在方法尾追加：

```java
scheduledFlowRuleService.invalidateByAccount(id);
// 或
scheduledFlowRuleService.invalidateByType(id);
```

`invalidateByAccount(accountId)` 逻辑：
- 查 `status=开始 AND (account_id=?  OR account_to_id=?)` 的规则
- 对每条 `stateMachine.transit(rule, INVALIDATE)`（不写执行日志，因为是主数据事件触发的即时保护）

> ⚠️ Review 点 R9：切面挂钩用「Service 方法内直接调用」还是「Spring ApplicationEvent」？前者耦合直观，后者解耦但难追踪。倾向直接调用，本项目规模不需要事件总线。

---

## 五、事前提醒

### 5.1 触发逻辑 `ReminderDispatchTask`

```
读 app_config.reminder → (N, HH:mm)
若当前时间分钟精度 != HH:mm → 直接 return
targetRunDate = today + N
findRules(status=开始, reminder_enabled=1, next_run_date=targetRunDate)
    ↓ for each rule
    写 user_notice(
        type=1,
        title=规则名,
        content="将于 {targetRunDate} {run_time} 自动记账：{金额} 元 {分类}",
        related_rule_id=rule.id,
        related_run_date=targetRunDate
    )
    若 rule.email_enabled:
        发邮件 via WebHook (payload 待与 WebHook 对齐)
```

### 5.2 邮件依赖提示

邮件发送能力依赖 WebHook 服务。后端只负责**发出请求**，WebHook 未配/不可达则记 warn 日志、不影响站内通知。**前端**在用户勾选"发邮件"时做 UI 提示（产品需求 §八第 11 条），不是后端的事。

---

## 六、生成流水的复用

不重造 Flow 创建流程，复用现有 `FlowService`。有两条路可选：

**A. 直接调用 `FlowService.doAddFlow(FlowAddRequestDto)`**（推荐）
- 优点：账户余额、exempt、内部转账逻辑与手工记账 100% 一致，未来 FlowService 改了这里自动同步
- 需要：把规则转成 `FlowAddRequestDto`，带上 `from="scheduled"`，`note` 追加 `【定时】`
- 需要区分：`doAddFlow` 里抛出的异常要在调度器里分类为"主数据类"和"其他类"

**B. 抽取一个 `FlowService.doAddFlowInternal()` 供调度器和 Controller 共用**
- 优点：显式区分用户发起和系统发起
- 缺点：要改动 FlowService，范围扩大

倾向 **A**。

> ⚠️ Review 点 R10：采用方案 A 还是 B？

**异常分类实现**：
- 主数据类异常 = 在 `doAddFlow` 前置检查阶段抛的 `BusinessException(ACCOUNT_DISABLED | TYPE_DISABLED | TYPE_ARCHIVED)`
- 其他类 = 其它 `BusinessException` 或 `RuntimeException`
- 需要在调度器 catch 时根据 `ErrorCode` 分支，这要求 ErrorCode 枚举里有这几个明确的错误码（现有有 `ACCOUNT_NOT_FOUND` `TYPE_NOT_FOUND` 但可能没有"停用""归档"专属码） → **可能需要补几个 ErrorCode**（见 R11）

> ⚠️ Review 点 R11：是否新增 `ErrorCode.ACCOUNT_DISABLED` / `TYPE_DISABLED` / `TYPE_ARCHIVED`？或者用 `OPERATION_NOT_ALLOWED` 复用？倾向新增专属码，分类判断干净。

---

## 七、实施阶段（供主管划分 feature 分支参考）

每阶段产出独立可测试，阶段间有依赖。

| 阶段 | 内容 | 交付 | 预估 |
|---|---|---|---|
| **P1 数据层** | Liquibase / Entity / Repository / DTO / 异常码 | 表已建，JPA 能 CRUD | 1d |
| **P2 规则 API** | 规则 CRUD + 状态机 + 预览 + 计算器单测 | 前端能管规则，无调度 | 2d |
| **P3 调度执行** | `ScheduledFlowExecuteTask` + 启动补偿 + 执行日志 + Flow.from 标记 | 规则到点自动记账 | 2d |
| **P4 主数据挂钩** | AccountService / TypeService 停用路径切入 + 规则失效 | 主数据事件正确触发失效 | 0.5d |
| **P5 提醒与通知** | `app_config` + `user_notice` + `ReminderDispatchTask` + `/notice` 接口 + 邮件 WebHook 对接 | 站内通知按时发 | 1.5d |
| **P6 联调收尾** | 跨端联调 / 边界测试（闰年 / 月末 / 停机） / 日志补充 | 端到端可用 | 1d |

**合计后端 ≈ 8d**，比主管旧版 plan 的 5d 多（新增通知/提醒、执行日志、状态机、主数据事件挂钩等产品需求）。

---

## 八、待主管 Review 的决策点汇总

| # | 决策点 | 备选 | 倾向 |
|---|---|---|---|
| R1 | `cycle_dates` 存 JSON 还是关联表 | JSON / 关联表 | JSON |
| R3 | `Flow.from` 枚举字面值 | `scheduled` / `auto` / `SCHEDULED` | `scheduled` |
| R4 | `Flow.from` DB 列名核实 | 动手前 grep 核实 | 动手前必做 |
| R5 | 规则删除时执行日志策略 | 级联删 / 保留 | 级联删 |
| R6 | 通知接口路径 | `/notice` / `/home/notice` | `/notice` |
| R7 | 调度 cron 频率 | 1min / 5min / 1s | 1min |
| R8 | 主数据失效挂钩方式 | Service 直调 / ApplicationEvent | Service 直调 |
| R9 | 生成流水复用方式 | 调 doAddFlow / 抽 internal | 调 doAddFlow |
| R10 | 停用归档错误码 | 新增专属码 / 复用 OPERATION_NOT_ALLOWED | 新增专属码 |

---

## 九、风险

| 风险 | 等级 | 后端缓解 |
|---|---|---|
| 月末 / 闰年边界算错 | 🟡 | `CycleCalculator` 单测覆盖全部边界 |
| 调度任务长期运行内存泄漏 | 🟢 | 单次扫描用短生命周期对象，SQL 分页取 |
| 启动补偿把 `next_run_date` 推到未来，用户误以为"为什么还没执行" | 🟡 | 启动日志打印每条规则的推进情况 |
| `Flow.from` DB 列名与 Bean 不一致 | 🟡 | 动手前 grep 核实（R4） |
| 多实例部署产生重复执行 | 🟢 | 当前产品定位单用户单实例，不处理；部署文档注明不支持多实例 |
| 主数据事件挂钩遗漏入口 | 🟡 | grep `setDisable(true)` / `setArchive(true)` 的所有写入路径统一走 Service 方法 |
| 通知表长期累积 | 🟢 | 产品 §十二 已登记"删除/归档能力"为后补，本版本不强制 |

---

## 十、不在本版本范围

明确拒绝的产品对应后端不做的事：

- 立即执行一次（`run-now`）
- 自动补漏（停机恢复补记）
- AI 端工具（`add_recurring_flow` 等）
- 定时规则 → 快记模板互转
- 执行失败自动暂停规则（产品 §十一第 4 条）
- 流水反向追溯到规则（不加 `source_rule_id` 外键）
- 多设备/多实例部署

---

## 文档边界声明

本文档由**后端开发 Claude** 起草，供**项目主管 Review**。
- 技术选型 / 表结构 / 接口清单 / 调度细节均为后端草案
- Review 通过前**不动代码**
- Review 后的修改历史在本文件末尾追加「修订记录」小节
