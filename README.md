# EasyAccounts 开源版

## 项目简介

这是 [EasyAccounts](https://github.com/QingHeYang/EasyAccounts) 的源码仓库。

- **有开发能力**：可根据源码二次开发或自行编译打包
- **仅使用**：直接使用 [EasyAccounts](https://github.com/QingHeYang/EasyAccounts) 部署仓库即可

## 版本

**v2.7.0**

完整版本信息：[changelog](https://github.com/QingHeYang/EasyAccounts/blob/main/docs/changelog.md) | [GitBook](https://mercys-organization-2.gitbook.io/easyaccounts/)

## 主要目录结构

```
.
├── README.md
├── CONTRIBUTING.md             # 贡献指南
├── CLAUDE.md                   # 项目主管 Claude 角色定义
├── build.sh                    # 统一构建脚本（交互式）
├── .gitignore
│
├── Server/                     # 后端服务
│   ├── README.md
│   ├── CLAUDE.md               # 后端开发 Claude 简报
│   ├── Dockerfile              # eclipse-temurin:17-jre-jammy
│   ├── MySQL/                  # MySQL Docker 配置（含初始化 SQL）
│   └── YD_JZ/                  # Spring Boot 3.x 源码
│       ├── excel_template/     # Excel 导出模板（.xlsx，勿改）
│       └── src/
│
├── Web/                        # 前端服务
│   ├── README.md
│   ├── CLAUDE.md               # 前端开发 Claude 简报
│   ├── Dockerfile              # nginx:1.27-alpine
│   ├── nginx/                  # Nginx 反向代理配置
│   └── ydjz_web_v2/            # Vue 3 + TypeScript 源码（PC + 移动双端）
│
└── ai/                         # AI 服务（KoalaqHub）
    ├── README.md
    ├── CLAUDE.md               # AI 开发 Claude 简报
    ├── Dockerfile              # python:3.10.16-slim-bookworm
    └── KoalaqHub/              # Python + FastAPI + MCP 源码
```

## 技术栈

| 模块 | 技术栈 | 运行环境 |
|------|--------|----------|
| **Server** | Spring Boot 3.x · JPA + MyBatis · Liquibase · MySQL 8 · 邮件内嵌 | JDK 17 |
| **Web** | Vue 3 + TypeScript · Vite 7 · Element Plus（PC）· Vant（移动）| Node.js 18+ / pnpm |
| **AI** | Python 3.10 · FastAPI · MCP 协议 · 多 LLM 平台兼容 | Python 3.10+ |
| **MySQL** | 官方 MySQL 8.0.31 镜像 + 内置 init SQL + 内存优化 cnf | - |

> ⚠️ **v2.7.0 起 WebHook 模块已移除**：邮件发送能力已内聚到 Server。原 `WebHook/` 目录、`easyaccounts-webhook` 镜像、SMTP 环境变量均不再使用，邮件配置改在前端「**系统设置 → 邮件**」中维护。

## 快速开始

### 统一构建（推荐）

```bash
./build.sh
```

交互式菜单，支持单模块或全部构建。

### 分端开发

各端的开发命令、配置示例、调试指南详见各端 README：

- [Server/README.md](Server/README.md) — 后端开发
- [Web/README.md](Web/README.md) — 前端开发
- [ai/README.md](ai/README.md) — AI 开发

## Docker 端口映射

| 模块 | 容器内 | Docker 端口（标准 compose）|
|------|--------|----------------------------|
| nginx | 80 | **10669**（唯一对外端口，反代一切）|
| server | 8081 | 10670（v2.6.0+ 默认不对外，通过 nginx 反代）|
| mysql | 3306 | 10668（默认不对外）|
| ai | 8001 | 10673（可选）|

## v2.7.0 主要更新

- **新增定时记账**：周期性账单（订阅、房贷、水电、工资）自动生成流水
- **新增自动月度 Excel + 站内通知中心 + 统计页日支出趋势**
- **设置全面 UI 化**：邮件 SMTP / 备份时间 / 登录方式全部前端配置，无需重启
- **AI 错误友好提示**：失败原因前端显示
- **WebHook 模块废弃**：邮件能力内聚到 server
- **镜像瘦身**：整套部署包从 ~2GB 砍到 ~1.24GB，基础镜像锁版本

完整说明：[v2.7.0 release notes](https://github.com/QingHeYang/EasyAccounts/blob/main/docs/changelog.md#270-2026-05)

## 贡献指南

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

> ⚠️ **本项目仅接受 Bug 修复类 PR，暂不接受新功能 PR**
>
> 新功能涉及产品定位、数据模型一致性等多方面取舍，需要从全局规划，避免破坏性升级影响已有用户。有功能想法请先在 [Issue](https://github.com/QingHeYang/EasyAccounts/issues) 区讨论。

## 安全声明

- 开源项目，禁止商业用途
- 不上传任何用户数据
- 欢迎代码审查

## 开发者的话

业余时间开发，代码可能不够规范，还望谅解。

源码仓库相对发布版本会**延迟一段时间**——新版本通常包含较多结构调整，需要先在内部跑稳再开源，避免半成品代码误导贡献者或让基于源码二次开发的用户踩坑。
