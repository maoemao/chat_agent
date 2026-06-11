
# 聊天机器人Agent实现计划

## 1. 需求分析

用户需要创建一个聊天机器人agent，具备以下核心功能：

| 功能模块 | 描述 |
|---------|------|
| **通用聊天接入层** | **可复用的消息抽象层，支持多平台扩展，当前先实现Telegram** |
| RAG问答 | 基于markdown文档进行检索增强生成问答 |
| 火山Codeing Plan | 接入火山引擎Codeing Plan服务 |
| MCP功能调用 | 支持自定义MCP服务集成，可配置启用/禁用特定MCP |

## 2. 技术架构

### 2.1 整体架构

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Chat Adapter  │     │   RAG Engine    │     │  Codeing Plan   │     │    MCP Manager  │
│   (Telegram等)  │     │   文档问答层    │     │    接入层       │     │    MCP调用层    │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │                       │
         └───────────┬───────────┴───────────┬───────────┴───────────┬───────────┘
                     ▼                       ▼
              ┌───────────────┐      ┌───────────────┐
              │  Message      │      │    Config     │
              │   Abstraction │      │    Manager    │
              └───────────────┘      └───────────────┘
```

### 2.2 聊天接入层架构（适配器模式）

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Telegram Bot   │     │   Slack Bot     │     │   其他平台      │
│    Adapter      │     │    Adapter      │     │    Adapter      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────┬───────────┴───────────┬───────────┘
                     ▼
              ┌───────────────┐
              │  Message      │
              │    Router     │
              │ (统一接口)     │
              └───────┬───────┘
                      │
              ┌───────▼───────┐
              │   Agent Core  │
              │   (业务逻辑)   │
              └───────────────┘
```

### 2.3 技术栈

| 层级 | 技术 | 说明 |
|-----|------|------|
| 语言 | Python 3.10+ | 主流后端语言，生态丰富 |
| 框架 | FastAPI | 高性能异步API框架 |
| 数据库 | SQLite | 轻量级嵌入式数据库 |
| 消息队列 | Redis (可选) | 用于异步消息处理 |
| Telegram | python-telegram-bot | Telegram Bot官方SDK |
| RAG | LangChain | 流行的LLM应用框架 |
| 嵌入模型 | sentence-transformers | 文本嵌入模型 |
| 向量数据库 | FAISS | Facebook开源向量数据库 |
| MCP | HTTP Client | 通过HTTP调用MCP服务 |

## 3. 项目结构

```
maoge_agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # 主入口
│   ├── adapters/            # 聊天平台适配器（可扩展）
│   │   ├── __init__.py
│   │   ├── base.py          # 适配器基类/接口
│   │   ├── telegram.py      # Telegram适配器
│   │   └── slack.py         # Slack适配器（预留）
│   ├── routers/             # API路由
│   │   ├── __init__.py
│   │   └── webhook.py       # 统一Webhook入口
│   ├── services/            # 业务服务层
│   │   ├── __init__.py
│   │   ├── rag_service.py        # RAG问答服务
│   │   ├── codeing_plan_service.py # 火山Codeing Plan服务
│   │   └── mcp_service.py        # MCP调用服务
│   ├── core/                # 核心模块
│   │   ├── __init__.py
│   │   ├── message_router.py     # 消息路由器
│   │   ├── agent.py              # Agent核心逻辑
│   │   └── types.py              # 消息类型定义
│   ├── utils/               # 工具模块
│   │   ├── __init__.py
│   │   └── markdown_parser.py    # Markdown解析工具
│   └── config/              # 配置文件
│       ├── __init__.py
│       ├── settings.py      # 环境配置
│       └── mcp_config.py    # MCP服务配置
├── data/
│   └── documents/           # Markdown文档存储目录
├── tests/                   # 测试目录
├── requirements.txt         # 依赖列表
└── .env.example            # 环境变量模板
```

## 4. 功能模块设计

### 4.1 通用聊天接入层

**设计模式：适配器模式（Adapter Pattern）**

**适配器基类接口：**
```python
class ChatAdapter(ABC):
    @abstractmethod
    async def handle_webhook(self, request: Request) -> Response:
        pass
    
    @abstractmethod
    async def send_message(self, recipient: str, message: Message) -> None:
        pass
    
    @abstractmethod
    def parse_message(self, raw_data: dict) -> Message:
        pass
```

