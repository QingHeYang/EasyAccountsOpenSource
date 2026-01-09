# 使用 python:3.10-slim 瘦身镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装依赖
COPY requirements.txt .

RUN pip install --no-cache-dir \
    -i https://pypi.tuna.tsinghua.edu.cn/simple \
    --trusted-host pypi.tuna.tsinghua.edu.cn \
    --timeout=1000 \
    -r /app/requirements.txt

# 复制应用程序代码
COPY webhook.py .

# 暴露端口
EXPOSE 8083

# 启动FastAPI应用
CMD ["uvicorn", "webhook:app", "--host", "0.0.0.0", "--port", "8083"]
