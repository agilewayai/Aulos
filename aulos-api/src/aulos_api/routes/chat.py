from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import get_current_user
from aulos_api.config import get_settings
from aulos_api.db.models import User
from aulos_api.db.session import get_db
from aulos_api.services import AgentProxy

router = APIRouter(prefix="/v1", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    thread_id: str = Field(default="default", max_length=120)


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    source: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    _user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Authenticated chat — unauthenticated LLM calls were an abuse sink."""
    settings = get_settings()
    proxy = AgentProxy(settings)
    result = await proxy.chat(body.message, body.thread_id, db=db)
    return ChatResponse(
        reply=result.reply,
        thread_id=result.thread_id,
        source=result.source,
    )
