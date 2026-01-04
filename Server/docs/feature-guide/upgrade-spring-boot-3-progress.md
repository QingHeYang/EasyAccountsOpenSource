# Spring Boot 3.x 升级进度

本文档跟踪 EasyAccounts Server 模块升级到 Spring Boot 3.x 的进度。

---

## 升级概览

| 项目 | 内容 |
|------|------|
| **分支** | 2.6.0 |
| **开始时间** | 2026-01-04 |
| **目标版本** | Spring Boot 3.4.1 + Java 17 |
| **状态** | 进行中 |

---

## 阶段进度

### 阶段 1: 准备工作

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 1.1 | 创建特性分支 | ✅ 完成 | 2026-01-04 | 已在特性分支 |
| 1.2 | 升级 Java 11 → 17 | ✅ 完成 | 2026-01-04 | pom.xml java.version=17 |
| 1.3 | 验证编译通过 | ✅ 完成 | 2026-01-04 | mvn clean compile 成功 |

---

### 阶段 2: Spring Boot 过渡升级 (2.4 → 2.7)

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 2.1 | Spring Boot 2.4.11 → 2.7.18 | ✅ 完成 | 2026-01-04 | 编译通过，修复了 mysql-connector 版本和重复依赖 |
| 2.2 | 添加 properties-migrator | ✅ 完成 | 2026-01-04 | 临时依赖，升级后删除 |
| 2.3 | 验证编译和运行 | ✅ 完成 | 2026-01-04 | 需添加兼容性配置（见问题记录） |

---

### 阶段 3: Spring Boot 3.x 升级 (2.7 → 3.4)

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 3.1 | Spring Boot 2.7.18 → 3.4.1 | ✅ 完成 | 2026-01-04 | pom.xml parent version 更新 |
| 3.2 | javax.* → jakarta.* 替换 | ✅ 完成 | 2026-01-04 | 8个文件：7个Entity + TokenInterceptor |
| 3.3 | 验证编译通过 | ✅ 完成 | 2026-01-04 | mvn clean compile 成功 |

**javax → jakarta 修改的文件：**
- `entity/Account.java`
- `entity/Action.java`
- `entity/Type.java`
- `entity/FlowJpaEntity.java`
- `entity/FlowImage.java`
- `entity/FlowTemplate.java`
- `entity/TemplateTag.java`
- `config/TokenInterceptor.java`

---

### 阶段 4: MyBatis 升级

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 4.1 | mybatis-starter 1.3.0 → 3.0.5 | ✅ 完成 | 2026-01-04 | 必须升级，旧版本不兼容 Spring Boot 3 |
| 4.2 | pagehelper 处理 | ✅ 完成 | 2026-01-04 | 代码未使用，已删除依赖 |
| 4.3 | 验证数据库操作 | ✅ 完成 | 2026-01-04 | 编译通过 |

---

### 阶段 5: Swagger → SpringDoc

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 5.1 | 删除 springfox 依赖 | ✅ 完成 | 2026-01-04 | springfox-swagger2, springfox-swagger-ui |
| 5.2 | 添加 springdoc 依赖 | ✅ 完成 | 2026-01-04 | springdoc-openapi-starter-webmvc-ui 2.8.3 |
| 5.3 | 替换注解 | ✅ 完成 | 2026-01-04 | 11个Controller |
| 5.4 | 更新 SwaggerConfig | ✅ 完成 | 2026-01-04 | Docket → OpenAPI Bean |
| 5.5 | 验证 API 文档 | ✅ 完成 | 2026-01-04 | 访问 /docs 正常 |

**注解替换详情：**

| 旧注解 | 新注解 |
|--------|--------|
| `@Api(tags={...})` | `@Tag(name=...)` |
| `@ApiOperation(value=...)` | `@Operation(summary=...)` |
| `@ApiParam` | `@Parameter` |
| `import io.swagger.annotations.*` | `import io.swagger.v3.oas.annotations.*` |

**修改的 Controller：**
- AccountController, ActionController, AnalysisController
- AuthController, FlowController, FlowTemplateController
- HomeController, ImageController, ScreenController
- TagController, TypeController

**配置更新：**
- `application.properties`: 添加 `springdoc.swagger-ui.path=/docs`
- `WebConfig.java`: 更新排除路径（/docs, /v3/api-docs 等）

---

### 阶段 6: 其他依赖升级

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 6.1 | easyexcel 2.2.4 → 4.0.3 | ✅ 完成 | 2026-01-04 | Java 17 必须升级，修复 CellWriteHandler API，新增行颜色功能 |
| 6.2 | gson 2.8.2 → 2.11.0 | ✅ 完成 | 2026-01-04 | 在阶段2.3已完成 |
| 6.3 | okhttp 4.9.1 → 4.12.0 | ✅ 完成 | 2026-01-04 | 5.x 还是 alpha，用 4.12.0 |
| 6.4 | mysql-connector 更新 | ✅ 完成 | 2026-01-04 | mysql:8.0.33 → com.mysql:9.1.0 |
| 6.5 | org.json 升级 | ✅ 完成 | 2026-01-04 | 20210307 → 20250107 |
| 6.6 | JAXB 迁移到 Jakarta | ✅ 完成 | 2026-01-04 | javax → jakarta.xml.bind 4.0.2 |
| 6.7 | Activation 迁移到 Jakarta | ✅ 完成 | 2026-01-04 | javax → jakarta.activation 2.1.3 |
| 6.8 | jaxb-runtime 升级 | ✅ 完成 | 2026-01-04 | 2.3.3 → 4.0.5 |

**EasyExcel 升级详情：**

升级原因：EasyExcel 2.2.4 使用 cglib 动态代理，在 Java 17 模块系统下触发 `InaccessibleObjectException`。

