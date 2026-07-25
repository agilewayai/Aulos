from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    skills_root: str = Field(default="", alias="AULOS_SKILLS_ROOT")
    include_bundled: bool = Field(default=True, alias="AULOS_SKILLS_INCLUDE_BUNDLED")

    def resolved_roots(self, package_root: Path) -> list[Path]:
        roots: list[Path] = []
        if self.include_bundled:
            # Prefer workspace skills/ next to package; fall back to installed bundle.
            workspace = package_root / "skills"
            bundled = Path(__file__).resolve().parent / "bundled_skills"
            if workspace.is_dir():
                roots.append(workspace)
            elif bundled.is_dir():
                roots.append(bundled)
        if self.skills_root:
            roots.append(Path(self.skills_root).expanduser().resolve())
        return roots


@lru_cache
def get_settings() -> Settings:
    return Settings()
