#!/bin/bash

# Chatbot Agent 启动脚本 - 同时启动ngrok和FastAPI服务

echo "🤖 启动 Chatbot Agent..."
echo ""

# 检查ngrok是否运行
if pgrep -x "ngrok" > /dev/null; then
    echo "✅ ngrok 已在运行"
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print([t['public_url'] for t in data['tunnels']][0] if data['tunnels'] else '')")
    echo "   URL: $NGROK_URL"
else
    echo "🚀 启动 ngrok..."
    nohup ngrok http 8000 > ngrok.log 2>&1 &
    sleep 3
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; data = json.load(sys.stdin); print([t['public_url'] for t in data['tunnels']][0] if data['tunnels'] else '')")
    echo "✅ ngrok 已启动"
    echo "   URL: $NGROK_URL"
fi

echo ""

# 检查端口8000
if lsof -ti:8000 > /dev/null; then
    echo "⚠️  端口8000已被占用，正在停止旧进程..."
    lsof -ti:8000 | xargs kill -9
    sleep 1
fi

# 激活虚拟环境并启动服务
echo "🚀 启动 FastAPI 服务..."
cd "$(dirname "$0")"
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

