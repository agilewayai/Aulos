from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="0.0.0.0", alias="AULOS_API_HOST")
    port: int = Field(default=8000, alias="AULOS_API_PORT")
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="AULOS_API_CORS_ORIGINS",
    )
    agent_base_url: str = Field(default="", alias="AULOS_AGENT_BASE_URL")
    mcp_base_url: str = Field(default="", alias="AULOS_MCP_BASE_URL")
    fake_agent: bool = Field(default=True, alias="AULOS_API_FAKE_AGENT")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
