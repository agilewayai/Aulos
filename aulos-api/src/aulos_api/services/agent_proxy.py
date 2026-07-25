"""Proxy (or fake) adapter toward aulos-agent / aulos-mcp backends."""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from aulos_api.config import Settings


@dataclass
class ChatResult:
    reply: str
    thread_id: str
    source: str


class AgentProxy:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def chat(self, message: str, thread_id: str = "default") -> ChatResult:
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

    async def health_backends(self) -> dict[str, str]:
        status: dict[str, str] = {
            "agent": "fake" if self._settings.fake_agent or not self._settings.agent_base_url else "configured",
            "mcp": "unconfigured" if not self._settings.mcp_base_url else "configured",
        }
        return status
