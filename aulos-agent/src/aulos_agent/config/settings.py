"""Typed runtime settings for aulos-agent."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: Literal["openai", "anthropic", "deepseek", "grok", "fake"] = Field(
        default="fake",
        alias="AULOS_LLM_PROVIDER",
    )
    llm_model: str = Field(default="gpt-4o-mini", alias="AULOS_LLM_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        alias="DEEPSEEK_BASE_URL",
    )
    grok_api_key: str | None = Field(default=None, alias="XAI_API_KEY")
    grok_base_url: str = Field(default="https://api.x.ai/v1", alias="XAI_BASE_URL")

    system_prompt: str = Field(
        default=(
            "You are Aulos, a powerful classical-art and deep-listening agent. "
            "When a listener names a masterwork they are learning, research it with "
            "breadth (history, reception, context) and depth (form, ear cues, practice), "
            "and help them listen more attentively. Use tools when they improve accuracy."
        ),
        alias="AULOS_SYSTEM_PROMPT",
    )
    recursion_limit: int = Field(default=25, alias="AULOS_RECURSION_LIMIT")

    langchain_tracing_v2: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    langchain_project: str = Field(default="aulos-agent", alias="LANGCHAIN_PROJECT")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")

    def require_live_credentials(self) -> None:
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when AULOS_LLM_PROVIDER=openai")
        if self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is required when AULOS_LLM_PROVIDER=anthropic"
            )
        if self.llm_provider == "deepseek" and not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required when AULOS_LLM_PROVIDER=deepseek")
        if self.llm_provider == "grok" and not self.grok_api_key:
            raise ValueError("XAI_API_KEY is required when AULOS_LLM_PROVIDER=grok")


@lru_cache
def get_settings() -> Settings:
    return Settings()
