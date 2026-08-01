"""OPS switch for listening Intent Critic LLM layer (SPEC-018)."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from aulos_api.db.models import SystemSetting

LISTENING_REVIEW_SETTING_KEY = "listening.review_llm"


def load_review_llm_enabled(db: Session) -> bool:
    """Default True — deterministic Critic always runs; flag gates LLM completer attach."""
    row = db.query(SystemSetting).filter(SystemSetting.key == LISTENING_REVIEW_SETTING_KEY).one_or_none()
    if row is None:
        return True
    try:
        data = json.loads(row.value or "{}")
    except json.JSONDecodeError:
        return True
    if isinstance(data, bool):
        return data
    if isinstance(data, dict) and "enabled" in data:
        return bool(data.get("enabled"))
    return True


def save_review_llm_enabled(db: Session, *, enabled: bool) -> bool:
    payload = json.dumps({"enabled": bool(enabled)})
    row = db.query(SystemSetting).filter(SystemSetting.key == LISTENING_REVIEW_SETTING_KEY).one_or_none()
    if row is None:
        db.add(SystemSetting(key=LISTENING_REVIEW_SETTING_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    return bool(enabled)


def public_review_config(db: Session) -> dict:
    return {
        "key": LISTENING_REVIEW_SETTING_KEY,
        "enabled": load_review_llm_enabled(db),
    }
