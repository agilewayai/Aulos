"""Wikipedia connector — EN/ZH summary extracts via MediaWiki Action API (CC BY-SA)."""

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
    ComposerEntity,
    FetchArtifact,
    FetchJob,
    KnowledgeChunk,
    KnowledgeDocument,
    SourceAuthority,
)
from aulos_knowledge.fetch_policy import assert_url_allowed, throttle
from aulos_knowledge.publish_policy import document_status_for_source

EXTRACTOR_VERSION = "wikipedia/0.1.0"
UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"

LANG_HOST = {
    "en": "https://en.wikipedia.org",
    "zh": "https://zh.wikipedia.org",
}


def wiki_extract_url(lang: str, title: str) -> str:
    host = LANG_HOST.get(lang, LANG_HOST["en"])
    return (
        f"{host}/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1"
        f"&redirects=1&format=json&titles={quote(title)}"
    )


def fetch_wikipedia_extract(
    client: httpx.Client,
    *,
    source: SourceAuthority,
    lang: str,
    title: str,
) -> dict[str, Any]:
    url = wiki_extract_url(lang, title)
    assert_url_allowed(source, url)
    throttle(source)
    resp = client.get(url)
    resp.raise_for_status()
    data = resp.json()
    pages = ((data.get("query") or {}).get("pages") or {})
    page = next(iter(pages.values()), {}) if pages else {}
    extract = str(page.get("extract") or "").strip()
    page_title = str(page.get("title") or title)
    page_id = page.get("pageid")
    page_url = f"{LANG_HOST.get(lang, LANG_HOST['en'])}/wiki/{quote(page_title.replace(' ', '_'))}"
    return {
        "lang": lang,
        "title": page_title,
        "pageid": page_id,
        "extract": extract,
        "url": url,
        "page_url": page_url,
        "raw": data,
    }


def run_wikipedia(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    """Params:
    - titles: list[str] page titles (required unless title set)
    - title: single title shorthand
    - langs: list[str] default ["en"] (en|zh)
    - composer_id / aulos_work_id: optional identity linkage
    """
    titles = params.get("titles")
    if not titles:
        one = str(params.get("title") or "").strip()
        titles = [one] if one else ["Johann Sebastian Bach"]
    if isinstance(titles, str):
        titles = [titles]
    langs = params.get("langs") or ["en"]
    if isinstance(langs, str):
        langs = [langs]
    langs = [str(x).strip().lower() for x in langs if str(x).strip()]
    langs = [x for x in langs if x in LANG_HOST] or ["en"]

    composer_id = str(params.get("composer_id") or "")
    aulos_work_id = str(params.get("aulos_work_id") or "")
    settings = get_settings()
    results: list[dict[str, Any]] = []

    with httpx.Client(timeout=30.0, headers={"User-Agent": UA}) as client:
        for title in titles:
            for lang in langs:
                results.append(
                    fetch_wikipedia_extract(client, source=source, lang=lang, title=str(title))
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
        source_url="https://en.wikipedia.org/w/api.php",
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()

    for item in results:
        extract = item.get("extract") or ""
        if not extract:
            continue
        lang = item["lang"]
        page_title = item["title"]
        attribution = (
            f"Wikipedia ({lang}), «{page_title}», CC BY-SA. "
            f"Source: {item.get('page_url')} — attribution required."
        )
        body = f"{extract}\n\n—\n{attribution}"
        entity_key = composer_id or aulos_work_id or page_title
        if composer_id and not aulos_work_id:
            row = db.get(ComposerEntity, composer_id)
            if row is None:
                row = ComposerEntity(id=composer_id)
                db.add(row)
            if lang == "en" and not row.name_en:
                row.name_en = page_title
            if lang == "zh" and not row.name_zh:
                row.name_zh = page_title
            ext: dict[str, Any] = {}
            try:
                ext = json.loads(row.external_ids_json or "{}")
            except json.JSONDecodeError:
                ext = {}
            ext[f"wikipedia_{lang}"] = page_title
            row.external_ids_json = json.dumps(ext, ensure_ascii=False)

        doc = KnowledgeDocument(
            title=f"Wikipedia {lang} — {page_title}",
            entity_type="composer" if composer_id and not aulos_work_id else ("work" if aulos_work_id else "history"),
            entity_id=entity_key,
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
                section=f"wikipedia-{lang}",
                text=body,
                aulos_work_id=aulos_work_id,
            )
        )
    db.commit()
