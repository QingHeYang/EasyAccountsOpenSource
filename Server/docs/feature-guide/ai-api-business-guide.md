# AI 工具调用 · 后端 API 业务语义说明

> **目标读者**：AI 端 Claude（KoalaqHub），用于重写 LLM 工具的 docstring 和提示词
> **作者**：Server 后端 Claude
> **创建时间**：2026-04-29
> **覆盖范围**：AI 端目前在调的 9 个接口（6 读 + 3 写）+ 跨接口共性
> **本文档定位**：业务/产品语义说明，不是技术契约（字段类型详情请配合 Swagger 看）

---

## 〇、读完本文档你应该掌握

1. **核心实体**：account / action / type / handle / collect / from / note / fDate 在产品里到底指什么
2. **handle 三态**：0=收入、1=支出、2=内部转账，是整个数据模型的中枢，影响余额计算、统计口径、accountToId 必填性
3. **type 与 action 的关系**：N:1 但允许 actionId=null（"通用分类"），父子两级，父分类有 actionId 时不允许直接记账
4. **筛选语义**：types/actions 多选组内 OR、组间 AND；types 选父类自动覆盖子类；types/actions 都不传 = 不筛选
5. **统计口径**：totalIn/totalOut 仅看 handle=0/1，**转账不计**；totalEarn = totalIn - totalOut
6. **写流水副作用**：自动改账户余额；更新/删除会自动按 lastFlow.exempt 回滚再正向应用，不需要 AI 端关心余额
7. **makeExcel 不返回下载 URL**：是发邮件附件，返回的是 `{success, log}` 字符串
8. **鉴权**：单一用户系统，header `Authorization: <raw_token>`（无 Bearer 前缀）；登录开关关闭时全部接口直接放行
9. **错误码**：HTTP 状态码 200/401/418/500；业务错误走 BaseDto.code，全部枚举见末尾

---

## 一、核心实体的产品定义

### 1.1 Account（资金账户）

代表用户实际持有资金的容器：现金、银行卡、信用卡、支付宝、余额宝、应付账款……

| 字段 | 含义 | 备注 |
|---|---|---|
| `id` | 账户唯一 ID | int |
| `name` | 账户显示名（响应里叫 `name`，DB 列叫 `a_name`） | 如果账户已停用，name 后会拼接 `(已停用)`（仅在 noLimit 接口中可见） |
| `money` | **当前余额**（字符串，2 位小数） | 系统自动维护，AI **永远不要**直接改 |
| `exemptMoney` | 豁免金额（不计入"净资产"统计的部分，例如借出的钱） | 字符串，可能为空字符串 |
| `card` | 卡号备注（用户自填，非真实卡号） | 可空 |
| `note` | 账户备注 | 最长 100 字符 |
| `accountType` | 账户类型：0=资产账户，1=负债账户（信用卡等） | v2.6.0 引入，默认 0 |
| `disable` | 是否停用 | 停用后 `getAccount` 不返回，但历史流水仍引用 |

**产品规则**：
- 一个用户可有多个账户，停用后仍可在历史流水里查到
- 账户余额可以是负数（信用卡欠款场景）
- **永远没有"删除账户"**，只有停用

### 1.2 Action（收支动作）

定义"这笔流水是哪种性质"。不是单纯的类别，而是**改余额的方向控制器**。

| 字段 | 含义 |
|---|---|
| `id` | 动作 ID |
| `hName` | 动作显示名（如"工资"、"购物"、"信用卡还款"） |
| `handle` | **关键字段**：0=收入、1=支出、2=内部转账 |
| `exempt` | 该动作产生的流水是否默认计入豁免金额 |
| `exemptMode` | 仅 handle=2 时使用：0=都不豁免、1=转出豁免、2=转入豁免、3=都豁免（v2.6.0 新增） |
| `disable` | 是否禁用 |

