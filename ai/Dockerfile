# 使用Python 3.10基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 先复制requirements.txt（依赖文件变化较少）
COPY koalaq_hub_python/requirements.txt /app/requirements.txt

# 安装Python依赖（使用清华源）
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout=1000 \
    -r /app/requirements.txt

# 最后复制项目代码（代码变化频繁）
COPY koalaq_hub_python /app/koalaq_hub_python

# 设置Python路径
ENV PYTHONPATH="/app/koalaq_hub_python"

# 设置工作目录
WORKDIR /app/koalaq_hub_python

# 暴露端口
# KoalaQ Hub API端口
EXPOSE 8001

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV API_PORT=8001
ENV API_HOST=0.0.0.0

# EasyAccounts配置（通过Docker网络访问）
ENV EASYACCOUNTS_URL=http://easy_accounts_server:8081

# 健康检查 - 使用Python内置的urllib
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health').read()" || exit 1

# 启动服务
CMD ["python", "-m", "koalaq_hub"]