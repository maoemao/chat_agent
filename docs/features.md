# 聊天机器人 Agent 功能详解

本文档详细介绍项目中各个功能的实现原理和运行流程。

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Telegram 用户                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ 发送消息/命令
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Telegram Adapter                             │
│  ┌─────────────────┐  ┌─────────────────┐                    │
│  │   Webhook 模式  │  │   Polling 模式  │                    │
│  └────────┬────────┘  └────────┬────────┘                    │
└───────────┼────────────────────┼───────────────────────────────┘
            │                    │
            └────────┬───────────┘
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Message Router                              │
│     根据消息类型路由到不同的 Handler                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Command    │     │   Text      │     │  Document   │
│  Handler    │     │  Handler    │     │   Handler   │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent Core                                │
│  解析命令 → 路由到对应服务 → 返回结果                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────┬───────┼───────┬───────────┬───────────┐
        ▼           ▼       ▼       ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ RAG       │ │ Code      │ │ Git       │ │ MCP       │ │ AI Chat   │
│ Service   │ │ Editor    │ │ Service   │ │ Manager   │ │ Service   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
        │           │           │           │
        ▼           ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ FAISS     │ │ 火山引擎  │ │ 本地 Git  │ │ DuckDuckGo│
│ 向量数据库│ │ Code API  │ │ 仓库      │ │ 搜索API   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘
```

---

## 二、Telegram 通讯机制

### 2.1 两种运行模式

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **Webhook** | 生产环境 | 实时响应、资源占用低 | 需要公网 HTTPS 地址 |
| **Polling** | 开发调试 | 无需公网、配置简单 | 轮询间隔延迟、资源占用高 |

### 2.2 Webhook 模式流程

```python
# app/adapters/telegram.py
async def handle_webhook(self, request: Request) -> Response:
    # 1. 接收 Telegram 服务器的 POST 请求
    data = await request.json()
    
    # 2. 解析消息数据
    message = self.parse_message(data)
    
    # 3. 转发给消息处理器
    if message and self.message_handler:
        await self.message_handler(message)
    
    # 4. 返回 200 响应
    return Response(status_code=200)
```

**设置 Webhook：**

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook/telegram"}'
```

### 2.3 Polling 模式流程

```python
# app/adapters/telegram.py
async def start_polling(self):
    # 1. 创建 Telegram Application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # 2. 注册消息处理器
    application.add_handler(MessageHandler(filters.ALL, handle_update))
    
    # 3. 启动轮询
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # 4. 持续监听
    while True:
        await asyncio.sleep(1)
```

### 2.4 消息解析流程

```python
# app/adapters/telegram.py
def parse_message(self, raw_data: dict) -> Optional[Message]:
    # 1. 提取消息数据
    message_data = raw_data.get('message', {})
    
    # 2. 解析基本信息
    message_id = str(message_data.get('message_id', ''))
    chat_id = str(message_data.get('chat', {}).get('id', ''))
    sender_name = message_data.get('chat', {}).get('first_name', 'Unknown')
    
    # 3. 判断消息类型
    content = message_data.get('text', '')
    if content.startswith('/'):
        msg_type = MessageType.COMMAND
    else:
        msg_type = MessageType.TEXT
    
    # 4. 封装为统一的 Message 对象
    return Message(
        id=message_id,
        type=msg_type,
        content=content,
        sender=chat_id,
        sender_name=sender_name,
        platform=PlatformType.TELEGRAM,
        timestamp=datetime.fromtimestamp(message_data.get('date', 0))
    )
```

### 2.5 消息发送流程

```python
# app/adapters/telegram.py
async def send_message(self, recipient: str, message: ResponseMessage) -> None:
    # 1. 构造请求
    url = f"https://api.telegram.org/bot{self.token}/sendMessage"
    data = {
        "chat_id": int(recipient),
        "text": message.content
    }
    
    # 2. 发送 HTTP 请求
    response = requests.post(url, data=data, timeout=30)
    
    # 3. 处理响应
    if response.status_code == 200:
        telegram_logger.info(f"Message sent successfully")
    else:
        telegram_logger.error(f"Failed to send message")
```

---

## 三、RAG 文档问答（/rag）

### 3.1 核心原理

RAG（Retrieval-Augmented Generation）通过检索相关文档并结合 LLM 生成回答。

### 3.2 处理流程

```
用户问题 → 向量化 → FAISS检索 → 拼接上下文 → LLM生成 → 返回答案
```