**产品规则**：
- AI 端的 `actions` 工具不存在 → AI 选 actionId 时只能从 `types` 接口节点上挂的 `action` 字段拿
- handle 是 1:N（一个 handle 值可对应多个 action，如"购物"和"餐饮"都是 handle=1）
- handle 决定了 accountToId 是否必填：handle=2 必填，否则忽略

### 1.3 Type（分类）

记账的分类树，最多两级。

| 字段 | 含义 |
|---|---|
| `id` | 分类 ID |
| `tName` | 分类名（响应中归档/停用会拼后缀 `(已归档)` / `(已停用)`） |
| `parent` | 父分类 ID，**`-1` 表示是一级分类** |
| `actionId` | **关联的 action**（决定本分类下流水的 handle）；可为 null |
| `action` | EAGER 加载的 Action 实体（响应里直接附带） |
| `disable` / `archive` / `analysisDisable` | 停用 / 归档 / 不参与分析 |
| `childrenTypes` | 子分类列表（仅 `getType` 接口拼装） |

**关键规则（AI 端理解错误重灾区）**：

1. **type 与 action 的关系**：N:1，**且允许 type.actionId = null**
   - 用例：定义一个"通用"分类，在记账时再选 action（"工资/购物"由用户当场决定）
   - `getType` 返回的节点上 `action` 字段为 null 是合法的，**不是后端漏字段**

2. **父分类是否能直接记账，看 actionId**：
   - 父分类有子分类 + 父分类 actionId 不为 null → **禁止用父分类记账**，必须选子分类（后端会抛 `TYPE_HAS_CHILDREN` 42002）
   - 父分类有子分类 + 父分类 actionId 为 null → **可以用父分类记账**（这种父分类是"通用容器"，子分类是细分场景）
   - 父分类无子分类 → 直接用父分类记账

3. **AI 端目前自加"可用/不可用"标记**：理解大体对，但**判断条件错了**——光看"有无子分类"不够，要看父分类自己的 actionId。
   - 推荐 AI 端的判断改为：`canUseDirectly = !hasChildren || parentType.actionId == null`
   - 后端没有标准字段表达这个，AI 端可以继续在客户端包装，但请按上面的规则判

4. **筛选 types 时父子等价**：
   - 用户选了"餐饮"（一级分类，id=10），筛选会把 typeId=10 或 parentTypeId=10 的流水都算进来（即子分类自动包含在内）
   - 用户选了"早餐"（二级分类），只会筛选 typeId=11

### 1.4 Flow（流水）

一笔记账记录。

| 字段 | 含义 |
|---|---|
| `id` | 流水 ID |
| `money` | 金额，**字符串，2 位小数，永远是正数**（方向由 action.handle 决定） |
| `fDate` | **流水日期**（业务时间），格式 `yyyy-MM-dd`；用户可改 |
| `fCreateDate` | 创建时间（系统时间），格式 `yyyy-MM-dd HH:mm:ss`；不可改 |
| `typeId` | 分类 ID |
| `actionId` | 动作 ID |
| `accountId` | 账户 ID（来源账户） |
| `accountToId` | 目标账户 ID（**仅 handle=2 时使用**），其他 handle 时虽然字段在但语义上不存在 |
| `exempt` | 该笔流水是否豁免（创建时取 action.exempt 快照） |
| `collect` | 是否收藏 |
| `note` | 备注（用户自填） |
| `from` | **来源标识**，文本字段，后端不校验取值 |
| `images` | 图片文件名列表（来自 `/image/upload` 接口的 `fileName`） |

**from 字段语义（后端实际行为）**：
- DB 列名 `from_source`，Java/JSON 字段名 `from`
- **后端只是原样存储**，不参与任何统计、筛选、校验
- 历史值：`pc` / `mobile` / `mcp` / `ai` / `Claw` / `scheduled`（v2.7.0 新增，定时记账触发的流水自动带 scheduled）
- AI 端可以传任意字符串，但建议沿用现有约定：MCP 工具传 `mcp`、AI 内部接口传 `ai`
- updateFlow 时如果不传 from，后端会置空字符串（不会保留原值）—— **AI 端在 update 时务必传回原 from**

