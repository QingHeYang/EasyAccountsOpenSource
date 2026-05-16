# EasyAccounts Server 后端

EasyAccounts 的后端服务，提供 RESTful API 支持财务数据管理。

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | Spring Boot | 3.4.x |
| 语言 | Java | 17 |
| 数据库 | MySQL | 8.0 |
| ORM | JPA + MyBatis | 双重数据访问 |
| 数据库迁移 | Liquibase | 4.x |
| API 文档 | SpringDoc OpenAPI | 2.x |
| 日志 | Log4j2 | 2.x |
| Excel | EasyExcel | 3.x |
| 构建工具 | Maven | 3.x |

---

## 项目结构

```
YD_JZ/
├── src/main/java/com/deepblue/yd_jz/
│   ├── YdJzApplication.java          # 应用入口
│   │
│   ├── config/                       # 配置类
│   │   ├── SwaggerConfig.java        # API 文档配置
│   │   ├── WebConfig.java            # Web 配置
│   │   └── TokenInterceptor.java     # Token 拦截器
│   │
│   ├── controller/                   # 控制器层
│   │   ├── AccountController.java    # 账户 API
│   │   ├── FlowController.java       # 流水 API
│   │   ├── TypeController.java       # 分类 API
│   │   ├── AnalysisController.java   # 统计 API
│   │   ├── HomeController.java       # 首页 API
│   │   ├── AuthController.java       # 认证 API
│   │   ├── ImageController.java      # 图片 API
│   │   ├── ScreenController.java     # 筛选 API
│   │   └── FlowTemplateController.java # 模板 API
│   │
│   ├── service/                      # 业务逻辑层
│   │   ├── FlowService.java          # 流水业务
│   │   ├── AccountService.java       # 账户业务
│   │   ├── TypeService.java          # 分类业务
│   │   ├── AnalysisService.java      # 统计业务
│   │   ├── ExcelService.java         # Excel 导出
│   │   └── AuthService.java          # 认证业务
│   │
│   ├── dao/                          # 数据访问层
│   │   ├── jpa/                      # JPA Repository（简单 CRUD）
│   │   │   ├── FlowRepository.java
│   │   │   ├── AccountRepository.java
│   │   │   └── TypeRepository.java
│   │   └── mybatis/                  # MyBatis Mapper（复杂查询）
│   │       ├── FlowDao.java
│   │       └── FlowSelectProvider.java
│   │
│   ├── entity/                       # 实体类
│   │   ├── Flow.java                 # 流水
│   │   ├── Account.java              # 账户
│   │   ├── Type.java                 # 分类
│   │   └── FlowTemplate.java         # 模板
│   │
│   ├── dto/                          # 数据传输对象
│   │   ├── BaseDto.java              # 统一响应格式
│   │   ├── FlowListDto.java          # 流水列表
│   │   └── AnalysisResponseDto.java  # 统计响应
│   │
│   ├── exception/                    # 异常处理
│   │   ├── ErrorCode.java            # 错误码定义
│   │   ├── BusinessException.java    # 业务异常
│   │   └── GlobalExceptionHandler.java # 全局异常处理器
│   │
│   ├── utils/                        # 工具类
│   │   ├── DateUtils.java            # 日期工具
│   │   ├── MoneyUtils.java           # 金额工具
│   │   └── VersionUtils.java         # 版本工具
│   │
│   └── task/                         # 定时任务
│       └── SQLBackUpTask.java        # 数据库备份
│
├── src/main/resources/
│   ├── application-server.properties # 生产配置
│   ├── application-local.properties.example # 本地配置示例
│   ├── db/changelog/                 # Liquibase 迁移脚本
│   └── log4j2.xml                    # 日志配置
│
├── excel_template/                   # Excel 模板
│   ├── auto_excel.xlsx               # 月度报表模板
│   └── screen_excel.xlsx             # 筛选报表模板
│
└── pom.xml                           # Maven 配置
```

---

## 环境配置

### 1. 环境要求

- JDK 17+
- Maven 3.6+
- MySQL 8.0+

### 2. 数据库初始化

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE yd_jz CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入初始数据（可选，Liquibase 会自动迁移）
mysql -u root -p yd_jz < MySQL/yd_jz_base.sql
```

### 3. 本地配置

复制示例配置文件：

```bash
cd YD_JZ/src/main/resources
cp application-local.properties.example application-local.properties
```

编辑 `application-local.properties`：

```properties
# 数据库配置
spring.datasource.url=jdbc:mysql://localhost:3306/yd_jz?useUnicode=true&characterEncoding=utf-8&serverTimezone=Asia/Shanghai
spring.datasource.username=root
spring.datasource.password=你的密码

# 文件路径（必须使用绝对路径）
baseAutoExcel=D:/你的项目路径/Server/YD_JZ/excel_template/auto_excel.xlsx
baseScreenExcel=D:/你的项目路径/Server/YD_JZ/excel_template/screen_excel.xlsx
excelAutoFolder=D:/你的输出路径/excel/month/
excelScreenFolder=D:/你的输出路径/excel/screen/
excelAnalysisFolder=D:/你的输出路径/excel/analysis/
image.upload.path=D:/你的输出路径/images/
auth.folder=D:/你的输出路径/auth/
sqlBackUpFolder=D:/你的输出路径/backup/
```

> 注意：输出目录需要手动创建，Spring Boot 内嵌 Tomcat 不支持相对路径。

---

## 开发调试

### 启动服务

```bash
cd YD_JZ

