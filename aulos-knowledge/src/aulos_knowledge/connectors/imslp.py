"""IMSLP connector — MediaWiki summary extracts (scores/PD catalog pages)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import quote

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

EXTRACTOR_VERSION = "imslp/0.1.0"
UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"
API = "https://imslp.org/api.php"


def run_imslp(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    """Params:
    - titles: list of IMSLP page titles
    - title: single title
    - composer_id / aulos_work_id: optional linkage
    """
    titles = params.get("titles")
    if not titles:
        one = str(params.get("title") or "").strip()
        titles = [one] if one else ["Category:Bach, Johann Sebastian"]
    if isinstance(titles, str):
        titles = [titles]
    composer_id = str(params.get("composer_id") or "")
    aulos_work_id = str(params.get("aulos_work_id") or "")
    settings = get_settings()
    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=45.0, headers={"User-Agent": UA}) as client:
        for title in titles:
            url = (
                f"{API}?action=query&prop=extracts&exintro=1&explaintext=1"
                f"&redirects=1&format=json&titles={quote(str(title))}"
            )
            assert_url_allowed(source, url)
            throttle(source)
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            pages = ((data.get("query") or {}).get("pages") or {})
            page = next(iter(pages.values()), {}) if pages else {}
            extract = str(page.get("extract") or "").strip()
            page_title = str(page.get("title") or title)
            results.append(
                {
                    "title": page_title,
                    "extract": extract,
                    "url": url,
                    "page_url": f"https://imslp.org/wiki/{quote(page_title.replace(' ', '_'))}",
                    "raw": data,
                }
            )

    payload = json.dumps(results, ensure_ascii=False).encode("utf-8")
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
        content_type="application/json",
        storage_path=rel,
        source_url=API,
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()

    for item in results:
        extract = item.get("extract") or ""
        body = (
            (extract or f"(No intro extract for {item['title']})")
            + f"\n\n—\nIMSLP / Petrucci: {item.get('page_url')} "
            f"(license mixed — verify PD/score rights before publish)."
        )
        doc = KnowledgeDocument(
            title=f"IMSLP — {item['title']}",
            entity_type="composer" if composer_id and not aulos_work_id else ("work" if aulos_work_id else "history"),
            entity_id=composer_id or aulos_work_id or item["title"],
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
                section="imslp",
                text=body,
                aulos_work_id=aulos_work_id,
            )
        )
    db.commit()
