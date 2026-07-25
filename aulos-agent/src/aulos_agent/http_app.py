"""Optional HTTP surface for aulos-agent listening jobs."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from aulos_agent.listening.service import run_listening_via_agent


class ListeningRunRequest(BaseModel):
    message: str = Field(min_length=1)
    work_hint: str | None = None
    llm_enrichment: str | None = None
    llm_dossier: dict[str, Any] | None = None
    kb_dossier: dict[str, Any] | None = None
    rag_hits: list[str] | None = None
    rag_mode: str | None = None
    disabled_skill_ids: list[str] | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="aulos-agent", version="0.2.0")

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "aulos-agent"}

    @app.post("/v1/listening/run")
    def listening_run(body: ListeningRunRequest) -> dict[str, Any]:
        report = run_listening_via_agent(
            message=body.message,
            work_hint=body.work_hint,
            llm_enrichment=body.llm_enrichment,
            llm_dossier=body.llm_dossier,
            kb_dossier=body.kb_dossier,
            rag_hits=body.rag_hits,
            rag_mode=body.rag_mode,
            disabled_skill_ids=body.disabled_skill_ids,
        )
        return report.to_dict()

    return app


app = create_app()
