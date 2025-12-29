#!/bin/bash

# 重启koalaq_hub服务的脚本
# 功能：杀死占用8001端口的进程，然后重新启动服务

echo "正在停止koalaq_hub服务..."

# 查找并杀死占用8001端口的进程
PORT=8001
PID=$(lsof -t -i:$PORT)

if [ ! -z "$PID" ]; then
    echo "发现占用端口 $PORT 的进程 PID: $PID"
    kill $PID
    
    # 等待一段时间让进程正常退出
    sleep 3
    
    # 检查进程是否仍然存在，如果存在则强制杀死
    if kill -0 $PID 2>/dev/null; then
        echo "进程未正常退出，正在强制终止..."
        kill -9 $PID
    fi
    echo "已停止 PID 为 $PID 的进程"
else
    echo "没有发现占用端口 $PORT 的进程"
fi

echo "正在启动koalaq_hub服务..."
cd /root/mcp/koalaq_hub_python

# 启动服务并将其输出重定向到日志文件
nohup python -m koalaq_hub > koalaq_hub.log 2>&1 &

# 等待一小段时间让服务启动
sleep 2

# 检查服务是否成功启动
NEW_PID=$(lsof -t -i:$PORT)
if [ ! -z "$NEW_PID" ]; then
    echo "服务已成功启动，新的进程 PID: $NEW_PID"
else
    echo "警告：服务可能启动失败，请检查日志文件 koalaq_hub.log"
fi

echo "重启完成。"