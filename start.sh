#!/bin/bash

# 聊天机器人Agent启动脚本

echo "正在启动聊天机器人Agent..."

# 检查端口8000是否被占用
if lsof -ti:8000 > /dev/null; then
    echo "⚠️  端口8000已被占用，正在停止旧进程..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# 启动服务器
echo "🚀 启动服务..."
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug

