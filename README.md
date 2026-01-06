# EasyAccounts 开源版

## 项目简介

这是 [EasyAccounts](https://github.com/QingHeYang/EasyAccounts) 的源码。

- 有开发能力：可根据源码二次开发或自行编译打包
- 仅使用：直接下载 [EasyAccounts](https://github.com/QingHeYang/EasyAccounts)

## 版本

v2.6.0
更新时间：2026.01.06
项目说明：https://qingheyang.github.io/EasyAccounts/#/README

## 主要目录结构

```bash
.
├── README.md
├── CLAUDE.md                   # Claude Code 项目指南
├── build.sh                    # 统一构建脚本
├── versions.json               # 版本信息
│
├── Server/                     # 后端服务
│   ├── Dockerfile
│   ├── README.md
│   ├── MySQL/                  # MySQL Docker 配置
│   └── YD_JZ/                  # Spring Boot 源码
│       ├── excel_template/     # Excel 模板 (.xlsx)
│       └── src/
│
├── Web/                        # 前端服务
│   ├── Dockerfile
│   ├── README.md
│   ├── nginx/                  # Nginx 配置
│   └── ydjz_web_v2/            # Vue 3 + TypeScript 源码
│
├── ai/                         # AI 服务
│   ├── README.md
│   └── KoalaqHub/              # AI Agent 服务
│       ├── Dockerfile
│       └── koalaq_hub/         # Python 源码
│
├── WebHook/                    # WebHook 服务
│   ├── Dockerfile
│   ├── README.md
│   └── webhook.py              # FastAPI 源码
│
└── version/                    # 版本文档
    └── README.md               # 分支合并记录
```

## 技术栈

| 模块 | 技术栈 | 运行环境 |
|------|--------|----------|
| **Server** | Spring Boot 3.x, JPA + MyBatis, MySQL | JDK 17 |
| **Web** | Vue 3 + TypeScript, Vant UI | Node.js 16+ |
| **AI** | Python, FastAPI, MCP 架构 | Python 3.10+ |
| **WebHook** | Python, FastAPI | Python 3.10+ |

## 快速开始

### 统一构建（推荐）

```bash
./build.sh
```

交互式菜单，支持单模块或全部构建。

### Server（后端）

```bash
cd Server/YD_JZ

# 本地开发
cp src/main/resources/application-local.properties.example \
   src/main/resources/application-local.properties
# 修改数据库配置后启动

# 构建
mvn clean package -P server

# Docker
docker build -t easyaccounts-server ../
```

**配置文件：**
- `application-server.properties` - 生产环境（Docker）
- `application-local.properties` - 本地开发

**端口：** 本地 8085 / Docker 10670

**API 文档：** http://{IP}:8085/swagger-ui/index.html

### Web（前端）

```bash
cd Web/ydjz_web_v2

npm install
npm run serve        # 开发 http://localhost:8081
npm run build        # 生产构建
```

**端口：** 本地 8081 / Docker 10669

### AI（KoalaqHub）

```bash
cd ai/KoalaqHub

pip install -r requirements.txt
cp .env.example .env  # 配置 LLM API Key
python -m koalaq_hub  # http://localhost:8001
```

**端口：** 本地 8001 / Docker 10672

### WebHook

```bash
cd WebHook

pip install -r requirements.txt
# 配置 SMTP 环境变量
uvicorn webhook:app --host 0.0.0.0 --port 8083
```

**端口：** 本地 8083 / Docker 10671

## Docker 端口映射

| 模块 | 本地端口 | Docker 端口 |
|------|----------|-------------|
| Server | 8085 | 10670 |
| Web | 8081 | 10669 |
| AI | 8001 | 10672 |
| WebHook | 8083 | 10671 |
| MySQL | 3306 | 10668 |

## 2.6.0 主要更新

- **Server**: Spring Boot 3.x 升级，Java 17，API 错误处理优化
- **Web**: Vue 3 + TypeScript 重构，移动端 + 桌面端双版本
- **AI**: VL 多模态支持（图片识别记账），MCP 架构
- **Excel**: 模板升级为 .xlsx 格式

## 开发建议

### 轻度开发
基于 WebHook 扩展，调用现有 API，Python 编码。

### 中度开发
修改前端/后端源码，不变更数据库结构。

### 重度开发
变更数据库结构，需要 Liquibase 迁移脚本。

## 贡献指南

[CONTRIBUTING.md](CONTRIBUTING.md)

> 仅接受轻度、中度开发 PR

## 安全声明

- 开源项目，禁止商业用途
- 不上传任何用户数据
- 欢迎代码审查

## 开发者的话

业余时间开发，代码可能不够规范，还望谅解。
