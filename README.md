# 聊天机器人 Agent

一个基于 FastAPI 的聊天机器人 Agent，支持 Telegram 接入、RAG 文档问答、火山 Codeing Plan 集成、MCP 功能调用（包含 DuckDuckGo 搜索）和 GitHub 代码推送。

---

## 🚀 快速开始

### 一键启动

```bash
# 进入项目目录
cd maoge_agent

# 启动所有服务
chmod +x start_all.sh
./start_all.sh

# 停止所有服务
chmod +x stop_all.sh
./stop_all.sh
```

---

## 🤖 Telegram 命令用法

| 命令 | 描述 | 示例 |
|------|------|------|
| `/start` | 欢迎消息 | `/start` |
| `/help` | 帮助信息 | `/help` |
| `/rag [问题]` | 基于文档进行问答 | `/rag 如何配置 MCP？` |
| `/plan [需求]` | 生成代码规划 | `/plan 创建一个登录页面` |
| `/code [需求]` | 分析并修改本地代码 | `/code 添加用户登录功能` |
| `/git [操作]` | Git 操作（查看状态、提交、推送） | `/git status` |
| `/mcp` | 显示可用 MCP 工具 | `/mcp` |
| `/mcp search [关键词]` | DuckDuckGo 网络搜索 | `/mcp search AI最新动态` |

### Git 操作详细用法

| 命令 | 描述 | 示例 |
|------|------|------|
| `/git` | 显示帮助信息 | `/git` |
| `/git status` | 查看工作区状态 | `/git status` |
| `/git diff` | 查看未暂存的更改 | `/git diff` |
| `/git log [数量]` | 查看最近的提交记录 | `/git log 5` |
| `/git branch` | 查看当前分支信息 | `/git branch` |
| `/git add` | 暂存所有更改 | `/git add` |
| `/git commit [信息]` | 提交更改 | `/git commit 修复了登录bug` |
| `/git push` | 推送到远程仓库 | `/git push` |
| `/git commitpush [信息]` | 一键提交并推送 | `/git commitpush 添加了新功能` |

### 一键推送代码示例

```bash
# 提交并推送到 GitHub（最常用）
/git commitpush 修复了搜索功能

# 先查看状态，再提交推送
/git status
/git commitpush 添加了新功能
```

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| **通用聊天接入层** | 基于适配器模式设计，当前支持 Telegram，预留 Slack 等平台扩展 |
| **RAG 文档问答** | 基于 LangChain + FAISS 实现 Markdown 文档检索增强生成 |
| **火山 Codeing Plan** | 接入火山引擎代码规划 API，自动生成代码实现方案 |
| **代码修改助手** | 自动分析项目代码，生成修改方案，支持一键应用修改 |
| **MCP 功能调用** | 支持自定义配置 MCP 服务，内置 DuckDuckGo 搜索和文件系统操作 |
| **GitHub 代码推送** | 通过 Telegram 随时随地提交和推送代码到 GitHub |
| **一键启停脚本** | `start_all.sh` 和 `stop_all.sh` 方便管理服务 |

---

## 📖 功能文档

每个功能都有详细的实现说明文档：

| 文档 | 说明 |
|------|------|
| [telegram.md](docs/telegram.md) | Telegram 通讯机制详解 |
| [rag.md](docs/rag.md) | RAG 文档问答实现原理 |
| [code.md](docs/code.md) | 代码修改助手工作流程 |
| [git.md](docs/git.md) | Git 操作服务实现 |
| [mcp.md](docs/mcp.md) | MCP 功能调用机制 |

---

## 📤 GitHub 代码推送

### 配置 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 生成新的 Personal Access Token
3. 勾选 `repo` 权限
4. 在 `.env` 文件中添加：

```env
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

### 使用流程

```
1. 修改代码文件
2. 使用 /git status 查看修改状态
3. 使用 /git commitpush [提交信息] 一键提交并推送
```

### 特点

- ✅ HTTPS 协议自动切换
- ✅ 详细的错误提示
- ✅ 支持查看状态、差异、日志
- ✅ 自动处理远程仓库配置

---

## 🛠️ 技术栈

- **框架**: FastAPI 0.104.1
- **语言**: Python 3.10+
- **数据库**: SQLite
- **消息队列**: Redis (可选)
- **Telegram SDK**: python-telegram-bot 20.7
- **RAG**: LangChain 1.3.7 + FAISS + sentence-transformers
- **HTTP Client**: aiohttp

---

## 📦 安装指南

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

# GitHub配置（用于代码推送）
GITHUB_TOKEN=your_github_token

# RAG配置
RAG_DOCS_PATH=data/documents

# 数据库配置（本地SQLite，无需额外安装）
DATABASE_URL=sqlite:///./app.db

# MCP配置
MCP_CONFIG_PATH=config/mcp_config.json

# 启用的适配器
ENABLED_ADAPTERS=telegram
```

### 手动启动服务

