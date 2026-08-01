"""Stable public share slug helper (listening guide + diary)."""

from __future__ import annotations

import secrets


def new_share_slug(*, length: int = 16) -> str:
    """URL-safe slug without `-`/`_`; length capped for VARCHAR(64) columns."""
    return secrets.token_urlsafe(12).replace("-", "").replace("_", "")[:length]
