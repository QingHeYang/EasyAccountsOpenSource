# 数据库开发详情

本文档详细介绍 EasyAccounts Server 模块的数据库设计、表结构、关联关系和配置方法。

---

## 目录

1. [数据库概述](#数据库概述)
2. [连接配置](#连接配置)
3. [表结构详情](#表结构详情)
4. [表关联关系](#表关联关系)
5. [Liquibase 版本管理](#liquibase-版本管理)
6. [双重数据访问模式](#双重数据访问模式)
7. [常见操作示例](#常见操作示例)
8. [注意事项](#注意事项)

---

## 数据库概述

| 项目 | 说明 |
|------|------|
| 数据库类型 | MySQL 8.0.31 |
| 数据库名 | `yd_jz` |
| 字符集 | UTF-8 |
| 时区 | GMT+8 |
| ORM 框架 | JPA + MyBatis（双重数据访问） |
| 版本管理 | Liquibase |

---

## 连接配置

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|-------|------|
| `MYSQL_HOST` | db | MySQL 服务器地址 |
| `MYSQL_PORT` | 3306 | MySQL 端口 |
| `MYSQL_USERNAME` | root | 数据库用户名 |
| `DB_PASSWORD` | easy_accounts | 数据库密码 |

### 配置文件

**生产环境 (application-server.properties):**
```properties
spring.datasource.url=jdbc:mysql://${MYSQL_HOST:db}:${MYSQL_PORT:3306}/yd_jz?useUnicode=true&characterEncoding=utf-8&serverTimezone=GMT%2B8
spring.datasource.username=${MYSQL_USERNAME:root}
spring.datasource.password=${DB_PASSWORD:easy_accounts}
spring.datasource.driverClassName=com.mysql.jdbc.Driver

# MyBatis 配置：下划线转驼峰
mybatis.configuration.map-underscore-to-camel-case=true

# Liquibase 配置
spring.liquibase.change-log=classpath:/db/changelog/db.changelog-master.yaml
```

**Windows 本地开发 (application-windows.properties):**
```properties
spring.datasource.url=jdbc:mysql://localhost:3306/yd_jz?useUnicode=true&characterEncoding=utf-8&serverTimezone=GMT%2B8
spring.datasource.username=root
spring.datasource.password=your_password
```

### Docker 环境

在 Docker Compose 中，数据库服务通常命名为 `db`，应用通过服务名连接：

```yaml
services:
  db:
    image: mysql:8.0.31
    environment:
      MYSQL_ROOT_PASSWORD: easy_accounts
      MYSQL_DATABASE: yd_jz
    volumes:
      - mysql_data:/var/lib/mysql

  server:
    image: easyaccounts-server
    environment:
      MYSQL_HOST: db
      MYSQL_PORT: 3306
      DB_PASSWORD: easy_accounts
    depends_on:
      - db
```

---

## 表结构详情

### 核心表概览

| 表名 | 实体类 | 功能 | 版本 |
|------|--------|------|------|
| `flow` | FlowJpaEntity / Flow | 交易流水记录 | 2.1.0 |
| `account` | Account | 账户管理 | 2.1.0 |
| `type` | Type | 交易类型（收入/支出分类） | 2.1.0 |
| `action` | Action | 操作类型（收入/支出/转账） | 2.1.0 |
| `flow_template` | FlowTemplate | 交易模板（快速记账） | 2.1.0 |
| `tag` | TemplateTag | 模板标签 | 2.1.0 |
| `flow_image` | FlowImage | 流水图片附件 | 2.5.0 |

---

### 1. flow（交易流水表）

存储所有财务交易记录，是系统核心表。

```sql
CREATE TABLE flow (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    f_date          VARCHAR(20) NOT NULL,      -- 交易日期 (yyyy-MM-dd)
    money           VARCHAR(20) NOT NULL,      -- 交易金额（字符串存储，保留2位小数）
    type_id         INT NOT NULL,              -- 关联 type 表
    action_id       INT NOT NULL,              -- 关联 action 表
    exempt          BIT(1),                    -- 是否免计入账户余额
    account_id      INT,                       -- 主账户 ID
    account_to_id   INT,                       -- 目标账户 ID（转账时使用）
    note            VARCHAR(200),              -- 备注
    collect         BIT(1),                    -- 是否收藏
    f_create_date   VARCHAR(30),               -- 创建时间
    f_disable       BIT(1),                    -- 是否禁用（软删除）
    from_source     VARCHAR(50)                -- 来源标识（如 'ai' 表示AI记录）
);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | INT | 是 | 主键，自增 |
| `f_date` | VARCHAR(20) | 是 | 交易日期，格式 `yyyy-MM-dd` |
| `money` | VARCHAR(20) | 是 | 金额，字符串存储（避免浮点精度问题） |
| `type_id` | INT | 是 | 交易类型 ID，关联 `type.id` |
| `action_id` | INT | 是 | 操作类型 ID，关联 `action.id` |
| `exempt` | BIT(1) | 否 | 是否免计：true=不影响账户余额 |
| `account_id` | INT | 否 | 主账户，关联 `account.id` |
| `account_to_id` | INT | 否 | 转账目标账户，关联 `account.id` |
| `note` | VARCHAR(200) | 否 | 交易备注 |
| `collect` | BIT(1) | 否 | 是否收藏标记 |
| `f_create_date` | VARCHAR(30) | 否 | 记录创建时间 |
| `f_disable` | BIT(1) | 否 | 软删除标记 |
| `from_source` | VARCHAR(50) | 否 | 来源标识（v2.5.0新增） |

**对应实体类：** `FlowJpaEntity.java`（JPA）/ `Flow.java`（MyBatis）

---

### 2. account（账户表）

管理用户的各类账户（银行卡、现金、支付宝等）。

```sql
CREATE TABLE account (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    a_name          VARCHAR(50) NOT NULL,      -- 账户名称
    money           VARCHAR(20) NOT NULL,      -- 当前余额
    exempt_money    VARCHAR(20) NOT NULL,      -- 免计金额
    card            VARCHAR(50),               -- 卡号（可选）
    disable         BIT(1) DEFAULT 0,          -- 是否禁用
    create_time     DATETIME,                  -- 创建时间
    note            VARCHAR(100)               -- 备注
);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | INT | 是 | 主键，自增 |
| `a_name` | VARCHAR(50) | 是 | 账户名称（如"招商银行"） |
| `money` | VARCHAR(20) | 是 | 当前余额 |
| `exempt_money` | VARCHAR(20) | 是 | 免计金额（不计入统计） |
| `card` | VARCHAR(50) | 否 | 银行卡号 |
| `disable` | BIT(1) | 否 | 是否禁用，默认 0 |
| `create_time` | DATETIME | 否 | 创建时间 |
| `note` | VARCHAR(100) | 否 | 备注 |

**对应实体类：** `Account.java`

---

### 3. type（交易类型表）

管理交易分类，支持多级分类（父子结构）。

```sql
CREATE TABLE type (
    id                INT PRIMARY KEY AUTO_INCREMENT,
    t_name            VARCHAR(50) NOT NULL,    -- 类型名称
    parent            INT DEFAULT -1,          -- 父类型 ID（-1 表示顶级）
    t_disable         BIT(1) DEFAULT 0,        -- 是否禁用
    has_child         BIT(1) DEFAULT 0,        -- 是否有子类型
    archive           BIT(1) DEFAULT 0,        -- 是否归档
    action_id         INT,                     -- 关联操作类型
    analysis_disable  TINYINT(3) DEFAULT 0     -- 是否排除出分析
);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | INT | 是 | 主键，自增 |
| `t_name` | VARCHAR(50) | 是 | 类型名称（如"餐饮"、"工资"） |
| `parent` | INT | 否 | 父类型 ID，-1 表示顶级分类 |
| `t_disable` | BIT(1) | 否 | 是否禁用 |
| `has_child` | BIT(1) | 否 | 是否有子分类 |
| `archive` | BIT(1) | 否 | 是否归档（隐藏但不删除） |
| `action_id` | INT | 否 | 关联 `action.id`，决定是收入还是支出类型 |
| `analysis_disable` | TINYINT(3) | 否 | 是否排除出财务分析 |

**对应实体类：** `Type.java`

**层级结构示例：**
```
餐饮 (parent=-1, action_id=2)  # 支出类型
├── 早餐 (parent=餐饮.id)
├── 午餐 (parent=餐饮.id)
└── 晚餐 (parent=餐饮.id)

工资 (parent=-1, action_id=1)  # 收入类型
├── 基本工资
└── 奖金
```

---

### 4. action（操作类型表）

定义交易的基本操作类型：收入、支出、转账。

```sql
CREATE TABLE action (
    id      INT PRIMARY KEY AUTO_INCREMENT,
    h_name  VARCHAR(50) NOT NULL,      -- 操作名称
    exempt  BIT(1),                    -- 是否默认免计
    handle  INT NOT NULL               -- 操作标识
);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | INT | 是 | 主键，自增 |
| `h_name` | VARCHAR(50) | 是 | 操作名称 |
| `exempt` | BIT(1) | 否 | 是否默认免计 |
| `handle` | INT | 是 | 操作标识码 |

**预设数据：**

| id | h_name | handle | 说明 |
|----|--------|--------|------|
| 1 | 收入 | 1 | 金额增加到账户 |
| 2 | 支出 | 2 | 金额从账户减少 |
| 3 | 转账 | 3 | 账户间转移 |

**对应实体类：** `Action.java`

---

### 5. flow_template（交易模板表）

存储常用交易模板，用于快速记账。

```sql
CREATE TABLE flow_template (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(50) NOT NULL,      -- 模板名称
    date_type       TINYINT(3) DEFAULT 0,      -- 日期类型
    money           VARCHAR(20),               -- 预设金额
    type_id         INT,                       -- 交易类型 ID
    action_id       INT,                       -- 操作类型 ID
    account_id      INT,                       -- 主账户 ID
    account_to_id   INT,                       -- 目标账户 ID
    tag_id          INT                        -- 标签 ID
);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | INT | 是 | 主键，自增 |
| `name` | VARCHAR(50) | 是 | 模板名称 |
| `date_type` | TINYINT(3) | 否 | 日期类型标识 |
| `money` | VARCHAR(20) | 否 | 预设金额 |
| `type_id` | INT | 否 | 关联 `type.id` |
| `action_id` | INT | 否 | 关联 `action.id` |
| `account_id` | INT | 否 | 关联 `account.id` |
| `account_to_id` | INT | 否 | 转账目标账户 |
| `tag_id` | INT | 否 | 关联 `tag.id` |

**对应实体类：** `FlowTemplate.java`

---

### 6. tag（标签表）

用于模板分组标签。

```sql
CREATE TABLE tag (
    id      INT PRIMARY KEY AUTO_INCREMENT,
    name    VARCHAR(30) NOT NULL,      -- 标签名称
    color   VARCHAR(15) NOT NULL       -- 标签颜色（十六进制）
);
```

**对应实体类：** `TemplateTag.java`

---

### 7. flow_image（流水图片表）

存储流水的图片附件信息（v2.5.0 新增）。

```sql
CREATE TABLE flow_image (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    flow_id     INT NOT NULL,                  -- 关联流水 ID
    image_name  VARCHAR(100) NOT NULL,         -- 图片文件名
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_flow_id (flow_id)                -- 索引优化查询
);
```

**字段说明：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | INT | 是 | 主键，自增 |
| `flow_id` | INT | 是 | 关联 `flow.id` |
| `image_name` | VARCHAR(100) | 是 | 图片文件名 |
| `upload_time` | DATETIME | 否 | 上传时间，默认当前时间 |

**对应实体类：** `FlowImage.java`

---

## 表关联关系

### ER 图（实体关系）

```
                    ┌─────────────┐
                    │   action    │
                    │  (操作类型)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌─────────────────┐
        │   type   │ │   flow   │ │  flow_template  │
        │ (交易类型)│ │ (交易流水)│ │   (交易模板)     │
        └────┬─────┘ └────┬─────┘ └────────┬────────┘
             │            │                │
             │            │                │
             └──────┬─────┴────────┬───────┘
                    │              │
                    ▼              ▼
              ┌──────────┐  ┌──────────┐
              │ account  │  │   tag    │
              │  (账户)   │  │  (标签)  │
              └──────────┘  └──────────┘
                    │
                    │ (1:N)
                    ▼
              ┌────────────┐
              │ flow_image │
              │ (流水图片)  │
              └────────────┘
```

### 关联关系说明

| 主表 | 从表 | 关系 | 外键 | 说明 |
|------|------|------|------|------|
| action | flow | 1:N | flow.action_id | 每条流水有一个操作类型 |
| action | type | 1:N | type.action_id | 交易类型属于收入或支出 |
| action | flow_template | 1:N | flow_template.action_id | 模板的操作类型 |
| type | flow | 1:N | flow.type_id | 每条流水有一个分类 |
| type | flow_template | 1:N | flow_template.type_id | 模板的分类 |
| type | type | 1:N | type.parent | 类型层级（自关联） |
| account | flow | 1:N | flow.account_id | 主账户 |
| account | flow | 1:N | flow.account_to_id | 转账目标账户 |
| account | flow_template | 1:N | flow_template.account_id | 模板主账户 |
| tag | flow_template | 1:N | flow_template.tag_id | 模板标签 |
| flow | flow_image | 1:N | flow_image.flow_id | 流水的图片附件 |

### JPA 实体关联代码示例

**FlowJpaEntity.java 中的关联：**

```java
@Entity
@Table(name = "flow")
public class FlowJpaEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Integer id;

    @Column(name = "type_id", nullable = false)
    private int typeId;

    @Column(name = "action_id", nullable = false)
    private int actionId;

    @Column(name = "account_id")
    private int accountId;

    @Column(name = "account_to_id")
    private int accountToId;

    // JPA 关联 - 多对一
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "type_id", insertable = false, updatable = false)
    private Type type;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "action_id", insertable = false, updatable = false)
    private Action action;

    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "account_id", insertable = false, updatable = false)
    private Account account;

    @ManyToOne(fetch = FetchType.LAZY, optional = true)
    @JoinColumn(name = "account_to_id", insertable = false, updatable = false)
    private Account accountTo;
}
```

**Type.java 中的关联：**

```java
@Entity
@Table(name = "type")
public class Type {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private int id;

    @Column(name = "action_id")
    private Integer actionId;

    // 关联到 Action
    @ManyToOne(fetch = FetchType.EAGER)
    @JoinColumn(name = "action_id", insertable = false, updatable = false)
    private Action action;
}
```

---

## Liquibase 版本管理

### 概述

项目使用 Liquibase 管理数据库版本，所有表结构变更必须通过 changelog 文件进行。

**配置文件位置：** `src/main/resources/db/changelog/`

### Changelog 文件结构

```
db/changelog/
├── db.changelog-master.yaml      # 主文件，引入其他版本文件
├── yd_jz_2.1.0.yaml              # v2.1.0 初始结构
├── yd_jz_2.3.0.yaml              # v2.3.0 功能扩展
├── yd_jz_2.4.1_fix_decimal.yaml  # v2.4.1 精度修复
└── yd_jz_2.5.0.yaml              # v2.5.0 图片功能
```

### 主配置文件

**db.changelog-master.yaml:**
```yaml
databaseChangeLog:
  - include:
      file: classpath:/db/changelog/yd_jz_2.1.0.yaml
  - include:
      file: classpath:/db/changelog/yd_jz_2.3.0.yaml
  - include:
      file: classpath:/db/changelog/yd_jz_2.4.1_fix_decimal.yaml
  - include:
      file: classpath:/db/changelog/yd_jz_2.5.0.yaml
```

### 版本变更说明

#### v2.1.0 - 初始版本
- 创建 `flow_template` 表
- 创建 `tag` 表
- 添加 `type.archive` 字段
- 添加 `account.disable` 字段
- 添加 `type.action_id` 字段

#### v2.3.0 - 功能扩展
- 添加 `type.analysis_disable` 字段（排除分析）

#### v2.4.1 - 精度修复
- 修复 `flow.money` 小数精度问题
- 修复 `account.money` 和 `account.exempt_money` 精度

#### v2.5.0 - 图片附件
- 添加 `flow.from_source` 字段（来源标识）
- 创建 `flow_image` 表
- 添加 `idx_flow_id` 索引

### 添加新的数据库变更

1. 在 `db/changelog/` 目录创建新的 yaml 文件
2. 在 `db.changelog-master.yaml` 中引入
3. 使用唯一的 changeSet id

**示例 - 添加新字段：**

```yaml
databaseChangeLog:
  - changeSet:
      id: 2.6.0-1
      author: your_name
      changes:
        - addColumn:
            tableName: flow
            columns:
              - column:
                  name: new_field
                  type: VARCHAR(50)
                  remarks: 新字段说明
```

**示例 - 创建新表：**

```yaml
databaseChangeLog:
  - changeSet:
      id: 2.6.0-2
      author: your_name
      changes:
        - createTable:
            tableName: new_table
            columns:
              - column:
                  name: id
                  type: INT
                  autoIncrement: true
                  constraints:
                    primaryKey: true
                    nullable: false
              - column:
                  name: name
                  type: VARCHAR(100)
                  constraints:
                    nullable: false
```

---

## 双重数据访问模式

项目同时使用 JPA 和 MyBatis 进行数据访问，各有分工。

### JPA - 简单 CRUD

**使用场景：** 单表增删改查、简单关联查询

**Repository 位置：** `com.deepblue.yd_jz.dao.jpa`

```java
@Repository
public interface FlowRepository extends JpaRepository<FlowJpaEntity, Integer> {
    // 简单查询
    List<FlowJpaEntity> findByAccountId(int accountId);

    // 条件查询
    List<FlowJpaEntity> findByFDateBetween(String startDate, String endDate);

    // 排序
    List<FlowJpaEntity> findByAccountIdOrderByFDateDesc(int accountId);
}
```

**Repository 列表：**
- `AccountRepository` - 账户 CRUD
- `FlowRepository` - 流水 CRUD
- `FlowTemplateRepository` - 模板 CRUD
- `FlowImageRepository` - 图片 CRUD
- `TypeRepository` - 类型 CRUD
- `ActionRepository` - 操作类型
- `TemplateTagRepository` - 标签 CRUD

### MyBatis - 复杂查询

**使用场景：** 动态条件查询、复杂联表、统计分析

**DAO 位置：** `com.deepblue.yd_jz.dao.mybatis`

```java
@Mapper
public interface FlowDao {
    // 动态条件查询
    @SelectProvider(type = FlowSelectProvider.class, method = "selectFlows")
    List<Flow> selectFlows(FlowQueryDTO query);

    // 复杂统计
    @Select("SELECT type_id, SUM(money) as total FROM flow " +
            "WHERE f_date BETWEEN #{start} AND #{end} GROUP BY type_id")
    List<TypeSummary> getTypeSummary(@Param("start") String start,
                                      @Param("end") String end);
}
```

**动态 SQL Provider 示例：**

```java
public class FlowSelectProvider {
    public String selectFlows(FlowQueryDTO query) {
        return new SQL() {{
            SELECT("*");
            FROM("flow");

            if (query.getAccountId() != null) {
                WHERE("account_id = #{accountId}");
            }
            if (query.getTypeId() != null) {
                WHERE("type_id = #{typeId}");
            }
            if (query.getStartDate() != null) {
                WHERE("f_date >= #{startDate}");
            }
            if (query.getEndDate() != null) {
                WHERE("f_date <= #{endDate}");
            }

            ORDER_BY("f_date DESC");
        }}.toString();
    }
}
```

### 选择原则

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| 单表 CRUD | JPA | 代码简洁，自动生成 SQL |
| 简单关联查询 | JPA | @ManyToOne 自动加载 |
| 动态条件查询 | MyBatis | SQL 灵活，易于调试 |
| 复杂统计分析 | MyBatis | 原生 SQL 性能更好 |
| 分页查询 | MyBatis + PageHelper | 分页插件支持 |

---

## 常见操作示例

### 1. 添加交易流水

```java
@Service
public class FlowService {
    @Autowired
    private FlowRepository flowRepository;

    @Autowired
    private AccountRepository accountRepository;

    @Transactional
    public FlowJpaEntity addFlow(FlowDTO dto) {
        // 1. 创建流水记录
        FlowJpaEntity flow = new FlowJpaEntity();
        flow.setFDate(dto.getDate());
        flow.setMoney(dto.getMoney());
        flow.setTypeId(dto.getTypeId());
        flow.setActionId(dto.getActionId());
        flow.setAccountId(dto.getAccountId());
        flow.setNote(dto.getNote());
        flow.setFCreateDate(LocalDateTime.now().toString());

        // 2. 保存流水
        flow = flowRepository.save(flow);

        // 3. 更新账户余额（如果不是免计）
        if (!dto.isExempt()) {
            updateAccountBalance(dto);
        }

        return flow;
    }
}
```

### 2. 查询月度流水

```java
// JPA 方式
List<FlowJpaEntity> flows = flowRepository
    .findByFDateBetweenOrderByFDateDesc("2024-01-01", "2024-01-31");

// MyBatis 方式（支持更多条件）
FlowQueryDTO query = new FlowQueryDTO();
query.setStartDate("2024-01-01");
query.setEndDate("2024-01-31");
query.setAccountId(1);
query.setActionId(2);  // 只查支出
List<Flow> flows = flowDao.selectFlows(query);
```

### 3. 统计分类支出

```java
@Mapper
public interface FlowDao {
    @Select("""
        SELECT t.t_name as typeName,
               SUM(CAST(f.money AS DECIMAL(20,2))) as total
        FROM flow f
        JOIN type t ON f.type_id = t.id
        WHERE f.f_date BETWEEN #{start} AND #{end}
          AND f.action_id = 2
        GROUP BY f.type_id
        ORDER BY total DESC
    """)
    List<TypeSummary> getCategorySummary(@Param("start") String start,
                                          @Param("end") String end);
}
```

### 4. 添加流水图片

```java
@Service
public class FlowImageService {
    @Autowired
    private FlowImageRepository flowImageRepository;

    public FlowImage addImage(int flowId, String imageName) {
        FlowImage image = new FlowImage();
        image.setFlowId(flowId);
        image.setImageName(imageName);
        image.setUploadTime(new Date());
        return flowImageRepository.save(image);
    }

    public List<FlowImage> getImagesByFlowId(int flowId) {
        return flowImageRepository.findByFlowId(flowId);
    }
}
```

---

## 注意事项

### 1. 金额字段存储

**重要：** 金额使用 `VARCHAR` 类型存储，而非 `DECIMAL`。

```java
// 正确：字符串存储
private String money;

// 计算时转换
BigDecimal amount = new BigDecimal(flow.getMoney());
```

**原因：** 避免浮点精度问题，前端 JavaScript 也使用字符串处理。

### 2. 软删除

流水记录使用 `f_disable` 字段进行软删除：

```java
// 软删除
flow.setFDisable(true);
flowRepository.save(flow);

// 查询时排除已删除
@Query("SELECT f FROM FlowJpaEntity f WHERE f.fDisable = false")
List<FlowJpaEntity> findAllActive();
```

### 3. 日期格式

统一使用字符串格式 `yyyy-MM-dd`：

```java
// 日期字段
private String fDate;  // 如 "2024-01-15"

// 创建时间
private String fCreateDate;  // 如 "2024-01-15 10:30:00"
```

### 4. 外键约束

**当前设计未使用数据库外键约束**，关联通过应用层维护：

- 删除账户前需检查是否有关联流水
- 删除类型前需检查是否有关联流水
- 代码层面保证数据完整性

### 5. 索引优化

已创建的索引：
- `flow_image.idx_flow_id` - 按流水 ID 查询图片

建议添加的索引：
```sql
-- 按日期范围查询优化
CREATE INDEX idx_flow_date ON flow(f_date);

-- 按账户查询优化
CREATE INDEX idx_flow_account ON flow(account_id);

-- 按类型统计优化
CREATE INDEX idx_flow_type_date ON flow(type_id, f_date);
```

### 6. 事务管理

涉及余额变更的操作必须使用事务：

```java
@Transactional
public void transferMoney(int fromAccountId, int toAccountId, String amount) {
    // 1. 扣减源账户
    // 2. 增加目标账户
    // 3. 记录流水
    // 任一步骤失败，整体回滚
}
```

---

## 相关文件路径

| 类型 | 路径 |
|------|------|
| 实体类 | `src/main/java/com/deepblue/yd_jz/entity/` |
| JPA Repository | `src/main/java/com/deepblue/yd_jz/dao/jpa/` |
| MyBatis DAO | `src/main/java/com/deepblue/yd_jz/dao/mybatis/` |
| Liquibase 脚本 | `src/main/resources/db/changelog/` |
| 配置文件 | `src/main/resources/application-*.properties` |

---

## 数据库备份与恢复

### 概述

系统支持自动备份和手动备份/恢复功能，使用 `mysqldump` 和 `mysql` 命令行工具。

### 配置项

| 配置项 | 说明 | Windows 示例 | Ubuntu 示例 |
|--------|------|--------------|-------------|
| `sqlBackUpFolder` | 备份文件目录 | `D:/backup/` | `/Ledger/backup/` |
| `system.os` | 操作系统类型 | `win` | `ubuntu` |
| `sqldumpCmd` | 备份命令 | `D:/mysql/bin/mysqldump ...` | `/usr/bin/mysqldump ...` |
| `sqlRestoreCmd` | 恢复命令 | `D:/mysql/bin/mysql ...` | `/usr/bin/mysql ...` |
| `sqlDropCreateCmd` | 清空数据库命令 | `D:/mysql/bin/mysql ... -e "DROP..."` | `/usr/bin/mysql ... -e "DROP..."` |
| `cron.sqlBackupTime` | 自动备份 cron 表达式 | `0 0 22 * * ?` | `0 0 22 * * ?` |

### 自动备份

由 `SQLBackUpTask.java` 定时任务执行，默认每天 22:00 运行。

**流程：**
1. 生成文件名：`yd_jz_yyyyMMdd_HHmm.sql`
2. 执行 `mysqldump` 命令
3. 发送 WebHook 通知（邮件）

### 手动备份

**接口：** `POST /backup/backup`

**流程：**
1. 生成文件名：`yd_jz_manual_yyyyMMdd_HHmm.sql`
2. 执行 `mysqldump` 命令
3. 发送 WebHook 通知
4. 返回文件名

### 恢复数据库

**接口：** `POST /backup/restore`（multipart/form-data）

**流程：**
1. 上传 `.sql` 备份文件
2. 保存到备份目录
3. 执行 `DROP DATABASE; CREATE DATABASE;`（清空数据库）
4. 执行 `mysql < backup.sql`（导入数据）
5. 3 秒后自动重启服务
6. Liquibase 自动补齐新版本表结构

### 恢复兼容性

恢复前先清空数据库，解决以下问题：

| 场景 | 问题 | 解决方案 |
|------|------|----------|
| 旧备份无 `--databases` | 新版本表不会被删除 | `DROP DATABASE` 清空所有表 |
| 旧备份无 Liquibase 表 | 迁移记录不一致 | 清空后 Liquibase 从头运行 |
| 备份缺少新版本字段 | 启动报错 | Liquibase 自动补齐 |

### 跨平台支持

根据 `system.os` 配置选择命令执行方式：

```java
private String[] buildCommand(String command) {
    if ("win".equalsIgnoreCase(systemOs)) {
        return new String[]{"cmd", "/c", command};
    } else {
        return new String[]{"/bin/sh", "-c", command};
    }
}
```

### 相关文件

| 文件 | 说明 |
|------|------|
| `service/BackupService.java` | 备份恢复业务逻辑 |
| `controller/BackupController.java` | 备份恢复接口 |
| `task/SQLBackUpTask.java` | 自动备份定时任务 |
