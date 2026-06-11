#!/bin/bash

# Chatbot Agent 启动脚本

echo "🤖 启动 Chatbot Agent..."
echo ""

# 停止旧进程
echo "🔄 检查并停止旧进程..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "duckduckgo-mcp-server" 2>/dev/null || true
pkill -f "mcp-server-filesystem" 2>/dev/null || true
sleep 1

# 检查端口
for port in 8000 8787; do
    if lsof -ti:$port > /dev/null; then
        echo "⚠️  端口$port已被占用，强制停止..."
        lsof -ti:$port | xargs kill -9
        sleep 1
    fi
done

# 读取 MCP 配置，决定是否启动 DuckDuckGo MCP Server
DDG_MODE=$(python3 -c "import json; print(json.load(open('config/mcp_config.json'))['mcpServers']['ddg-search'].get('mode', 'http'))" 2>/dev/null || echo "http")
echo "📋 DuckDuckGo 搜索模式: $DDG_MODE"

if [ "$DDG_MODE" = "mcp" ]; then
    echo "🚀 启动 DuckDuckGo MCP Server..."
    cd "$(dirname "$0")"
    export DDG_REGION=cn-zh
    nohup venv/bin/duckduckgo-mcp-server --transport streamable-http --host 0.0.0.0 --port 8787 > mcp.log 2>&1 &
    sleep 2

    if pgrep -f "duckduckgo-mcp-server" > /dev/null; then
        echo "✅ DuckDuckGo MCP Server 已启动 (端口: 8787)"
    else
        echo "❌ DuckDuckGo MCP Server 启动失败"
    fi
else
    echo "ℹ️  HTTP 模式，无需启动 DuckDuckGo MCP Server"
fi

# 启动 Filesystem MCP Server
echo "🚀 启动 Filesystem MCP Server..."
nohup mcp-server-filesystem /Users/maogee/Documents/trae_projects/maoge_agent > filesystem_mcp.log 2>&1 &
sleep 2

if pgrep -f "mcp-server-filesystem" > /dev/null; then
    echo "✅ Filesystem MCP Server 已启动"
else
    echo "❌ Filesystem MCP Server 启动失败"
fi

echo ""

# 检查ngrok是否运行
echo "🔍 检查 ngrok..."
if pgrep -x "ngrok" > /dev/null; then
    echo "✅ ngrok 已在运行"
    NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print([t['public_url'] for t in data['tunnels']][0] if data['tunnels'] else '')")
    if [ -n "$NGROK_URL" ]; then
        echo "   URL: $NGROK_URL"
    fi
else
    echo "ℹ️  ngrok 未运行（如需外网访问，请手动启动: ngrok http 8000）"
fi

echo ""

# 启动主服务
echo "🚀 启动 FastAPI 服务..."
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
