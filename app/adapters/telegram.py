import json
import asyncio
from typing import Optional
from datetime import datetime
from fastapi import Request, Response
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from app.adapters.base import ChatAdapter
from app.core.types import Message, ResponseMessage, MessageType, PlatformType
from app.config.settings import settings
from app.utils.logger import telegram_logger

class TelegramAdapter(ChatAdapter):
    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.token)
        self.message_handler = None
        telegram_logger.info("TelegramAdapter initialized")
    
    def get_platform(self) -> PlatformType:
        return PlatformType.TELEGRAM
    
    def get_name(self) -> str:
        return "telegram"
    
    def parse_message(self, raw_data: dict) -> Optional[Message]:
        try:
            telegram_logger.debug(f"Parsing raw telegram data: {json.dumps(raw_data, ensure_ascii=False)[:500]}")
            
            message_data = raw_data.get('message', {})
            if not message_data:
                telegram_logger.warning("No message found in update")
                return None
            
            message_id = str(message_data.get('message_id', ''))
            chat = message_data.get('chat', {})
            chat_id = str(chat.get('id', ''))
            sender_name = chat.get('first_name', chat.get('username', 'Unknown'))
            
            from_user = message_data.get('from', {})
            if from_user:
                sender_name = from_user.get('first_name', from_user.get('username', sender_name))
            
            content = message_data.get('text', '')
            if content:
                msg_type = MessageType.COMMAND if content.startswith('/') else MessageType.TEXT
            elif message_data.get('document'):
                content = message_data['document'].get('file_name', 'Document')
                msg_type = MessageType.DOCUMENT
            elif message_data.get('photo'):
                content = "Photo"
                msg_type = MessageType.IMAGE
            else:
                content = str(message_data)
                msg_type = MessageType.TEXT
            
            date = message_data.get('date', datetime.now().timestamp())
            timestamp = datetime.fromtimestamp(date)
            
            message = Message(
                id=message_id,
                type=msg_type,
                content=content,
                sender=chat_id,
                sender_name=sender_name,
                platform=PlatformType.TELEGRAM,
                timestamp=timestamp
            )
            telegram_logger.info(f"Parsed message: id={message_id}, chat_id={chat_id}, sender={sender_name}, type={msg_type}, content={content[:100]}")
            return message
        except Exception as e:
            telegram_logger.error(f"Failed to parse message: {str(e)}", exc_info=True)
            return None
    
    async def handle_webhook(self, request: Request) -> Response:
        try:
            data = await request.json()
            telegram_logger.info(f"Received webhook request from Telegram")
            message = self.parse_message(data)
            if message and self.message_handler:
                telegram_logger.debug(f"Calling message handler for message: {message.id}")
                await self.message_handler(message)
            return Response(status_code=200)
        except Exception as e:
            telegram_logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
            return Response(status_code=500)
    
    async def send_message(self, recipient: str, message: ResponseMessage) -> None:
        try:
            chat_id = int(recipient)
            telegram_logger.info(f"Sending message to chat {chat_id}: {message.content[:100]}")
            
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message.content
            }
            
            response = requests.post(url, data=data, timeout=30)
            if response.status_code == 200:
                telegram_logger.info(f"Message sent successfully to chat {chat_id}")
            else:
                error_msg = response.json().get("description", f"HTTP {response.status_code}")
                telegram_logger.error(f"Failed to send message: {error_msg}")
            
        except Exception as e:
            telegram_logger.error(f"Failed to send message to chat {recipient}: {str(e)}", exc_info=True)
    
    def set_message_handler(self, handler):
        self.message_handler = handler
        telegram_logger.debug("Message handler set")
    
    async def start_polling(self):
        """启动Telegram轮询模式接收消息"""
        telegram_logger.info("Initializing Telegram application for polling...")
        
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                telegram_logger.info(f"Polling attempt {attempt + 1}/{max_retries}")
                
                application = (
                    Application.builder()
                    .token(settings.TELEGRAM_BOT_TOKEN)
                    .build()
                )
                
                async def handle_update(update: Update, context):
                    """处理接收到的更新"""
                    if update.message:
                        telegram_logger.info(f"Received message via polling: {update.message.text}")
                        raw_data = update.to_dict()
                        message = self.parse_message(raw_data)
                        if message and self.message_handler:
                            await self.message_handler(message)
                
                application.add_handler(MessageHandler(filters.ALL, handle_update))
                
                await application.initialize()
                await application.start()
                await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
                
                telegram_logger.info("Telegram polling started successfully, waiting for messages...")
                
                while True:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                telegram_logger.error(f"Polling error (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    telegram_logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)
                else:
                    telegram_logger.error("Max retries reached, stopping polling")
                    break
            finally:
                try:
                    await application.stop()
                    await application.shutdown()
                except:
                    pass
        
        telegram_logger.info("Telegram polling stopped")