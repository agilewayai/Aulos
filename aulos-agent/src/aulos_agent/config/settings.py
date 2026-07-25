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

    llm_provider: Literal["openai", "anthropic", "fake"] = Field(
        default="fake",
        alias="AULOS_LLM_PROVIDER",
    )
    llm_model: str = Field(default="gpt-4o-mini", alias="AULOS_LLM_MODEL")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")

    system_prompt: str = Field(
        default=(
            "You are Aulos, a helpful assistant. "
            "Use tools when they improve accuracy."
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
