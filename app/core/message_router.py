from typing import Dict, Callable, Optional, List
from app.core.types import Message, MessageType, ResponseMessage
from app.adapters.base import ChatAdapter
from app.utils.logger import router_logger

class MessageRouter:
    def __init__(self):
        self.adapters: Dict[str, ChatAdapter] = {}
        self.handlers: Dict[MessageType, List[Callable]] = {}
        router_logger.info("MessageRouter initialized")
    
    def register_adapter(self, adapter: ChatAdapter):
        adapter_name = adapter.get_name()
        router_logger.info(f"Registering adapter: {adapter_name}")
        self.adapters[adapter_name] = adapter
        adapter.set_message_handler(self.handle_message)
        router_logger.debug(f"Adapter {adapter_name} registered successfully")
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
        router_logger.debug(f"Registered handler for message type: {message_type}")
    
    async def handle_message(self, message: Message):
        router_logger.info(f"Handling message: id={message.id}, type={message.type}, platform={message.platform}, sender={message.sender_name}")
        
        handlers = self.handlers.get(message.type, [])
        if not handlers:
            router_logger.debug(f"No handlers for type {message.type}, falling back to TEXT handlers")
            handlers = self.handlers.get(MessageType.TEXT, [])
        
        if not handlers:
            router_logger.warning(f"No handlers found for message type {message.type}")
            return
        
        for handler in handlers:
            try:
                router_logger.debug(f"Calling handler {handler.__name__} for message {message.id}")
                response = await handler(message)
                if response:
                    router_logger.debug(f"Handler {handler.__name__} returned response, sending to {message.platform}")
                    await self.send_response(message.sender, message.platform, response)
                else:
                    router_logger.debug(f"Handler {handler.__name__} returned no response")
            except Exception as e:
                router_logger.error(f"Error in handler {handler.__name__}: {str(e)}", exc_info=True)
    
    async def send_response(self, recipient: str, platform: str, content: str):
        router_logger.debug(f"Sending response to {recipient} via {platform}: {content[:100]}")
        adapter = self.adapters.get(platform)
        if adapter:
            response_message = ResponseMessage(
                content=content,
                platform=platform,
                recipient=recipient
            )
            await adapter.send_message(recipient, response_message)
            router_logger.info(f"Response sent successfully to {recipient} via {platform}")
        else:
            router_logger.error(f"No adapter found for platform: {platform}")
    
    def get_adapter(self, name: str) -> Optional[ChatAdapter]:
        adapter = self.adapters.get(name)
        if adapter:
            router_logger.debug(f"Found adapter: {name}")
        else:
            router_logger.warning(f"Adapter not found: {name}")
        return adapter