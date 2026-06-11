#!/bin/bash

# Chatbot Agent 停止脚本 - 一键停止所有服务

echo "🛑 停止 Chatbot Agent..."
echo ""

# 停止 uvicorn
echo "⏹️  停止 FastAPI 服务..."
if pkill -f "uvicorn" 2>/dev/null; then
    echo "   ✅ FastAPI 服务已停止"
else
    echo "   ℹ️  FastAPI 服务未运行"
fi

# 停止 DuckDuckGo MCP Server
echo "⏹️  停止 DuckDuckGo MCP Server..."
if pkill -f "duckduckgo-mcp-server" 2>/dev/null; then
    echo "   ✅ DuckDuckGo MCP Server 已停止"
else
    echo "   ℹ️  DuckDuckGo MCP Server 未运行"
fi

# 停止 Filesystem MCP Server
echo "⏹️  停止 Filesystem MCP Server..."
if pkill -f "mcp-server-filesystem" 2>/dev/null; then
    echo "   ✅ Filesystem MCP Server 已停止"
else
    echo "   ℹ️  Filesystem MCP Server 未运行"
fi

# 停止 ngrok（可选）
echo "⏹️  停止 ngrok..."
if pkill -x "ngrok" 2>/dev/null; then
    echo "   ✅ ngrok 已停止"
else
    echo "   ℹ️  ngrok 未运行"
fi

# 检查端口占用
echo ""
echo "🔍 检查端口状态..."
for port in 8000 8787; do
    if lsof -ti:$port > /dev/null; then
        echo "⚠️  端口$port 仍被占用，强制停止..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        if lsof -ti:$port > /dev/null; then
            echo "   ❌ 端口$port 停止失败"
        else
            echo "   ✅ 端口$port 已释放"
        fi
    else
        echo "   ✅ 端口$port 已释放"
    fi
done

echo ""
echo "🎉 所有服务已停止！"
