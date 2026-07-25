"""Chat model factory for provider-agnostic LLM construction."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, PrivateAttr

from aulos_agent.config.settings import Settings, get_settings


class DeterministicFakeChatModel(BaseChatModel):
    """Minimal offline chat model for tests and local demos without API keys."""

    responses: list[str] = Field(default_factory=lambda: ["Hello from the fake Aulos model."])
    _call_count: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "deterministic-fake"

    def bind_tools(self, tools: Any, **kwargs: Any) -> DeterministicFakeChatModel:
        """Offline fake model ignores tool schemas but stays callable."""
        return self

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        idx = min(self._call_count, len(self.responses) - 1)
        text = self.responses[idx]
        self._call_count += 1
        message = AIMessage(content=text)
        return ChatResult(generations=[ChatGeneration(message=message)])


def create_chat_model(settings: Settings | None = None) -> BaseChatModel:
    cfg = settings or get_settings()

    if cfg.llm_provider == "fake":
        return DeterministicFakeChatModel()

    if cfg.llm_provider == "openai":
        cfg.require_live_credentials()
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=cfg.llm_model, api_key=cfg.openai_api_key)

    if cfg.llm_provider == "deepseek":
        cfg.require_live_credentials()
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=cfg.llm_model or "deepseek-chat",
            api_key=cfg.deepseek_api_key,
            base_url=cfg.deepseek_base_url,
        )

    if cfg.llm_provider == "grok":
        cfg.require_live_credentials()
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=cfg.llm_model or "grok-3-mini",
            api_key=cfg.grok_api_key,
            base_url=cfg.grok_base_url,
        )

    if cfg.llm_provider == "anthropic":
        cfg.require_live_credentials()
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:  # pragma: no cover - optional extra
            raise ImportError(
                "Install anthropic support with: pip install 'aulos-agent[anthropic]'"
            ) from exc
        return ChatAnthropic(model=cfg.llm_model, api_key=cfg.anthropic_api_key)

    raise ValueError(f"Unsupported LLM provider: {cfg.llm_provider}")
