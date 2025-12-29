# KoalaQ Hub

KoalaQ Hub 是一个基于 FastAPI 和 WebSocket 的智能对话系统，支持多 Agent 协作、Function Calling 和 MCP（Model Context Protocol）工具集成。

## 主要特性

- 🤖 **多 Agent 协作**：支持不同专业领域的 Agent 相互调用和协作
- 🛠️ **Function Calling**：基于 OpenAI Function Calling 标准的工具调用机制
- 🔌 **MCP 工具集成**：支持通过 MCP 协议集成各种外部工具
- 💬 **实时通信**：基于 WebSocket 的实时消息推送
- 📊 **对话管理**：完整的对话历史记录和上下文管理
- 🎯 **灵活配置**：支持多种 LLM 模型和自定义 Agent 配置

## 快速开始

### 环境要求

- Python 3.8+
- Conda（推荐）或其他 Python 环境管理工具

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/koalaq_hub_python.git
cd koalaq_hub_python
```

2. **创建并激活 Conda 环境**
```bash
conda create -n mcp python=3.10
conda activate mcp
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境**
```bash
# 复制环境变量模板
cp config/.env.template config/.env

# 编辑配置文件，设置 API 密钥等
vim config/.env
```

5. **配置 MCP 服务器（可选）**
```bash
# 复制 MCP 配置模板
cp resource/mcp/servers_config.json.template config/servers_config.json

# 编辑 MCP 服务器配置
vim config/servers_config.json
```

### 运行服务

```bash
conda activate mcp
python -m koalaq_hub
```

服务将在 `http://localhost:8001` 启动。

### API 文档

启动服务后，访问 `http://localhost:8001/docs` 查看自动生成的 API 文档。

## 项目结构

```
koalaq_hub_python/
├── koalaq_hub/          # 主应用代码
│   ├── api/             # API 端点定义
│   ├── core/            # 核心业务逻辑
│   ├── database/        # 数据库访问层
│   ├── models/          # 数据模型
│   └── config/          # 配置管理
├── resource/            # 资源文件
│   ├── agents/          # Agent 配置文件
│   ├── prompts/         # 提示词模板
│   └── role/            # 角色定义
├── docs/                # 项目文档
├── test/                # 测试代码
└── config/              # 配置文件
```

## Agent 配置

Agent 配置文件位于 `resource/agents/` 目录，使用 YAML 格式定义。

示例配置：
```yaml
# easy-accounts-agent.yaml
name: 小易客服
description: 易账房智能客服助手，专门处理易账房相关的客户咨询
model: qwen-plus
temperature: 0.3
tool_round: 3
mcp_servers:
  - easy_accounts
role_file: 小易.role
task_instructions_file: easy_accounts_instructions.prompt
```

## 开发指南

### 代码规范

项目使用 `ruff` 进行代码检查和格式化：

```bash
conda activate mcp
ruff check --fix
ruff format
```

### 运行测试

```bash
conda activate mcp
pytest
```

### 提交代码

请遵循以下提交信息格式：
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建过程或辅助工具的变动

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'feat: 添加某某功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue
- 发送邮件至：your-email@example.com