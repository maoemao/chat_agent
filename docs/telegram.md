# Telegram 通讯机制

## 一、概述

Telegram Adapter 是项目与 Telegram 平台交互的核心组件，负责消息的接收和发送。支持两种运行模式：Webhook（生产环境）和 Polling（开发调试）。

## 二、架构位置

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
└─────────────────────────────────────────────────────────────────┘
```

## 三、两种运行模式对比

| 模式 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **Webhook** | 生产环境 | 实时响应、资源占用低 | 需要公网 HTTPS 地址 |
| **Polling** | 开发调试 | 无需公网、配置简单 | 轮询间隔延迟、资源占用高 |

## 四、Webhook 模式

### 4.1 工作流程

Webhook 模式下，Telegram 服务器会主动将消息推送到我们的服务端点。

### 4.2 核心代码

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
    
    # 4. 返回 200 响应（必须在5秒内返回）
    return Response(status_code=200)
```

### 4.3 设置 Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://your-domain.com/webhook/telegram"}'
```

### 4.4 取消 Webhook

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

## 五、Polling 模式

### 5.1 工作流程

Polling 模式下，服务定期向 Telegram 服务器请求新消息。

### 5.2 核心代码

```python
# app/adapters/telegram.py
async def start_polling(self):
    # 1. 创建 Telegram Application
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
    
    # 2. 注册消息处理器
    application.add_handler(MessageHandler(filters.ALL, handle_update))
    
    # 3. 启动轮询
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # 4. 持续运行
    while True:
        await asyncio.sleep(1)
```

## 六、消息解析流程

### 6.1 消息结构

Telegram 发送的原始消息数据结构：

```json
{
  "update_id": 123456789,
  "message": {
    "message_id": 123,
    "from": {
      "id": 123456789,
      "first_name": "张三",
      "username": "zhangsan"
    },
    "chat": {
      "id": 123456789,
      "type": "private"
    },
    "date": 1620000000,
    "text": "/rag 如何配置 MCP？"
  }
}
```

### 6.2 解析代码

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

## 七、消息发送流程

### 7.1 发送代码

```python
# app/adapters/telegram.py
async def send_message(self, recipient: str, message: ResponseMessage) -> None:
    # 1. 构造请求
    url = f"https://api.telegram.org/bot{self.token}/sendMessage"
    data = {
        "chat_id": int(recipient),
        "text": message.content,
        "parse_mode": "Markdown"  # 支持 Markdown 格式
    }
    
    # 2. 发送 HTTP 请求
    response = requests.post(url, data=data, timeout=30)
    
    # 3. 处理响应
    if response.status_code == 200:
        telegram_logger.info(f"Message sent successfully")
    else:
        telegram_logger.error(f"Failed to send message: {response.text}")
```

### 7.2 消息格式支持

| 格式 | 说明 | 示例 |
|------|------|------|
| **Text** | 纯文本 | `"Hello World"` |
| **Markdown** | Markdown 格式 | `"**粗体**"` |
| **HTML** | HTML 格式 | `"<b>粗体</b>"` |

## 八、适配器基类

TelegramAdapter 继承自 ChatAdapter 基类：

```python
# app/adapters/base.py
class ChatAdapter(ABC):
    @abstractmethod
    async def handle_webhook(self, request: Request) -> Response:
        pass
    
    @abstractmethod
    async def send_message(self, recipient: str, message: ResponseMessage) -> None:
        pass
    
    @abstractmethod
    def parse_message(self, raw_data: dict) -> Optional[Message]:
        pass
    
    @abstractmethod
    def get_platform(self) -> PlatformType:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass
```

## 九、配置说明

### 9.1 环境变量

```env
# Telegram 配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 9.2 启用适配器

在 `settings.py` 中配置：

```python
ENABLED_ADAPTERS = "telegram"  # 可配置多个，逗号分隔
```

## 十、完整请求流程

```
用户发送消息 → Telegram 服务器 → Webhook/Polling → TelegramAdapter → MessageRouter → AgentCore
                                                                                            │
←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
```

## 十一、代码位置

| 文件 | 说明 |
|------|------|
| `app/adapters/telegram.py` | Telegram 适配器实现 |
| `app/adapters/base.py` | 适配器基类定义 |
| `app/core/message_router.py` | 消息路由分发 |
