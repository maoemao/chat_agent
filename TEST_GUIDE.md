# Telegram Bot 测试指南

## 快速测试流程

### 1. 启动服务（运行一次即可）
```bash
# 给脚本添加执行权限
chmod +x start_all.sh

# 启动所有服务（ngrok + FastAPI）
./start_all.sh
```

### 2. 获取公网URL
启动后会显示ngrok URL，例如：
```
✅ ngrok 已启动
   URL: https://verse-choice-bunkhouse.ngrok-free.dev
```

### 3. 设置Telegram Webhook（只需设置一次）
```bash
curl "https://api.telegram.org/bot8747849148:AAH9e4K3I1l4KoRYXPnmpzCIiJBd1nlenj4/setWebhook?url=https://你的ngrokURL/webhook/telegram"
```

### 4. 测试机器人
1. 打开Telegram
2. 搜索机器人：`@maoge_vibecoding_bot`
3. 发送消息测试：
   - `hello` - 普通对话
   - `/start` - 欢迎消息
   - `/help` - 帮助信息
   - `/plan 你好世界` - 代码规划测试

### 5. 查看日志
```bash
# 查看Telegram消息日志
tail -f logs/telegram_*.log

# 查看Agent执行日志
tail -f logs/agent_*.log

# 查看所有日志
ls -la logs/
```

## 当前配置
- **公网URL**: `https://verse-choice-bunkhouse.ngrok-free.dev`
- **Telegram Bot**: `@maoge_vibecoding_bot`
- **Webhook**: 已设置

## 常用命令
```bash
# 停止所有服务
pkill -f "ngrok|uvicorn"

# 查看服务状态
ps aux | grep -E "ngrok|uvicorn" | grep -v grep

# 测试本地服务器
curl http://localhost:8000/health

# 测试公网服务器
curl https://verse-choice-bunkhouse.ngrok-free.dev/health

# 重新设置Webhook（如果URL变化）
curl "https://api.telegram.org/bot8747849148:AAH9e4K3I1l4KoRYXPnmpzCIiJBd1nlenj4/setWebhook?url=https://新URL/webhook/telegram"

# 删除Webhook
curl "https://api.telegram.org/bot8747849148:AAH9e4K3I1l4KoRYXPnmpzCIiJBd1nlenj4/deleteWebhook"
```