**关键约束**：
- `money` 入参：字符串，**只传正数**（如 "30.00"），后端会 `MoneyUtils.formatMoney` 校验并保留 2 位小数
- 余额负数：v2.6.0 起允许（信用卡场景），AI 端不需要做余额够不够的预判

---

## 二、读类接口（6 个）

### 2.1 GET `/account/getAccount` —— 获取全部资金账户

**业务定位**：用户在记账页选择"用哪个账户付款"时的列表来源。

**入参**：无。

**返回**（`data` 是数组）：
```json
[
  { "id": 1, "name": "招商银行", "money": "12345.67",
    "exemptMoney": "0", "card": "尾号 1234", "createTime": "2024-01-01 12:00:00",
    "note": "工资卡", "accountType": 0 }
]
```

**规则**：
- 仅返回未停用账户（`disable=false`）
- 已停用账户的历史流水仍可查到，但本接口不会列出该账户
- 余额是字符串，**直接显示**给用户即可，不要做格式化运算

---

### 2.2 GET `/type/getType` —— 获取分类树

**业务定位**：记账时选"这是什么分类"的树状选择器数据源。

**入参**：无。

**返回结构**（`data` 是一级分类数组，每个元素含 `childrenTypes`）：
```json
[
  {
    "id": 10, "tName": "餐饮", "parent": -1,
    "action": { "id": 2, "hName": "购物", "handle": 1 },
    "disable": false, "archive": false, "analysisDisable": false,
    "childrenTypes": [
      { "id": 11, "tName": "早餐", "parent": 10,
        "action": { "id": 2, "hName": "购物", "handle": 1 },
        "childrenTypes": null }
    ]
  }
]
```

**规则**：
- 默认过滤掉 `disable=true` 和 `archive=true` 的分类
- `parent=-1` 是一级分类标记
- `action` 字段可能为 null（"通用分类"，记账时让用户当场选 action）
- 返回的分类已经组装好父子结构，AI 端不需要再用 parent 字段重新拼

**与 `/type/getTypeByActionId/{actionId}` 的差异**：
- 后者还会把 actionId=null 的"通用分类"也带进来（用 OR 逻辑）
- 用户先选"购物" action 再选分类时用后者；从根开始浏览全部分类时用前者

---

### 2.3 GET `/action/getAction` —— 获取所有收支动作

**业务定位**：管理"动作"自身（添加/编辑分类时给分类挂哪个 action）。

**入参**：无。

**返回**：
```json
[
  { "id": 1, "hName": "工资", "handle": 0, "exempt": false,
    "exemptMode": 0, "disable": false }
]
```

**规则**：
- 默认只返回未禁用（`disable=false`）的动作
- 在 AI 端的 `add_flow` 流程里**通常用不上**——AI 是先选 type，type 上已挂了 action
- 仅当 type.action == null（通用分类）时，AI 才需要选一个 action

---

### 2.4 GET `/home/getHomeInfoV2/{year}` —— 首页年度概览

**业务定位**：用户进首页看到的"今年挣了多少花了多少"+"每个月明细"+"账户余额分布"。

**入参**：path `year`（如 2026）。

**返回**：
```json
{
  "totalAsset": "50000.00",          // 全部账户余额加总
  "netAsset": "45000.00",            // totalAsset - 全部 exemptMoney 加总
  "yearIncome": "120000.00",         // 该年度收入合计 (handle=0)
  "yearOutCome": "80000.00",         // 该年度支出合计 (handle=1)
  "yearBalance": "40000.00",         // yearIncome - yearOutCome
  "accounts": [...],                 // 各账户余额 + 占总资产百分比（数组）
  "monthDetails": [                  // 每月明细
    { "month": "1", "income": "10000.00", "outcome": "8000.00", "balance": "2000.00" }
  ]
}
```

