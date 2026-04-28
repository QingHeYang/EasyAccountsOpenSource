# 配置 UI 化 · 后端技术方案（v2.7.0）

本文档是**后端技术方案草案**，用于提交给项目主管 Review。产品需求见根目录 `docs/v2.7.0/plan-config-ui.md`，本文档**不重复产品语义**，只回答「后端怎么实现」。

---

## 概览

| 项目 | 内容 |
|------|------|
| **分支** | `2.7.0`（与定时记账同分支） |
| **产品文档** | `docs/v2.7.0/plan-config-ui.md` |
| **本文档作者** | 后端开发 Claude（Server + WebHook 一体） |
| **状态** | 🟡 方案草案 + 开发计划已落盘；代码尚未动 |
| **涉及模块** | Server（含吸收 WebHook 邮件能力） |
| **开发分支** | `2.7.0-config-ui`（已创建） |

---

## 与产品需求的关键对齐

| 产品原则 | 后端含义 |
|---|---|
| 邮件 SMTP / 备份 cron / 认证开关 全部 UI 化 | 配置入库，运行时热生效，不重启 |
| WebHook 容器取消发布 | 把现 `webhook.py` 的邮件组装能力内聚到 Server，删除 `NotificationWebHook` Bean，移除 `webhook_url` 配置 |
| 老版本 env **直接失效**，不做兼容回退 | 升级即弃用旧 env；用户在前端重填一次。后端**不**实现"读不到 DB 就 fallback 到 env"的回退逻辑 |
| 备份频率：每天 / 每周 / 每月 三选一，时间 HH:mm，月内日期限 1-28，单选 | DB 存简单结构（frequency + time + dayOfWeek + dayOfMonth），运行时拼成 cron |
| 修改备份配置后立即生效 | `@Scheduled(cron=)` 不再适用，改用 `SchedulingConfigurer` 动态调度 |
| auth.enable 也 UI 化 | 主管已确认采纳 C 选项（即可切换登录开关） |
| 邮件密码加密存储 | AES 对称加密，密钥写死代码（详见 §三） |

---

## 一、数据模型

### 1.1 表结构

**不新建表**。完全复用 v2.7.0 已建的 `app_config` 表：

| 列 | 类型 | 说明 |
|---|---|---|
| `id` | INT PK AUTO_INCREMENT | |
| `domain` | VARCHAR(50) NOT NULL | 业务域 |
| `config_key` | VARCHAR(50) NOT NULL | 域内 key |
| `config_value` | VARCHAR(255) NOT NULL | 字符串存储 |
| `updated_at` | DATETIME NOT NULL | 最近更新时间 |
| UK | `(domain, config_key)` | 域内 key 唯一 |

**长度评估**：
- AES 加密后的 SMTP 密码（16 字节明文 → AES-128/CBC + IV + Base64）≈ 64 字节，最长 ~150 字节，VARCHAR(255) 够用
- to_list 多收件人逗号分隔，10 个邮箱内 ≤ 255
- 暂不扩 TEXT，不需要额外索引

### 1.2 配置项总清单

按 domain 分组：

#### domain = `mail`（邮件 SMTP，吸收 WebHook 的活）

| key | 默认值 | 加密 | 说明 |
|---|---|---|---|
| `smtp_server` | `''` | 否 | SMTP 服务器地址 |
| `smtp_port` | `465` | 否 | 端口 |
| `from_email` | `''` | 否 | 发件邮箱 |
| `password` | `''` | **是** | 发件邮箱密码（明文进，密文存） |
| `to_list` | `''` | 否 | 收件人列表（逗号分隔） |
| `send_sql_backup` | `true` | 否 | SQL 备份邮件全局开关 |
| `send_excel` | `true` | 否 | 月度/筛选/分析 Excel 邮件全局开关 |

> 定时记账提醒邮件无独立全局开关，由规则级 `email_enabled` 字段控制（已实现）。

#### domain = `backup`（备份 cron）

