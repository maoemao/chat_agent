
# 聊天机器人 Agent

一个基于 FastAPI 的聊天机器人 Agent，支持 Telegram 接入、RAG 文档问答、火山 Codeing Plan 集成和 MCP 功能调用。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| **通用聊天接入层** | 基于适配器模式设计，当前支持 Telegram，预留 Slack 等平台扩展 |
| **RAG 文档问答** | 基于 LangChain + FAISS 实现 Markdown 文档检索增强生成 |
| **火山 Codeing Plan** | 接入火山引擎代码规划 API，自动生成代码实现方案 |
| **MCP 功能调用** | 支持自定义配置 MCP 服务，可启用/禁用特定工具 |

## 🛠️ 技术栈

- **框架**: FastAPI 0.104.1
- **语言**: Python 3.10+
- **数据库**: SQLite
- **消息队列**: Redis (可选)
- **Telegram SDK**: python-telegram-bot 20.7
- **RAG**: LangChain + FAISS + sentence-transformers
- **HTTP Client**: aiohttp

## 🚀 快速开始

### 环境要求

- Python 3.10+
- pip

### 克隆项目

```bash
git clone <repository-url>
cd maoge_agent
```

### 创建虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 安装依赖

```bash
# 在虚拟环境中安装依赖
pip install -r requirements.txt

# 安装额外依赖（如果需要）
pip install pydantic-settings
```

### 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下参数：

```env
# Telegram配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# 火山引擎配置（两种方式任选其一）
VOLC_API_KEY=your_volc_api_key
# VOLC_ACCESS_KEY=your_volc_access_key
# VOLC_SECRET_KEY=your_volc_secret_key

# RAG配置
RAG_DOCS_PATH=data/documents

# 数据库配置（本地SQLite，无需额外安装）
DATABASE_URL=sqlite:///./app.db

# MCP配置
MCP_CONFIG_PATH=config/mcp_config.json

# 启用的适配器
ENABLED_ADAPTERS=telegram
```

### 启动服务

```bash
# 确保已激活虚拟环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问: http://localhost:8000

### 退出虚拟环境

```bash
deactivate
```

## 📡 Telegram 配置

### 创建 Telegram Bot

1. 在 Telegram 中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 按照提示设置机器人名称和用户名
4. 获取 Bot Token

### 设置 Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook/telegram"}'
```

## 📚 RAG 文档问答

### 添加文档

将 Markdown 文档放入 `data/documents/` 目录，系统会自动加载并构建向量索引。

### 使用方法

在 Telegram 中发送：
```
/rag 你的问题
```

## 🔧 火山 Codeing Plan

### 使用方法

在 Telegram 中发送：
```
/plan 你的需求描述
```

示例：
```
/plan 创建一个登录页面，包含用户名和密码输入框
```

## 🧩 MCP 功能调用

### 配置 MCP 服务

创建 `config/mcp_config.json` 文件：

```json
{
  "servers": [
    {
      "name": "mcp_server_name",
      "url": "http://mcp-server:port",
      "enabled": true,
      "tools": [
        {
          "name": "tool_name",
          "enabled": true,
          "description": "工具描述"
        }
      ]
    }
  ]
}
```

### 查看可用工具

在 Telegram 中发送：
```
/mcp
```

## 📖 API 接口

### 健康检查

```
GET /health
```

响应：
```json
{"status": "healthy"}
```

### Webhook 入口

```
POST /webhook/{platform}
```

支持的 platform: `telegram`

## 📁 项目结构

```
maoge_agent/
├── app/                    # 应用代码
│   ├── adapters/           # 聊天平台适配器
│   │   ├── base.py         # 适配器基类接口
│   │   ├── telegram.py     # Telegram适配器
│   │   └── slack.py        # Slack适配器（预留）
│   ├── core/               # 核心模块
│   │   ├── types.py        # 消息类型定义
│   │   ├── message_router.py # 消息路由器
│   │   └── agent.py        # Agent核心逻辑
│   ├── services/           # 业务服务层
│   │   ├── rag_service.py  # RAG问答服务
│   │   ├── codeing_plan_service.py # 火山Codeing Plan
│   │   └── mcp_service.py  # MCP功能调用服务
│   ├── config/             # 配置文件
│   │   ├── settings.py     # 环境配置
│   │   └── mcp_config.py   # MCP配置
│   ├── routers/            # API路由
│   │   └── webhook.py      # Webhook入口
│   ├── utils/              # 工具模块
│   │   └── markdown_parser.py # Markdown解析工具
│   └── main.py             # 主入口
├── data/
│   └── documents/          # Markdown文档存储
├── tests/                  # 测试目录
├── requirements.txt        # 依赖列表
├── .env.example            # 环境变量模板
└── .env                    # 环境变量（需创建）
```

## 🤖 Telegram 命令

| 命令 | 描述 |
|------|------|
| `/start` | 欢迎消息 |
| `/help` | 帮助信息 |
| `/rag [问题]` | 基于文档进行问答 |
| `/plan [需求]` | 生成代码规划 |
| `/mcp` | 显示可用 MCP 工具 |

## 🔌 添加新聊天平台

1. 创建新的适配器类继承 `ChatAdapter` 基类
2. 实现以下方法：
   - `handle_webhook(request)` - 处理 Webhook 请求
   - `send_message(recipient, message)` - 发送消息
   - `parse_message(raw_data)` - 解析原始消息
   - `get_platform()` - 返回平台类型
   - `get_name()` - 返回平台名称
3. 在 `settings.py` 中启用适配器

## 🧪 测试

```bash
# 运行健康检查
curl http://localhost:8000/health

# 测试 Telegram Webhook
curl -X POST http://localhost:8000/webhook/telegram \
     -H "Content-Type: application/json" \
     -d '{"update_id":12345,"message":{"message_id":1,"from":{"id":12345,"first_name":"Test"},"chat":{"id":12345},"date":1234567890,"text":"/start"}}'
```

## 📝 日志

服务启动后会输出日志到控制台，包含：
- 服务启动信息
- 接收到的消息
- 错误信息

## 🔒 安全注意事项

1. 不要将 `.env` 文件提交到版本控制
2. 使用 HTTPS 部署生产环境
3. 配置适当的访问控制
4. 定期更新依赖版本

## 📄 License

MIT License

---

**注意**: 首次启动时，系统会自动创建 `data/documents/welcome.md` 欢迎文档。RAG 功能需要 OpenAI API Key 才能正常工作。
