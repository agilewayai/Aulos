"""OPS switch for ambient video fallback mode (SPEC-006 / REQ-005)."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from aulos_api.db.models import SystemSetting

LISTENING_AMBIENT_FALLBACK_KEY = "listening.ambient_fallback_mode"
VALID_MODES = frozenset({"embed", "stream"})
DEFAULT_MODE = "embed"


def normalize_ambient_fallback_mode(raw: object) -> str:
    mode = str(raw or DEFAULT_MODE).strip().lower()
    return mode if mode in VALID_MODES else DEFAULT_MODE


def load_ambient_fallback_mode(db: Session) -> str:
    """Default embed — compliance-first official iframe."""
    row = (
        db.query(SystemSetting)
        .filter(SystemSetting.key == LISTENING_AMBIENT_FALLBACK_KEY)
        .one_or_none()
    )
    if row is None:
        return DEFAULT_MODE
    try:
        data = json.loads(row.value or "{}")
    except json.JSONDecodeError:
        return normalize_ambient_fallback_mode(row.value)
    if isinstance(data, str):
        return normalize_ambient_fallback_mode(data)
    if isinstance(data, dict) and "mode" in data:
        return normalize_ambient_fallback_mode(data.get("mode"))
    return DEFAULT_MODE


def save_ambient_fallback_mode(db: Session, *, mode: str) -> str:
    normalized = normalize_ambient_fallback_mode(mode)
    payload = json.dumps({"mode": normalized})
    row = (
        db.query(SystemSetting)
        .filter(SystemSetting.key == LISTENING_AMBIENT_FALLBACK_KEY)
        .one_or_none()
    )
    if row is None:
        db.add(SystemSetting(key=LISTENING_AMBIENT_FALLBACK_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    return normalized


def public_ambient_fallback_config(db: Session) -> dict:
    return {
        "key": LISTENING_AMBIENT_FALLBACK_KEY,
        "mode": load_ambient_fallback_mode(db),
        "allowed": sorted(VALID_MODES),
    }
