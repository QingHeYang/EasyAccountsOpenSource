# 打包说明

本文档详细说明 KoalaqHub AI 服务的配置管理、环境变量传递机制和 Docker 打包流程。

---

## 目录

1. [配置文件层级](#配置文件层级)
2. [环境变量传递机制](#环境变量传递机制)
3. [配置文件详解](#配置文件详解)
4. [环境变量完整列表](#环境变量完整列表)
5. [Docker 打包流程](#docker-打包流程)
6. [docker-compose 集成](#docker-compose-集成)

---

## 配置文件层级

配置优先级从高到低：

```
docker-compose.yml environment  (最高优先级，运行时覆盖)
        ↓
    Dockerfile ENV              (构建时默认值)
        ↓
    settings.py 默认值          (代码级默认值)
        ↓
    .env 文件                   (本地开发配置)
```

### 文件职责

| 文件 | 职责 | 使用场景 |
|------|------|----------|
| `.env.example` | 配置模板，包含所有可配置项和说明 | 开发参考 |
| `.env` | 本地开发配置，包含实际值 | 本地开发 |
| `Dockerfile` | 构建时默认值，适用于 Docker 部署 | Docker 构建 |
| `settings.py` | 代码级默认值，兜底配置 | 所有场景 |
| `docker-compose.yml` | 运行时覆盖，用户自定义配置 | Docker 部署 |

---

## 环境变量传递机制

### 本地开发

```
.env 文件 → python-dotenv 加载 → settings.py 读取 → 应用使用
```

1. 应用启动时，`settings.py` 调用 `load_dotenv()` 加载 `.env` 文件
2. `os.getenv()` 读取环境变量，若不存在则使用代码默认值
3. 配置实例 `config` 被全局使用

### Docker 部署

```
Dockerfile ENV (默认值)
        ↓
docker-compose environment (覆盖)
        ↓
容器内环境变量
        ↓
settings.py os.getenv() 读取
        ↓
应用使用
```

1. `Dockerfile` 中 `ENV` 指令设置默认值
2. `docker-compose.yml` 中 `environment` 可覆盖任意值
3. 容器启动后，环境变量已注入
4. `settings.py` 通过 `os.getenv()` 读取

### 优先级示例

```python
# settings.py
self.api_port = int(os.getenv("API_PORT", "8001"))
```

| 场景 | API_PORT 值 | 来源 |
|------|-------------|------|
| 本地开发，.env 有值 | .env 中的值 | python-dotenv |
| Docker，compose 有值 | compose 中的值 | docker-compose |
| Docker，compose 无值 | 8001 | Dockerfile ENV |
| 都没有 | 8001 | settings.py 默认 |

---

## 配置文件详解

### .env.example

**作用**：配置模板，供开发者参考

```bash
# 位置：KoalaqHub/.env.example
# 使用：cp .env.example .env && vim .env
```

**特点**：
- 包含所有可配置项
- 敏感值留空（如 API_KEY）
- 包含详细注释说明
- 提交到 Git 仓库

### .env

**作用**：本地开发实际配置

```bash
# 位置：KoalaqHub/.env
# 注意：包含敏感信息，不提交到 Git
```

**特点**：
- 由 `.env.example` 复制而来
- 包含实际的 API Key 等敏感信息
- 已加入 `.gitignore`
- 仅用于本地开发

### Dockerfile

**作用**：Docker 镜像构建配置

```dockerfile
# 位置：ai/Dockerfile
# 构建：docker build -t easyaccounts-ai .
```

**环境变量设置原则**：
- 设置所有非敏感配置的默认值
- 敏感配置（API Key）注释掉，由 compose 注入
- 使用与 compose 服务名一致的网络配置

```dockerfile
# 示例：Dockerfile 中的环境变量
ENV API_PORT=8001
ENV EASYACCOUNTS_URL=http://server:8081  # server 是 compose 服务名
# ENV LLM_EASY_ACCOUNTS_API_KEY=         # 敏感，由 compose 注入
```

### settings.py

**作用**：Python 配置管理器

```python
# 位置：koalaq_hub/config/settings.py
# 职责：加载环境变量，提供配置访问接口
```

**核心逻辑**：

```python
class Configuration:
    def __init__(self):
        self.load_env()           # 加载 .env 文件
        self._init_paths()        # 初始化路径配置
        self._init_env_vars()     # 初始化环境变量

    def _init_env_vars(self):
        # os.getenv(环境变量名, 默认值)
        self.api_port = int(os.getenv("API_PORT", "8001"))
        self.easyaccounts_url = os.getenv("EASYACCOUNTS_URL", "http://server:8081")
```

---

## 环境变量完整列表

### API 服务配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_PORT` | 8001 | API 服务端口 |
| `API_HOST` | 0.0.0.0 | API 监听地址 |

### LLM 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_TIMEOUT` | 120.0 | LLM API 调用超时（秒） |
| `LLM_EASY_ACCOUNTS_API_KEY` | - | LLM API 密钥（敏感，compose 注入） |
| `LLM_EASY_ACCOUNTS_URL` | - | LLM API 地址（compose 注入） |
| `LLM_EASY_ACCOUNTS_MODEL` | - | LLM 模型名称（compose 注入） |

### 总结配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ROUND_SUMMARY_MAX_LENGTH` | 200 | 单轮总结最大长度 |
| `ROUND_SUMMARY_TIMES` | 5 | 多少轮后进行快照总结 |
| `SNAPSHOT_SUMMARY_MAX_LENGTH` | 500 | 快照总结最大长度 |
| `CONVERSATION_SUMMARY_SNAPSHOTS` | 3 | 多少个快照后进行对话总结 |
| `CONVERSATION_SUMMARY_MAX_LENGTH` | 800 | 对话总结最大长度 |

### Agent 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `AGENT_CACHE_TIMEOUT_MINUTES` | 30 | Agent 断开后缓存保留时间（分钟） |

### 超时配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TOOL_EXECUTION_TIMEOUT` | 60 | 工具执行超时（秒） |
| `MCP_SSE_TIMEOUT` | 30 | MCP SSE 连接超时（秒） |

### 数据库配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_DIR` | ./resource/database | 数据库目录路径 |
| `DATABASE_NAME` | koalaq.db | 数据库文件名 |

### 资源路径配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PROMPT_DIR` | ./resource/prompts | 提示词目录 |
| `ROLE_DIR` | ./resource/role | 角色文件目录 |
| `USER_INIT_DIR` | ./resource/user | 用户初始化数据目录 |
| `AGENT_GUIDE_DIR` | ./resource/agents | Agent 指南目录 |

### 配置文件路径

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_CONFIG` | ./resource/config/llm_config.ini | LLM 配置文件路径 |
| `AGENT` | ./resource/config/agent.ini | Agent 配置文件路径 |

### EasyAccounts 配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `EASYACCOUNTS_URL` | http://server:8081 | 后端服务地址（Docker 网桥） |

### MCP 服务器配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MCP_SERVER_ENABLED` | false | 是否启用 MCP 服务器 |
| `MCP_TRANSPORT_MODE` | sse | MCP 传输模式（sse/streamable-http） |

---

## Docker 打包流程

### 1. 目录结构

```
ai/
├── Dockerfile              # Docker 构建文件
├── .dockerignore           # 忽略文件
└── KoalaqHub/              # 源代码目录
    ├── koalaq_hub/         # Python 包
    ├── resource/           # 资源文件
    ├── requirements.txt    # Python 依赖
    └── .env.example        # 配置模板
```

### 2. Dockerfile 解析

```dockerfile
# 基础镜像
FROM python:3.10-slim

# 工作目录
WORKDIR /app

# 复制依赖文件（利用 Docker 缓存）
COPY KoalaqHub/requirements.txt /app/requirements.txt

# 安装依赖（使用国内镜像源）
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r /app/requirements.txt

# 复制源代码
# 注意：本地目录 KoalaqHub，容器内 koalaq_hub_python（与 compose 一致）
COPY KoalaqHub /app/koalaq_hub_python

# 设置 Python 路径
ENV PYTHONPATH="/app/koalaq_hub_python"
WORKDIR /app/koalaq_hub_python

# 暴露端口
EXPOSE 8001

# 环境变量（完整列表见上文）
ENV API_PORT=8001
ENV EASYACCOUNTS_URL=http://server:8081
# ... 其他环境变量

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()" || exit 1

# 启动命令
CMD ["python", "-m", "koalaq_hub"]
```

### 3. 构建命令

```bash
# 进入 ai 目录
cd ai

# 构建镜像
docker build -t easyaccounts-ai:latest .

# 带版本标签
docker build -t easyaccounts-ai:2.6.0 .

# 推送到仓库
docker tag easyaccounts-ai:latest 775495797/easyaccounts-ai:latest
docker push 775495797/easyaccounts-ai:latest
```

### 4. 本地测试

```bash
# 单独运行（需要后端服务）
docker run -d \
  --name test-ai \
  -p 8001:8001 \
  -e LLM_EASY_ACCOUNTS_API_KEY=your-key \
  -e LLM_EASY_ACCOUNTS_URL=https://api.openai.com/v1 \
  -e LLM_EASY_ACCOUNTS_MODEL=gpt-3.5-turbo \
  -e EASYACCOUNTS_URL=http://host.docker.internal:8081 \
  easyaccounts-ai:latest

# 查看日志
docker logs -f test-ai

# 停止并删除
docker stop test-ai && docker rm test-ai
```

---

## docker-compose 集成

### 完整服务配置

```yaml
# docker-compose.yml 中的 ai 服务
ai:
  image: 775495797/easyaccounts-ai:latest
  container_name: easy_accounts_ai
  restart: always
  environment:
    # ===== LLM 配置（必填）=====
    - LLM_EASY_ACCOUNTS_API_KEY=sk-your-api-key    # 替换为实际 API Key
    - LLM_EASY_ACCOUNTS_URL=https://api.openai.com/v1
    - LLM_EASY_ACCOUNTS_MODEL=gpt-3.5-turbo

    # ===== 可选覆盖配置 =====
    # - LLM_TIMEOUT=120.0
    # - ROUND_SUMMARY_MAX_LENGTH=200
    # - AGENT_CACHE_TIMEOUT_MINUTES=30

  volumes:
    # 数据库持久化
    - ./AI/database:/app/koalaq_hub_python/resource/database
    # 自定义角色文件（可选）
    - ./AI/小易.role:/app/koalaq_hub_python/resource/role/小易.role
    # 自定义任务指令（可选）
    - ./AI/task.prompt:/app/koalaq_hub_python/resource/prompts/layers/task/easy_accounts_instructions.prompt

  depends_on:
    - server
  networks:
    - easy_accounts_net
```

### 网络通信

```
┌─────────────────────────────────────────────────────────────┐
│                    easy_accounts_net                         │
│                                                              │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐            │
│  │    db    │     │  server  │     │    ai    │            │
│  │ (MySQL)  │◄───►│ (Spring) │◄───►│ (Python) │            │
│  │  :3306   │     │  :8081   │     │  :8001   │            │
│  └──────────┘     └──────────┘     └──────────┘            │
│        │                │                │                  │
│        │                │                │                  │
└────────┼────────────────┼────────────────┼──────────────────┘
         │                │                │
    10668:3306       10670:8081       (内部)
         │                │
    ┌────┴────────────────┴────┐
    │       宿主机/外部访问      │
    └──────────────────────────┘
```

### 服务依赖关系

```
db (MySQL)
  └──► server (Spring Boot)
         └──► ai (KoalaqHub)
         └──► nginx (前端)
         └──► webhook (钩子)
```

### 环境变量覆盖示例

```yaml
# 使用智谱 AI
environment:
  - LLM_EASY_ACCOUNTS_API_KEY=your-zhipu-key
  - LLM_EASY_ACCOUNTS_URL=https://open.bigmodel.cn/api/paas/v4/
  - LLM_EASY_ACCOUNTS_MODEL=glm-4

# 使用月之暗面 Kimi
environment:
  - LLM_EASY_ACCOUNTS_API_KEY=your-kimi-key
  - LLM_EASY_ACCOUNTS_URL=https://api.moonshot.cn/v1
  - LLM_EASY_ACCOUNTS_MODEL=moonshot-v1-8k

# 调整超时配置
environment:
  - LLM_TIMEOUT=180.0
  - TOOL_EXECUTION_TIMEOUT=120
```

---

## 最佳实践

### 1. 敏感信息管理

- **不要** 将 API Key 写入 Dockerfile
- **不要** 将 `.env` 文件提交到 Git
- **使用** docker-compose 的 environment 注入敏感配置
- **使用** Docker secrets（生产环境）

### 2. 镜像优化

- 使用 `python:3.10-slim` 减小镜像体积
- 分离依赖安装和代码复制（利用缓存）
- 使用 `.dockerignore` 排除不必要文件

### 3. 版本管理

```bash
# 标签规范
easyaccounts-ai:latest      # 最新版
easyaccounts-ai:2.6.0       # 版本号
easyaccounts-ai:2.6.0-beta  # 测试版
```

### 4. 健康检查

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()" || exit 1
```

---

## 常见问题

### Q: 容器无法连接后端服务？

检查 `EASYACCOUNTS_URL` 是否使用正确的服务名：
- Docker 网络内：`http://server:8081`（使用 compose 服务名）
- 宿主机访问：`http://localhost:10670`（使用映射端口）

### Q: LLM 配置不生效？

1. 检查 compose 中 environment 格式是否正确
2. 确认没有拼写错误
3. 重启容器：`docker-compose restart ai`

### Q: 数据库文件丢失？

确保配置了 volume 持久化：
```yaml
volumes:
  - ./AI/database:/app/koalaq_hub_python/resource/database
```

### Q: 如何查看当前配置？

```bash
# 进入容器
docker exec -it easy_accounts_ai bash

# 查看环境变量
env | grep -E "LLM|API|EASY"

# 查看配置文件
cat /app/koalaq_hub_python/resource/config/agent.ini
```