# 使用本地配置启动
mvn spring-boot:run -Dspring-boot.run.profiles=local
```

服务地址：http://localhost:8085

### API 文档

启动后访问 Swagger UI：http://localhost:8085/docs

### 常用命令

```bash
# 编译
mvn clean compile

# 打包（跳过测试）
mvn clean package -DskipTests

# 运行测试
mvn test

# 查看依赖树
mvn dependency:tree
```

### 调试技巧

**1. 热重载**

项目已配置 `spring-boot-devtools`，修改代码后自动重启。

**2. 日志级别**

修改 `log4j2.xml` 或在配置文件中设置：

```properties
logging.level.com.deepblue.yd_jz=DEBUG
logging.level.org.springframework.jdbc=DEBUG
```

**3. SQL 日志**

```properties
# 显示 MyBatis SQL
logging.level.com.deepblue.yd_jz.dao.mybatis=DEBUG
```

---

## API 概览

### 核心 API

| 模块 | 路径 | 说明 |
|------|------|------|
| 首页 | `/api/home/*` | 总览数据、余额统计 |
| 流水 | `/api/flow/*` | 流水 CRUD、批量操作 |
| 账户 | `/api/account/*` | 账户管理 |
| 分类 | `/api/type/*` | 分类管理（支持二级） |
| 统计 | `/api/analysis/*` | 统计报表 |
| 认证 | `/api/auth/*` | 登录、Token 管理 |
| 图片 | `/api/image/*` | 图片上传、获取 |

### 响应格式

所有 API 返回统一格式：

```json
{
  "code": 0,
  "msg": "success",
  "data": { ... }
}
```

### 错误码规范

| 范围 | 说明 |
|------|------|
| 0 | 成功 |
| 40xxx | 参数校验错误 |
| 401 | 未登录 |
| 418 | Token 过期 |
| 42xxx | 业务规则错误 |
| 44xxx | 资源不存在 |
| 50xxx | 系统错误 |

---

## 打包部署

### Maven 打包

```bash
cd YD_JZ
mvn clean package -DskipTests
```

产物：`target/YD_JZ-SNAPSHOT.jar`

### Docker 构建

```bash
cd Server
docker build -t easyaccounts-server .
```

### Docker Compose 示例

```yaml
services:
  server:
    image: easyaccounts-server
    ports:
      - "8085:8085"
    environment:
      - DB_PASSWORD=your_password
      - ENABLE_LOGIN=true
    volumes:
      - ./data/images:/Ledger/images
      - ./data/excel:/Ledger/excel
    depends_on:
      - db

  db:
    image: easyaccounts-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=your_password
    volumes:
      - ./data/mysql:/var/lib/mysql
```

---

## 数据库

### 迁移管理

使用 Liquibase 管理数据库版本，迁移脚本位于：

```
src/main/resources/db/changelog/
├── db.changelog-master.yaml    # 主配置
└── changes/                    # 变更脚本
```

启动时自动执行未应用的迁移。

### MySQL Docker 镜像

项目提供预置初始化脚本的 MySQL 镜像：

```bash
cd MySQL
docker build -t easyaccounts-mysql .
```

镜像特点：
- 基于 MySQL 8.0.31
- 内置 `yd_jz_base.sql` 初始化脚本
- 首次启动自动初始化

---

## 认证系统

### 配置项

> **v2.7.0 起**：以下配置已从 `application-*.properties` 下沉到数据库（前端「**系统设置 → 鉴权**」UI 管理），**改完立即生效，无需重启**。开发期可直接在数据库 `app_config` 表里查看/调整：

| 配置 key | 说明 | 默认 |
|---------|------|------|
| `auth.enable` | 是否启用登录 | true |
| `auth.expired` | Token 过期时间（分钟）| 30 |
| `auth.single_login` | 单设备登录（true=新登录踢掉旧设备）| true |

### Token 机制

- Token 存储在文件系统（`auth.folder` 目录）
- 支持多设备登录或单设备登录模式
- Token 过期后返回 418 状态码

---

## 定时任务

### 数据库备份

> **v2.7.0 起**：备份开关与 cron 表达式已迁移到「**系统设置 → 备份**」UI（数据库 `app_config` 表），运行期可动态调整。

```properties
# 仅作为备份命令模板（mysqldump 路径，开发期可在 application-local.properties 中覆盖）
sqldumpCmd=mysqldump -h localhost -P 3306 -uroot -p密码 --databases yd_jz >
```

备份文件存储在 `sqlBackUpFolder` 配置的目录。

### v2.7.0 新增定时任务

| 任务 | 用途 | 实现位置 |
|------|------|---------|
| `ScheduledFlowExecuteTask` | 定时记账（周期账单自动生成流水）| `task/ScheduledFlowExecuteTask.java` |
| `AutoExcelExecuteTask` | 每月自动导出 Excel 报表 | `task/AutoExcelExecuteTask.java` |
| `ReminderDispatchTask` | 提醒分发（站内通知 + 邮件）| `task/ReminderDispatchTask.java` |
| `SQLBackUpTask` | SQL 数据库备份 | `task/SQLBackUpTask.java` |

---

## 相关文档

各端架构指南、开发日志、专项设计已迁移到独立的 Devlog 仓库（不在开源源码仓库中）。开源用户可参考：

- [GitBook 用户文档](https://mercys-organization-2.gitbook.io/easyaccounts/)
- [部署仓库](https://github.com/QingHeYang/EasyAccounts)