**统计口径（重要）**：
- `yearIncome / yearOutCome / yearBalance`：走 MyBatis 直接 `SUM(CASE WHEN handle=0/1)`，**不过滤 fDisable**
- `monthDetails`：走 JPA 在 Java 层算，**会过滤 fDisable=true** 的流水
- **已知小不一致**：fDisable 字段当前没有产品入口能切换它，所以年度合计 = 月度合计；AI 端可以视为一致，但出现极小偏差时这是来源
- 所有口径都**不含转账**（handle=2）

**月份枚举**：
- monthDetails 只包含**有流水的月份**（没流水的月份不出现），AI 端不要假设一定 12 条
- month 是 "1"~"12" 的字符串

---

### 2.5 POST `/screen/getFlowByScreen` —— 多条件筛选流水

**业务定位**：用户在"流水管理"页按账户/日期/分类/动作/收藏/备注关键字筛选。

**入参**（`ScreenFlowRequestDto`）：

| 字段 | 类型 | 含义 | 默认/约束 |
|---|---|---|---|
| `chooseHandle` | int | 0=只看收入、1=只看支出、2=只看转账、**3=全部** | 必填，AI 端要"全部"传 3 |
| `accountId` | int | 限定某账户的流水（`account_id` 或 `account_to_id` 命中即算） | 0 表示不筛选 |
| `startDate` | string `yyyy-MM-dd` | 起始日期 | 空字符串/null/`"null"`字符串 = 不限 |
| `endDate` | string `yyyy-MM-dd` | 结束日期 | 同上；闭区间 |
| `singleMonth` | boolean | true 时**只看 startDate 所在的月**（取 yyyy-MM），endDate 被忽略 | 默认 false |
| `collect` | boolean | true 时只返回收藏 | 默认 false |
| `note` | string | 备注模糊匹配（LIKE `%xxx%`） | null/空 = 不筛选 |
| `types` | `int[]` | **分类多选筛选**，组内 OR；选父类自动覆盖其全部子类 | 数组为空 = 不筛选 |
| `actions` | `int[]` | **动作多选筛选**，组内 OR | 数组为空 = 不筛选 |

**types 与 actions 同时传时**：组间 AND（既要在 types 里又要在 actions 里）。

**返回**：
```json
{
  "totalIn": "10000.00",   // 收入合计 (handle=0)
  "totalOut": "8000.00",   // 支出合计 (handle=1)
  "totalEarn": "2000.00",  // = totalIn - totalOut（不含转账）
  "typeList": [...],       // 按一级分类分组的金额聚合（含 children）
  "flows": [
    {
      "id": 100, "money": "30.00", "exempt": false, "collect": false,
      "handle": 1, "hName": "购物", "tName": "餐饮/早餐",
      "note": "煎饼果子", "aName": "招商银行", "toAName": null,
      "fDate": "2026-04-29", "from": "ai", "hasImages": false
    }
  ]
}
```

**统计口径**：
- `totalIn` / `totalOut`：仅算 handle=0/1，转账不算
- `totalEarn` = `totalIn - totalOut`
- 即使 chooseHandle=2（仅看转账），转账记录会出现在 `flows` 里，但 totalIn/totalOut 都是 0

**时间字段**：
- `fDate` 在 DB 是字符串（不是 datetime），**SQL 用字符串比较**——**必须严格 `yyyy-MM-dd` 10 位**，不要传 `2026-4-9`
- 时区不参与（字符串无时区概念），但全系统约定 GMT+8 录入

**无分页**：
- 后端不分页，一次返回全部命中流水
- 数据量大时风险在客户端；AI 端目前固定截断 100 条是合理保守做法
- 想缩小返回量请把日期范围收窄（最常用 singleMonth=true）

