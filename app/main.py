from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.webhook import router, set_agent
from app.adapters.telegram import TelegramAdapter
from app.core.agent import AgentCore
from app.config.settings import settings
from app.utils.logger import telegram_logger

app = FastAPI(title="Chatbot Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

agent = AgentCore()
set_agent(agent)

enabled_adapters = settings.ENABLED_ADAPTERS.split(',')

telegram_adapter = None

if 'telegram' in enabled_adapters:
    telegram_adapter = TelegramAdapter()
    agent.register_adapter(telegram_adapter)
    telegram_logger.info("Telegram adapter initialized")

@app.on_event("startup")
async def startup_event():
    telegram_logger.info("Application started")
    if telegram_adapter:
        import asyncio
        asyncio.create_task(telegram_adapter.start_polling())

@app.on_event("shutdown")
async def shutdown_event():
    telegram_logger.info("Application shutting down")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)