```bash
# 确保已激活虚拟环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后访问: http://localhost:8000

### 退出虚拟环境

```bash
deactivate
```

---

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

---

## 📚 RAG 文档问答

### 添加文档

将 Markdown 文档放入 `data/documents/` 目录，系统会自动加载并构建向量索引。

### 使用方法

```
/rag 你的问题
```

示例：
```
/rag 如何配置 MCP 服务？
```

---

## 🔧 火山 Codeing Plan

### 使用方法

```
/plan 你的需求描述
```

示例：
```
/plan 创建一个登录页面，包含用户名和密码输入框
```

---

## 📝 代码修改助手

### 使用方法

```
/code 你的需求描述
```

示例：
```
/code 添加用户登录功能
/code 修改数据库连接配置
/code 为RAG服务添加缓存机制
```

### 工作流程

1. **分析项目结构** - 自动扫描项目中的 Python 文件（排除虚拟环境）
2. **读取文件内容** - 获取关键文件内容（最多10个文件）
3. **调用火山引擎 API** - 使用 ark-code-latest 模型分析需求
4. **生成修改方案** - 返回修改建议和完整代码块
5. **安全备份** - 自动创建 `.backup` 备份文件

### 功能特点

- ✅ 自动扫描项目文件结构
- ✅ 智能分析代码并生成修改方案
- ✅ 修改前自动备份原文件
- ✅ 支持代码块提取和展示

---

## 🧩 MCP 功能调用

### DuckDuckGo 搜索

```
/mcp search 搜索关键词
```

示例：
```
/mcp search AI最新动态
/mcp search Python教程
```

### 文件系统操作

MCP 文件系统服务器提供项目文件浏览功能：

- ✅ 列出目录文件
- ✅ 读取文件内容
- ✅ 搜索文件
- ✅ 获取文件统计信息

> **注意**: 文件系统 MCP 使用 stdio 模式，与 HTTP 模式的服务不同。

### 配置 MCP 服务

`config/mcp_config.json` 文件支持 LangChain 标准格式：

```json
{
  "mcpServers": {
    "ddg-search": {
      "command": "duckduckgo-mcp-server",
      "args": ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8787"],
      "env": {
        "DDG_REGION": "cn-zh"
      },
      "mode": "http"
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/项目路径"],
      "env": {}
    }
  }
}
```

### 搜索模式切换

DuckDuckGo 搜索支持两种模式：

| 模式 | 说明 |
|------|------|
| `http` | **推荐** - 直接通过 HTTP 请求调用 DuckDuckGo 搜索，无需启动额外服务器 |
| `mcp` | 通过官方 MCP 服务器调用，需要先启动 `duckduckgo-mcp-server` |

**切换方法**: 修改 `config/mcp_config.json` 中的 `mode` 字段：

```json
"mode": "http"   // HTTP模式（默认）
// 或
"mode": "mcp"    // MCP模式
```

启动脚本会自动根据配置决定是否启动 MCP 服务器。

### 查看可用工具

```
/mcp
```

---

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

---

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
│   │   ├── code_editor_service.py # 代码修改助手
│   │   ├── git_service.py # Git操作服务
│   │   └── mcp_service.py  # MCP功能调用服务（含DuckDuckGo搜索）
│   ├── config/             # 配置文件
│   │   ├── settings.py     # 环境配置
│   │   └── mcp_config.py   # MCP配置
│   ├── routers/            # API路由
│   │   └── webhook.py      # Webhook入口
│   ├── utils/              # 工具模块
│   │   └── logger.py       # 日志工具
│   └── main.py             # 主入口
├── config/
│   └── mcp_config.json     # MCP服务配置
├── data/
│   └── documents/          # Markdown文档存储
├── tests/                  # 测试目录
├── requirements.txt        # 依赖列表
├── .env.example            # 环境变量模板
├── .env                    # 环境变量（需创建）
├── start_all.sh            # 一键启动脚本
├── stop_all.sh             # 一键停止脚本
└── README.md               # 项目文档
```

---

## 🔌 添加新聊天平台

1. 创建新的适配器类继承 `ChatAdapter` 基类
2. 实现以下方法：
   - `handle_webhook(request)` - 处理 Webhook 请求
   - `send_message(recipient, message)` - 发送消息
   - `parse_message(raw_data)` - 解析原始消息
   - `get_platform()` - 返回平台类型
   - `get_name()` - 返回平台名称
3. 在 `settings.py` 中启用适配器

---

## 🧪 测试

```bash
# 运行健康检查
curl http://localhost:8000/health

# 测试 Telegram Webhook
curl -X POST http://localhost:8000/webhook/telegram \
     -H "Content-Type: application/json" \
     -d '{"update_id":12345,"message":{"message_id":1,"from":{"id":12345,"first_name":"Test"},"chat":{"id":12345},"date":1234567890,"text":"/start"}}'
```

---

## 📝 日志

服务启动后会输出日志到控制台，包含：
- 服务启动信息
- 接收到的消息
- 错误信息

---

## 🔒 安全注意事项

1. 不要将 `.env` 文件提交到版本控制
2. 使用 HTTPS 部署生产环境
3. 配置适当的访问控制
4. 定期更新依赖版本
5. GitHub Token 具有代码仓库访问权限，请妥善保管

---

## 📄 License

MIT License

---

**注意**: 首次启动时，系统会自动创建 `data/documents/welcome.md` 欢迎文档。
