# 使用Python 3.10基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 先复制requirements.txt（依赖文件变化较少）
COPY KoalaqHub/requirements.txt /app/requirements.txt

# 安装Python依赖（使用清华源）
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout=1000 \
    -r /app/requirements.txt

# 最后复制项目代码（代码变化频繁）
# 注意：本地目录是 KoalaqHub，容器内使用 koalaq_hub_python（与 docker-compose 保持一致）
COPY KoalaqHub /app/koalaq_hub_python

# 设置Python路径
ENV PYTHONPATH="/app/koalaq_hub_python"

# 设置工作目录
WORKDIR /app/koalaq_hub_python

# 暴露端口
# KoalaQ Hub API端口
EXPOSE 8001

# ===== 基础环境变量 =====
ENV PYTHONUNBUFFERED=1

# ===== API 服务配置 =====
ENV API_PORT=8001
ENV API_HOST=0.0.0.0

# ===== 日志配置 =====
# 日志目录，配合 docker-compose 挂载使用
ENV LOG_DIR=/app/logs

# ===== LLM 配置 =====
ENV LLM_TIMEOUT=120.0
# LLM 密钥等敏感配置通过 docker-compose 注入
# ENV LLM_EASY_ACCOUNTS_API_KEY=
# ENV LLM_EASY_ACCOUNTS_URL=
# ENV LLM_EASY_ACCOUNTS_MODEL=

# ===== 总结配置 =====
ENV ROUND_SUMMARY_MAX_LENGTH=200
ENV ROUND_SUMMARY_TIMES=5
ENV SNAPSHOT_SUMMARY_MAX_LENGTH=500
ENV CONVERSATION_SUMMARY_SNAPSHOTS=3
ENV CONVERSATION_SUMMARY_MAX_LENGTH=800

# ===== Agent 缓存配置 =====
ENV AGENT_CACHE_TIMEOUT_MINUTES=30

# ===== 工具和超时配置 =====
ENV TOOL_EXECUTION_TIMEOUT=60
ENV MCP_SSE_TIMEOUT=30

# ===== 数据库配置 =====
ENV DATABASE_DIR=./resource/database
ENV DATABASE_NAME=koalaq.db

# ===== 资源路径配置 =====
ENV PROMPT_DIR=./resource/prompts
ENV ROLE_DIR=./resource/role
ENV USER_INIT_DIR=./resource/user
ENV AGENT_GUIDE_DIR=./resource/agents

# ===== 配置文件路径 =====
ENV LLM_CONFIG=./resource/config/llm_config.ini
ENV AGENT=./resource/config/agent.ini

# ===== EasyAccounts 配置（通过Docker网络访问）=====
ENV EASYACCOUNTS_URL=http://server:8081

# ===== MCP 服务器配置 =====
ENV MCP_SERVER_ENABLED=false
ENV MCP_TRANSPORT_MODE=sse

# 健康检查 - 使用Python内置的urllib
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()" || exit 1

# 启动服务
CMD ["python", "-m", "koalaq_hub"]