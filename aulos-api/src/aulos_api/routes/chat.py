from fastapi import APIRouter
from pydantic import BaseModel, Field

from aulos_api.config import get_settings
from aulos_api.services import AgentProxy

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str = Field(default="default")


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    source: str


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
    settings = get_settings()
    proxy = AgentProxy(settings)
    result = await proxy.chat(body.message, body.thread_id)
    return ChatResponse(
        reply=result.reply,
        thread_id=result.thread_id,
        source=result.source,
    )
