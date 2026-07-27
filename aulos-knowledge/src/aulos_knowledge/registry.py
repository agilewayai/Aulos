"""Sync Authority Source Registry manifest (REG-SRC-001 / REQ-008)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from aulos_knowledge.db import SourceAuthority

logger = logging.getLogger("aulos_knowledge.registry")

VERIFICATION_STATUSES = frozenset({"candidate", "review", "verified", "rejected", "suspended"})
ORIGIN_CLASSES = frozenset({"encyclopedia", "identity_seed", "media", "editorial"})


def default_manifest_path() -> Path:
    # aulos_knowledge/seed.py → package → src → aulos-knowledge/
    here = Path(__file__).resolve()
    root = here.parents[2]  # aulos-knowledge/
    return root / "data" / "registry" / "sources.yaml"


def load_registry_manifest(path: Path | None = None) -> dict[str, Any]:
    p = path or default_manifest_path()
    if not p.is_file():
        logger.warning("registry_manifest_missing path=%s", p)
        return {"revision": "", "sources": [], "candidates": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"registry manifest must be a mapping: {p}")
    return data


def _apply_row_metadata(row: SourceAuthority, entry: dict[str, Any], *, revision: str, force: bool) -> None:
    row.name = str(entry.get("name") or row.name or row.id)
    row.tier = str(entry.get("tier") or row.tier or "A")
    row.connector = str(entry.get("connector") or "")
    row.base_urls_json = json.dumps(entry.get("base_urls") or [], ensure_ascii=False)
    row.license_class = str(entry.get("license_class") or row.license_class or "unknown")
    row.rate_limit_qps = float(entry.get("rate_limit_qps") or row.rate_limit_qps or 1.0)
    row.notes = str(entry.get("notes") or row.notes or "")
    row.tos_notes = str(entry.get("tos_notes") or row.tos_notes or "")
    row.attribution_template = str(entry.get("attribution_template") or row.attribution_template or "")
    row.allowed_path_prefixes_json = json.dumps(
        entry.get("allowed_path_prefixes") or json.loads(row.allowed_path_prefixes_json or "[]"),
        ensure_ascii=False,
    )
    row.connector_semver = str(entry.get("connector_semver") or row.connector_semver or "")
    origin = str(entry.get("origin_class") or row.origin_class or "encyclopedia")
    if origin in ORIGIN_CLASSES:
        row.origin_class = origin
    row.registry_revision = revision
    if force or not row.verification_status:
        status = str(entry.get("verification_status") or "candidate")
        if status in VERIFICATION_STATUSES:
            row.verification_status = status
        if "enabled" in entry:
            row.enabled = bool(entry["enabled"])


def sync_registry_manifest(
    db: Session,
    *,
    path: Path | None = None,
    sync_candidates: bool = True,
) -> dict[str, int]:
    """Upsert sources from YAML. Does not clobber verification/enabled unless force."""
    data = load_registry_manifest(path)
    revision = str(data.get("revision") or "")
    created = updated = 0

    for entry in list(data.get("sources") or []):
        if not isinstance(entry, dict) or not entry.get("id"):
            continue
        sid = str(entry["id"])
        force = bool(entry.get("force"))
        row = db.get(SourceAuthority, sid)
        if row is None:
            row = SourceAuthority(id=sid)
            status = str(entry.get("verification_status") or "candidate")
            row.verification_status = status if status in VERIFICATION_STATUSES else "candidate"
            row.enabled = bool(entry.get("enabled", False))
            _apply_row_metadata(row, entry, revision=revision, force=True)
            db.add(row)
            created += 1
        else:
            _apply_row_metadata(row, entry, revision=revision, force=force)
            updated += 1

    if sync_candidates:
        for entry in list(data.get("candidates") or []):
            if not isinstance(entry, dict) or not entry.get("id"):
                continue
            sid = str(entry["id"])
            row = db.get(SourceAuthority, sid)
            if row is not None:
                continue
            cand = {
                **entry,
                "verification_status": "candidate",
                "enabled": False,
                "tier": entry.get("tier") or "A",
                "origin_class": entry.get("origin_class") or "encyclopedia",
            }
            row = SourceAuthority(id=sid)
            _apply_row_metadata(row, cand, revision=revision, force=True)
            row.verification_status = "candidate"
            row.enabled = False
            db.add(row)
            created += 1

    db.commit()
    logger.info("registry_sync revision=%s created=%s updated=%s", revision, created, updated)
    return {"created": created, "updated": updated, "revision": revision}


def seed_default_sources(db: Session) -> int:
    """Backward-compatible entry used by app lifespan."""
    result = sync_registry_manifest(db)
    return int(result.get("created") or 0)
