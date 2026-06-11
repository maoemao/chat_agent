from abc import ABC, abstractmethod
from typing import Optional
from fastapi import Request, Response
from app.core.types import Message, ResponseMessage, PlatformType

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