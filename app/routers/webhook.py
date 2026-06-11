from fastapi import APIRouter, Request, Response

router = APIRouter()

agent_instance = None

def set_agent(agent):
    global agent_instance
    agent_instance = agent

@router.post("/webhook/{platform}")
async def webhook(request: Request, platform: str):
    if agent_instance:
        adapter = agent_instance.message_router.get_adapter(platform)
        if adapter:
            return await adapter.handle_webhook(request)
        return Response(status_code=404, content="Platform not found")
    return Response(status_code=500, content="Agent not initialized")

@router.get("/health")
async def health_check():
    return {"status": "healthy"}