# v2.7.0 · 定时记账功能实施方案

> 创建时间：2026-04-23
> 分支：`2.7.0`
> 负责人：各端 Claude（本文档由项目主管拟订，执行时各端 Claude 细化过程文档）
> 状态：🟡 评估完成，待确认后开工

---

## 〇、版本定位

v2.7.0 的**主线功能**，亦是用户问卷反馈中呼声较高的场景：
- 每月订阅：Netflix、云盘、视频会员
- 房贷、车贷
- 水电燃气、物业费
- 工资（固定日期入账）
- 定投、储蓄

---

## 一、可行性评估（现状盘点）

| 模块 | 现状 | 结论 |
|---|---|---|
| **Server · 数据层** | `FlowTemplate` 实体已存在，`date_type` 字段**已预留但未充分使用** | 🟢 不新增主表，扩展既有表即可 |
| **Server · 调度** | `@EnableScheduling + @Scheduled(cron)` 已投入使用（`SQLBackUpTask`） | 🟢 不引入新依赖 |
| **Server · 来源标记** | Flow 表的 `from` 字段已支持枚举扩展（ai / mcp / Claw / …） | 🟢 新增 `scheduled` 枚举值即可 |
| **Web · 设置入口** | 已有 `TemplateManager.vue` 管理快记模板 | 🟢 扩展 Template 而非新建页面 |
| **Web · 流水标签** | `FlowItem.vue` 已展示 ai/mcp/Claw 标签 | 🟢 追加"定时"标签同构即可 |
| **AI · 工具注册** | 装饰器注册 + 自动发现 | 🟢 新增 `add_recurring_flow` 等工具无感接入 |

**核心判断**：**不做大手术**，复用 `FlowTemplate` 扩展 `date_type` + 定时调度任务 + UI 周期配置三件事即可。

---

## 二、核心架构决策

### 决策 1：复用 `FlowTemplate` vs 新建 `scheduled_flow`

**决策**：复用 `FlowTemplate`，扩展其 `date_type` 字段含义。

**理由**：
- 定时记账本质是"带周期策略的模板"，与快记模板共享 80% 字段（账户、分类、金额、备注）
- 避免在两个地方维护相似逻辑
- 数据迁移成本为零，已有的快记模板可视为"不自动触发"的特例

**新语义**：

| `date_type` | 含义 | 是否自动生成 |
|---|---|---|
| `0` | 纯快记模板（一键录入，手动触发） | 否（现有行为） |
| `1` | 每日 | 是 |
| `2` | 每周（配合 `cycle_value` 指定星期几） | 是 |
| `3` | 每月（配合 `cycle_value` 指定日期） | 是 |
| `4` | 每年（配合 `cycle_value` 指定 MM-DD） | 是 |

### 决策 2：调度策略

**决策**：单一 `@Scheduled(cron)` 每日凌晨扫描，幂等推进 `next_run_date`。

**理由**：
- 最简方案，无需引入 Quartz
- 幂等性基于 `next_run_date` 前进保证，即使服务重启漏执行也能自动补齐
- 用户日常感知的定时记账精度到"天"即可，无需精确到分钟

### 决策 3：漏执行补偿

**决策**：启动时检查 `next_run_date <= today`，**补齐每一笔**（批量生成）。

**场景**：服务器停机一周，回来后该月 5 号的房贷应当被补上。

### 决策 4：新增流水的来源标记

**决策**：`flow.from = 'scheduled'`，前端展示粉紫色"定时"标签。

---

## 三、数据模型变更

### 3.1 `flow_template` 表扩展

在 `db/changelog/yd_jz_2.7.0.yaml` 中新增 changeset：

```yaml
# 字段示意，实际以 Liquibase YAML 语法为准
- addColumn tableName=flow_template
    - column name=cycle_value      type=VARCHAR(32)   # 周期具体值：星期几/几号/MM-DD
    - column name=start_date       type=DATE          # 规则生效起始
    - column name=end_date         type=DATE NULL     # 规则结束（可空）
    - column name=next_run_date    type=DATE NULL     # 下次执行日（NULL = 非周期性）
    - column name=last_run_date    type=DATE NULL     # 上次执行日
    - column name=enabled          type=BOOLEAN DEFAULT TRUE  # 暂停/恢复
    - column name=auto_run         type=BOOLEAN DEFAULT FALSE # 是否自动生成（区分快记模板）
```