| key | 默认值 | 说明 |
|---|---|---|
| `enabled` | `true` | 是否启用自动备份 |
| `frequency` | `daily` | `daily` / `weekly` / `monthly` |
| `time` | `22:00` | HH:mm，与现 env 默认 22:00 对齐 |
| `day_of_week` | `1` | 1-7，1=周一；仅 frequency=weekly 用 |
| `day_of_month` | `1` | 1-28（UI 限制 1-28，避免 29/30/31 部分月份不执行）；仅 frequency=monthly 用 |

> 不存 cron 原文，运行时由 5 个字段拼成 `0 mm HH * * ?` / `0 mm HH ? * MON` / `0 mm HH dd * ?`。

#### domain = `auth`（认证）

| key | 默认值 | 说明 |
|---|---|---|
| `login_enable` | `false` | 是否启用登录功能（与原 env `ENABLE_LOGIN` 默认值一致） |
| `single_login` | `true` | 单端 / 多端登录 |
| `token_expired_minutes` | `30` | Token 过期分钟数（**确认单位为分钟**，对应 `AuthService.expired * 60 * 1000`） |

#### domain = `scheduled_flow`（已存在，本次不动）

| key | 当前值 | 说明 |
|---|---|---|
| `remind_before_days` | `1` | 已存在 |
| `remind_time` | `09:00` | 已存在 |

### 1.3 Liquibase changeset

**追加到 `yd_jz_2.7.0.yaml` 末尾**（v2.7.0 还未发布，作为同版本 seed 一并交付）：

```yaml
- changeSet:
    id: 2.7.0-seed-app-config-mail-backup-auth
    author: claude
    changes:
      - sql:
          sql: |
            INSERT INTO app_config (domain, config_key, config_value, updated_at) VALUES
              -- mail
              ('mail',   'smtp_server',     '',      NOW()),
              ('mail',   'smtp_port',       '465',   NOW()),
              ('mail',   'from_email',      '',      NOW()),
              ('mail',   'password',        '',      NOW()),
              ('mail',   'to_list',         '',      NOW()),
              ('mail',   'send_sql_backup', 'true',  NOW()),
              ('mail',   'send_excel',      'true',  NOW()),
              -- backup
              ('backup', 'enabled',         'true',  NOW()),
              ('backup', 'frequency',       'daily', NOW()),
              ('backup', 'time',            '22:00', NOW()),
              ('backup', 'day_of_week',     '1',     NOW()),
              ('backup', 'day_of_month',    '1',     NOW()),
              -- auth
              ('auth',   'login_enable',          'false', NOW()),
              ('auth',   'single_login',          'true',  NOW()),
              ('auth',   'token_expired_minutes', '30',    NOW());
```

**不新增唯一约束**（已有 `uk_app_config_domain_key`）。
**不改 `app_config` 表结构**（VARCHAR(255) 够用）。
**不动其他业务表**。

---

## 二、env 配置变更

### 2.1 即将失效的 env / properties

| env / 配置 | 处置 |
|---|---|
| `SQL_BACKUP_TIME` / `cron.sqlBackupTime` | **删除**，改读 `app_config.backup.*` |
| `ENABLE_LOGIN` / `auth.enable` | **删除**，改读 `app_config.auth.login_enable` |
| `EXPIRED_TIME` / `auth.expired` | **删除**，改读 `app_config.auth.token_expired_minutes` |
| `SINGLE_LOGIN` / `auth.single_login` | **删除**，改读 `app_config.auth.single_login` |
| `webhook_url` | **删除**，邮件改 Server 内聚 |
| `SMTP_SERVER` / `SMTP_PORT` / `SMTP_MAIL` / `SMTP_PASSWORD` / `SMTP_TO_LIST` | **删除**，改读 `app_config.mail.*` |
| `SEND_SQL_BACKUP` / `SEND_EXCEL` | **删除**，改读 `app_config.mail.send_sql_backup` / `send_excel` |

`docker-compose.yml` 升级时也要清理这些 env，**升级指南**单独说明。

### 2.2 仍保留 env

DB 连接 / `server.port` / 文件路径 / Hikari / Liquibase / `system.os` / `sqldumpCmd` 等启动期常量保持原样。

---

## 三、SMTP 密码加密设计

### 3.1 加密参数（用户拍板）

