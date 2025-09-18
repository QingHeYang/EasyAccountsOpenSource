# EasyAccounts AI 服务部署指南

## 部署所需文件

在其他文件夹部署时，需要准备以下文件：

### 1. 核心文件（必需）
```
easyaccounts-ai/
├── docker-compose.yml        # Docker Compose配置文件
└── custom/                    # 自定义配置目录（可选）
    ├── 小易.role             # AI角色配置（可选）
    └── easy_accounts_instructions.prompt  # AI指令配置（可选）
```

### 2. Docker镜像
- **镜像名称**: `775495797/easyaccounts-ai:latest`
- **获取方式**: 
  - 从Docker Hub拉取: `docker pull 775495797/easyaccounts-ai:latest`
  - 或使用本地构建的镜像

## 快速部署步骤

### 步骤1: 创建部署目录
```bash
mkdir easyaccounts-ai
cd easyaccounts-ai
```

### 步骤2: 创建 docker-compose.yml
创建 `docker-compose.yml` 文件，内容如下：

```yaml
version: '3.8'

services:
  ai:
    image: 775495797/easyaccounts-ai:latest
    container_name: easy_accounts_ai
    restart: always
    ports:
      - "8001:8001"
    environment:
      - EASYACCOUNTS_URL=http://easy_accounts_server:8081
      
      # LLM 配置（必需 - 请填入您的实际值）
      # 如不配置，服务将无法启动
      - LLM_EASY_ACCOUNTS_API_KEY=sk-xxxxxxxxxxxxx  # 替换为您的API密钥
      - LLM_EASY_ACCOUNTS_URL=https://api.openai.com/v1  # 替换为您的API地址
      - LLM_EASY_ACCOUNTS_MODEL=gpt-4-turbo-preview  # 替换为您要使用的模型
      
    volumes:
      # 数据库持久化
      - ./data/database:/app/koalaq_hub_python/resource/database
      
      # 自定义AI角色和指令（可选）
      - ./custom/小易.role:/app/koalaq_hub_python/resource/role/小易.role
      - ./custom/easy_accounts_instructions.prompt:/app/koalaq_hub_python/resource/prompts/layers/task/easy_accounts_instructions.prompt
    
    networks:
      - easy_accounts_net

networks:
  easy_accounts_net:
    external: true
```

### 步骤3: 配置LLM参数
编辑 `docker-compose.yml`，替换以下环境变量为您的实际值：
- `LLM_EASY_ACCOUNTS_API_KEY`: 您的OpenAI或兼容API的密钥
- `LLM_EASY_ACCOUNTS_URL`: API端点地址
- `LLM_EASY_ACCOUNTS_MODEL`: 使用的模型名称

### 步骤4: （可选）准备自定义配置
如果需要自定义AI行为，创建 `custom` 目录并添加配置文件：

```bash
mkdir -p custom

# 创建自定义角色文件（可选）
cat > custom/小易.role << 'EOF'
你是小易，一个专业的财务管理助手。
你可以帮助用户管理账单、分析财务数据、生成报表。
请用友好、专业的语气与用户交流。
EOF

# 创建自定义指令文件（可选）
cat > custom/easy_accounts_instructions.prompt << 'EOF'
在处理财务数据时，请确保：
1. 数据准确性
2. 保护用户隐私
3. 提供清晰的解释
EOF
```

### 步骤5: 启动服务
```bash
# 确保EasyAccounts主服务已经运行，并且网络存在
docker network ls | grep easy_accounts_net || docker network create easy_accounts_net

# 启动AI服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 验证部署

### 检查服务状态
```bash
# 检查容器状态
docker ps | grep easy_accounts_ai

# 测试API健康检查
curl http://localhost:8001/health

# 查看API文档
# 在浏览器访问: http://localhost:8001/docs
```

### 测试WebSocket连接
```bash
# 使用wscat测试（需要先安装: npm install -g wscat）
wscat -c ws://localhost:8001/ws/chat
```

## 环境变量说明

### 必需配置
| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| LLM_EASY_ACCOUNTS_API_KEY | LLM API密钥 | sk-xxxxxxxxxxxxx |
| LLM_EASY_ACCOUNTS_URL | LLM API地址 | https://api.openai.com/v1 |
| LLM_EASY_ACCOUNTS_MODEL | 使用的模型 | gpt-4-turbo-preview |

### 可选配置
| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| EASYACCOUNTS_URL | EasyAccounts后端地址 | http://easy_accounts_server:8081 |
| API_PORT | API服务端口 | 8001 |
| API_HOST | API服务主机 | 0.0.0.0 |

## 数据持久化

服务会在以下位置存储数据：
- `./data/database/koalaq.db` - 用户对话历史和配置数据

建议定期备份此文件。

## 故障排查

### 1. 服务无法启动
- 检查LLM配置是否正确填写
- 查看日志: `docker-compose logs ai`

### 2. 无法连接到EasyAccounts
- 确认easy_accounts_net网络存在
- 确认EasyAccounts服务正在运行
- 检查EASYACCOUNTS_URL配置

### 3. WebSocket连接失败
- 确认8001端口未被占用
- 检查防火墙设置

## 更新服务

```bash
# 拉取最新镜像
docker pull 775495797/easyaccounts-ai:latest

# 重启服务
docker-compose down
docker-compose up -d
```

## 完整部署示例

```bash
# 一键部署脚本
cat > deploy.sh << 'EOF'
#!/bin/bash

# 创建目录
mkdir -p easyaccounts-ai/custom
cd easyaccounts-ai

# 下载docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
version: '3.8'

services:
  ai:
    image: 775495797/easyaccounts-ai:latest
    container_name: easy_accounts_ai
    restart: always
    ports:
      - "8001:8001"
    environment:
      - EASYACCOUNTS_URL=http://easy_accounts_server:8081
      - LLM_EASY_ACCOUNTS_API_KEY=${LLM_API_KEY}
      - LLM_EASY_ACCOUNTS_URL=${LLM_URL:-https://api.openai.com/v1}
      - LLM_EASY_ACCOUNTS_MODEL=${LLM_MODEL:-gpt-4-turbo-preview}
    volumes:
      - ./data/database:/app/koalaq_hub_python/resource/database
    networks:
      - easy_accounts_net

networks:
  easy_accounts_net:
    external: true
COMPOSE

# 提示用户设置环境变量
echo "请设置以下环境变量后运行 docker-compose up -d："
echo "export LLM_API_KEY=your_api_key_here"
echo "export LLM_URL=https://api.openai.com/v1"
echo "export LLM_MODEL=gpt-4-turbo-preview"
EOF

chmod +x deploy.sh
```

然后运行：
```bash
export LLM_API_KEY=sk-xxxxxxxxxxxxx
export LLM_URL=https://api.openai.com/v1
export LLM_MODEL=gpt-4-turbo-preview
./deploy.sh
docker-compose up -d
```