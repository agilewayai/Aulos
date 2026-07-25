"""Ops helpers for aulos-skills domain packs."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import SystemSetting

SKILLS_DISABLED_KEY = "skills.disabled"


def _runtime():
    try:
        from aulos_skills.runtime import SkillRuntime
    except ImportError:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.runtime import SkillRuntime
    return SkillRuntime()


def _load_disabled(db: Session | None) -> set[str]:
    if db is None:
        return set()
    row = db.query(SystemSetting).filter(SystemSetting.key == SKILLS_DISABLED_KEY).one_or_none()
    if row is None or not row.value:
        return set()
    try:
        data = json.loads(row.value)
        return {str(x) for x in data} if isinstance(data, list) else set()
    except json.JSONDecodeError:
        return set()


def list_domain_skills(db: Session | None = None) -> list[dict[str, Any]]:
    runtime = _runtime()
    disabled = _load_disabled(db)
    rows = runtime.list_skills()
    for row in rows:
        row["enabled"] = row["id"] not in disabled
    domain = [r for r in rows if r["layer"] == "domain-runtime"]
    other = [r for r in rows if r["layer"] != "domain-runtime"]
    return domain + other


def set_skill_enabled(db: Session, skill_id: str, enabled: bool) -> dict[str, Any]:
    disabled = _load_disabled(db)
    if enabled:
        disabled.discard(skill_id)
    else:
        disabled.add(skill_id)
    payload = json.dumps(sorted(disabled))
    row = db.query(SystemSetting).filter(SystemSetting.key == SKILLS_DISABLED_KEY).one_or_none()
    if row is None:
        db.add(SystemSetting(key=SKILLS_DISABLED_KEY, value=payload))
    else:
        row.value = payload
    db.commit()
    runtime = _runtime()
    skill = runtime.skills.get(skill_id)
    if skill is None:
        raise KeyError(f"Unknown skill: {skill_id}")
    return {
        "id": skill.skill_id,
        "name": skill.name,
        "layer": skill.layer,
        "runtime": skill.runtime,
        "version": skill.version,
        "summary": skill.summary,
        "triggers": list(skill.triggers),
        "observability_title": skill.observability_title,
        "enabled": skill_id not in disabled,
    }


def run_skill_probe(message: str = "Bach Goldberg Variations", db: Session | None = None) -> dict[str, Any]:
    from aulos_skills.runtime import run_report_to_dict

    disabled = _load_disabled(db)
    report = _runtime().run_listening_chain(message=message, disabled_skill_ids=disabled)
    payload = run_report_to_dict(report)
    payload["guide_html_chars"] = len(payload.pop("guide_html", "") or "")
    return payload