| 项 | 值 |
|---|---|
| 算法 | AES |
| 密钥 | 字符串 `easyaccounts`（写死代码，不走 env） |
| 模式 | AES/CBC/PKCS5Padding（含 IV） |
| 编码 | 密文 → Base64 字符串入库 |
| 入库格式 | 单段 Base64（IV 拼在密文前一并 Base64） |

**密钥来源说明**：用户明确指定写死代码、不走环境变量。这是项目级简化方案，不追求"换机器无法解密"的强度，目的是**避免密码以明文形式出现在数据库导出中**。

### 3.2 流转

```
前端表单 ──(明文 password)──▶ Server Controller
                                      │
                              MailConfigService.update()
                                      │
                            CryptoUtils.aesEncrypt(明文, "easyaccounts")
                                      │
                              app_config.mail.password = 密文 Base64
                                      │
                                  发邮件时
                                      │
                            CryptoUtils.aesDecrypt(密文, "easyaccounts")
                                      │
                              SMTP login(from_email, 明文密码)
```

### 3.3 边界

- **GET 配置接口不返回 password 明文**：返回时整个字段置空 `""`，UI 上显示"已设置"。前端不传该字段视为不修改；前端传空字符串视为清空密码
- **解密失败兜底**：log error + 抛 BusinessException，邮件流程整体失败，不发降级邮件
- **新建空字段**：seed 默认 `password=''` 表示未配置，`MailService` 启动期或发送时检测空字符串则直接跳过发送 + log warn

### 3.4 不做

- ❌ 不引入 BCrypt / Argon2 等单向哈希（密码需要可解密回明文喂给 SMTP）
- ❌ 不做密钥轮换机制（项目级强度够用）
- ❌ 不在日志输出加密前后任何形式的密码

---

## 四、鉴权代码盘点（Phase 5 改造范围）

通过 `grep "@Value\(.*auth\."` 全量扫描，鉴权相关 `@Value` 共 8 处分布在 4 个文件：

| 文件 | 行 | 字段 | 改造方向 |
|---|---|---|---|
| `config/WebConfig.java` | 17 | `auth.enable` | **关键改造点**：当前 `if (authEnable)` 启动期决定是否注册拦截器。需改为**始终注册拦截器**，由拦截器内部每次现读 `AuthConfigService.isLoginEnable()`，否则切换开关需重启 |
| `service/AuthService.java` | 23 | `auth.expired` | 改读 `AuthConfigService.getTokenExpiredMinutes()` |
| `service/AuthService.java` | 25 | `auth.single_login` | 改读 `AuthConfigService.isSingleLogin()` |
| `utils/AuthUtils.java` | 20 | `auth.enable` | 改读 `AuthConfigService.isLoginEnable()` |
| `utils/AuthUtils.java` | 23 | `auth.folder` | **保留 env**，部署级常量（如 `/Ledger/auth/`），不入库 |
| `utils/AuthUtils.java` | 26 | `auth.expired` | 改读 `AuthConfigService.getTokenExpiredMinutes()` |
| `utils/VersionUtils.java` | 45 | `auth.enable` | 改读 `AuthConfigService` |
| `utils/VersionUtils.java` | 48 | `auth.expired` | 改读 `AuthConfigService` |
| `utils/VersionUtils.java` | 51 | `auth.single_login` | 改读 `AuthConfigService` |

**Token 切换处置规则**：用户已确认**不考虑**。即开关从 true→false / false→true 时，后端不主动作废 / 续命已有 Auth 文件，由拦截器实时启停结果自然生效。

**鉴权流程参考文档**：`Server/docs/dev-guide/auth_认证鉴权流程.md`（详细架构图、流程图、核心组件已沉淀，本文档不重复）。

---

## 五、开发推进路径（8 Phase 串行）

> 落盘的开发计划。每个 Phase 完成后在对应行打 ✅ 并记 commit hash 与日期。

### Phase 1: 数据库 seed + AES 加密工具 — ✅ 完成 2026-04-27

**目标**：基础设施层就绪，后续业务代码有数据可读、有工具可用。

