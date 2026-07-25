"""Wikidata connector — fetch entity JSON via WB API; store artifact + summary doc."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
from aulos_knowledge.media_fetch import fetch_wikidata_media_claims

EXTRACTOR_VERSION = "wikidata/0.3.0"
UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"


def _lifespan_from_claims(claims: dict[str, Any]) -> str:
    def _year(prop: str) -> str:
        vals = claims.get(prop) or []
        if not vals:
            return ""
        t = (((vals[0] or {}).get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
        raw = str(t.get("time") or "")
        # +1685-03-21T00:00:00Z → 1685
        if raw.startswith("+") or raw.startswith("-"):
            return raw[1:5]
        return ""

    birth, death = _year("P569"), _year("P570")
    if birth and death:
        return f"{birth}–{death}"
    return birth or death or ""


def run_wikidata(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    qids = params.get("qids") or ["Q1339"]
    if isinstance(qids, str):
        qids = [qids]
    aulos_work_id = str(params.get("aulos_work_id") or "")
    composer_id = str(params.get("composer_id") or "")
    settings = get_settings()
    results: list[dict[str, Any]] = []
    with httpx.Client(timeout=30.0, headers={"User-Agent": UA}) as client:
        for qid in qids:
            url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
            resp = client.get(url)
            resp.raise_for_status()
            results.append({"qid": qid, "url": url, "payload": resp.json()})

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
        source_url="https://www.wikidata.org/wiki/Special:EntityData",
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()

    for item in results:
        qid = item["qid"]
        entity = (item["payload"].get("entities") or {}).get(qid) or {}
        labels = entity.get("labels") or {}
        label_en = (labels.get("en") or {}).get("value") or qid
        label_zh = (labels.get("zh-hans") or labels.get("zh") or {}).get("value") or ""
        desc = ((entity.get("descriptions") or {}).get("en") or {}).get("value") or ""
        desc_zh = (
            ((entity.get("descriptions") or {}).get("zh-hans") or {}).get("value")
            or ((entity.get("descriptions") or {}).get("zh") or {}).get("value")
            or ""
        )
        claims = entity.get("claims") or {}
        lifespan = _lifespan_from_claims(claims)
        sitelinks = entity.get("sitelinks") or {}
        enwiki = (sitelinks.get("enwiki") or {}).get("title") or ""
        zhwiki = (sitelinks.get("zhwiki") or {}).get("title") or ""
        body = (
            f"Wikidata {qid}: {label_en} / {label_zh}\n"
            f"{desc}\n{desc_zh}\n"
            f"Lifespan: {lifespan or 'n/a'}\n"
            f"Wikipedia EN: {enwiki}\nWikipedia ZH: {zhwiki}\n"
            f"Source: {item['url']} (license: CC0)"
        )
        entity_key = composer_id or qid
        if composer_id and not aulos_work_id:
            row = db.get(ComposerEntity, composer_id)
            if row is None:
                row = ComposerEntity(id=composer_id)
                db.add(row)
            row.name_en = label_en or row.name_en
            row.name_zh = label_zh or row.name_zh
            row.lifespan = lifespan or row.lifespan
            ext = {}
            try:
                ext = json.loads(row.external_ids_json or "{}")
            except json.JSONDecodeError:
                ext = {}
            ext["wikidata"] = qid
            if enwiki:
                ext["enwiki"] = enwiki
            if zhwiki:
                ext["zhwiki"] = zhwiki
            row.external_ids_json = json.dumps(ext, ensure_ascii=False)

        doc = KnowledgeDocument(
            title=f"Wikidata {qid} — {label_en}",
            entity_type="composer" if not aulos_work_id else "work",
            entity_id=entity_key,
            aulos_work_id=aulos_work_id,
            body=body,
            status="published",
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
                section="wikidata",
                text=body,
                aulos_work_id=aulos_work_id,
            )
        )
        # Durable portrait / PD audio (Commons) under data/persist/artifacts/media/
        media_assets = fetch_wikidata_media_claims(
            db,
            source=source,
            job=job,
            qid=qid,
            claims=claims,
            composer_id=composer_id,
            aulos_work_id=aulos_work_id,
        )
        if media_assets:
            doc.body = (
                body
                + "\nMedia files stored: "
                + ", ".join(f"{m.kind}:{m.storage_path}" for m in media_assets)
            )
    db.commit()
