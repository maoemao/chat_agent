from typing import Optional
from datetime import datetime
from fastapi import Request, Response

from app.adapters.base import ChatAdapter
from app.core.types import Message, ResponseMessage, MessageType, PlatformType

class SlackAdapter(ChatAdapter):
    def __init__(self):
        self.message_handler = None
    
    def get_platform(self) -> PlatformType:
        return PlatformType.SLACK
    
    def get_name(self) -> str:
        return "slack"
    
    def parse_message(self, raw_data: dict) -> Optional[Message]:
        try:
            event = raw_data.get('event', {})
            message_id = event.get('ts', '')
            sender = event.get('user', '')
            content = event.get('text', '')
            sender_name = event.get('username', '')
            
            if content.startswith('/'):
                msg_type = MessageType.COMMAND
            else:
                msg_type = MessageType.TEXT
            
            timestamp = datetime.fromtimestamp(float(message_id)) if message_id else datetime.now()
            
            return Message(
                id=message_id,
                type=msg_type,
                content=content,
                sender=sender,
                sender_name=sender_name,
                platform=PlatformType.SLACK,
                timestamp=timestamp
            )
        except Exception as e:
            return None
    
    async def handle_webhook(self, request: Request) -> Response:
        try:
            data = await request.json()
            if data.get('type') == 'url_verification':
                return Response(content=data.get('challenge', ''), status_code=200)
            
            message = self.parse_message(data)
            if message and self.message_handler:
                await self.message_handler(message)
            return Response(status_code=200)
        except Exception as e:
            return Response(status_code=500)
    
    async def send_message(self, recipient: str, message: ResponseMessage) -> None:
        pass
    
    def set_message_handler(self, handler):
        self.message_handler = handler