### 3.3 关键代码解析

```python
# app/services/rag_service.py
async def query(self, question: str) -> str:
    # 1. 加载文档并构建向量索引
    if not self.vector_store:
        await self._load_documents()
    
    # 2. 检索相关文档（默认返回3条）
    retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
    docs = await retriever.ainvoke(question)
    
    # 3. 拼接上下文
    context = "\n\n".join([doc.page_content for doc in docs])
    
    # 4. 构建提示词
    prompt = f"""根据以下上下文回答问题：
    
    {context}
    
    问题：{question}
    
    如果上下文没有相关信息，请回答"未找到相关答案"。
    """
    
    # 5. 调用 LLM 生成回答
    response = await self.ai_chat_service.chat(prompt)
    return response
```

### 3.4 文档加载机制

```python
# app/services/rag_service.py
async def _load_documents(self):
    # 1. 扫描 documents 目录
    docs_path = settings.rag_docs_path
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
    
    # 2. 加载所有 Markdown 文件
    md_files = list(docs_path.glob("*.md"))
    if not md_files:
        # 创建默认欢迎文档
        welcome_content = "# 欢迎使用\n\n这是一个聊天机器人..."
        (docs_path / "welcome.md").write_text(welcome_content, encoding='utf-8')
        md_files = [docs_path / "welcome.md"]
    
    # 3. 分割文档为 chunks
    from langchain.text_splitter import MarkdownTextSplitter
    text_splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    # 4. 向量化并构建 FAISS 索引
    from langchain.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    self.vector_store = FAISS.from_documents(docs, embeddings)
```

### 3.5 使用示例

```
/rag 如何配置 MCP 服务？
/rag 项目的目录结构是什么？
/rag 如何添加新的聊天平台？
```

---

## 四、代码修改助手（/code）

### 4.1 功能概述

自动分析项目代码结构，根据用户需求生成代码修改方案。

### 4.2 处理流程

```
用户需求 → 扫描项目文件 → 读取关键文件 → 调用火山API → 生成修改方案 → 返回结果
```

### 4.3 关键代码解析

```python
# app/services/code_editor_service.py
async def analyze_and_modify(self, requirement: str) -> str:
    # 1. 获取项目文件列表（排除虚拟环境）
    project_files = self._list_project_files()
    
    # 2. 读取关键文件内容（最多10个文件，每个文件最多1000字符）
    file_contents = {}
    for file_path in project_files[:10]:
        content = self._get_file_content(file_path)
        if content:
            file_contents[file_path] = content[:1000]
    
    # 3. 构建提示词
    files_info = "\n\n".join([
        f"=== {path} ===\n{content}"
        for path, content in file_contents.items()
    ])
    
    # 4. 调用火山引擎代码规划 API
    data = {
        "model": "ark-code-latest",
        "messages": [
            {"role": "system", "content": "你是一个专业的代码修改助手..."},
            {"role": "user", "content": f"项目文件：\n{files_info}\n\n需求：{requirement}"}
        ],
        "max_tokens": 4096,
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=data
        )
    
    # 5. 解析并返回结果
    result = response.json()
    return result["choices"][0]["message"]["content"]
```

### 4.4 安全机制

```python
# app/services/code_editor_service.py
async def apply_modification(self, file_path: str, new_content: str) -> str:
    # 1. 安全检查：确保路径在项目目录内
    path = Path(file_path)
    if not path.is_absolute():
        path = self.project_path / path
    
    try:
        path.relative_to(self.project_path)
    except ValueError:
        return "❌ 错误：只能修改项目目录内的文件"
    
    # 2. 自动备份原文件
    if path.exists():
        backup_path = path.with_suffix(path.suffix + ".backup")
        backup_path.write_text(path.read_text(encoding='utf-8'), encoding='utf-8')
    
    # 3. 写入新内容
    path.write_text(new_content, encoding='utf-8')
    return f"✅ 文件修改成功"
```

### 4.5 使用示例

```
/code 添加用户登录功能
/code 修改数据库连接配置
/code 为RAG服务添加缓存机制
```

---

## 五、Git 操作服务（/git）

### 5.1 功能概述

通过 Telegram 命令执行 Git 操作，支持代码提交和推送。

### 5.2 支持的命令