### 3.2 `flow` 表扩展

- `from` 字段**新增枚举值** `scheduled`（无需改表结构，仅扩语义）
- 建议新增 `source_template_id` 关联回定时模板，方便追溯（选做）

---

## 四、任务拆分（按模块）

### 🟦 Server 端任务清单

> 交付到 `2.7.0-server-scheduled` feature 分支（如需要），或直接在 `2.7.0` 上推进

| # | 任务 | 产出 | 预估 |
|---|---|---|---|
| S1 | Liquibase changeset 扩展 `flow_template` 表 | `yd_jz_2.7.0.yaml` | 0.5d |
| S2 | `FlowTemplate` 实体字段同步 | `FlowTemplate.java` | 0.5d |
| S3 | 周期计算工具类 `CycleCalculator` | 输入 dateType + cycleValue + 基准日，输出 nextRunDate | 1d |
| S4 | `ScheduledFlowTask` 定时任务 | `@Scheduled(cron="0 5 0 * * *")` 每日 00:05 扫描、生成、推进 | 1d |
| S5 | 补偿逻辑 | 启动时 `@PostConstruct` 扫一遍过期的 `next_run_date` | 0.5d |
| S6 | REST API 改造 | `/flowTemplate` 系列接口新增周期字段；新增 `enable/disable` `run-now`（手动触发一次）`preview`（预览未来 N 次执行日） | 1d |
| S7 | 生成的 Flow 标记 | 写入时 `from='scheduled'`（+ 可选 `source_template_id`） | 0.2d |
| S8 | 单元测试 | `CycleCalculator` 各周期边界（闰年、月末 31 号、跨年） | 0.5d |
| **合计** | | | **~5d** |

**关键边界**：
- 月末兼容：月定为 31 号时，2 月 → 28/29 号，4/6/9/11 月 → 30 号
- 用户时区：服务器默认 +08:00，跨时区场景暂不考虑
- 账户被删：规则自动置为 `enabled=false`，不报错
- 分类被删：同上

### 🟩 Web 端任务清单

| # | 任务 | 产出 | 预估 |
|---|---|---|---|
| W1 | `TemplateManager.vue` 扩展"定时记账"标签页 | 桌面端 + 移动端两套 | 1d |
| W2 | 周期配置组件 `CycleSelector.vue` | 四种 dateType + cycleValue 表单 | 1d |
| W3 | 启停开关 + 手动触发按钮 | 调用 S6 的 enable/disable/run-now | 0.5d |
| W4 | 未来执行日预览 | 调用 S6 的 preview，列出未来 3 次执行日 | 0.5d |
| W5 | `FlowItem.vue` 新增"定时"标签 | `flow.from === 'scheduled'` 展示 | 0.3d |
| W6 | 流水明细页展示关联定时规则 | 点击标签跳转到规则详情（可选） | 0.5d |
| W7 | 路由 + 菜单入口 | 设置页菜单加"定时记账"入口 | 0.2d |
| **合计** | | | **~4d** |

**UX 要点**：
- 创建规则时**可选立即执行一次**（防止"下月 1 号才开始记的房贷，这个月已经交过了"场景的重复）
- 列表排序：按下次执行日升序
- 暂停的规则视觉上灰掉

### 🟨 AI 端任务清单