**实际交付**（与方案一致 + 一处差异）：
- [x] `db/changelog/yd_jz_2.7.0.yaml`：**合并**老 seed (`scheduled_flow.*` 2 行) 与新 seed (mail/backup/auth 16 行) 到**单一 changeset** `2.7.0-seed-app-config`，共 18 行 `INSERT IGNORE`（开发期可改写，不需要拆两个 changeset）
- [x] `utils/CryptoUtils.java`：AES-256/CBC/PKCS5Padding，SHA-256(`easyaccounts`) 派生 32 字节密钥，IV 随机 16 字节拼接密文一并 Base64
- [x] `test/utils/CryptoUtilsTest.java`：10 个用例覆盖默认/自定义密钥往返、null/空串透传、空明文加密、特殊字符、IV 随机性、密文过短、Base64 非法、错密钥
- [x] `exception/ErrorCode.java`：新增 `CRYPTO_FAILED(50005)`

**验收结果**：56 个测试全绿（原 46 + 新 10）；DB 待用户重启时 Liquibase 重跑验证。

**与方案差异**：原计划用两个独立 changeset，开发期可改写规则下合并为一个。

---

### Phase 2: 三个 ConfigService 语义层 — ✅ 完成 2026-04-27

**目标**：业务代码不直接调通用 `getValue/setValue`，全部走语义化方法。

**实际交付**：
- [x] `utils/SystemConfigConst.java`：mail / backup / auth 三域 16 个 key 常量 + 默认值常量
- [x] `utils/CronBuilder.java`：纯函数 `build(frequency, time, dow, dom)` → cron 表达式（拆出来便于单测）
- [x] `test/utils/CronBuilderTest.java`：13 个用例覆盖 daily/weekly/monthly + 全部校验失败路径
- [x] DTO 6 个：`{Mail,Backup,Auth}Config{Update,Response}Dto`
- [x] `service/MailConfigService.java`：getMaskedConfig（password 脱敏 + isPasswordSet 标记） / update（null=不修改 / 空串=清空 / 非空=AES 加密） / getDecryptedPassword / isMailConfigured 等语义读方法
- [x] `service/BackupConfigService.java`：get（含 cron 一并展示） / update（合并新旧值后 CronBuilder 校验 + 入库；Phase 4 reload 留 TODO） / getCron / isEnabled
- [x] `service/AuthConfigService.java`：isLoginEnable / isSingleLogin / getTokenExpiredMinutes / update（校验 expired 正整数）

**验收结果**：69 测试全绿（原 46 + CryptoUtils 10 + CronBuilder 13）；Service 层 @SpringBootTest 集成测试**未写**，复杂逻辑（加密 / cron 拼装）已抽到 utils 层覆盖，剩余是 thin wrapper，Phase 8 curl 端到端覆盖即可。

**与方案差异**：
- 抽出 `CronBuilder` 为独立工具类（原计划在 Service 内联），换来纯函数级单测覆盖
- DTO 命名 `MailConfigUpdate/ResponseDto` 而非主管文档里的 `*Dto`，加 `Update/Response` 后缀消歧义

---

### Phase 3: 邮件能力内聚 Server — ✅ 完成 2026-04-27

**目标**：吃掉 WebHook 这个中转层，Server 直接连 SMTP。

**实际交付**（在原方案基础上整体重构旧设计）：
- [x] `pom.xml`：新增 `spring-boot-starter-mail` 依赖
- [x] `service/MailService.java`：6 个语义化方法（`sendSqlBackup` / `sendMonthExcel(File, period)` / `sendAnalysisExcel(File, dateRange)` / `sendScreenExcel(File, filterDesc)` / `sendScheduledReminder(ruleName, body)` / `sendTestMail()`），主题统一 `[EasyAccounts]` 前缀，正文结构化（信息块 + 操作建议 + 签名），端口 465 自动 SMTPS，其他端口 STARTTLS，SMTP 参数每次现读 `MailConfigService` 不重启即生效
- [x] 改造 6 个调用点：`SQLBackUpTask` / `BackupService` / `AnalysisService` / `ExcelService` / `ScreenService` / `ReminderService`
- [x] 删除 `utils/NotificationWebHook.java` / `utils/FileMakeWebHook.java` / `dto/WebHookDto.java`
- [x] 删除 `controller/HomeController` 里残留的 `@Value("${webhook_url}")`
- [x] `application-server.properties` / `application-local.properties.example` / `application-local.properties` 全部去掉 `webhook_url`