| 变更项 | 旧版本 (2.2.4) | 新版本 (4.0.3) |
|--------|----------------|----------------|
| CellWriteHandler | 多个回调方法 | 单一 `afterCellDispose(CellWriteHandlerContext)` |
| CellData | `CellData` | `WriteCellData` |
| 样式设置 | 直接操作 POI CellStyle | 使用 `WriteCellStyle.getOrCreateStyle()` |
| 模板填充 | 自动处理 | 大数据需添加 `.inMemory(true)` |
| Excel格式 | .xls / .xlsx | 统一使用 .xlsx |

**新增功能 - Excel行颜色：**

根据 `handle` 字段为流水数据行设置颜色：
- `handle=0` (收入) → 绿色
- `handle=1` (支出) → 红色
- `handle=2` (转账) → 蓝色

修改文件：
- `ExcelService.java` - 更新 ExcelWriteHandler 实现
- `ScreenService.java` - 添加 handle 字段传递
- `MonthExcelData.java` - Flow 类新增 handle 字段

---

### 阶段 7: 配置和清理

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 7.1 | 删除 properties-migrator | ✅ 完成 | 2026-01-04 | 升级完成，已删除 |
| 7.2 | 环境配置重构 | ✅ 完成 | 2026-01-04 | windows→local, 删除dev, 创建example模板 |
| 7.3 | 清理旧配置 | ✅ 完成 | 2026-01-04 | 删除Springfox兼容配置，规范化注释 |
| 7.4 | 更新 Dockerfile (Java 17) | ⬜ 待开始 | - | - |
| 7.5 | 全面测试 | ⬜ 待开始 | - | - |

---

### 阶段 8: 完成

| 步骤 | 描述 | 状态 | 完成时间 | 备注 |
|------|------|------|----------|------|
| 8.1 | 更新版本号 | ⬜ 待开始 | - | - |
| 8.2 | 编写升级总结 | ⬜ 待开始 | - | - |
| 8.3 | 合并到版本分支 | ⬜ 待开始 | - | - |

---

## 问题记录

| # | 问题描述 | 发现阶段 | 解决方案 | 状态 |
|---|----------|----------|----------|------|
| 1 | mysql-connector-java 缺少版本号 | 2.1 | 添加 version=8.0.33 | ✅ |
| 2 | spring-boot-starter-jdbc 重复声明 | 2.1 | 删除重复依赖 | ✅ |
| 3 | logback 与 log4j2 冲突 | 2.3 | 给多个依赖添加 exclusion | ✅ |
| 4 | 循环依赖报错 | 2.3 | 添加 spring.main.allow-circular-references=true | ✅ |
| 5 | Springfox 与 Spring Boot 2.6+ 不兼容 | 2.3 | 添加 spring.mvc.pathmatch.matching-strategy=ant_path_matcher | ✅ |
| 6 | org.json JSONObject 构造函数不兼容 | 2.3 | LogUtils.java 改用 Gson 格式化 JSON | ✅ |
| 7 | Gson 版本过旧 | 2.3 | 升级 2.8.2 → 2.11.0 | ✅ |
| 8 | MyBatis 1.3.0 不兼容 Spring Boot 3 | 3.3 | 升级到 3.0.5 | ✅ |
| 9 | Springfox 不兼容 Spring 6 | 3.3 | 替换为 SpringDoc 2.8.3 | ✅ |
| 10 | @ApiOperation notes 参数不存在 | 5.3 | 删除 notes 参数或改为 description | ✅ |
| 11 | SpringDoc /docs 路径 404 | 5.5 | 更新 WebConfig 排除路径，升级 SpringDoc 版本 | ✅ |

---

## 版本变更汇总

| 依赖 | 旧版本 | 新版本 |
|------|--------|--------|
| spring-boot-parent | 2.4.11 | 3.4.1 |
| java.version | 11 | 17 |
| mybatis-spring-boot-starter | 1.3.0 | 3.0.5 |
| pagehelper-spring-boot-starter | 1.2.5 | (删除，未使用) |
| springfox-swagger2 | 2.9.2 | (删除) |
| springfox-swagger-ui | 2.9.2 | (删除) |
| springdoc-openapi-starter-webmvc-ui | (新增) | 2.8.3 |
| gson | 2.8.2 | 2.11.0 |
| mysql-connector | mysql:8.0.33 | com.mysql:9.1.0 |
| okhttp | 4.9.1 | 4.12.0 |
| org.json | 20210307 | 20250107 |
| jaxb-api | javax:2.3.1 | jakarta:4.0.2 |
| activation | javax:1.1.1 | jakarta:2.1.3 |
| jaxb-runtime | 2.3.3 | 4.0.5 |
| easyexcel | 2.2.4 | 4.0.3 |

**配置文件变更：**

| 文件 | 变更 |
|------|------|
| application-windows.properties | → 重命名为 application-local.properties |
| application-dev.properties | 删除 |
| application-local.properties.example | 新增（开发模板） |
| .gitignore | 添加 application-local.properties |

**Maven Profile 变更：**

| Profile | 变更 |
|---------|------|
| windows | → 重命名为 local |
| dev | 删除 |
| server | 保留 |

---

## 统计

| 指标 | 数值 |
|------|------|
| 总步骤数 | 33 |
| 已完成 | 28 |
| 已跳过 | 0 |
| 进行中 | 0 |
| 待开始 | 5 |
| 完成率 | 85% |

---

## 状态说明

| 符号 | 含义 |
|------|------|
| ✅ | 已完成 |
| 🔄 | 进行中 |
| ⬜ | 待开始 |
| ❌ | 失败/阻塞 |
| ⏸️ | 暂停 |

---

*文档创建时间：2026-01-04*
*最后更新：2026-01-04*
