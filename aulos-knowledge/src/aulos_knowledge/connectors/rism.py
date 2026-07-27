"""RISM Online connector — JSON-LD search API (public Accept negotiation)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy.orm import Session

from aulos_knowledge.artifacts import write_artifact
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import (
    FetchArtifact,
    FetchJob,
    KnowledgeChunk,
    KnowledgeDocument,
    SourceAuthority,
)
from aulos_knowledge.fetch_policy import assert_url_allowed, throttle
from aulos_knowledge.publish_policy import document_status_for_source

EXTRACTOR_VERSION = "rism/0.1.0"
UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"
SEARCH = "https://rism.online/search"


def _summarize_item(item: dict[str, Any]) -> str:
    label = (
        item.get("label")
        or item.get("title")
        or item.get("name")
        or item.get("id")
        or "(untitled)"
    )
    parts = [f"Label: {label}"]
    for key in ("composer", "creator", "dating", "date", "shelfmark", "siglum", "type"):
        if item.get(key):
            parts.append(f"{key}: {item[key]}")
    if item.get("id"):
        parts.append(f"id: {item['id']}")
    return "\n".join(str(p) for p in parts)


def run_rism(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    """Params:
    - query / q: search string (default Bach)
    - mode: people|sources|institutions|incipits (default people)
    - limit: max items to materialize (default 5)
    - composer_id / aulos_work_id: optional linkage
    """
    query = str(params.get("query") or params.get("q") or "Bach").strip()
    mode = str(params.get("mode") or "people").strip()
    limit = min(int(params.get("limit") or 5), 20)
    composer_id = str(params.get("composer_id") or "")
    aulos_work_id = str(params.get("aulos_work_id") or "")
    settings = get_settings()

    url = str(httpx.URL(SEARCH, params={"mode": mode, "q": query}))
    assert_url_allowed(source, url)
    throttle(source)

    with httpx.Client(
        timeout=45.0,
        headers={"User-Agent": UA, "Accept": "application/ld+json"},
    ) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()

    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    digest, rel, _ = write_artifact(
        root=Path(settings.artifact_root),
        source_id=source.id,
        job_id=job.id,
        payload=payload,
        suffix="json",
    )
    art = FetchArtifact(
        job_id=job.id,
        source_id=source.id,
        content_hash=digest,
        content_type="application/ld+json",
        storage_path=rel,
        source_url=url,
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()

    items: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key in ("items", "member", "results", "data"):
            cand = data.get(key)
            if isinstance(cand, list):
                items = [x for x in cand if isinstance(x, dict)]
                break
        if not items and isinstance(data.get("graph"), list):
            items = [x for x in data["graph"] if isinstance(x, dict)]

    for item in items[:limit]:
        summary = _summarize_item(item)
        body = (
            f"RISM Online search ({mode}): {query}\n\n{summary}\n\n"
            f"—\nSource: {url} (RISM Online JSON-LD)."
        )
        label = item.get("label") or item.get("title") or item.get("name") or "RISM hit"
        doc = KnowledgeDocument(
            title=f"RISM — {label}",
            entity_type="composer" if composer_id and not aulos_work_id else ("work" if aulos_work_id else "history"),
            entity_id=composer_id or aulos_work_id or str(item.get("id") or label),
            aulos_work_id=aulos_work_id,
            body=body,
            status=document_status_for_source(source),
            source_id=source.id,
            artifact_id=art.id,
            job_id=job.id,
            extractor_version=EXTRACTOR_VERSION,
            license_class=source.license_class,
        )
        db.add(doc)
        db.flush()
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                section="rism",
                text=body,
                aulos_work_id=aulos_work_id,
            )
        )

    if not items:
        # Still record a document so operators see the empty search outcome
        body = f"RISM Online search ({mode}): {query}\n\n(No items parsed from JSON-LD.)\n\nSource: {url}"
        doc = KnowledgeDocument(
            title=f"RISM — search {query}",
            entity_type="history",
            entity_id=composer_id or query,
            aulos_work_id=aulos_work_id,
            body=body,
            status=document_status_for_source(source),
            source_id=source.id,
            artifact_id=art.id,
            job_id=job.id,
            extractor_version=EXTRACTOR_VERSION,
            license_class=source.license_class,
        )
        db.add(doc)
        db.flush()
        db.add(KnowledgeChunk(document_id=doc.id, section="rism", text=body, aulos_work_id=aulos_work_id))

    db.commit()