**验收结果**：69 测试全绿；grep 全仓库代码层零残留；待 Phase 8 实际配 SMTP 跑端到端测试

**与方案差异（重构旧设计）**：
- API 由 `sendFile(file, type, name)` 黑盒分发改为按业务事件分语义方法，调用方零魔术字符串
- 主题统一 `[EasyAccounts] 业务子类型` 格式（之前部分邮件无前缀 / 主题里塞文件名）
- 正文从一句话敷衍改成"说明 + 信息块 + 操作建议 + 签名"四段式
- 旧设计里 `SEND_SQL_BACKUP=False` env 实际从未生效（Java 传 `"sql"`，Python 检查 `"sql_backup"`），新设计统一靠 `mail.send_sql_backup` UI 配置项替代
- 旧 `NotificationWebHook` 把通知正文字节假装成"文件"用 multipart 上传的 hack 彻底消除
- 端口 465 自动 SMTPS（旧实现一刀切 STARTTLS，QQ 邮箱 465 端口实际会失败）
- 测试发邮件返回 `SendResult { success, message }` 把 SMTP 异常透出给前端

---

### Phase 4: 备份调度改动态（运行时热重载） — ✅ 完成 2026-04-27

**目标**：用户在 UI 改备份配置后立即生效，不重启容器。

**实际交付**：
- [x] `event/BackupConfigChangedEvent.java`：新建事件类用于解耦循环依赖
- [x] `task/SQLBackUpTask.java` 重写
  - 删 `@Configuration` + `@EnableScheduling` + 静态 cron 字段，改 `@Component`
  - `@PostConstruct init()` 启动时按当前 DB 配置首次安排
  - `@EventListener onConfigChanged()` 监听事件，重排调度
  - `schedule()` 方法 synchronized：取消旧 `ScheduledFuture` + 现读 `BackupConfigService.getCron()` + 用 `TaskScheduler` + `CronTrigger` 重新安排
  - `backup.enabled = false` 时不安排任务
- [x] `service/BackupConfigService.java`：`update()` 后 `eventPublisher.publishEvent(new BackupConfigChangedEvent(this))`
- [x] `utils/VersionUtils.java`：删 `@Value("${cron.sqlBackupTime:}")` 字段，改 `@Autowired BackupConfigService`，`/getVersion` 接口的 `Backup` 部分现读 `backupConfigService.getCron()` / `isEnabled()`
- [x] 删除 `application-server.properties` / `application-local.properties.example` / `application-local.properties` 三处 `cron.sqlBackupTime`

**验收结果**：69 测试全绿；代码层零 `cron.sqlBackupTime` 残留（仅剩 2 处历史注释）；待 Phase 8 实跑切 daily/weekly/monthly 验证调度热生效

**与方案差异**：
- 方案原计划用 `SchedulingConfigurer`，实际用更简洁的 `TaskScheduler + CronTrigger + ScheduledFuture` 直接管理（理由：SchedulingConfigurer 注册任务后不易动态取消，直接用 TaskScheduler 更直观）
- 用 `ApplicationEventPublisher` 解耦 BackupConfigService 与 SQLBackUpTask，避免双向 Bean 依赖。设计更优于方案描述的"BackupConfigService 直接调 SQLBackUpTask.reload()"

---

### Phase 5: 认证配置读库 — ✅ 完成 2026-04-27

**目标**：把 8 个 `@Value("${auth.*}")` 全部改读 `AuthConfigService`（`auth.folder` 除外）。