---

### 2.6 GET `/flow/getFlow/{id}` —— 单条流水详情

**业务定位**：点开一条流水查看完整信息（含图片、转入账户）。

**入参**：path `id`。

**返回**：
```json
{
  "id": 100, "money": "30.00", "fDate": "2026-04-29",
  "isCollect": false, "note": "...", "from": "ai",
  "account": { ...完整 Account 实体 },
  "accountTo": { ...完整 Account 实体 },   // 仅 handle=2 时返回，否则 null
  "action": { ...完整 Action 实体 },
  "type": {
    "id": 11, "tName": "餐饮——早餐",   // 父类 + 子类用"——"拼接
    "parent": 10, "action": {...}
  },
  "images": ["1714123456_8923.jpg", ...]   // 图片文件名列表，下载用 GET /image/{fileName}
}
```

**特殊**：
- 不存在的 id 返回 `code=403, msg="未查询到该条记录"`（**不是 404**，后端这里历史代码用了 403）
- `images` 是文件名（非 URL），AI 端要下载需拼 `${API_BASE}/image/{fileName}`
- 图片路径是 GET，但**不需要鉴权**（在 WebConfig.excludePathPatterns 中）

---

## 三、写类接口（3 个）

### 3.1 POST `/flow/addFlow` —— 添加流水

**业务定位**：用户/AI 创建一笔新流水。

**入参**（`FlowAddRequestDto`）：

| 字段 | 类型 | 是否必填 | 说明 |
|---|---|---|---|
| `money` | string | 必填 | 正数，2 位小数（如 "30.00"）；非法格式后端兜底为 "0.00" |
| `fDate` | string | 必填 | 业务日期 `yyyy-MM-dd` |
| `actionId` | int | 必填 | 来源：`type.action.id`，如果 type.action 为 null 需 AI 自己选 |
| `typeId` | int | 必填 | 父分类 + 父分类 actionId 不为 null + 有子分类 → 抛 42002 |
| `accountId` | int | 必填 | 资金来源账户 |
| `accountToId` | int | **handle=2 时必填，其他时传 0** | 仅转账场景的目标账户 |
| `isCollect` | boolean | 可选 | 默认 false |
| `note` | string | 可选 | 备注；AI 端约定追加 `#AI记账` |
| `from` | string | 推荐传 | `"ai"` 或 `"mcp"`；不传则空字符串 |
| `images` | `string[]` | 可选 | `/image/upload` 返回的 fileName 列表 |

**自动副作用（AI 端不需要参与）**：
1. 后端按 `action.handle` 自动改账户余额：
   - handle=0 → `account.money += money`
   - handle=1 → `account.money -= money`
   - handle=2 → `accountTo.money += money` AND `account.money -= money`
2. 如果 `action.exempt=true`，账户的 `exemptMoney` 同步加减
3. handle=2 时还会按 `action.exemptMode`（0/1/2/3）决定哪一边的 exempt

**返回**：`{ "id": 新流水id }`

---

### 3.2 PUT `/flow/updateFlow/{id}` —— 更新流水

**业务定位**：编辑已有流水（改金额/账户/分类/转账目标等）。

**入参**：与 addFlow 完全相同（PathVariable id 标识更新对象）。

**自动回滚 + 重放（AI 端最容易踩的坑）**：
1. 后端先读旧 flow，按 **`lastFlow.exempt`** 反向回滚旧账户余额
   - 用 `flow.exempt` 而不是 `lastAction.exempt` 是为了避免 action 的 exempt 配置被改后回滚错位
2. 然后按新参数正向应用新流水
3. 即使你只改 note，后端也会跑一次"回滚 + 重放"，但金额相等所以无副作用

**from 字段陷阱**：
- 后端 `if (flowAddRequestDto.getFrom() == null) flowAddRequestDto.setFrom("");`
- **不传 from 会被置空，不会保留原值** —— AI 端 update 时若不想动 from，**必须先 GET 原 from 再传回**

