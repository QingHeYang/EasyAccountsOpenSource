# 定时记账完整设计（v2.7.0）

本文档描述 EasyAccounts 后端"定时记账"功能的完整架构：数据模型、核心决策、状态机、服务层、调度执行、提醒机制、REST 接口、边界坑。

---

## 目录

1. [产品语义速览](#1-产品语义速览)
2. [数据库设计](#2-数据库设计)
3. [关键设计决策](#3-关键设计决策)
4. [状态机](#4-状态机)
5. [服务层](#5-服务层)
6. [REST 接口](#6-rest-接口)
7. [调度执行全流程](#7-调度执行全流程)
8. [提醒机制全流程](#8-提醒机制全流程)
9. [通知清理七处](#9-通知清理七处)
10. [主数据失效挂钩](#10-主数据失效挂钩)
11. [边界场景与历史坑](#11-边界场景与历史坑)
12. [相关代码文件清单](#12-相关代码文件清单)

---

## 1. 产品语义速览

### 1.1 这是什么

**定时记账**：让用户把**周期性真实账单**（房贷、订阅、工资、水电费等）交给系统代为记录，到点自动生成一笔 `flow`。

### 1.2 与快记模板的本质区别

| 维度 | 快记模板 `flow_template` | 定时记账 `scheduled_flow_rule` |
|---|---|---|
| 定位 | 预填辅助，用户手动触发 | 系统代执行，真实发生的账单 |
| 字段完整性 | 可部分填（作模板骨架） | **必须完整**（金额/账户/分类/收支/周期/时间） |
| 触发方式 | 用户点"使用模板"→ 进入填表页 | 扫描器到点自动生成 flow |
| 表归属 | `flow_template` | **独立表 `scheduled_flow_rule`**（不复用） |

### 1.3 产品硬约束（必须记住）

| 约束 | 含义 |
|---|---|
| **不补漏** | 服务停机/错过时刻 一律不补执行，只推游标 |
| **不重试** | 任何执行失败都不自动重试 |
| **五态单入口** | 所有 status 变更必须走状态机，禁止代码里 `setStatus` |
| **主数据失效触发** | 账户停用、分类停用/归档 → 规则自动失效 + 引用字段清空 |
| **邮件依赖 WebHook** | 后端只发 HTTP 到 WebHook，SMTP 由 WebHook 处理 |

产品需求原文：`docs/v2.7.0/plan-scheduled-flow.md`。

---

## 2. 数据库设计

### 2.1 四张表总览

| 表 | 用途 | 估算行数 |
|---|---|---|
| `scheduled_flow_rule` | 定时记账规则本体 | 个位数 ~ 百级 |
| `scheduled_flow_log` | 每次执行的事后日志（审计） | 规则数 × 周期累积 |
| `user_notice` | 站内通知（事前提醒用，预留扩展） | 低频累积 |
| `app_config` | 全局应用配置 k-v | 少量 key |

### 2.2 `scheduled_flow_rule` 规则表

```sql
id                 INT PK AUTO_INCREMENT
name               VARCHAR(50)  NOT NULL        -- 规则名
-- 记账完整字段（与 flow 对齐）
money              VARCHAR(20)  NOT NULL        -- 正数字符串；方向由 action.handle 决定
type_id            INT          NULL            -- 失效时置 NULL
action_id          INT          NOT NULL        -- action 不会失效，保持 NOT NULL
account_id         INT          NULL            -- 失效时置 NULL
account_to_id      INT          NULL            -- 转账场景必填
note               VARCHAR(200)
-- 周期配置
cycle_type         TINYINT      NOT NULL        -- 1每日 2每周 3每月 4每年
cycle_dates        VARCHAR(255)                  -- JSON；每日=null；每周=[1-7];每月=[1-31];每年=["MM-DD"]
run_time           VARCHAR(8)   NOT NULL        -- HH:mm:ss
-- 起止与状态
start_date         DATE         NOT NULL
end_date           DATE         NULL            -- NULL=永久
is_permanent       TINYINT(1)   NOT NULL DEFAULT 0
status             TINYINT      NOT NULL DEFAULT 1   -- 1未开始 2开始 3暂停 4完成 5失效
-- 调度游标
next_run_date      DATE
last_run_date      DATE
-- 提醒配置（per-规则）
reminder_enabled   TINYINT(1)   NOT NULL DEFAULT 0
email_enabled      TINYINT(1)   NOT NULL DEFAULT 0
create_time        DATETIME     NOT NULL

INDEX idx_sfr_status_next_run (status, next_run_date)
```

**重点字段**：

- `account_id / type_id` 允许 NULL —— 失效时置空，前端拿到 null 即知道该字段要补齐
- `action_id` 保持 NOT NULL —— action 是系统常量级数据，不会失效
- `cycle_dates` 用 JSON 字符串，按 cycle_type 解释：

| cycle_type | 样例 | 解释 |
|---|---|---|
| 1 每日 | `null` | 无需选 |
| 2 每周 | `[1,4]` | ISO 周一=1 周日=7 |
| 3 每月 | `[1,15,31]` | 1~31；31 号遇 2 月回退月末 |
| 4 每年 | `["03-01","10-01"]` | MM-DD；2-30 回退 2 月末 |

### 2.3 `scheduled_flow_log` 执行日志表

```sql
id             INT PK AUTO_INCREMENT
rule_id        INT          NOT NULL      -- 逻辑外键，不加 DB 约束
execute_time   DATETIME     NOT NULL
success        TINYINT(1)   NOT NULL
flow_id        INT          NULL          -- 成功时关联 flow.id
fail_category  TINYINT      NULL          -- 1=主数据类 2=其他类；成功为 NULL
fail_reason    VARCHAR(500) NULL

INDEX idx_sfl_rule_time (rule_id, execute_time DESC)
```

**特性**：
- **删规则后日志保留**（审计）。孤儿日志的 `rule_id` 指向已删规则
- Entity `@ManyToOne(rule)` 加 `@NotFound(IGNORE)`，避免 `EntityNotFoundException`
- DTO 对 `rule=null` 显示 `[规则已删除]` 兜底
- 用户可用 `DELETE /scheduledFlow/log/{id}` 或 `DELETE /scheduledFlow/log?ruleId=x` 手动清

### 2.4 `user_notice` 本地通知表

```sql
id                INT PK AUTO_INCREMENT
type              TINYINT      NOT NULL      -- 1=定时记账事前提醒（预留扩展）
title             VARCHAR(100) NOT NULL
content           VARCHAR(500) NOT NULL
related_rule_id   INT          NULL
related_run_date  DATE         NULL
is_read           TINYINT(1)   NOT NULL DEFAULT 0
create_time       DATETIME     NOT NULL

INDEX idx_un_read_create (is_read, create_time DESC)
```

**特性**：
- 本地生成，区别于云端公告 `NoticeService`（读 OSS JSON）
- 通过 `(related_rule_id, related_run_date)` 做防重复 + 精确清理

### 2.5 `app_config` 全局配置表

```sql
id            INT PK AUTO_INCREMENT
domain        VARCHAR(50)  NOT NULL
config_key    VARCHAR(50)  NOT NULL
config_value  VARCHAR(255) NOT NULL
updated_at    DATETIME     NOT NULL

UNIQUE KEY uk_app_config_domain_key (domain, config_key)
```

**定时记账用到的 key**（domain = `scheduled_flow`）：
- `remind_before_days`：提醒前 N 天（1~5）
- `remind_time`：全局提醒时刻 `HH:mm`

### 2.6 Liquibase changeset

文件：`resources/db/changelog/yd_jz_2.7.0.yaml`

9 个 changeset（建表 + 索引 + 种子数据），master 追加 include。

---

## 3. 关键设计决策

### 3.1 复用 FlowTemplate vs 独立表 → 独立表 ✅

产品明确"定时记账 ≠ 快记模板，不互转"。独立表 + 独立 Service，业务语义干净。

### 3.2 全局扫描 + 游标 vs 每规则一个 Trigger → 全局扫描 ✅

一个 `@Scheduled(cron = "0 * * * * ?")` 每分钟扫库，读 `next_run_date` 决定行动。不用 Quartz 等重型方案。

| 方案 | 优点 | 缺点 |
|---|---|---|
| ✅ 全局扫描+游标 | 持久化天然（游标在 DB）；规则增删改零成本；不依赖 Quartz | 精度 1 分钟 |
| ❌ 每规则 Trigger | 精度秒级 | Trigger 生命周期管理复杂；重启要重建；要引 Quartz 建 11 张表 |

### 3.3 cron 表达式 vs 自定义周期 → 自定义 ✅

产品要求**月末回退**（31 号遇 2 月落月末、2-29 非闰年落 2-28），**标准 cron 和 Quartz 扩展 cron 都表达不了**。所以必须自写 `CycleCalculator`。

### 3.4 失效清空字段 ≠ 删除规则 ✅

规则失效时：
- `status = 5 INVALID`
- **`account_id = NULL`** 或 **`type_id = NULL`**（被停用的那个）
- 通知全清

前端拿到规则详情看 `accountId == null` 就知道"账户需要补齐"，不需要后端返回 `invalidFields: [...]` 这种额外结构。

### 3.5 删规则不级联删日志 ✅

日志是账本审计的一部分，即使规则删除也应保留。孤儿日志通过 `@NotFound(IGNORE)` + DTO 兜底展示 `[规则已删除]`。

用户可以通过 `DELETE /scheduledFlow/log/{id}` 或 `DELETE /scheduledFlow/log?ruleId=x` 手动清理。

### 3.6 生成流水复用 FlowService.doAddFlow ✅

扫描器不自己造 flow 逻辑，而是构造一个 `FlowAddRequestDto`（带 `from="scheduled"` + note 尾追 ` #定时`）调现有 `FlowService.doAddFlow`。

**收益**：账户余额扣减、exempt/exemptMode、转账分流、事务保护等逻辑全部自动继承。未来 FlowService 改，定时记账自动同步。

### 3.7 邮件品牌标识 ✅

站内通知**不带** `[EasyAccounts]` 前缀（用户在 App 内自带上下文）；邮件 subject **加** `[EasyAccounts] ` 前缀 + body 末尾追 `—— EasyAccounts 记账助手`（跨出 App 要自证身份）。

### 3.8 开始日期校验下放前端 ⚠️

产品需求要求 `startDate ≥ today+1`。**后端已解除该校验**（`validateStartDateAfterToday` 方法保留但不调）交前端做 UX，方便测试 + 允许"今天即时启动"场景。

---

## 4. 状态机

### 4.1 五态 + 五事件

```
         ┌─── USER_START ────┐
         │                   │
   ┌───► 暂停 ─────┐         │
   │             │           │
未开始 ─ sys ──► 开始 ─── sys ──► 完成
                 │               │
                 │ sys/主数据    │
                 ▼               │
               失效 ◄────────────┘
                 │
                 └── USER_START ──┘
```

### 4.2 转移矩阵

| 源 \ 目标 | 开始 | 暂停 | 完成 | 失效 |
|---|---|---|---|---|
| 未开始 | `SYS_BECOME_RUNNING` | — | — | `SYS_INVALIDATE` |
| 开始 | — | `USER_PAUSE` | `SYS_COMPLETE` | `SYS_INVALIDATE` |
| 暂停 | `USER_START` | — | — | `SYS_INVALIDATE` |
| 完成 | `USER_START` | — | — | `SYS_INVALIDATE` |
| 失效 | `USER_START` | — | — | — |

其他组合一律抛 `BusinessException(ILLEGAL_STATE_TRANSITION, code=42011)`。

**关键点**：`SYS_INVALIDATE` 前置**非 INVALID 均可**（产品语义：任何活跃规则遇到主数据失效都该进入失效）。

### 4.3 实现位置

`utils/ScheduledFlowRuleStateMachine.java`，仅一个 public 方法：

```java
public static void transit(ScheduledFlowRule rule, Event event)
```

**强制约束**：所有改 `status` 的代码必须走这个方法，不允许直接 `rule.setStatus(x)`。违规会绕过合法性校验。

### 4.4 单测覆盖

`src/test/java/.../ScheduledFlowRuleStateMachineTest.java`：23 个用例，10 个合法转移 + 12 个非法转移 + 1 个错误码断言 + 1 个副作用安全断言。

---

## 5. 服务层

### 5.1 分层示意

```
Controller 层
  ScheduledFlowController         /scheduledFlow/**
  NoticeController                /notice/**
     │
     ▼
Service 层
  ScheduledFlowRuleService        核心业务（CRUD、状态、执行、失效挂钩）
  ReminderService                 提醒派发（资格判断+防重复+发送）
  AppConfigService                全局配置 k-v 读写
  UserNoticeService               通知 CRUD
     │
     ▼
Task 层
  ScheduledFlowExecuteTask        每分钟扫描执行
  ReminderDispatchTask            每天 remind_time 扫描提醒
     │
     ▼
工具层
  CycleCalculator                 周期计算（纯函数）
  ScheduledFlowRuleStateMachine   状态机
  NotificationWebHook             邮件对接 WebHook
  ScheduledFlowConst              全部常量
```

### 5.2 `ScheduledFlowRuleService` 方法清单

| 方法 | 用途 |
|---|---|
| `createRule(Entity)` | 创建 + 算首次 next_run_date + `checkAndDispatch` 即时补发 |
| `updateRule(id, patch)` | 覆盖字段 + 重算游标 + 清旧通知 + 补发 |
| `deleteRule(id)` | 删规则 + 级联删通知（**不删日志**） |
| `getRule(id)` / `listRules()` | 查 |
| `startRule(id)` | 状态机 + 字段校验 + 重算游标 + 补发 |
| `pauseRule(id)` | 状态机 + 清该规则通知 |
| `previewNextCycle(id)` | 调 CycleCalculator 返回下一轮执行日 |
| `executeRuleOrThrow(rule, today)` | 扫描器调：调 `FlowService.doAddFlow` + 删当天通知 |
| `recordSuccess / recordFailure` | 写执行日志 |
| `advanceCursor(rule, today, markExecuted)` | 推游标 + 完成转移 + 清旧 runDate 通知 |
| `markRunning(rule) / markInvalid(rule)` | 状态机封装 |
| `invalidateByAccount(id)` | 主数据事件：账户停用时 AccountService 调 |
| `invalidateByType(id)` | 主数据事件：分类停用/归档时 TypeService 调 |
| `deleteLog / clearLogsByRule` | 执行日志手动清理 |

### 5.3 `ReminderService.checkAndDispatch(rule)`

派发提醒的**单一入口**，内部串联：

1. `rule.reminderEnabled` 过滤
2. 状态在 `{NOT_START, RUNNING}` 过滤
3. `nextRunDate ∈ [today, today+N]` 窗口过滤
4. `existsReminderFor` 防重复
5. 写 `user_notice`
6. 若 `emailEnabled=true`，调 `NotificationWebHook.sendEmail`

被两个调用方使用：
- `ReminderDispatchTask` 每天 `remind_time` 扫一批
- `ScheduledFlowRuleService.createRule / updateRule / startRule` 后立即调一次（即时补发）

### 5.4 两个 Task

| Task | cron | 做什么 |
|---|---|---|
| `ScheduledFlowExecuteTask` | `0 * * * * ?` 每分钟 | 扫规则，按四分支决策执行/推游标/跳过 |
| `ReminderDispatchTask` | `0 * * * * ?` 每分钟 | 非 remind_time 立即 return；命中时扫区间内所有规则调 `checkAndDispatch` |

两个 Task 都挂 `@Configuration + @EnableScheduling`，跟 `SQLBackUpTask` 同风格。

### 5.5 CycleCalculator

纯函数工具类，无 Spring 依赖。对外两个方法：

```java
LocalDate nextRunDate(int cycleType, String cycleDatesJson, LocalDate from)
List<LocalDate> previewNextCycle(int cycleType, String cycleDatesJson, LocalDate anchor)
```

**硬原则**：比较一律 `LocalDate` 整体比（`isAfter / equals`），**禁止**拆 `getDayOfMonth()` 比较。否则"5/30 vs 6/1"会判反。

月末回退：`ym.atDay(Math.min(d, ym.lengthOfMonth()))` 一步到位。

单测：`CycleCalculatorTest` 23 个用例覆盖闰年、月末、跨月、跨年、预览、非法参数。

---

## 6. REST 接口

### 6.1 规则 CRUD（5）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/scheduledFlow/rule` | 新建 |
| PUT | `/scheduledFlow/rule/{id}` | 修改 |
| DELETE | `/scheduledFlow/rule/{id}` | 删除（级联删通知；**保留日志**） |
| GET | `/scheduledFlow/rule/{id}` | 详情 |
| GET | `/scheduledFlow/rule/list` | 列表 |

### 6.2 状态操作（2）

| 方法 | 路径 | 合法前置 |
|---|---|---|
| POST | `/scheduledFlow/rule/{id}/start` | 暂停 / 完成 / 失效 |
| POST | `/scheduledFlow/rule/{id}/pause` | 开始 |

### 6.3 预览（1）

| 方法 | 路径 | 返回 |
|---|---|---|
| GET | `/scheduledFlow/rule/{id}/preview` | 下一轮执行日列表；每日/每周=空 |

### 6.4 执行日志（3）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/scheduledFlow/log?ruleId=&page=&size=` | 倒序分页查 |
| DELETE | `/scheduledFlow/log/{id}` | 单条删 |
| DELETE | `/scheduledFlow/log?ruleId=x` | 按规则批量清 |

### 6.5 全局提醒配置（2）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/scheduledFlow/config/reminder` | 返回 `{remindBeforeDays, remindTime}` |
| PUT | `/scheduledFlow/config/reminder` | 更新；`remindBeforeDays` 1~5 校验，`remindTime` HH:mm 校验 |

### 6.6 通知（4）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/notice/list?isRead=` | 可按已读过滤；不传返回全部 |
| PUT | `/notice/{id}/read` | 单条标已读 |
| PUT | `/notice/markAllRead` | 全部标已读 |
| DELETE | `/notice/{id}` | 删除 |

### 6.7 主数据挂钩（改现有接口，3）

| 接口 | 挂钩动作 |
|---|---|
| `DELETE /account/deleteAccount/{id}` | 尾部调 `ScheduledFlowRuleService.invalidateByAccount(id)` |
| `DELETE /type/deleteType/{id}` | 尾部调 `invalidateByType(id)`（主+子分类都调） |
| `PUT /type/archiveType/{id}?archive=true` | 仅 `archive=true` 时调 `invalidateByType(id)` |

### 6.8 响应字段映射

| 字段 | 值 → 含义 |
|---|---|
| `cycleType` | 1每日 / 2每周 / 3每月 / 4每年 |
| `status` | 1未开始 / 2开始 / 3暂停 / 4完成 / 5失效 |
| `failCategory` | 1主数据类 / 2其他类 / null成功 |
| `notice.type` | 1事前提醒（预留扩展） |
| `ruleName`（日志 DTO） | 规则删除后为 `"[规则已删除]"` |
| `ruleName === null`（规则 DTO） | 无 |
| `accountId/typeId === null`（规则 DTO） | 规则失效导致的字段清空，前端提示"请补齐" |

---

## 7. 调度执行全流程

### 7.1 两步扫描

```
@Scheduled(cron = "0 * * * * ?") scan() {
  今日 today = LocalDate.now()
  现时 nowTime = LocalTime.now()

  // 步骤 1：未开始到期 → 自动切 RUNNING
  starting = ruleRepo.findDueRules(status=NOT_START, next_run_date<=today)
  for r in starting:
    ruleService.markRunning(r)   // SYS_BECOME_RUNNING

  // 步骤 2：开始态规则按四分支决策
  running = ruleRepo.findDueRules(status=RUNNING, next_run_date<=today)
  for r in running:
    processRule(r, today, nowTime)
}
```

### 7.2 四分支决策树

```
对一条命中规则:
  │
  ├── last_run_date == today      → skip（今天已执行过，幂等保护）
  │
  ├── next_run_date < today        → advanceCursor(markExecuted=false)
  │                                   (历史遗留：停机期间错过)
  │
  ├── now < run_time               → skip（今天还没到点，等）
  │
  ├── now.分钟 == run_time.分钟   → executeRule(rule, today)
  │                                   - executeRuleOrThrow → 生成 flow + 删当天通知
  │                                   - recordSuccess / recordFailure
  │                                   - advanceCursor(markExecuted=true)
  │
  └── now > run_time               → advanceCursor(markExecuted=false)
                                      (今天已过点，不执行)
```

### 7.3 `advanceCursor` 细节

```java
public void advanceCursor(rule, today, markExecuted) {
    Date oldNextRunDate = rule.getNextRunDate();

    if (markExecuted) rule.setLastRunDate(today);
    LocalDate next = CycleCalculator.nextRunDate(cycleType, cycleDates, today);

    if (endDate != null && next > endDate) {
        rule.setNextRunDate(null);
        stateMachine.transit(SYS_COMPLETE);
        completed = true;
    } else {
        rule.setNextRunDate(next);
    }
    save(rule);

    if (completed) {
        noticeRepo.deleteByRelatedRuleId(rule.id);           // 全清
    } else if (oldNextRunDate != null) {
        noticeRepo.deleteByRelatedRuleIdAndRelatedRunDate(
                rule.id, oldNextRunDate);                      // 清旧 runDate 那条
    }
}
```

**核心不变式**：每次调用 `advanceCursor`，`next_run_date` 一定前进（或 null 完成），**绝不停留在过去**。

### 7.4 失败分类

执行路径抛 `BusinessException` 时按 error code 分类：

| 错误码 | 分类 | 后续动作 |
|---|---|---|
| `ACCOUNT_DISABLED / TYPE_DISABLED / TYPE_ARCHIVED / TYPE_HAS_CHILDREN / ACCOUNT_NOT_FOUND / TYPE_NOT_FOUND / ACTION_NOT_FOUND` | 主数据类（1） | 写日志 + `markInvalid` |
| 其他 `BusinessException` / `Exception` | 其他类（2） | 写日志 + `advanceCursor`（保持 RUNNING） |

**两者都不重试不补记**（产品硬原则）。

---

## 8. 提醒机制全流程

### 8.1 全局配置 + per-规则开关

| 开关位置 | 字段 | 作用 |
|---|---|---|
| 全局 `app_config` | `remind_before_days`（1~5） | 提前 N 天发提醒 |
| 全局 `app_config` | `remind_time`（HH:mm） | 每天什么时候批量扫 |
| per-规则 `rule` | `reminder_enabled` | 这条规则要不要提醒 |
| per-规则 `rule` | `email_enabled` | 除站内通知外是否同时发邮件 |

### 8.2 两个扫描路径 + 即时补发

```
路径 A · Task 每天 remind_time 扫一批
  ReminderDispatchTask.scan():
    if now.time != remind_time: return
    rules = ruleRepo.findRulesForReminder(
              status IN [NOT_START, RUNNING],
              next_run_date ∈ [today, today+N])
    for r in rules: reminderService.checkAndDispatch(r)

路径 B · Service 创建/修改/启动规则后立即补发
  createRule / updateRule / startRule {
    save(rule)
    reminderService.checkAndDispatch(saved)
  }
```

**路径 B 的意义**：覆盖"用户下午新建规则 `startDate=明天 + remindBeforeDays=3`"这种窗口已开启的场景，不用等到明天 `remind_time`。

### 8.3 `checkAndDispatch` 决策链

```
checkAndDispatch(rule):
  if !rule.reminderEnabled: return
  if rule.status not in {NOT_START, RUNNING}: return
  if rule.nextRunDate == null: return

  runDate = toLocalDate(rule.nextRunDate)
  if runDate not in [today, today+N]: return     # 窗口外

  if noticeService.existsReminderFor(ruleId, runDate): return  # 已发过

  // 走到这里 → 发
  title = "定时记账提醒：" + rule.name
  content = 多行正文（见 §8.4）

  noticeService.create(NOTICE_TYPE_PRE_REMIND, title, content, ruleId, runDate)

  if rule.emailEnabled:
    emailSubject = "[EasyAccounts] " + title
    emailBody = content + "\n\n—— EasyAccounts 记账助手"
    notificationWebHook.sendEmail(emailSubject, emailBody)
```

### 8.4 站内通知 vs 邮件 的内容差异

**站内通知**（用户已在 App 内，自带品牌上下文）：

```
title: 定时记账提醒：房贷
content:
  您的定时记账规则「房贷」即将自动执行：

    执行时间：2026-05-24 09:00（30 天后）
    记账金额：3500.00 元
    账户：招商银行
    分类：贷款支出/房贷

  如无异常，系统将按时自动生成这笔流水。
```

**邮件**（跨出 App 要自证身份，加品牌前缀 + 签名）：

```
subject: [EasyAccounts] 定时记账提醒：房贷
body: <同上 content>

—— EasyAccounts 记账助手
```

### 8.5 邮件 ⇄ WebHook 契约

后端 `NotificationWebHook.sendEmail` 以 `multipart/form-data` POST 到 `webhook_url`：

| form 字段 | 值 |
|---|---|
| `file` | body 的 UTF-8 字节（伪装成文件上传，WebHook 端解码当正文） |
| `file_name` | subject |
| `file_type` | `"scheduled_reminder"` |

WebHook 端 `webhook.py` 匹配 `file_type == "scheduled_reminder"` 分支：不加附件，`MIMEText(file_content.decode('utf-8'), 'plain', 'utf-8')` 当 body 发纯文本邮件。

**无全局开关**：发不发由 `rule.email_enabled` 决定（Server 端控制）。用户没勾选就不会调 WebHook，不需要 WebHook 端再加一重开关。

---

## 9. 通知清理七处

规则进入"不会再执行"的状态或字段已对不上旧通知时，都要清：

| 触发点 | 清理范围 | 代码位置 |
|---|---|---|
| 执行成功 | 删该规则当天执行日那条（精确匹配） | `executeRuleOrThrow` |
| 规则删除 | 删该规则全部 | `deleteRule` |
| 规则更新 | 删该规则全部 + 补发新的 | `updateRule` |
| 规则暂停 | 删该规则全部 | `pauseRule` |
| 规则失效（账户停用） | 删该规则全部 | `invalidateByAccount` |
| 规则失效（分类停用/归档） | 删该规则全部 | `invalidateByType` |
| 规则自然完成（到 end_date） | 删该规则全部 | `advanceCursor` SYS_COMPLETE 分支 |
| 扫描推游标（错过/历史遗留） | 精确删旧 runDate 那条 | `advanceCursor` 其他分支 |

**设计理念**：用户在通知中心看到的永远是"还有意义的提醒"。

---

## 10. 主数据失效挂钩

### 10.1 三个触发源

| Service 方法 | 挂钩调用 | 顺便 |
|---|---|---|
| `AccountService.disableAccount(id)` | `scheduledFlowRuleService.invalidateByAccount(id)` | 主+转账目标账户都会命中 |
| `TypeService.disableType(id)` | `invalidateByType(parentId)` + 对每个子分类 `invalidateByType(childId)` | — |
| `TypeService.archiveType(id, archive=true)` | 同上，`archive=true` 时才调 | 取消归档不触发 |

### 10.2 `invalidateByAccount` 细节

```java
public void invalidateByAccount(Integer accountId) {
    List<Rule> rules = ruleRepo.findRulesByAccountId(accountId);  // 查所有引用（不过滤 status）
    for (rule : rules) {
        // 置空被停用账户的引用字段（主账户 / 转账目标账户 任一命中就置空）
        if (accountId.equals(rule.getAccountId()))   rule.setAccountId(null);
        if (accountId.equals(rule.getAccountToId())) rule.setAccountToId(null);

        stateMachine.transit(rule, SYS_INVALIDATE);   // status → 5
        ruleRepo.save(rule);
        noticeRepo.deleteByRelatedRuleId(rule.id);    // 清该规则所有通知
    }
}
```

### 10.3 为什么不过滤 status

**Repository 查询故意不加 `status = RUNNING`**，而是查所有引用该主数据的规则。这样：

- `status=NOT_START`（未到 startDate 的规则）：挂钩也会把它置失效，正确
- `status=PAUSED`（暂停中的规则）：挂钩也处理，正确
- `status=INVALID`（已失效）：已失效的规则 `accountId/typeId` 已经是 null，查询条件 `accountId = :id` 天然不命中，自动跳过

### 10.4 循环依赖说明

`AccountService → ScheduledFlowRuleService → FlowService → AccountService` 形成字段注入循环。

`application-local.properties` / `application-server.properties` 已有 `spring.main.allow-circular-references=true` 兜底，启动不报错。长期可重构为 `ApplicationEvent` 解耦（非必须）。

---

## 11. 边界场景与历史坑

### 11.1 月末回退

规则每月 31 号 / 每年 2-30 这类"无效日期"：`CycleCalculator` 内部用 `YearMonth.atDay(Math.min(d, ym.lengthOfMonth()))` 自动回退到当月最后一天。

具体：
- 每月 31 号：2 月 → 28/29（闰年）、4/6/9/11 月 → 30
- 每年 2-29：平年回退 2-28
- 每年 4-31：回退 4-30

### 11.2 `baselineForRecompute` 必须考虑 `lastRunDate`

update / start 重算 `next_run_date` 时的基准：

```java
base = max(today - 1, startDate - 1, lastRunDate)
```

三项都要纳入：
- `today - 1`：保底，已过的 startDate 时用今天作下限
- `startDate - 1`：未来的 startDate 作下限
- `lastRunDate`：**已执行过的规则不能回退到已执行日期之前**（否则 PUT 规则后会丢天）

### 11.3 `java.sql.Date.toInstant()` 抛异常

Hibernate 从 `@Temporal(TemporalType.DATE)` 列读出 `java.sql.Date`（`java.util.Date` 子类），它重写 `toInstant()` 强制抛 `UnsupportedOperationException`。

转 LocalDate 必须用 `getTime()` 绕过：

```java
private static LocalDate toLocalDate(Date date) {
    if (date == null) return null;
    return new java.sql.Date(date.getTime()).toLocalDate();
}
```

Task 和 Service 里的 `toLocalDate` 都要这样写。

### 11.4 Windows javac 编码陷阱

中文字符串 `【定时】` 编译后乱码（Windows 默认 GBK 读 UTF-8 源文件）。排查规律：
- **全角括号** `【】` 容易踩坑
- 半角括号 `[]` + 常用汉字 OK（如 `[规则已删除]`）
- `#` + 常用汉字 OK（如 ` #定时`）

根治：IDE `File Encodings` 全部 UTF-8 + `pom.xml` 显式 `<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>`。

短期兜底：避开全角特殊字符，复杂场景返回 ASCII marker（如 `[DELETED]`）让前端翻译。

### 11.5 `Flow.from` 列名

| 项 | 值 |
|---|---|
| DB 列名 | `from_source` |
| Entity `Flow.java` 字段 | `from` |
| MyBatis SelectProvider | `flow.from_source AS fromSource` + `BeanUtils.copyProperties` 对齐 |

定时记账写入 `from = "scheduled"` 通过 `BeanUtils.copyProperties(dto, flow)` + `FlowDao.addFlow(flow)` 的 MyBatis Mapper 显式 SQL 生效。

### 11.6 字段删除策略 `account_id/type_id NOT NULL` 放宽

`scheduled_flow_rule.account_id` / `type_id` 建表时**不设** NOT NULL，允许失效时置 null。`action_id` 保留 NOT NULL（action 不会失效）。

### 11.7 金额永远是正数

`flow.money` 和 `rule.money` **只存正数字符串**。扣减还是增加由 `action.handle` 决定（0 加 / 1 减 / 2 转账）。

账户余额可以为负（v2.6.0 注释了余额检查，支持信用卡/透支场景）。

---

## 12. 相关代码文件清单

### 12.1 Server

```
YD_JZ/src/main/java/com/deepblue/yd_jz/
├── entity/
│   ├── ScheduledFlowRule.java
│   ├── ScheduledFlowLog.java           (@NotFound(IGNORE))
│   ├── UserNotice.java
│   └── AppConfig.java
├── dao/jpa/
│   ├── ScheduledFlowRuleRepository.java
│   ├── ScheduledFlowLogRepository.java
│   ├── UserNoticeRepository.java
│   └── AppConfigRepository.java
├── utils/
│   ├── ScheduledFlowConst.java         (常量)
│   ├── CycleCalculator.java            (周期计算纯函数 + 23 单测)
│   ├── ScheduledFlowRuleStateMachine.java  (状态机 + 23 单测)
│   └── NotificationWebHook.java        (邮件对接 WebHook)
├── service/
│   ├── ScheduledFlowRuleService.java   (核心业务)
│   ├── ReminderService.java            (提醒派发单一入口)
│   ├── AppConfigService.java
│   └── UserNoticeService.java
├── task/
│   ├── ScheduledFlowExecuteTask.java   (每分钟执行扫描)
│   └── ReminderDispatchTask.java       (每天 remind_time 批量扫)
├── dto/
│   ├── ScheduledFlowRuleRequestDto.java
│   ├── ScheduledFlowRuleResponseDto.java
│   ├── ScheduledFlowPreviewDto.java
│   ├── ScheduledFlowLogResponseDto.java
│   ├── UserNoticeResponseDto.java
│   └── ReminderConfigDto.java
└── controller/
    ├── ScheduledFlowController.java    (15 个接口)
    └── NoticeController.java           (4 个接口)

YD_JZ/src/main/resources/db/changelog/
└── yd_jz_2.7.0.yaml                    (9 个 changeset)

YD_JZ/src/test/java/com/deepblue/yd_jz/utils/
├── CycleCalculatorTest.java
└── ScheduledFlowRuleStateMachineTest.java
```

### 12.2 WebHook

```
WebHook/webhook.py                      (新增 scheduled_reminder file_type 分支)
```

### 12.3 修改的现有文件

| 文件 | 改动 |
|---|---|
| `service/AccountService.java` | `disableAccount` 挂钩 `invalidateByAccount` |
| `service/TypeService.java` | `disableType` / `archiveType` 挂钩 `invalidateByType` |
| `exception/ErrorCode.java` | 追加定时记账相关错误码（42008-42016, 44007-44008） |
| `resources/db/changelog/db.changelog-master.yaml` | 追加 `yd_jz_2.7.0.yaml` include |

---

## 13. 相关文档

- 产品需求：`docs/v2.7.0/plan-scheduled-flow.md`
- 技术方案 + 迭代记录：`Server/docs/feature-guide/scheduled-flow-backend-design.md`
- 开发日志：
  - `Server/docs/dev-log/dev-log-2026-04-23.md`（P1-P5 落地）
  - `Server/docs/dev-log/dev-log-2026-04-24.md`（自测 + 8 bug 修复 + 机制迭代）

---

*文档版本：v2.7.0*
*更新时间：2026-04-24*