**实际交付**：
- [x] `config/WebConfig.java`：删 `@Value("${auth.enable}")` 字段 + 删 `if (authEnable)`，**始终注册拦截器**；通过构造函数把 `AuthConfigService` 注入 TokenInterceptor
- [x] `config/TokenInterceptor.java`：删 `authEnable` 字段，改用 `AuthConfigService` 字段，`preHandle()` 进入时现读 `authConfigService.isLoginEnable()`
- [x] `utils/AuthUtils.java`：删 `authEnable` / `expired` 字段，方法内部现读 `AuthConfigService`
- [x] `service/AuthService.java`：删 `expired` / `singleLogin` 字段，方法内部现读 `AuthConfigService`
- [x] `utils/VersionUtils.java`：3 个字段全部删除，改 `@Autowired AuthConfigService` 现读
- [x] `utils/AuthUtils.java` 的 `auth.folder` **保留** `@Value`，路径常量
- [x] 删除 `application-server.properties` / `application-local.properties.example` / `application-local.properties` 的 `auth.enable` / `auth.expired` / `auth.single_login` 共 9 行

**验收结果**：69 测试全绿；grep `@Value.*auth\.` 仅剩 `auth.folder` 1 处（符合预期）；待 Phase 8 实跑切换登录开关验证

**与方案差异**：无显著差异，按方案落实

---

### Phase 6: 对外 REST 接口 — ✅ 完成 2026-04-27

**目标**：前端有完整入口操作配置。

**实际交付**：
- [x] `controller/SystemConfigController.java`：7 个端点
  - `GET  /system/config/mail` → `MailConfigResponseDto`（password 脱敏，含 `isPasswordSet` 标记）
  - `PUT  /system/config/mail` → 同上
  - `POST /system/config/mail/test` → `SendResult`（success + message，SMTP 异常透出给前端）
  - `GET  /system/config/backup` → `BackupConfigResponseDto`（含拼出的 cron 字段）
  - `PUT  /system/config/backup` → 变更后自动派发 `BackupConfigChangedEvent` → 调度热重载
  - `GET  /system/config/auth` → `AuthConfigResponseDto`
  - `PUT  /system/config/auth` → 变更后下一个请求即生效（拦截器现读 DB）
- [x] 改用现有 `BaseDto<T>` + Swagger `@Operation` / `@Tag` 注解，与既有控制器风格一致
- [x] 不需要新增 `ErrorCode`：CRYPTO_FAILED 已在 Phase 1 加；cron / 参数校验复用现有 PARAM_INVALID / PARAM_FORMAT_ERROR；测试发邮件用 SendResult 携带成功/失败信息，无需独立错误码

**注**：`scheduled_flow` domain 已有 `/scheduledFlow/config/reminder`，**本次未动**。

**验收结果**：69 测试全绿；端到端测试待 Phase 8 实跑

**与方案差异**：
- 取消"通用 GET /system/config/{domain}"模式，改成 3 个 typed GET（mail / backup / auth），前端 OpenAPI 类型推导更友好
- ErrorCode 没新增 SMTP_TEST_FAILED / CRON_INVALID / CONFIG_NOT_FOUND，发现这些场景已被现有错误码或 SendResult 业务字段覆盖

---

### Phase 7: properties 全面清理 — ✅ 完成 2026-04-27

**目标**：被替代的 env / properties 删干净，避免 `@Value` 残留导致启动期 PlaceholderResolutionException。

**实际清理**（Phase 3/4/5 推进过程中已增量清理，本 Phase 主要做总验证）：
- [x] `webhook_url`（Phase 3）
- [x] `cron.sqlBackupTime`（Phase 4）
- [x] `auth.enable` / `auth.expired` / `auth.single_login`（Phase 5）
- [x] `version.webhook_branch`（用户单独要求清理）

**清理范围**：
- [x] `application-server.properties`：全部替换为说明性注释
- [x] `application-local.properties.example`：同上
- [x] `application-local.properties`：本机配置已同步

**验收结果**：
- grep `@Value\(.*\$\{(cron.sqlBackupTime|auth.enable|auth.expired|auth.single_login|webhook_url|...)` 零命中
- grep `(cron.sqlBackupTime|auth.enable|...)` 在 src/ 下命中**全部为说明性注释**（无活引用）
- 69 测试全绿
- 启动无 PlaceholderResolutionException 验证待 Phase 8 实跑

---

### Phase 8: 自测 + 文档收尾 — ✅ 完成 2026-04-27

**目标**：闭环验证 + 文档与代码同步。

