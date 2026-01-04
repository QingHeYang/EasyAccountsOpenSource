# 不计入总金额（exempt）功能设计

本文档描述 EasyAccounts 中"不计入总金额"功能的设计思想和实现细节。

---

## 1. 产品背景

### 1.1 需求场景

在个人记账中，并非所有的"收入"和"支出"都应该影响用户的实际可用资产：

| 场景 | 操作类型 | 为什么不计入 |
|------|----------|-------------|
| 理财收益 | 理财利息到账 | 钱在理财里锁着，不能随时用 |
| 借出/收回 | 借给朋友钱 | 钱还是我的，只是暂时不在手边 |
| 借入/还款 | 向朋友借钱 | 钱不是我的，是负债 |
| 公积金/社保 | 公积金入账 | 账面上是我的，但取不出来 |
| 押金/保证金 | 交租房押金 | 会退回来，不是真正的支出 |

### 1.2 核心目标

让用户看清两个数字：

- **总资产**：账面上所有的钱（含锁定的）
- **净资产**：真正可以动用的钱

```
净资产 = 总资产 - 不计入总金额的部分
```

---

## 2. 数据模型设计

### 2.1 三层结构

```
┌─────────────────────────────────────────────────────────┐
│  Action (操作类型)                                        │
│  ├─ exempt: boolean  ← 配置层：定义默认行为               │
│  │    例如："理财收入" exempt=true                        │
│  │         "工资收入" exempt=false                       │
└─────────────────────────────────────────────────────────┘
                         ↓ 继承
┌─────────────────────────────────────────────────────────┐
│  Flow (流水)                                             │
│  ├─ exempt: boolean  ← 记录层：每笔交易的实际状态         │
│  │    从 Action.exempt 自动继承                          │
└─────────────────────────────────────────────────────────┘
                         ↓ 累积
┌─────────────────────────────────────────────────────────┐
│  Account (账户)                                          │
│  ├─ money: String        ← 账户总金额（含所有交易）       │
│  ├─ exemptMoney: String  ← 不计入的累积值（冗余存储）     │
│  │                                                       │
│  │  净资产 = money - exemptMoney                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 数据库表结构

#### action 表

```sql
CREATE TABLE action (
    id INT PRIMARY KEY AUTO_INCREMENT,
    h_name VARCHAR(50) NOT NULL,     -- 操作名称
    exempt BIT,                       -- 是否不计入总金额
    handle INT NOT NULL               -- 操作类型：0=增加，1=减少，2=转账
);
```

#### flow 表

```sql
CREATE TABLE flow (
    id INT PRIMARY KEY AUTO_INCREMENT,
    f_date DATE,
    money VARCHAR(20),
    action_id INT,
    account_id INT,
    exempt BIT,                       -- 该笔交易是否不计入总金额
    -- 其他字段...
);
```

#### account 表

```sql
CREATE TABLE account (
    id INT PRIMARY KEY AUTO_INCREMENT,
    a_name VARCHAR(50) NOT NULL,
    money VARCHAR(20) NOT NULL,       -- 账户总金额
    exempt_money VARCHAR(20) NOT NULL, -- 不计入总金额的累积值
    -- 其他字段...
);
```

---

## 3. 业务逻辑

### 3.1 添加流水

```java
// FlowService.setNewFlow()
Action action = actionService.getAction(flowAddRequestDto.getActionId());
Account account = accountService.getOriginAccountById(flowAddRequestDto.getAccountId());

// 从 Action 获取 exempt 配置
boolean isExempt = action.isExempt();

// 处理账户金额
account = handleAccount(action.getHandle(), money, account, isExempt);

// 创建流水记录，继承 exempt 状态
Flow flow = new Flow();
flow.setExempt(isExempt);
```

### 3.2 账户金额处理

```java
// FlowService.handleAccount()
private Account handleAccount(int handle, String money, Account account, boolean isExempt) {
    BigDecimal flowMoney = new BigDecimal(money);
    BigDecimal accountMoney = new BigDecimal(account.getMoney());

    // 处理 exemptMoney 空值
    String exemptMoneyStr = account.getExemptMoney();
    if (exemptMoneyStr == null || exemptMoneyStr.isEmpty()) {
        exemptMoneyStr = "0";
    }
    BigDecimal accountExemptMoney = isExempt ? new BigDecimal(exemptMoneyStr) : null;

    switch (handle) {
        case ACTION_ADD:  // 增加
            accountMoney = accountMoney.add(flowMoney);
            if (isExempt) {
                accountExemptMoney = accountExemptMoney.add(flowMoney);
                account.setExemptMoney(accountExemptMoney.setScale(2, RoundingMode.HALF_UP).toString());
            }
            break;
        case ACTION_SUB:  // 减少
            accountMoney = accountMoney.subtract(flowMoney);
            if (isExempt) {
                accountExemptMoney = accountExemptMoney.subtract(flowMoney);
                account.setExemptMoney(accountExemptMoney.setScale(2, RoundingMode.HALF_UP).toString());
            }
            break;
    }

    account.setMoney(accountMoney.setScale(2, RoundingMode.HALF_UP).toString());
    return account;
}
```

### 3.3 删除/更新流水（还原操作）

**重要：** 还原操作必须使用流水记录时的 exempt 状态，而非当前 Action 配置

```java
// FlowService.doDeleteFlow() / doUpdateFlow()
Flow flow = flowDao.queryFlowById(id).get(0);
Action lastAction = actionService.getAction(flow.getActionId());

