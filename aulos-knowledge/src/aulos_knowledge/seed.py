"""Legacy seed entry — delegates to Authority Source Registry sync."""

from __future__ import annotations

from sqlalchemy.orm import Session

from aulos_knowledge.registry import seed_default_sources as seed_default_sources

__all__ = ["seed_default_sources"]
