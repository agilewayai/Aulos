from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "aulos-knowledge"
    app_version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 5095
    db_url: str = "sqlite:///./data/knowledge.db"
    artifact_root: str = "./data/artifacts"
    admin_token: str = ""  # optional shared secret for direct admin; ops uses api proxy
    catalog_root: str = ""  # default: sibling aulos-skills catalog
    redis_url: str = "redis://127.0.0.1:6379/0"
    sync_jobs: bool = True  # run jobs in-process when True (dev)


@lru_cache
def get_settings() -> Settings:
    default_artifacts = str(Path(__file__).resolve().parents[2] / "data" / "persist" / "artifacts")
    return Settings(
        db_url=__import__("os").environ.get("AULOS_KNOWLEDGE_DB_URL", "sqlite:///./data/knowledge.db"),
        artifact_root=__import__("os").environ.get("AULOS_KNOWLEDGE_ARTIFACT_ROOT", default_artifacts),
        catalog_root=__import__("os").environ.get("AULOS_KNOWLEDGE_CATALOG_ROOT", ""),
        admin_token=__import__("os").environ.get("AULOS_KNOWLEDGE_ADMIN_TOKEN", ""),
        sync_jobs=__import__("os").environ.get("AULOS_KNOWLEDGE_SYNC_JOBS", "true").lower()
        in {"1", "true", "yes"},
    )