// v2.5.1: 使用 flow.isExempt() 而非 lastAction.isExempt()
// 避免 Action 配置变更后导致还原操作使用错误的 exempt 状态
boolean flowExempt = flow.isExempt();

// 还原账户金额
switch (lastAction.getHandle()) {
    case ACTION_ADD:
        lastAccount = handleAccount(ACTION_SUB, flow.getMoney(), lastAccount, flowExempt);
        break;
    case ACTION_SUB:
        lastAccount = handleAccount(ACTION_ADD, flow.getMoney(), lastAccount, flowExempt);
        break;
}
```

### 3.4 首页资产计算

```java
// HomeService.setAccountsBean()
BigDecimal totalAsset = new BigDecimal("0");
BigDecimal exemptAsset = new BigDecimal("0");

for (Account account : accounts) {
    totalAsset = totalAsset.add(new BigDecimal(account.getMoney()));

    String exemptStr = account.getExemptMoney();
    if (exemptStr == null || exemptStr.isEmpty()) {
        exemptStr = "0";
    }
    exemptAsset = exemptAsset.add(new BigDecimal(exemptStr));
}

homeDto.setTotalAsset(totalAsset.toString());
homeDto.setNetAsset(totalAsset.subtract(exemptAsset).toString());
```

---

## 4. 借入借出场景分析

### 4.1 四种操作配置

| 操作 | handle | exempt | 说明 |
|------|--------|--------|------|
| 借出 | 1 (减少) | true | 我借给别人，账户减少但钱还是我的 |
| 收钱 | 0 (增加) | true | 别人还我，账户增加但不是真收入 |
| 借入 | 0 (增加) | true | 别人借给我，账户增加但不是我的钱 |
| 还钱 | 1 (减少) | true | 我还给别人，账户减少但不是真支出 |

### 4.2 计算示例

**初始状态：** money=1000, exemptMoney=0, 净资产=1000

**借出场景：**

```
操作1: 借出 100
├─ money: 1000 → 900
├─ exemptMoney: 0 → -100  (负数表示有钱在外面)
└─ 净资产 = 900 - (-100) = 1000 ✓ 没变

操作2: 收钱 100 (对方还款)
├─ money: 900 → 1000
├─ exemptMoney: -100 → 0
└─ 净资产 = 1000 - 0 = 1000 ✓ 恢复
```

**借入场景：**

```
操作1: 借入 100
├─ money: 1000 → 1100
├─ exemptMoney: 0 → 100  (正数表示有欠款)
└─ 净资产 = 1100 - 100 = 1000 ✓ 没变

操作2: 还钱 100
├─ money: 1100 → 1000
├─ exemptMoney: 100 → 0
└─ 净资产 = 1000 - 0 = 1000 ✓ 恢复
```

### 4.3 exemptMoney 正负含义

| 值 | 含义 | 典型场景 |
|----|------|----------|
| 正数 (+) | 账上有钱但不是真正可用的 | 借入、理财锁定 |
| 负数 (-) | 账上少了钱但还是我的 | 借出、押金 |
| 零 (0) | 账户金额全部为真实可用 | 正常状态 |

---

## 5. 设计优点

### 5.1 高效资产计算

- 不需要每次查询都遍历所有 Flow 记录
- 直接读取 Account.exemptMoney，O(1) 复杂度

### 5.2 灵活的操作类型配置

- 同一操作类型的所有交易自动标记
- 可轻松配置新操作类型的行为

### 5.3 完整的审计信息

- 每笔交易都记录 exempt 状态
- 支持详细的数据分析和验证

---

## 6. 注意事项

### 6.1 数据一致性

- exemptMoney 必须与 Flow 记录同步
- 删除或修改流水时必须反向调整 exemptMoney
- 建议定期校验 exemptMoney 与 Flow 记录的一致性

### 6.2 还原操作

- **必须**使用 Flow.exempt 而非 Action.exempt
- 否则 Action 配置变更会导致账目错乱

### 6.3 精度控制

- money 和 exemptMoney 都应使用 `.setScale(2, RoundingMode.HALF_UP)`
- 避免浮点数精度问题

### 6.4 混合问题

当前设计中，所有 exempt 交易的 exemptMoney 是混合累加的，无法区分：
- 借出给张三的 100
- 借入李四的 200
- 理财收益 50

如需详细追踪，可考虑：
1. 按 Action 分类查询统计
2. 增加交易对象字段
3. 分拆 exemptMoney 为多个字段

---

## 7. 相关代码

| 文件 | 说明 |
|------|------|
| `entity/Account.java` | exemptMoney 字段定义 |
| `entity/Flow.java` | exempt 字段定义 |
| `entity/Action.java` | exempt 配置字段 |
| `service/FlowService.java` | handleAccount() 核心逻辑 |
| `service/HomeService.java` | 首页资产计算 |

---

*文档版本：v2.5.1*
*更新时间：2026-01-04*