| 命令 | 功能 | 实现方式 |
|------|------|----------|
| `/git status` | 查看工作区状态 | `git status` |
| `/git diff` | 查看未暂存的更改 | `git diff` |
| `/git log` | 查看提交记录 | `git log --oneline` |
| `/git branch` | 查看分支信息 | `git branch --show-current` |
| `/git add` | 暂存所有更改 | `git add -A` |
| `/git commit` | 提交更改 | `git commit -m` |
| `/git push` | 推送到远程 | `git push origin main` |
| `/git commitpush` | 一键提交并推送 | 组合操作 |

### 5.3 关键代码解析

```python
# app/services/git_service.py
def _run_git_command(self, *args) -> Dict[str, Any]:
    """执行 Git 命令并返回结果"""
    result = subprocess.run(
        ["git"] + list(args),
        cwd=self.repo_path,
        capture_output=True,
        text=True,
        timeout=30
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "returncode": result.returncode
    }

async def _handle_git(self, command: Command, message: Message) -> str:
    subcommand = command.args[0].lower()
    
    if subcommand == "status":
        return self.git_service.get_status()
    
    elif subcommand == "commitpush":
        # 一键提交并推送
        commit_message = " ".join(command.args[1:])
        
        # 先提交
        commit_result = self.git_service.commit(commit_message)
        if not commit_result.startswith("✅"):
            return commit_result
        
        # 再推送
        push_result = self.git_service.push()
        return f"{commit_result}\n\n{push_result}"
```

### 5.4 认证处理

```python
# app/services/git_service.py
def push(self) -> str:
    # 检查远程 URL 是否为 SSH 协议
    remote_result = self._run_git_command("remote", "-v")
    for line in remote_result["stdout"].split('\n'):
        if 'origin' in line and '(push)' in line:
            remote_url = line.split()[1]
            
            # 如果是 SSH 协议，自动切换为 HTTPS
            if remote_url.startswith('git@github.com:'):
                repo_path = remote_url.replace('git@github.com:', '')
                https_url = f"https://github.com/{repo_path}"
                self._run_git_command("remote", "set-url", "origin", https_url)
    
    # 执行推送
    result = self._run_git_command("push", "origin", "main")
    
    # 处理认证失败
    if "Authentication failed" in result["stderr"]:
        return "❌ GitHub 认证失败，请配置 GITHUB_TOKEN"
    
    return result["stdout"]
```

### 5.5 使用示例

```
/git status
/git commit 修复了登录bug
/git commitpush 添加了新功能
/git log 5
```

---

## 六、MCP 功能调用（/mcp）

### 6.1 MCP 架构

MCP（Model Context Protocol）是 LangChain 定义的工具调用协议。

```
┌──────────────────────┐
│      Agent Core      │
└──────────┬─────────┘
           │ 调用工具
           ▼
┌──────────────────────┐
│     MCP Manager      │
│  ┌────────────────┐  │
│  │ 模式判断逻辑   │  │
│  └────────┬───────┘  │
└───────────┼──────────┘
            │
    ┌───────┴───────┐
    ▼               ▼
┌─────────┐   ┌─────────┐
│ HTTP    │   │ MCP     │
│ 模式    │   │ 模式    │
└────┬────┘   └────┬────┘
     │             │
     ▼             ▼
┌─────────┐   ┌─────────────┐
│ DuckDuckGo│ │ MCP Server  │
│ HTTP API │   │ (ddg-mcp)  │
└─────────┘   └─────────────┘
```

### 6.2 模式切换机制

```python
# app/services/mcp_service.py
async def call_mcp_tool(self, server_name: str, tool_name: str, **kwargs) -> Optional[str]:
    server = self.servers.get(server_name)
    if not server:
        return None
    
    if tool_name == "search":
        # 根据配置的模式选择执行方式
        mode = server.mode.lower()
        
        if mode == "http":
            # HTTP 模式：直接调用 DuckDuckGo API
            return await self._call_search_http(**kwargs)
        elif mode == "mcp":
            # MCP 模式：通过 MCP 服务器调用
            return await self._call_search_mcp(server, **kwargs)
        else:
            return f"未知模式: {mode}"
```

### 6.3 HTTP 模式实现

```python
# app/services/mcp_service.py
async def _call_search_http(self, query: str) -> str:
    # 直接调用 DuckDuckGo 搜索 API
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "t": "maoge_agent",
        "region": "cn-zh"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
    
    if response.status_code == 200:
        results = response.json()
        # 解析搜索结果
        return self._format_search_results(results)
```

### 6.4 MCP 模式实现

