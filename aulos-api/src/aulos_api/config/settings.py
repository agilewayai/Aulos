from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    host: str = Field(default="0.0.0.0", alias="AULOS_API_HOST")
    port: int = Field(default=8000, alias="AULOS_API_PORT")
    cors_origins: str = Field(
        default=(
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:5174,http://127.0.0.1:5174,"
            "https://aulos.purezen.ai,https://aulos-ops.purezen.ai"
        ),
        alias="AULOS_API_CORS_ORIGINS",
    )
    agent_base_url: str = Field(default="", alias="AULOS_AGENT_BASE_URL")
    mcp_base_url: str = Field(default="", alias="AULOS_MCP_BASE_URL")
    fake_agent: bool = Field(default=True, alias="AULOS_API_FAKE_AGENT")

    db_url: str = Field(default="sqlite:///./data/aulos.db", alias="AULOS_DB_URL")
    # SQLite (or secondary) mirror for HA — kept in sync from primary
    db_failover_url: str = Field(default="", alias="AULOS_DB_FAILOVER_URL")
    db_active_role: str = Field(default="primary", alias="AULOS_DB_ACTIVE_ROLE")  # primary|failover
    db_sync_enabled: bool = Field(default=True, alias="AULOS_DB_SYNC_ENABLED")
    db_sync_interval_sec: int = Field(default=300, alias="AULOS_DB_SYNC_INTERVAL_SEC")
    db_auto_failover: bool = Field(default=True, alias="AULOS_DB_AUTO_FAILOVER")
    db_auto_failback: bool = Field(default=False, alias="AULOS_DB_AUTO_FAILBACK")
    redis_url: str = Field(default="redis://127.0.0.1:6379/0", alias="AULOS_REDIS_URL")
    db_sync_redis_url: str = Field(default="", alias="AULOS_DB_SYNC_REDIS_URL")  # empty → use redis_url

    jwt_secret: str = Field(default="dev-only-change-me", alias="AULOS_JWT_SECRET")
    jwt_expire_minutes: int = Field(default=60 * 24, alias="AULOS_JWT_EXPIRE_MINUTES")
    mail_provider: str = Field(default="auto", alias="AULOS_MAIL_PROVIDER")
    web_base_url: str = Field(default="http://127.0.0.1:5173", alias="AULOS_WEB_BASE_URL")
    verification_ttl_hours: int = Field(default=48, alias="AULOS_VERIFICATION_TTL_HOURS")
    bootstrap_superadmin_email: str = Field(
        default="",
        alias="AULOS_BOOTSTRAP_SUPERADMIN_EMAIL",
    )
    bootstrap_superadmin_password: str = Field(
        default="",
        alias="AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD",
    )
    rate_limit_enabled: bool = Field(default=True, alias="AULOS_RATE_LIMIT_ENABLED")
    trust_proxy: bool = Field(default=True, alias="AULOS_TRUST_PROXY")
    abuse_strike_limit: int = Field(default=8, alias="AULOS_ABUSE_STRIKE_LIMIT")
    abuse_strike_window_sec: int = Field(default=300, alias="AULOS_ABUSE_STRIKE_WINDOW_SEC")

    media_cache_dir: str = Field(default="data/media-cache", alias="AULOS_MEDIA_CACHE_DIR")

    # Professional music knowledge plane (aulos-knowledge) — separate from business DB
    knowledge_base_url: str = Field(
        default="http://127.0.0.1:5095",
        alias="AULOS_KNOWLEDGE_BASE_URL",
    )
    knowledge_plane_enabled: bool = Field(
        default=False,
        alias="AULOS_KNOWLEDGE_PLANE_ENABLED",
    )

    # Monorepo root for Ops daily dev-blog evidence (git + harness)
    repo_root: str = Field(default="", alias="AULOS_REPO_ROOT")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