**返回**：`{ "id": 更新后的流水id（与入参一致）}`

---

### 3.3 POST `/screen/makeExcel?excelName={name}` —— 筛选条件生成 Excel

**业务定位**：把当前筛选结果导出 Excel 并通过邮件发到用户邮箱。

**入参**：
- query: `excelName`（文件名，不带扩展名；后端会自动追加 `_yyyyMMdd_HHmmss.xlsx`）
- body: `ScreenFlowRequestDto`（同 `getFlowByScreen`）

**返回**：
```json
{
  "code": 0,
  "data": {
    "success": true,
    "log": "\n筛选 Excel 已生成并发送邮件\n报销_20260429_213045.xlsx"
  }
}
```

**重要纠正（AI 端理解错误）**：

1. **不返回下载 URL**。文档中"返回 downloadUrl"的描述是错的
2. 实际行为是：生成 Excel 文件 → **通过邮件发给用户**（前提：SMTP 配好）
3. 客户端只能拿到一个 success/log 字符串组合
4. **如果 SMTP 没配置**，`success=true`（文件生成了）但邮件没发出去——AI 端要在 docstring 里告诉用户"请到系统设置检查邮件配置"

**边界**：
- 筛选无数据 → `{ "success": false, "log": "筛选条件无数据" }`
- 这个接口对应的"月度 Excel"是 `GET /flow/makeExcel/{date}`（参数是 `yyyy-MM`），AI 端如果要月度导出走那个

---

## 四、跨接口共性

### 4.1 响应包格式（BaseDto）

所有接口（除 `/image/{fileName}` 直接返回二进制）一律 `{ code, msg, data }`：

```json
{ "code": 0, "msg": "Success", "data": <T> }
```

**code 完整枚举（来自 ErrorCode.java）**：

| 区段 | 含义 | 出现位置 |
|---|---|---|
| **0** | SUCCESS | 全部接口成功 |
| **40000-40004** | 参数错误（PARAM_ERROR / PARAM_REQUIRED / PARAM_FORMAT_ERROR / PARAM_INVALID / FILE_VALIDATION_ERROR） | 入参校验 |
| **401** | UNAUTHORIZED 或 LOGIN_FAILED | 鉴权失败、登录失败（**HTTP 状态码也是 401**） |
| **418** | NEED_REGISTER | 首次启动、未注册（**HTTP 状态码 418**） |
| **42001-42017** | 业务规则错误 | 详见下表 |
| **44001-44008** | 资源不存在 | ACCOUNT_NOT_FOUND / TYPE_NOT_FOUND / FLOW_NOT_FOUND / TEMPLATE_NOT_FOUND / FILE_NOT_FOUND / ACTION_NOT_FOUND / SCHEDULED_RULE_NOT_FOUND / NOTICE_NOT_FOUND |
| **50001-50005** | 系统错误 | SYSTEM_ERROR / DATABASE_ERROR / FILE_OPERATION_ERROR / EXTERNAL_SERVICE_ERROR / CRYPTO_FAILED（HTTP 状态码 500） |

**业务规则错误码（42xxx）**，AI 端最可能撞到的几个：

