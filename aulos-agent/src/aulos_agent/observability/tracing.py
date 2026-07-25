"""Optional LangSmith / LangChain tracing bootstrap."""

from __future__ import annotations

import os

from aulos_agent.config.settings import Settings, get_settings


def configure_tracing(settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    if cfg.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = cfg.langchain_project
        if cfg.langsmith_api_key:
            os.environ["LANGSMITH_API_KEY"] = cfg.langsmith_api_key