| # | 任务 | 产出 | 预估 |
|---|---|---|---|
| A1 | 新工具 `add_recurring_flow` | 基于自然语言创建定时规则 | 0.5d |
| A2 | 新工具 `list_recurring_flows` | 查询所有启用的规则 | 0.3d |
| A3 | 新工具 `toggle_recurring_flow` | 暂停/恢复 | 0.3d |
| A4 | 新工具 `delete_recurring_flow` | 删除（对应 Web 端能做的操作） | 0.3d |
| A5 | Prompt 层指令补充 | 在 `easy_accounts_instructions_inner.prompt` 补充"定时/重复/每月"等语义识别 | 0.5d |
| A6 | 对话样例 | "每月 1 号工资 20000 到银行卡" / "取消 Netflix 订阅记账" | 0.3d |
| **合计** | | | **~2d** |

**不在本版本范围**：AI 主动提醒"该月房贷没记" —— 归到远期。

### 🟥 WebHook 端任务清单

| # | 任务 | 产出 | 预估 |
|---|---|---|---|
| H1 | 可选：定时规则执行成功/失败通知 | 扩展已有邮件钩子 | 0.5d |

> **优先级 🟢 观察**：v2.7.0 不强制交付，看开发余量。

---

## 五、里程碑

| 阶段 | 交付 | 负责端 |
|---|---|---|
| **M1 · 数据层就绪** | S1 + S2 + S3 + 单测 | Server |
| **M2 · 后端核心** | S4 + S5 + S6 + S7 | Server |
| **M3 · Web 主流程** | W1–W5 | Web |
| **M4 · AI 打通** | A1 + A5 + A6 | AI |
| **M5 · 收尾** | W6 + W7 + A2–A4 + H1（可选） | 各端 |
| **M6 · 联调测试** | 跨端完整链路验证 | 主管 |

---

## 六、连带修复（借 v2.7.0 一起上）

根据 `docs/roadmap-v2.6-v2.7.md`，v2.7.0 同期处理：

| 条目 | 归属 | 与定时记账的关系 |
|---|---|---|
| #29 AI 错误提示展示 | AI + Web | 定时记账的 AI 入口依赖更好的错误反馈 |
| #31 AI 重复记账防护 | AI | 定时记账后重复风险更高，必修 |
| #23 外网 AI 访问根治（user_id → URL query） | AI | 独立修 |
| #32 删除回收站 | Server + Web | 定时记账生成的流水必然更多，回收站是配套安全网 |
| #33 单日/月日支出统计 | Web + Server | 独立功能 |
| #26 授权设备记住密码 | Server + Web | 独立功能 |

建议开 feature 分支顺序：
1. `2.7.0-scheduled-flow`（主线，包含 S1–S8 / W1–W5 / A1,A5,A6）
2. `2.7.0-ai-fixes`（#29/#31/#23 打包）
3. `2.7.0-recycle-bin`（#32）
4. `2.7.0-stats`（#33）
5. `2.7.0-auth`（#26）

---

## 七、待确认事项（等用户定）

- [ ] **版本号**：抬升到 `2.7.0` 的具体时机（application-server.properties）
- [ ] **feature 分支粒度**：是否按上面 5 个 feature 分别开分支，还是合并几个
- [ ] **WebHook H1** 是否纳入本版本
- [ ] **source_template_id** 字段是否加（追溯能力 vs 实现复杂度）
- [ ] **月末处理策略**：31 号 → 月末最后一天？还是 31 号跳过非 31 天月份？（建议前者）

---

## 八、风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 月末日期计算在跨年/闰年边界出错 | 🟡 | S8 单测覆盖所有边界 |
| 服务器时区与用户时区不一致导致生成日期错位 | 🟢 | 当前用户基本 +08:00，v2.7 不做多时区 |
| 停机恢复时一次性补过多流水（如停机 3 个月） | 🟡 | 补偿时给个上限（比如 90 天），超过的走一次"汇总补记"或弃用 |
| 用户把快记模板误配为自动生成 | 🟡 | UI 显著区分 + 创建时二次确认 |

---

## 九、文档交付（本版本结束时）

- [ ] `docs/v2.7.0/plan-scheduled-flow.md` （本文档，持续更新状态）
- [ ] `docs/v2.7.0/release-v2.7.0.md` （版本总文档，发版前整理）
- [ ] 各端 feature 分支合并前由各端 Claude 补交过程文档到自己的 `docs/dev-log/`
