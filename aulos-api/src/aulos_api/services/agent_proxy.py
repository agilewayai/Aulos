"""Proxy (or in-process) adapter toward aulos-agent listening / chat backends."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from aulos_api.config import Settings
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config


@dataclass
class ChatResult:
    reply: str
    thread_id: str
    source: str


@dataclass
class ListeningProxyReport:
    """Mirrors aulos_agent.listening.ListeningAgentReport for API persistence."""

    steps: list[dict[str, Any]]
    guide_html: str
    summary: str
    work_title: str
    composer: str
    eval_pass: bool
    eval_score: int
    skill_versions: dict[str, str]
    context: dict[str, Any]
    source: str = "agent-skills"


def _ensure_aulos_agent_importable() -> None:
    try:
        import aulos_agent  # noqa: F401
        return
    except ImportError:
        pass
    sibling = Path(__file__).resolve().parents[4] / "aulos-agent" / "src"
    skills = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
    for path in (sibling, skills):
        if path.is_dir() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


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

    def run_listening(
        self,
        *,
        message: str,
        work_hint: str | None = None,
        llm_enrichment: str | None = None,
        llm_dossier: dict[str, Any] | None = None,
        kb_dossier: dict[str, Any] | None = None,
        rag_hits: list[str] | None = None,
        rag_mode: str | None = None,
        disabled_skill_ids: list[str] | set[str] | None = None,
        on_step: Any = None,
    ) -> ListeningProxyReport:
        """Delegate 导赏 to aulos-agent (HTTP when configured, else in-process)."""
        use_http = bool(self._settings.agent_base_url) and not self._settings.fake_agent
        if use_http:
            return self._run_listening_http(
                message=message,
                work_hint=work_hint,
                llm_enrichment=llm_enrichment,
                llm_dossier=llm_dossier,
                kb_dossier=kb_dossier,
                rag_hits=rag_hits,
                rag_mode=rag_mode,
                disabled_skill_ids=list(disabled_skill_ids or []),
            )
        return self._run_listening_inprocess(
            message=message,
            work_hint=work_hint,
            llm_enrichment=llm_enrichment,
            llm_dossier=llm_dossier,
            kb_dossier=kb_dossier,
            rag_hits=rag_hits,
            rag_mode=rag_mode,
            disabled_skill_ids=disabled_skill_ids,
            on_step=on_step,
        )

    def _run_listening_inprocess(
        self,
        *,
        message: str,
        work_hint: str | None,
        llm_enrichment: str | None,
        llm_dossier: dict[str, Any] | None,
        kb_dossier: dict[str, Any] | None,
        rag_hits: list[str] | None,
        rag_mode: str | None,
        disabled_skill_ids: list[str] | set[str] | None,
        on_step: Any,
    ) -> ListeningProxyReport:
        _ensure_aulos_agent_importable()
        from aulos_agent.listening.service import run_listening_via_agent

        report = run_listening_via_agent(
            message=message,
            work_hint=work_hint,
            llm_enrichment=llm_enrichment,
            llm_dossier=llm_dossier,
            kb_dossier=kb_dossier,
            rag_hits=rag_hits,
            rag_mode=rag_mode,
            disabled_skill_ids=disabled_skill_ids,
            on_step=on_step,
        )
        return ListeningProxyReport(
            steps=list(report.steps),
            guide_html=report.guide_html,
            summary=report.summary,
            work_title=report.work_title,
            composer=report.composer,
            eval_pass=report.eval_pass,
            eval_score=report.eval_score,
            skill_versions=dict(report.skill_versions),
            context=dict(report.context),
            source=report.source,
        )

    def _run_listening_http(
        self,
        *,
        message: str,
        work_hint: str | None,
        llm_enrichment: str | None,
        llm_dossier: dict[str, Any] | None,
        kb_dossier: dict[str, Any] | None,
        rag_hits: list[str] | None,
        rag_mode: str | None,
        disabled_skill_ids: list[str],
    ) -> ListeningProxyReport:
        url = f"{self._settings.agent_base_url.rstrip('/')}/v1/listening/run"
        with httpx.Client(timeout=180.0) as client:
            response = client.post(
                url,
                json={
                    "message": message,
                    "work_hint": work_hint,
                    "llm_enrichment": llm_enrichment,
                    "llm_dossier": llm_dossier or {},
                    "kb_dossier": kb_dossier or {},
                    "rag_hits": rag_hits or [],
                    "rag_mode": rag_mode or "",
                    "disabled_skill_ids": disabled_skill_ids,
                },
            )
            response.raise_for_status()
            data = response.json()
        return ListeningProxyReport(
            steps=list(data.get("steps") or []),
            guide_html=str(data.get("guide_html") or ""),
            summary=str(data.get("summary") or ""),
            work_title=str(data.get("work_title") or ""),
            composer=str(data.get("composer") or ""),
            eval_pass=bool(data.get("eval_pass", True)),
            eval_score=int(data.get("eval_score") or 0),
            skill_versions=dict(data.get("skill_versions") or {}),
            context=dict(data.get("context") or {}),
            source=str(data.get("source") or "agent-skills"),
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
