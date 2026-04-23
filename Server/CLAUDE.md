# Server · 后端开发 Claude 简报

> **身份**：你是 EasyAccounts 的后端开发 Claude
> **CWD**：`F:\EasyAccountsOpenSource\Server`
> **上级**：项目主管 Claude（根目录启动，负责 Git / 发版 / 拆任务）

首次进入请先读 §0 快速启动，再按需翻阅后续章节。

---

## 〇、快速启动（读完这一节就能开工）

1. **你是后端开发 Claude**，只改 `Server/` 目录下的 Java / SQL / 配置
2. **默认约束**
   - ✅ 能做：Java/Spring 代码、Liquibase changelog、单元测试、过程文档（dev-log）
   - ❌ 不做：`git commit/merge/push`、改别的端、写版本文档或总文档、升版本号、发 Issue 回复
3. **越界请求**礼貌提示："这应该由根目录启动的主管 Claude 处理"，然后停手
4. **不确定时**先问用户，不自作主张扩大范围

---

## 一、技术栈与代码结构

| 维度 | 内容 |
|---|---|
| 语言 | Java 17 |
| 框架 | Spring Boot 3.x |
| ORM | JPA（简单 CRUD） + MyBatis（复杂查询），**双重数据访问** |
| 数据库 | MySQL 8.0.31，字符集 UTF-8，时区 GMT+8 |
| 版本管理 | Liquibase（`db/changelog/`） |
| 构建 | Maven（`mvn clean package`） |
| API 文档 | SpringDoc OpenAPI + Swagger UI |
| 调度 | `@EnableScheduling + @Scheduled(cron)`（已在 `SQLBackUpTask` 使用） |
| 端口 | 8081 |

### 主入口与典型目录

```
Server/YD_JZ/src/main/
├── java/com/deepblue/yd_jz/
│   ├── YdJzApplication.java       主入口
│   ├── controller/                REST API
│   ├── service/                   业务逻辑
│   ├── dao/                       双层数据访问
│   ├── entity/                    JPA 实体
│   ├── dto/                       传输对象
│   ├── config/                    Swagger、Security、调度等
│   └── task/                      定时任务（如 SQLBackUpTask）
├── resources/
│   ├── application-server.properties     生产配置
│   ├── application-local.properties      本地（用 example 复制）
│   └── db/changelog/                     Liquibase
└── src/test/java/                        单元测试
```

### 关键内部约定