```python
# app/services/mcp_service.py
async def _call_search_mcp(self, server, query: str) -> str:
    # 通过 MCP 服务器调用
    from langchain_mcp import MCPClient
    
    async with MCPClient(server.url) as client:
        result = await client.call_tool(
            tool_name="search",
            arguments={"query": query}
        )
    
    return result.content
```

### 6.5 配置文件

```json
// config/mcp_config.json
{
  "mcpServers": {
    "ddg-search": {
      "command": "duckduckgo-mcp-server",
      "args": ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8787"],
      "env": {
        "DDG_REGION": "cn-zh"
      },
      "mode": "http"  // 或 "mcp"
    }
  }
}
```

### 6.6 使用示例

```
/mcp                    # 显示可用工具
/mcp search AI最新动态  # DuckDuckGo搜索
/mcp search Python教程
```

---

## 七、完整请求流程图

### 7.1 命令处理流程

```
用户发送 /mcp search AI最新动态
        │
        ▼
┌──────────────────────┐
│ Telegram Adapter     │ 解析消息 → Message对象
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ Message Router       │ 判断消息类型 → COMMAND
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ Agent Core           │ 解析命令 → name="mcp", args=["search", "AI最新动态"]
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ _handle_mcp()        │ 识别工具名和参数
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ MCP Manager          │ 检查模式 → HTTP
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ DuckDuckGo HTTP API  │ 发送搜索请求
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ 格式化结果           │ 构建 Markdown 格式
└──────────┬─────────┘
           │
           ▼
┌──────────────────────┐
│ Telegram Adapter     │ 发送回复消息
└──────────────────────┘
```

### 7.2 关键组件职责

| 组件 | 职责 | 文件位置 |
|------|------|----------|
| **TelegramAdapter** | 处理 Telegram 消息的收发 | `app/adapters/telegram.py` |
| **MessageRouter** | 消息类型路由和分发 | `app/core/message_router.py` |
| **AgentCore** | 命令解析和服务调度 | `app/core/agent.py` |
| **RAGService** | 文档检索和问答 | `app/services/rag_service.py` |
| **CodeEditorService** | 代码分析和修改 | `app/services/code_editor_service.py` |
| **GitService** | Git 操作封装 | `app/services/git_service.py` |
| **MCPManager** | MCP 工具调用管理 | `app/services/mcp_service.py` |

---

## 八、启动流程

### 8.1 服务启动顺序

```
1. 加载环境变量 (.env)
2. 初始化各服务组件
3. 创建 Telegram Adapter
4. 启动 FastAPI 服务
5. 注册 Webhook 或启动 Polling
```

### 8.2 启动脚本

```bash
#!/bin/bash
# start_all.sh

# 激活虚拟环境
source venv/bin/activate

# 启动 FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
echo "FastAPI 服务已启动"

# 根据配置启动 MCP 服务器
if [ "$MODE" = "mcp" ]; then
    duckduckgo-mcp-server --transport streamable-http --host 0.0.0.0 --port 8787 &
    echo "DuckDuckGo MCP Server 已启动"
fi

# 启动文件系统 MCP
mcp-server-filesystem /path/to/project &
echo "Filesystem MCP Server 已启动"
```

---

## 九、配置说明

### 9.1 环境变量

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# 火山引擎
VOLC_API_KEY=your_api_key

# GitHub
GITHUB_TOKEN=your_github_token

# RAG
RAG_DOCS_PATH=data/documents

# MCP
MCP_CONFIG_PATH=config/mcp_config.json
```

### 9.2 MCP 配置

```json
{
  "mcpServers": {
    "ddg-search": {
      "command": "duckduckgo-mcp-server",
      "args": ["--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8787"],
      "env": {"DDG_REGION": "cn-zh"},
      "mode": "http"
    },
    "filesystem": {
      "command": "mcp-server-filesystem",
      "args": ["/path/to/project"]
    }
  }
}
```

---

## 十、安全注意事项

1. **环境变量保护**：不要将 `.env` 提交到版本控制
2. **Token 安全**：GitHub Token 具有仓库访问权限，妥善保管
3. **路径限制**：代码修改仅允许操作项目目录内的文件
4. **HTTPS**：生产环境使用 HTTPS 部署
5. **输入验证**：对用户输入进行适当的验证和过滤

---

**文档版本**: v1.0  
**生成日期**: 2026年6月  
**适用项目**: 聊天机器人 Agent
