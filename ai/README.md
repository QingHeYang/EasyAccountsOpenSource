# KoalaQ Hub - EasyAccounts AI 助手

智能对话系统，内置 EasyAccounts 财务管理工具，无需 MCP 协议，直接内部调用。

## 🚀 核心特性

### 内置 EasyAccounts 工具集
- **8个工具**：查询账户、分类、流水，添加/更新记录，生成Excel报表
- **智能识别**：自动理解用户意图，选择合适的工具
- **Token认证**：支持有/无认证两种模式
- **参数统一**：`make_excel` 与 `flows` 参数完全一致

### 系统特性
- 多用户、多会话支持
- WebSocket 实时通信  
- 消息历史管理
- Agent 系统架构

## 📦 快速部署

### 前提条件
确保 EasyAccounts 主服务已经运行：
```bash
cd /path/to/EasyAccounts
docker-compose -f docker-compose-release.yml up -d
```

### 方式一：使用部署脚本（推荐）

```bash
# 运行部署脚本
./deploy.sh
```

### 方式二：使用 Docker Compose

```bash
# 启动 AI 服务
docker-compose up -d

# 查看状态
docker-compose ps
docker-compose logs -f
```

### 使用 Docker

```bash
# 构建镜像
docker build -t koalaq-hub:latest .

# 运行容器
docker run -d \
  --name koalaq-hub \
  -p 8001:8001 \
  -e EASYACCOUNTS_URL=http://your-easyaccounts:10670 \
  -v $(pwd)/data:/app/data \
  koalaq-hub:latest
```

### 本地开发

```bash
# 安装依赖
cd koalaq_hub_python
pip install -r ../requirements.txt

# 配置环境
vim config/.env
# 设置 EASYACCOUNTS_URL=http://localhost:10670

# 启动服务
python -m koalaq_hub
```

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EASYACCOUNTS_URL` | EasyAccounts服务地址 | http://easy_accounts_server:8081 |
| `API_PORT` | API端口 | 8001 |
| `API_HOST` | API地址 | 0.0.0.0 |
| `DATABASE_DIR` | 数据库目录 | ./resource/database |

### Docker网络配置

AI 服务会自动加入 `easy_accounts_net` 网络，通过内部网络访问 EasyAccounts：

- **默认配置**: `http://easy_accounts_server:8081`
- **容器名**: `easy_accounts_ai`
- **网络名**: `easy_accounts_net`

## 🔌 API使用

### WebSocket连接

```javascript
// 有认证
ws://localhost:8001/ws?user_id=user1&agent_id=easy-accounts-agent&tool_tokens=Authorization=your_token

// 无认证
ws://localhost:8001/ws?user_id=user1&agent_id=easy-accounts-agent
```

### HTTP API

访问 `http://localhost:8001/docs` 查看完整API文档

## 💬 对话示例

| 用户说 | AI调用工具 | 说明 |
|--------|------------|------|
| "我有多少钱" | `accounts` | 查询账户余额 |
| "这个月花了多少" | `flows` | 查询月度流水 |
| "生成9月报表" | `make_excel` | 导出Excel |
| "记一笔100元买菜" | `add_flow` | 添加流水 |
| "今年的收支情况" | `year_statistics` | 年度统计 |

## 🛠 EasyAccounts 工具列表

### 查询工具
- `accounts` - 查询资金账户
- `types` - 获取账单分类  
- `current_date` - 获取当前日期
- `year_statistics` - 年度统计
- `flows` - 查询流水记录

### 操作工具
- `add_flow` - 添加流水
- `update_flow` - 更新流水
- `make_excel` - 生成Excel报表

## 📂 项目结构

```
ai/
├── koalaq_hub_python/           # 主项目
│   ├── koalaq_hub/
│   │   ├── core/
│   │   │   └── tool/
│   │   │       └── function/
│   │   │           └── easyaccounts/  # 内置工具
│   │   │               ├── __init__.py
│   │   │               ├── definitions.py  # 工具定义
│   │   │               └── tools.py        # 工具实现
│   │   └── config/
│   │       └── .env            # 配置文件
│   └── resource/
├── Dockerfile                  # 单容器部署
├── docker-compose.yml          # 编排配置
└── requirements.txt            # 依赖列表
```

## 🐛 故障排除

### 问题：连接 EasyAccounts 失败
- 检查 `EASYACCOUNTS_URL` 配置
- 确认 EasyAccounts 服务运行正常
- 测试网络连通性：`curl http://your-easyaccounts:10670`

### 问题：Token认证失败
- 确认token格式：`tool_tokens=Authorization=Bearer_xxx`
- 检查 EasyAccounts 是否开启认证

### 问题：Docker容器无法访问宿主机
- Linux: 使用 `172.17.0.1` 或宿主机IP
- Mac/Windows: 使用 `host.docker.internal`

## 📄 License

MIT