**实际交付**：
- [x] 端到端 curl 自测 13 项全过：
  - GET 4 个 system/config 接口 + `/overview` 聚合（含 `humanReadable: "每天 22:00"`）
  - PUT mail 完整 + partial + 清空密码
  - PUT backup cron 拼装（daily/weekly/monthly）+ 校验失败拦截（dayOfMonth=29 → 40003）
  - PUT auth 切换登录开关 + **拦截器现读 DB 验证**（关键改造点）
  - 注册 + token 鉴权 + 关登录完整流程
  - **POST /mail/test 真实发邮件**（QQ 邮箱 465 SMTPS，双收件人收到）
  - **POST /backup/backup 手动备份 + 实际邮件**（包含附件）
  - **日志确认调度热重载**（`backup config changed, rescheduling...`）
  - **日志确认拦截器现读**（`Authentication is disabled. Allowing request`）
- [x] `docs/dev-log/dev-log-2026-04-27.md`：405 行，覆盖全部 8 Phase 实施 + 实测 + 跨端清单
- [x] 本文档（feature-guide）每个 Phase 状态回填 + 与方案差异记录
- [x] 跨端协作清单已嵌入 dev-log（前端 Claude 必须迁 `/scheduledFlow/config/reminder` → `/system/config/scheduledFlow`；移除 `versions.webhookBranch` 字段引用；可用 `/overview` 等新接口）
- [x] 升级指南素材已嵌入 dev-log，待主管整理成正式升级指南

**追加交付**（Phase 8 中追加的功能）：
- [x] `GET /system/config/overview` —— 4 域聚合，password / 收件人邮箱不暴露，含 `humanReadable` cron 翻译
- [x] `GET/PUT /system/config/scheduledFlow` —— 定时记账提醒配置迁到系统设置入口
- [x] 删除 `/scheduledFlow/config/reminder` 老路径

**单测**：69 全绿（46 主线 + 10 CryptoUtils + 13 CronBuilder）。

**待主管决定**：
- WebHook/ Python 目录 `git rm -r`
- `build.sh` 移除 webhook 构建项
- 正式升级指南文档 `docs/v2.7.0/upgrade-guide.md`

---

## 六、风险与对齐

| 风险 | 处置 |
|---|---|
| 启动期初始化早于配置可读 | `MailService` / 备份调度 / 拦截器读 `app_config` 都走"每次现读"，不在启动期 cache |
| 备份调度切动态后影响定时记账 | 定时记账两个 Task 是固定 cron（每分钟扫 + 每天扫），与 `SchedulingConfigurer` 共存无冲突，Phase 4 实测验证 |
| 加密密钥写死后用户改了源码 | 用户场景为单机部署，密钥即使被读到也只能解本机库，可接受 |
| seed 与已存在 `app_config` 冲突 | 唯一约束 `(domain, config_key)` 会拦住，本 changeset 用纯 INSERT；用户若已用过同 key 需手动调整（待主管确认是否需 INSERT IGNORE） |
| 拦截器始终注册带来的性能开销 | 即使关闭登录功能，每个请求多一次 `AuthConfigService.isLoginEnable()` DB 读取；可在 Service 内加 30s Caffeine cache |
| 🔴 **OSIV + 双 ORM 混用导致 Hikari 池等待超时** | 本特性 `AutoExcelExecuteService.runOnce()` 同方法内调 JPA（AppConfig/UserNotice）+ MyBatis（FlowDao），首次实跑触发死锁（详见 dev-log-2026-04-28）。修法：方法加 `@Transactional` 让 Spring 把整个方法绑到一个事务，JPA 和 MyBatis 共享同一 connection。**项目级 recurring 坑**，用户曾经历过类似问题。后续写跨 ORM 方法时需预防性加 @Transactional |

---

## 七、变更日志

| 日期 | 内容 |
|---|---|
| 2026-04-27 | 初稿：§一 数据库 / §二 env / §三 加密 |
| 2026-04-27 | 追加：§四 鉴权代码盘点 / §五 开发推进路径（8 Phase）；分支 `2.7.0-config-ui` 已创建 |
| 2026-04-28 | 追加：§六 风险表新增 OSIV + 双 ORM 死锁条目；HTML 邮件模板 + 启用邮件前 SMTP 校验 + 死锁修复落地（详见 dev-log-2026-04-28） |
