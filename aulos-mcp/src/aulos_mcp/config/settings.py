from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    transport: str = Field(default="stdio", alias="AULOS_MCP_TRANSPORT")
    server_name: str = Field(default="aulos-mcp", alias="AULOS_MCP_SERVER_NAME")
    api_base_url: str = Field(
        default="http://127.0.0.1:8000",
        alias="AULOS_API_BASE_URL",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
