"""Proxy (or fake) adapter toward aulos-agent / ops-managed LLM backends."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from aulos_api.config import Settings
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config


@dataclass
class ChatResult:
    reply: str
    thread_id: str
    source: str


class AgentProxy:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def chat(
        self,
        message: str,
        thread_id: str = "default",
        db: Session | None = None,
    ) -> ChatResult:
        if db is not None:
            live = await chat_with_ops_llm(db=db, message=message)
            if live is not None:
                reply, provider = live
                return ChatResult(reply=reply, thread_id=thread_id, source=provider)

        if self._settings.fake_agent or not self._settings.agent_base_url:
            return ChatResult(
                reply=f"[aulos-api fake] received: {message}",
                thread_id=thread_id,
                source="fake",
            )

        url = f"{self._settings.agent_base_url.rstrip('/')}/v1/chat"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json={"message": message, "thread_id": thread_id},
            )
            response.raise_for_status()
            data = response.json()
        return ChatResult(
            reply=str(data.get("reply", "")),
            thread_id=str(data.get("thread_id", thread_id)),
            source="agent",
        )

    async def health_backends(self, db: Session | None = None) -> dict[str, str]:
        llm_mode = "unconfigured"
        if db is not None:
            cfg = load_llm_config(db)
            if cfg.active_provider == "fake":
                llm_mode = "fake"
            elif cfg.ready_for_live:
                llm_mode = cfg.active_provider
            else:
                llm_mode = f"{cfg.active_provider}_incomplete"
        status: dict[str, str] = {
            "agent": "fake" if self._settings.fake_agent or not self._settings.agent_base_url else "configured",
            "mcp": "unconfigured" if not self._settings.mcp_base_url else "configured",
            "llm": llm_mode,
        }
        return status
