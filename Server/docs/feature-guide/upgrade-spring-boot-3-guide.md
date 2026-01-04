# Spring Boot 3.x 升级指南

本文档记录 EasyAccounts Server 模块从 Spring Boot 2.4.11 + Java 11 升级到 Spring Boot 3.x + Java 17+ 的技术调研和升级路线。

---

## 目录

1. [升级背景](#升级背景)
2. [核心变化概述](#核心变化概述)
3. [依赖版本对照表](#依赖版本对照表)
4. [升级路线规划](#升级路线规划)
5. [各阶段详细说明](#各阶段详细说明)
6. [风险评估](#风险评估)
7. [回滚方案](#回滚方案)
8. [参考资料](#参考资料)

---

## 升级背景

### 当前版本

| 组件 | 当前版本 | 发布年份 |
|------|----------|----------|
| Java | 11 | 2018 |
| Spring Boot | 2.4.11 | 2021 |
| MyBatis Starter | 1.3.0 | 2017 |
| PageHelper | 4.2.1 | 2016 |
| Swagger (Springfox) | 2.9.2 | 2018 |
| EasyExcel | 2.2.4 | 2020 |

### 升级目标

| 组件 | 目标版本 |
|------|----------|
| Java | 17 (LTS) |
| Spring Boot | 3.4.x |
| MyBatis Starter | 3.0.5 |
| PageHelper | 6.x (via starter 2.1.0) |
| SpringDoc OpenAPI | 2.8.3 |
| EasyExcel | 4.0.x |

### 升级原因

1. **安全性**：旧版本可能存在安全漏洞
2. **兼容性**：新特性和新库需要更高版本
3. **维护性**：旧版本可能不再维护
4. **性能**：新版本通常有性能优化

---

## 核心变化概述

### 1. Java 11 → Java 17

Spring Boot 3.x 强制要求 Java 17+。

**影响：**
- Dockerfile 需要更新基础镜像
- 开发环境需要升级 JDK
- 某些废弃 API 可能需要替换

### 2. javax.* → jakarta.*

Spring Boot 3.x 基于 Jakarta EE 9+，所有 `javax.*` 包需要改为 `jakarta.*`。

**需要修改的包：**
```java
// 修改前
import javax.persistence.*;
import javax.servlet.*;
import javax.validation.*;

// 修改后
import jakarta.persistence.*;
import jakarta.servlet.*;
import jakarta.validation.*;
```

### 3. Swagger (Springfox) → SpringDoc OpenAPI

Springfox 自 2020 年后不再更新，不兼容 Spring Boot 3。

**注解变化：**

| Springfox (旧) | SpringDoc (新) |
|----------------|----------------|
| `@Api` | `@Tag` |
| `@ApiOperation` | `@Operation` |
| `@ApiParam` | `@Parameter` |
| `@ApiResponse` | `@ApiResponse` (包名变化) |
| `@ApiIgnore` | `@Hidden` |

**配置变化：**
- 删除 `SwaggerConfig.java` 中的 Docket 配置
- SpringDoc 自动扫描，无需手动配置

### 4. Spring Security 变化

Spring Boot 3.0 使用 Spring Security 6.0：
- 移除 `WebSecurityConfigurerAdapter`
- 使用 `SecurityFilterChain` Bean 配置

### 5. Hibernate 6.x 变化

- `@Type` 注解变化
- ID 生成策略变化
- 某些方法签名变化

---

## 依赖版本对照表

| 依赖 | 当前版本 | 升级版本 | 兼容性说明 |
|------|----------|----------|------------|
| **spring-boot-starter-parent** | 2.4.11 | 3.4.1 | 核心升级 |
| **java.version** | 11 | 17 | 必须升级 |
| **mybatis-spring-boot-starter** | 1.3.0 | 3.0.5 | 支持 Spring Boot 3.2-3.5 |
| **pagehelper-spring-boot-starter** | - | 2.1.0 | 替代单独的 pagehelper |
| **pagehelper** | 4.2.1 | (由 starter 管理) | - |
| **springfox-swagger2** | 2.9.2 | 删除 | 废弃 |
| **springfox-swagger-ui** | 2.9.2 | 删除 | 废弃 |
| **springdoc-openapi-starter-webmvc-ui** | - | 2.8.3 | 替代 Swagger |
| **easyexcel** | 2.2.4 | 4.0.3 | 支持 Spring Boot 3 |
| **gson** | 2.8.2 | 2.11.0 | 建议升级 |
| **okhttp** | 4.9.1 | 4.12.0 | 建议升级 |
| **liquibase-core** | 4.29.0 | 4.31.1 | 由 Spring Boot 管理 |
| **mysql-connector-java** | (由 Boot 管理) | mysql-connector-j | 包名变化 |

---

## 升级路线规划

### 行动纲领

1. **小步快跑**：每次只升级一个组件或一类变更
2. **验证通过再继续**：每步完成后编译、测试、验证
3. **文档同步**：每步进度同步更新到进度文档
4. **可回滚**：每步都有独立的 commit

### 阶段划分

```
阶段 1: 准备工作
    ├── 1.1 备份当前代码（分支已创建）
    ├── 1.2 升级 Java 11 → 17
    └── 1.3 验证编译通过

阶段 2: Spring Boot 过渡升级
    ├── 2.1 升级 Spring Boot 2.4.11 → 2.7.18（最后的 2.x）
    ├── 2.2 添加 spring-boot-properties-migrator
    └── 2.3 验证编译和运行

阶段 3: Spring Boot 3.x 升级
    ├── 3.1 升级 Spring Boot 2.7.18 → 3.4.1
    ├── 3.2 javax.* → jakarta.* 替换
    └── 3.3 验证编译通过

阶段 4: 依赖升级 - MyBatis
    ├── 4.1 mybatis-spring-boot-starter 1.3.0 → 3.0.5
    ├── 4.2 删除旧 pagehelper，添加 pagehelper-spring-boot-starter 2.1.1
    └── 4.3 验证数据库操作

阶段 5: 依赖升级 - Swagger → SpringDoc
    ├── 5.1 删除 springfox 依赖
    ├── 5.2 添加 springdoc-openapi-starter-webmvc-ui
    ├── 5.3 替换注解（@Api → @Tag 等）
    ├── 5.4 删除 SwaggerConfig.java
    └── 5.5 验证 API 文档

阶段 6: 依赖升级 - 其他
    ├── 6.1 easyexcel 2.2.4 → 4.0.3
    ├── 6.2 gson 2.8.2 → 2.11.0
    ├── 6.3 okhttp 4.9.1 → 4.12.0
    └── 6.4 mysql-connector-java → mysql-connector-j

阶段 7: 配置和清理
    ├── 7.1 删除 spring-boot-properties-migrator
    ├── 7.2 更新 Dockerfile (Java 17)
    └── 7.3 全面测试

阶段 8: 完成
    ├── 8.1 更新版本号
    ├── 8.2 编写升级总结
    └── 8.3 合并到版本分支
```

---

## 各阶段详细说明

### 阶段 1: 准备工作

#### 1.1 备份当前代码
```bash
# 已在特性分支
git branch  # 确认当前分支
```

#### 1.2 升级 Java 版本

**pom.xml 修改：**
```xml
<properties>
    <java.version>17</java.version>
</properties>
```

**Dockerfile 修改：**
```dockerfile
# 安装 OpenJDK 17
RUN apt-get install -y openjdk-17-jdk

# 更新 JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

#### 1.3 验证
```bash
mvn clean compile
```

---

### 阶段 2: Spring Boot 过渡升级

官方建议先升级到 2.7.x 再升级到 3.x，避免跨版本问题。

#### 2.1 升级到 Spring Boot 2.7.18

**pom.xml 修改：**
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>2.7.18</version>
</parent>
```

#### 2.2 添加属性迁移器

帮助识别已废弃的配置属性：
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-properties-migrator</artifactId>
    <scope>runtime</scope>
</dependency>
```

---

### 阶段 3: Spring Boot 3.x 升级

#### 3.1 升级到 Spring Boot 3.4.1

**pom.xml 修改：**
```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.4.1</version>
</parent>
```

#### 3.2 javax → jakarta 替换

**需要修改的文件：**
- 所有 Entity 类（`@Entity`, `@Table`, `@Column` 等）
- 所有 Controller 类（如果使用 `HttpServletRequest`）
- 所有 Filter/Interceptor 类

**IDE 批量替换：**
```
查找: import javax.persistence
替换: import jakarta.persistence

查找: import javax.servlet
替换: import jakarta.servlet

查找: import javax.validation
替换: import jakarta.validation
```

---

### 阶段 4: MyBatis 升级

#### 4.1 升级 MyBatis Starter

**pom.xml 修改：**
```xml
<!-- 删除旧版本 -->
<!-- <version>1.3.0</version> -->

<!-- 新版本 -->
<dependency>
    <groupId>org.mybatis.spring.boot</groupId>
    <artifactId>mybatis-spring-boot-starter</artifactId>
    <version>3.0.5</version>
</dependency>
```

#### 4.2 升级 PageHelper

**pom.xml 修改：**
```xml
<!-- 删除旧的单独依赖 -->
<!--
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper</artifactId>
    <version>4.2.1</version>
</dependency>
-->

<!-- 使用 Spring Boot Starter -->
<dependency>
    <groupId>com.github.pagehelper</groupId>
    <artifactId>pagehelper-spring-boot-starter</artifactId>
    <version>2.1.0</version>
</dependency>
```

---

### 阶段 5: Swagger → SpringDoc

#### 5.1 删除 Springfox 依赖

**pom.xml 删除：**
```xml
<!-- 删除这些 -->
<dependency>
    <groupId>io.springfox</groupId>
    <artifactId>springfox-swagger2</artifactId>
    <version>2.9.2</version>
</dependency>
<dependency>
    <groupId>io.springfox</groupId>
    <artifactId>springfox-swagger-ui</artifactId>
    <version>2.9.2</version>
</dependency>
```

#### 5.2 添加 SpringDoc

**pom.xml 添加：**
```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.8.3</version>
</dependency>
```

#### 5.3 注解替换

**批量替换：**
```
查找: import io.swagger.annotations.Api;
替换: import io.swagger.v3.oas.annotations.tags.Tag;

查找: import io.swagger.annotations.ApiOperation;
替换: import io.swagger.v3.oas.annotations.Operation;

查找: @Api(value = "XXX", tags = {"YYY"})
替换: @Tag(name = "YYY", description = "XXX")

查找: @ApiOperation(value = "XXX", notes = "YYY")
替换: @Operation(summary = "XXX", description = "YYY")
```

#### 5.4 删除配置类

删除 `SwaggerConfig.java`，SpringDoc 自动配置。

#### 5.5 访问地址变化

| 旧地址 | 新地址 |
|--------|--------|
| `/swagger-ui.html` | `/swagger-ui/index.html` |
| `/v2/api-docs` | `/v3/api-docs` |

---

### 阶段 6: 其他依赖升级

#### 6.1 EasyExcel

```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>easyexcel</artifactId>
    <version>4.0.3</version>
</dependency>
```

**注意：** EasyExcel 4.x API 可能有变化，需要检查使用方式。

#### 6.2 Gson

```xml
<dependency>
    <groupId>com.google.code.gson</groupId>
    <artifactId>gson</artifactId>
    <version>2.11.0</version>
</dependency>
```

#### 6.3 OkHttp

```xml
<dependency>
    <groupId>com.squareup.okhttp3</groupId>
    <artifactId>okhttp</artifactId>
    <version>4.12.0</version>
</dependency>
```

#### 6.4 MySQL Connector

Spring Boot 3 使用新的 artifact：
```xml
<dependency>
    <groupId>com.mysql</groupId>
    <artifactId>mysql-connector-j</artifactId>
</dependency>
```

---

### 阶段 7: 配置和清理

#### 7.1 删除属性迁移器

确认没有警告后删除：
```xml
<!-- 删除 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-properties-migrator</artifactId>
</dependency>
```

#### 7.2 更新 Dockerfile

```dockerfile
FROM ubuntu:latest

# 安装 OpenJDK 17
RUN apt-get update \
    && apt-get install -y openjdk-17-jdk mysql-client

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
```

或使用更轻量的镜像：
```dockerfile
FROM eclipse-temurin:17-jre

RUN apt-get update && apt-get install -y mysql-client
```

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| javax → jakarta 遗漏 | 编译失败 | IDE 全局搜索 javax |
| MyBatis 分页失效 | 数据查询异常 | 单独测试分页功能 |
| Swagger 注解遗漏 | API 文档缺失 | 对比旧文档检查 |
| EasyExcel API 变化 | Excel 导出失败 | 单独测试导出功能 |
| 配置属性废弃 | 启动失败 | 使用 properties-migrator |

---

## 回滚方案

每个阶段完成后创建 commit，回滚时：

```bash
# 查看提交历史
git log --oneline

# 回滚到指定 commit
git reset --hard <commit-hash>

# 或者回滚整个分支
git checkout 2.6.0
```

---

## 参考资料

- [Spring Boot 3.0 Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide)
- [Migrate Spring Boot 2 To Spring Boot 3](https://javatechonline.com/spring-boot-3-migration-guide/)
- [SpringDoc - Migrating from SpringFox](https://springdoc.org/migrating-from-springfox.html)
- [MyBatis Spring Boot Starter](https://github.com/mybatis/spring-boot-starter)
- [PageHelper Spring Boot Starter](https://github.com/pagehelper/pagehelper-spring-boot)
- [EasyExcel GitHub](https://github.com/alibaba/easyexcel)

---

*文档创建时间：2026-01-04*
*最后更新：2026-01-04*
