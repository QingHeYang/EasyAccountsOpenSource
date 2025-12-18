# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.  
全部使用中文进行交互  

## 项目概述

EasyAccounts 是一个个人财务管理应用，采用三层架构：
- **Server**: Spring Boot 2.4.11 后端，Java 11，MySQL 数据库，双重数据访问（JPA + MyBatis）
- **Web**: Vue 3 前端，移动优先设计，使用 Vant UI 组件，还包含桌面 Electron 应用
- **WebHook**: FastAPI Python 服务，用于通过邮件发送文件通知

这是 EasyAccounts 的开源版本。当前版本：v2.4.0

## 开发命令

### 服务端 (Spring Boot)
```bash
# 进入服务端目录
cd Server/YD_JZ

# 使用 Maven 构建（需要 Java 11）
mvn clean package

# 运行带特定配置文件
mvn clean package -P dev
mvn clean package -P server  
mvn clean package -P windows

# 运行测试
mvn test

# 构建 Docker 镜像
cd ../
./make_jar.sh
```

### Web 前端
```bash
# 进入 Web 应用目录
cd Web/ydjz_web

# 安装依赖（需要 Node.js v16）
npm install

# 开发服务器 (http://localhost:8081)
npm run serve

# 生产构建
npm run build

# 运行单个测试文件
npm run test:unit -- tests/unit/example.spec.js

# 运行所有测试
npm run test:unit

# 代码检查和自动修复
npm run lint

# 构建 Docker 镜像
cd ../
./make_nginx.sh
```

### 桌面应用
```bash
# 进入桌面应用目录
cd Web/ydjz_web_desktop

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建 Electron 应用
npm run electron:build
```

### WebHook 服务
```bash
# 进入 webhook 目录
cd WebHook

# 构建 Docker 镜像
./make_webhook.sh
```

## 架构和关键组件

### 后端结构
- **YdJzApplication.java**: Spring Boot 应用主入口
- **Controllers**: REST API 端点，包括账户、流水、分析、认证等
- **Services**: 业务逻辑层
- **DAO**: 双重数据访问，JPA 仓库 + MyBatis 映射器
- **Entities/DTOs**: 数据模型和传输对象
- **Config**: Swagger、安全配置和应用配置

### 前端结构
- **Vue 3 + Vue Router**: 单页应用，基于路由的代码分割
- **Layouts**: HomeLayout 和 SettingLayout 用于不同页面布局
- **Views**: 主要应用界面（看板、流水、分析、设置）
- **Store**: Vuex 状态管理
- **移动优先**: 使用 Vant UI 组件提供移动端体验

### 核心功能
- 财务交易记录跟踪（流水）
- 账户和分类管理
- 分析报告和 Excel 导出
- 重复交易模板系统
- 身份验证和授权
- 多环境配置（dev/server/windows）

## 数据库和配置文件

使用 MySQL 数据库，Liquibase 进行架构管理。三个 Maven 配置文件：
- `dev`: 开发环境
- `server`: 生产服务器
- `windows`: Windows 开发环境

配置文件位于 `src/main/resources/application-{profile}.properties`

## API 文档

服务运行时，可通过 Swagger UI 查看 API 文档和进行测试。

## 开发工作流程

### 前端开发
- 开发服务器运行在 `http://localhost:8081`
- API 代理配置：所有 `/api/*` 请求会代理到 `http://yd_service:8081/`
- 使用 Jest 进行单元测试，配置文件：`jest.config.js`
- 代码规范使用 ESLint + Prettier，配置在 `.eslintrc.js` 和 `prettier.config.js`

### 后端开发  
- 使用 Maven profiles 管理不同环境配置 (`dev`, `server`, `windows`)
- 数据库迁移通过 Liquibase 管理，配置文件在 `src/main/resources/db/changelog/`
- Swagger UI 可用于 API 测试，运行后访问 `/swagger-ui.html`
- 双重数据访问模式：JPA 用于简单 CRUD，MyBatis 用于复杂查询

### 测试策略
- 前端：Jest 单元测试位于 `tests/unit/`
- 后端：Spring Boot Test 框架，测试类应放在 `src/test/java/`
- 运行前端测试前确保依赖已安装：`npm install`

## 重要说明

- 后端开发需要 Java 11 和 Maven
- 前端开发需要 Node.js v16
- `Server/excel_template/` 中的 Excel 模板不应修改（包含导出模板）
- WebHook 服务提供可扩展的通知系统
- 所有 Docker 构建脚本都在各组件根目录中
- 修改代码后需要重新构建 Docker 镜像才能生效