| code | 名称 | 触发条件 |
|---|---|---|
| 42001 | INSUFFICIENT_BALANCE | 余额不足（v2.6.0 起多数场景已注释，但保留枚举） |
| 42002 | TYPE_HAS_CHILDREN | 用有子分类且 actionId 不为 null 的父分类记账 |
| 42003 | OPERATION_NOT_ALLOWED | 通用"操作不允许" |
| 42004 | DATA_CONFLICT | 数据冲突 |
| 42005 | INVALID_STATE | 状态不正确 |
| 42006 | TYPE_CANNOT_DELETE | 该分类下有流水，不能直接删（要停用） |
| 42007 | ACCOUNT_CANNOT_DELETE | 该账户下有流水，不能直接删 |
| 42008 | ACCOUNT_DISABLED | 引用了已停用账户（v2.7.0 定时记账） |
| 42009 | TYPE_DISABLED | 引用了已停用分类 |
| 42010 | TYPE_ARCHIVED | 引用了已归档分类 |
| 42011 | ILLEGAL_STATE_TRANSITION | 状态机非法转换（定时记账） |
| 42012 | INVALID_START_DATE | 开始日期 ≤ 今天 |
| 42013 | INVALID_END_DATE | 结束日期 < 开始日期 |
| 42014 | INVALID_CYCLE_CONFIG | 周期配置非法 |
| 42015 | RULE_EXPIRED | 规则已过期 |
| 42016 | TRANSFER_ACCOUNT_REQUIRED | 转账场景未指定目标账户 |
| 42017 | MAIL_NOT_CONFIGURED | 启用邮件类功能时 SMTP 未配置 |

**HTTP 状态码 vs BaseDto.code**：
- HTTP 200 + code=0：成功
- HTTP 200 + code≠0：业务错误（看 msg）
- HTTP 401/418/500：鉴权或系统错误（**响应体不是 BaseDto，是 servlet 默认错误页**）

### 4.2 鉴权 header

- header 名：`Authorization`（servlet 不区分大小写，`authorization` 也可，但建议统一首字母大写）
- 取值：**直接是 token 字符串**，**没有 `Bearer ` 前缀**
- 例：`Authorization: a3f4b5...`（token 是 base64 加密后的字符串）

**特殊行为**：
- 系统是**单一用户**（一个 secret.key 文件存账号信息），不需要 user_id
- 如果 `auth.login_enable=false`，拦截器直接放行所有请求 —— AI 端可以不带 token
- token 滑动刷新：剩余时间 < 50% 时自动续期，AI 端不需要主动刷新
- token 过期后所有接口返回 HTTP 401，需要重新调 `/auth/login`

**AI 端注意**：不要去拼 `Bearer xxx`，后端用 `equals()` 直接比对，加前缀会鉴权失败。

### 4.3 from 字段

- DB 列：`from_source`，DTO 字段：`from`
- 后端**不校验、不参与统计**，仅原样存储
- 历史值：`pc` / `mobile` / `mcp` / `ai` / `Claw` / `scheduled`
- 推荐：MCP 工具传 `mcp`、AI 端内部接口传 `ai`，便于后续做来源分析
- **update 时不传 = 置空**（不是保留原值），update 务必先读再传回

### 4.4 金额字段

- 类型：**string**（后端 BigDecimal 处理）
- 精度：2 位小数，超过会四舍五入
- **永远只传正数**，方向由 action.handle 决定
- 非法格式（含字母、空字符串）后端兜底为 `"0.00"`
- 余额可以是负数（信用卡场景），但**用户输入的 money 永远 ≥ 0**

### 4.5 日期字段

| 字段 | 含义 | 格式 |
|---|---|---|
| `fDate` | **流水的业务日期**（用户记账时填的"哪天发生的"） | `yyyy-MM-dd` 字符串 |
| `fCreateDate` | 系统创建时间（流水写入时刻） | `yyyy-MM-dd HH:mm:ss` 字符串 |
| `createTime`（账户） | 账户创建时间 | `yyyy-MM-dd HH:mm:ss` |

**统计口径用 fDate**（不是 fCreateDate）：
- 月度/年度报表、筛选日期都看 `fDate`
- 用户可能"4 月 30 号补记 4 月 15 号那笔"，这种 fDate=4/15、fCreateDate=4/30
- AI 端如果要"昨天的流水"，要用 fDate 算

**时区**：
- 数据库 + 服务端约定 GMT+8（中国时区）
- 字段是字符串，**不带时区信息**，比较是字符串比较
- AI 端别做时区转换；当地时间是几号就传几号

