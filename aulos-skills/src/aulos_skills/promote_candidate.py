"""PromoteCandidate dry-run — unknown survivors → Catalog/craft draft (SPEC-029)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from aulos_skills.chamber_contracts import REQUIRED_EN, _lenish
from aulos_skills.salon_codex import coerce_dict

SCHEMA = "aulos.promote_candidate/v1"


def _slug_token(text: str) -> str:
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", "-", t)
    return t.strip("-")


def suggest_work_id(composer: str, work_title: str) -> str:
    """Heuristic Catalog-style id — dry-run only, never written to production."""
    name = (composer or "").strip()
    title = (work_title or "").strip()
    if name and title.lower().startswith(name.lower()):
        title = title[len(name) :].lstrip(" —–-")
    # Prefer last-name token for composer slug
    parts = [p for p in re.split(r"\s+", name) if p]
    composer_slug = _slug_token(parts[-1] if parts else name) or "unknown"
    # Drop leading articles / keep distinctive tokens
    title_slug = _slug_token(title)
    for drop in ("the-", "a-", "an-"):
        if title_slug.startswith(drop):
            title_slug = title_slug[len(drop) :]
    title_slug = title_slug[:48].strip("-") or "work"
    return f"{composer_slug}.{title_slug}"


def chamber_floor_ok(dossier: dict[str, Any]) -> bool:
    d = dict(dossier or {})
    for key, minimum in REQUIRED_EN:
        if _lenish(d.get(key)) < minimum:
            return False
    zh = coerce_dict(d.get("zh") or d.get("zh_hans"))
    return bool(str(zh.get("listening_thesis") or "").strip())


def build_promote_candidate(
    *,
    work_title: str,
    composer: str,
    classification: dict[str, Any] | None = None,
    dossier: dict[str, Any] | None = None,
    locked_composer: str | None = None,
    allow: bool = True,
) -> dict[str, Any] | None:
    """Emit promote_candidate JSON when unknown-path dossier meets chamber floors.

    Always dry_run=true — v1 never writes production Catalog/craft assets.
    SPEC-032: refuse when allow=False or locked composer drifts from dossier/name.
    """
    from aulos_skills.text_match import composers_compatible

    if not allow:
        return None
    title = (work_title or "").strip()
    name = (composer or "").strip()
    if not title or not name:
        return None
    d = dict(dossier or {})
    dossier_composer = str(d.get("composer") or name).strip()
    locked = (locked_composer or "").strip()
    if locked and not (
        composers_compatible(locked, name) and composers_compatible(locked, dossier_composer)
    ):
        return None
    if not chamber_floor_ok(d):
        return None

    clf = dict(classification or {})
    family_id = (
        str(clf.get("archetype_id") or "")
        or str(d.get("family_id") or "")
        or "chamber-generic"
    )
    zh = coerce_dict(d.get("zh") or d.get("zh_hans"))
    # Prefer locked composer for suggested id when present (anti poison-slug).
    id_composer = locked or name
    suggested = suggest_work_id(id_composer, title)
    return {
        "schema": SCHEMA,
        "dry_run": True,
        "suggested_work_id": suggested,
        "family_id": family_id,
        "facets": {
            "instruments": list(clf.get("instruments") or []),
            "forms": list(clf.get("forms") or []),
            "era": str(clf.get("era") or ""),
        },
        "craft_draft": {
            "listening_thesis": str(d.get("listening_thesis") or ""),
            "listening_map": list(d.get("listening_map") or []),
            "zh": {
                "listening_thesis": str(zh.get("listening_thesis") or ""),
                "listening_map": list(zh.get("listening_map") or []),
            },
        },
        "gates": {
            "chamber_floor": True,
            "identity_composer_title": True,
            "facet_confidence": float(clf.get("confidence") or 0.0),
            "intent_lock_composer": bool(locked),
        },
    }
