"""Explore seed network — A–Z composers with famous badges and portraits (REQ-009 / META-001 §3.4)."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.db import ComposerEntity, MediaAsset
from aulos_knowledge.famous_composers import (
    FEATURED_COMPOSER_IDS,
    FAMOUS_COMPOSERS,
    famous_by_id,
)
from aulos_knowledge.jobs import enqueue_and_maybe_run as enqueue_fetch_job
from aulos_knowledge.source_discovery import _source_crawlable

logger = logging.getLogger("aulos_knowledge.explore_seeds")


def _portrait_for_entity(db: Session, entity_id: str) -> dict[str, Any] | None:
    row = (
        db.query(MediaAsset)
        .filter(MediaAsset.entity_id == entity_id, MediaAsset.kind == "image")
        .order_by(MediaAsset.id.desc())
        .first()
    )
    if not row:
        return None
    return {
        "media_id": row.id,
        "title": row.title,
        "content_type": row.content_type,
        "license_class": row.license_class,
        "source_url": row.source_url,
        # Plane-proxied content URL (ops loads via /v1/ops/knowledge/plane/...)
        "content_path": f"/v1/admin/media/{row.id}/content",
    }


def list_explore_seeds(db: Session) -> dict[str, Any]:
    """Merge curated famous roster + DB composers into an A–Z product catalog."""
    by_id = famous_by_id()
    seen: set[str] = set()
    seeds: list[dict[str, Any]] = []

    for entry in FAMOUS_COMPOSERS:
        cid = entry["composer_id"]
        seen.add(cid)
        db_row = db.get(ComposerEntity, cid)
        ext: dict[str, Any] = {}
        lifespan = ""
        name_zh = entry.get("name_zh") or ""
        if db_row:
            try:
                ext = json.loads(db_row.external_ids_json or "{}")
            except json.JSONDecodeError:
                ext = {}
            lifespan = db_row.lifespan or ""
            if db_row.name_zh:
                name_zh = db_row.name_zh
        seeds.append(
            {
                "id": cid,
                "name_en": entry["name_en"],
                "name_zh": name_zh,
                "short_name": entry["short_name"],
                "era": entry.get("era") or "",
                "letter": entry["letter"],
                "sort_key": entry["sort_key"],
                "wikidata_qid": entry["wikidata_qid"],
                "wikipedia_title": entry["wikipedia_title"],
                "famous": True,
                "featured": cid in FEATURED_COMPOSER_IDS,
                "in_corpus": db_row is not None,
                "lifespan": lifespan,
                "external_ids": ext,
                "portrait": _portrait_for_entity(db, cid),
            }
        )

    for row in db.query(ComposerEntity).order_by(ComposerEntity.name_en, ComposerEntity.id).all():
        if row.id in seen:
            continue
        try:
            ext = json.loads(row.external_ids_json or "{}")
        except json.JSONDecodeError:
            ext = {}
        qid = str(ext.get("wikidata") or ext.get("wikidata_qid") or "")
        name = row.name_en or row.id
        short = name.split()[-1] if name else row.id
        letter = (short[:1] if short else "#").upper()
        if not letter.isalpha():
            letter = "#"
        seeds.append(
            {
                "id": row.id,
                "name_en": name,
                "name_zh": row.name_zh or "",
                "short_name": short,
                "era": "",
                "letter": letter,
                "sort_key": short.casefold(),
                "wikidata_qid": qid,
                "wikipedia_title": name,
                "famous": False,
                "featured": False,
                "in_corpus": True,
                "lifespan": row.lifespan or "",
                "external_ids": ext,
                "portrait": _portrait_for_entity(db, row.id),
            }
        )

    seeds.sort(key=lambda s: (s["sort_key"], s["id"]))
    letters = sorted({s["letter"] for s in seeds if s["letter"] != "#"})
    featured = [s for s in seeds if s.get("featured")]
    # Keep featured strip order stable
    featured_map = {s["id"]: s for s in featured}
    featured_ordered = [featured_map[i] for i in FEATURED_COMPOSER_IDS if i in featured_map]

    return {
        "seeds": seeds,
        "featured": featured_ordered,
        "letters": letters,
        "stats": {
            "total": len(seeds),
            "famous": sum(1 for s in seeds if s["famous"]),
            "with_portrait": sum(1 for s in seeds if s.get("portrait")),
            "in_corpus": sum(1 for s in seeds if s["in_corpus"]),
        },
    }


def prepare_famous_seed_crawls(
    db: Session,
    *,
    sync: bool | None = None,
    limit: int = 32,
    featured_only: bool = False,
) -> dict[str, Any]:
    """Enqueue Wikidata (+ Wikipedia) crawls for famous composers to seed portraits & corpus."""
    from aulos_knowledge.config import get_settings

    jobs: list[dict[str, Any]] = []
    if not _source_crawlable(db, "wikidata"):
        return {"ok": False, "error": "wikidata not crawl-ready", "jobs": []}

    settings = get_settings()
    run_sync = settings.sync_jobs if sync is None else sync
    roster = list(FAMOUS_COMPOSERS)
    if featured_only:
        want = set(FEATURED_COMPOSER_IDS)
        roster = [c for c in FAMOUS_COMPOSERS if c["composer_id"] in want]
    roster = roster[: max(1, min(limit, len(roster)))]

    for entry in roster:
        cid = entry["composer_id"]
        qid = entry["wikidata_qid"]
        title = entry["wikipedia_title"]
        try:
            job = enqueue_fetch_job(
                db,
                source_id="wikidata",
                params={"qids": [qid], "composer_id": cid},
                sync=run_sync,
            )
            jobs.append({"source_id": "wikidata", "composer_id": cid, "job_id": job.id, "status": job.status})
        except Exception as exc:  # noqa: BLE001
            logger.warning("prepare_seed_wikidata_failed cid=%s err=%s", cid, exc)
            jobs.append({"source_id": "wikidata", "composer_id": cid, "status": "failed", "error": str(exc)[:200]})

        if _source_crawlable(db, "wikipedia") and title:
            try:
                job = enqueue_fetch_job(
                    db,
                    source_id="wikipedia",
                    params={"title": title, "langs": ["en", "zh"], "composer_id": cid},
                    sync=run_sync,
                )
                jobs.append({"source_id": "wikipedia", "composer_id": cid, "job_id": job.id, "status": job.status})
            except Exception as exc:  # noqa: BLE001
                jobs.append(
                    {"source_id": "wikipedia", "composer_id": cid, "status": "failed", "error": str(exc)[:200]}
                )

    return {
        "ok": True,
        "jobs": jobs,
        "enqueued": sum(1 for j in jobs if j.get("job_id")),
        "composers": len(roster),
        "sync": run_sync,
    }