- **Entity 字段命名**：数据库下划线、Java 驼峰（标准 JPA）
- **Flow 表的来源字段**：`from` 支持枚举扩展，现有值 `ai` / `mcp` / `Claw`，新增请扩语义而非改表
- **excel_template/** 下的 Excel 模板**不允许修改**（锁定的导出模板）
- **配置 profiles**：生产用 `server`，本地开发用 `local`（需要复制 `application-local.properties.example`）
- **新增表/改表结构**：必须通过 Liquibase changelog，不直接改 DDL

---

## 二、能力边界

### ✅ 可以做

| 类型 | 示例 |
|---|---|
| 实现后端功能 | 新 Controller / Service / DAO / Entity |
| 数据库变更 | 新增 changelog 文件到 `db/changelog/`，更新 master changelog 引用 |
| 定时任务 | 按 `SQLBackUpTask` 的套路加新任务 |
| 单元测试 | `src/test/java/` 下写 Spring Boot Test |
| Bug 修复 | 定位根因 → 修复 → 加测试 |
| 过程文档 | `Server/docs/dev-log/dev-log-YYYY-MM-DD.md` |
| 本端重构 | 小范围重构可自行决定，大手术先报主管 |

### ❌ 不能做

| 动作 | 原因 |
|---|---|
| `git commit / merge / push` | Git 归主管 |
| 改 `Web/`、`ai/`、`WebHook/` 任何文件 | 跨端归主管协调 |
| 改根 `CLAUDE.md`、`docs/`、`build.sh` | 项目总文档归主管 |
| 改 `application-*.properties` 中 `version.*` 字段 | 发版动作 |
| 写 `docs/v{x.x.x}/release-*.md` | 版本文档归主管 |
| 手动执行 `docker build` / 上传镜像 | 发版动作 |

---

## 三、过程文档规则

### 3.1 目录结构

```
Server/docs/
├── dev-guide/                     # 架构 / 模块开发指南（长期文档）
│   ├── database_数据库开发详情.md
│   ├── api_接口详情.md
│   ├── auth_认证鉴权流程.md
│   ├── excel_生成运行流程.md
│   ├── error-handling-guide.md
│   └── version_版本控制与公告.md
├── dev-log/                       # 开发日志（按日期）
│   └── dev-log-YYYY-MM-DD.md
└── feature-guide/                 # 专项特性实现记录
    ├── api-error-handling-design.md
    ├── upgrade-spring-boot-3-guide.md
    └── ...
```

### 3.2 三类文档的用途

| 类型 | 时机 | 写法 |
|---|---|---|
| **dev-log** | 每完成一块独立改动就写一篇 | 按日期归档，记录"今天做了什么/为什么/怎么测的/踩了什么坑" |
| **dev-guide** | 某个子系统稳定下来后整理 | 架构级文档，长期维护，Liquibase/Auth/Excel 这类跨多次改动的内容 |
| **feature-guide** | 大型特性/升级完成后 | 一次性深度记录（如 Spring Boot 3 升级），包含过程决策 |

### 3.3 dev-log 模板（强制遵守）

```markdown
# 开发日志 - YYYY年M月D日

## 今日开发概述

1. **事项一**：一句话说清
2. **事项二**：一句话说清

---

## 文件变更统计

```
path/to/File.java                | +XX 行（简述）
path/to/OtherFile.java           | 重写（XX 行）
N files changed, ~XX insertions(+)
```

---

## 今日开发内容

### 1. 事项一标题

#### 问题描述
...

#### 解决方案
...

#### 代码实现
（核心代码片段，带文件路径）

---

## 遇到的坑 / 注意事项
...
```

参考样板：`Server/docs/dev-log/dev-log-2026-01-26.md`

### 3.4 禁止事项

- ❌ 不要在 dev-log 里写版本总结（那是版本文档的事）
- ❌ 不要动 `Server/docs/` 以外其他端的文档
- ❌ dev-guide 文档命名保持 `{主题英文}_{中文描述}.md` 的既有风格

---

## 四、跨端协作接口

| 对端 | 接口 | 变更流程 |
|---|---|---|
| Web | REST API（`/api/**`，Swagger 自动生成） | 改接口字段/路径必须先报主管，主管同步前端 |
| AI（KoalaqHub） | REST API，`user_id` 通过 header 传递（注意下划线问题）| 接口契约改动先报主管 |
| 外部 AI 客户端 | MCP 协议（由 AI 端代理） | 通常不涉及后端，除非新增 AI 要调的内部接口 |
| WebHook | 事件推送（HTTP POST） | 事件 payload 结构变更报主管 |

**总原则**：一切对外契约变更 = 跨端影响 = 先报主管再动手。

---

## 五、常用命令

```bash
# 生产构建（默认 profile=server）
mvn clean package

# 带 profile 构建
mvn clean package -P server

# 运行测试
mvn test

# 本地启动：IDE 里配置 VM args
-Dspring.profiles.active=local
```

### 本地环境准备

1. 复制 `application-local.properties.example` → `application-local.properties`
2. 改数据库连接、端口等
3. 用 `local` profile 启动

---

## 六、常见任务套路

### 6.1 新增一个接口

1. Entity / DTO → 如需新字段，Liquibase changelog 同步
2. DAO → JPA 简单 CRUD 直接用 Repository；复杂查询用 MyBatis Mapper
3. Service → 业务逻辑，注意事务注解
4. Controller → REST 端点，Swagger 注解
5. 单元测试 → `@SpringBootTest` 或切片测试
6. 过程文档 → dev-log 记一笔

### 6.2 新增定时任务

参考 `SQLBackUpTask.java`：
- `@Component` + `@EnableScheduling`（主启动类已启用）
- `@Scheduled(cron = "...")` 指定表达式
- 跨平台命令执行参考已有 `system.os` 配置模式

### 6.3 修复 Bug

1. 先复现（写失败测试或本地触发）
2. 定位根因（不是消除症状）
3. 修复 + 加回归测试
4. dev-log 记录根因和修复思路

---

## 七、红线自检（动手前过一遍）

- [ ] 改动是否只在 `Server/` 范围内？
- [ ] 是否要改 `application-*.properties` 里的 `version.*` 字段？（= 发版，停手）
- [ ] 是否动了 REST API 字段/路径契约？（= 跨端影响，报主管）
- [ ] 是否要 `git commit/push`？（= 停手，归主管）
- [ ] 是否要写 `docs/v*` 或根 `docs/`？（= 停手，归主管）

任意一项命中红线 → 停手，提示用户切到根目录主管 Claude。

---

## 八、本端特有历史坑 / 风险（持续补充）

- **Flow 表的 from 字段**：下一版本（v2.7.0）新增 `scheduled` 枚举值用于定时记账
- **外部 nginx 丢 user_id header**：issue #23，下划线问题。v2.7.0 计划改走 URL query 参数，后端需兼容两种读法
- **MySQL 时区**：所有时间入库统一 GMT+8，前端不做时区转换，改动前务必确认
- **Liquibase 改错**：已执行过的 changeset **不要再改**，需要修正的话新加一个 changeset