**消息类型定义：**
```python
class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    COMMAND = "command"

class Message(BaseModel):
    id: str
    type: MessageType
    content: str
    sender: str
    platform: str
    timestamp: datetime
```

**当前实现：Telegram适配器**

### 4.2 RAG问答模块

**功能：**
- 加载Markdown文档
- 文本向量化
- 相似性检索
- 生成回答

**关键类/函数：**
- `RAGService`: RAG服务类
- `load_documents`: 加载文档
- `build_vector_db`: 构建向量数据库
- `query`: 查询问答

### 4.3 火山Codeing Plan模块

**功能：**
- 接入火山引擎Codeing Plan API
- 代码规划生成
- 任务分解

**关键类/函数：**
- `CodeingPlanService`: Codeing Plan服务类
- `generate_plan`: 生成代码规划
- `execute_plan`: 执行规划

### 4.4 MCP功能调用模块

**功能：**
- MCP服务注册与管理
- 动态配置启用/禁用MCP服务
- MCP工具调用封装
- 请求签名与安全验证

**关键类/函数：**
- `MCPManager`: MCP管理器类
- `register_mcp_server`: 注册MCP服务器
- `call_mcp_tool`: 调用MCP工具
- `get_enabled_tools`: 获取已启用的工具列表

## 5. 配置与依赖

### 5.1 环境变量

| 变量名 | 说明 | 必填 |
|-------|------|------|
| TELEGRAM_BOT_TOKEN | Telegram Bot Token | 是 |
| VOLC_ACCESS_KEY | 火山引擎Access Key | 是 |
| VOLC_SECRET_KEY | 火山引擎Secret Key | 是 |
| RAG_DOCS_PATH | Markdown文档路径 | 否 |
| DATABASE_URL | 数据库连接URL | 否 |
| MCP_CONFIG_PATH | MCP配置文件路径 | 否 |
| ENABLED_ADAPTERS | 启用的适配器列表 | 否 |

### 5.2 依赖列表

```txt
fastapi==0.104.1
uvicorn==0.24.0
python-telegram-bot==20.7
python-dotenv==1.0.0
langchain==0.1.0
sentence-transformers==2.2.2
faiss-cpu==1.7.4
requests==2.31.0
sqlalchemy==2.0.23
pydantic==2.5.2
python-multipart==0.0.6
aiohttp==3.9.1
redis==5.0.1
```

## 6. 实施步骤

| 步骤 | 任务 | 预计时间 |
|-----|------|---------|
| 1 | 项目初始化，创建目录结构 | 1小时 |
| 2 | 安装依赖，配置环境变量 | 30分钟 |
| 3 | 实现核心消息类型和适配器基类 | 1.5小时 |
| 4 | 实现Telegram适配器 | 2小时 |
| 5 | 实现消息路由器和Agent核心 | 1.5小时 |
| 6 | 实现RAG问答模块 | 3小时 |
| 7 | 实现火山Codeing Plan模块 | 2小时 |
| 8 | 实现MCP功能调用模块 | 2小时 |
| 9 | 集成所有模块，编写主入口 | 2小时 |
| 10 | 测试与调试 | 2小时 |

## 7. 扩展性说明

### 7.1 添加新聊天平台

1. 创建新的适配器类继承`ChatAdapter`基类
2. 实现`handle_webhook`、`send_message`、`parse_message`方法
3. 在配置中启用新适配器

### 7.2 添加新功能模块

1. 创建新服务类
2. 在`AgentCore`中注册服务
3. 在消息路由器中添加路由规则

## 8. 风险与应对

| 风险 | 应对措施 |
|-----|---------|
| 消息延迟 | 增加消息队列机制（Redis） |
| RAG检索性能 | 使用FAISS索引优化 |
| API调用频率限制 | 添加请求节流 |
| 文档格式兼容性 | 增加文档格式校验 |
| MCP服务可用性 | 添加健康检查和重试机制 |
| 多平台适配复杂度 | 使用适配器模式统一接口 |

## 9. 部署建议

- 开发环境：本地运行
- 测试环境：Docker容器
- 生产环境：云服务器或Serverless

---

**计划状态**: 待审批
