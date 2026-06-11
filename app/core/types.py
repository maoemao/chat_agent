from enum import Enum
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    COMMAND = "command"

class PlatformType(str, Enum):
    TELEGRAM = "telegram"
    SLACK = "slack"

class Message(BaseModel):
    id: str
    type: MessageType
    content: str
    sender: str
    sender_name: Optional[str] = None
    platform: PlatformType
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ResponseMessage(BaseModel):
    content: str
    platform: PlatformType
    recipient: str
    message_type: MessageType = MessageType.TEXT

class Command(BaseModel):
    name: str
    args: list = []
    raw: str

class AgentResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None