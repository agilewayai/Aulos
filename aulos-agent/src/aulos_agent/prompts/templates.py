"""Prompt templates for the agent graph."""

from langchain_core.messages import SystemMessage

from aulos_agent.config.settings import Settings, get_settings


def build_system_message(settings: Settings | None = None) -> SystemMessage:
    cfg = settings or get_settings()
    return SystemMessage(content=cfg.system_prompt)
