# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

# 开发服务器
npm run serve

# 生产构建
npm run build

# 运行测试
npm run test:unit

# 代码检查
npm run lint

# 构建 Docker 镜像
cd ../
./make_nginx.sh
```

### 桌面应用
```bash
# 进入桌面应用目录
cd Web/ydjz_web_desktop

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

## 重要说明

- 后端开发需要 Java 11 和 Maven
- 前端开发需要 Node.js v16
- `Server/excel_template/` 中的 Excel 模板不应修改
- WebHook 服务提供可扩展的通知系统
- 所有 Docker 构建脚本都在各组件根目录中