### 4.6 分页

- **流水查询全部接口都没有分页参数**
- 一次返回全部命中
- 大数据量时客户端要自己处理（前端是无限滚动按月分页）
- AI 端固定截断 100 条是合理保守做法
- 缩小返回量的最佳办法：传 `singleMonth=true` 或收窄日期范围

---

## 五、AI 端可能的 docstring 重写建议

### 关于 `types` 工具

> 当前版本：「一级分类如果有子分类则一级本身不可用，要用子分类」

**建议改为**：
> 返回分类树。每个分类节点的 `action` 字段可能为 `null`（"通用分类"，记账时由用户当场选 action）。
>
> **能否直接用本节点记账**：
> - 节点无子分类（叶子）→ 可以
> - 节点有子分类 + `action == null` → 可以（这是"通用容器"）
> - 节点有子分类 + `action != null` → 不可以（必须选子分类，否则后端返回 42002）

### 关于 `add_flow` 工具

> 当前版本：「金额会去掉负号」

**建议补充**：
> - `money` 必须是正数字符串，2 位小数。方向由 action.handle 决定（0=收入加余额、1=支出减余额、2=转账双边）
> - `accountToId` 仅 `action.handle=2` 时必填，其他场景传 0 或省略
> - 如果分类是有子分类的父分类（且父分类自身配了 action），后端会拒绝（42002）—— 选子分类
> - 不需要预判余额，v2.6.0 起允许账户负余额（信用卡场景）

### 关于 `update_flow` 工具

**建议补充**：
> - **必须先 GET `/flow/getFlow/{id}` 拿到原 `from` 字段，传回时保留**，否则 from 会被置空
> - 后端会自动按原流水回滚账户余额再正向应用新参数，AI 不需要做差额计算

### 关于 `make_excel` 工具

**关键纠正**：
> - 这个工具**不返回下载 URL**
> - 实际行为：生成 Excel 文件并**通过邮件发送**到用户配置的邮箱
> - 返回 `{ success: bool, log: string }`；success=true 表示文件已生成（不保证邮件已成功发出，邮件失败不影响 success 标志）
> - 如果用户反馈"没收到邮件"，提示用户去"系统设置 → 邮件"检查 SMTP 配置

### 关于 `flows` 工具（getFlowByScreen）

**建议补充**：
> - `chooseHandle=3` 才是"全部"（不是 0），传 0 仅看收入
> - `singleMonth=true` 时只用 startDate 的 yyyy-MM，endDate 被忽略
> - `accountId=0` 表示不限账户
> - 选父分类会自动包含其全部子分类的流水
> - `types` 与 `actions` 多选：组内 OR、组间 AND
> - `totalIn/totalOut/totalEarn` 的统计**不含转账**（handle=2）
> - 接口**没有分页**，截断 100 条要在 AI 端做

---

## 六、未列在清单但 AI 端可能需要知道的接口

| URL | 用途 |
|---|---|
| GET `/type/getTypeByActionId/{actionId}` | 按 actionId 过滤分类（含 actionId=null 的通用分类）。当用户先选 action 再选分类时用这个 |
| POST `/image/upload` | 上传单张图片，返回 fileName，可拼到 addFlow 的 images 数组里 |
| GET `/image/{fileName}` | 下载图片二进制（**无需鉴权**） |
| GET `/flow/makeExcel/{date}` | **月度** Excel 生成（path 是 yyyy-MM）；与 screen/makeExcel 区别是不需要筛选条件 |
| POST `/auth/login` / `/auth/register` | 登录注册；**不需要鉴权**；password 是前端 MD5 后的字符串 |

---

## 七、变更日志

| 日期 | 内容 |
|---|---|
| 2026-04-29 | 初稿，覆盖 9 个 AI 端在用接口 + 4 个共性问题 |
