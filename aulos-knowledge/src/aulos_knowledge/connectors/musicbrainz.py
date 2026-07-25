"""MusicBrainz connector — artist/work/recording lookup; cover art + music-file metadata."""

from __future__ import annotations

import json
import time
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
from aulos_knowledge.media_fetch import fetch_cover_art, persist_meta_json

EXTRACTOR_VERSION = "musicbrainz/0.3.0"
UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"


def _mb_get(client: httpx.Client, path: str, params: dict[str, Any]) -> dict[str, Any]:
    time.sleep(1.05)
    url = f"https://musicbrainz.org/ws/2/{path}"
    resp = client.get(url, params={**params, "fmt": "json"})
    resp.raise_for_status()
    return resp.json()


def run_musicbrainz(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    params: dict[str, Any],
) -> None:
    """Params:
    - mode: work|artist|recording (default work)
    - query: Lucene search string
    - composer_id / aulos_work_id: optional identity linkage
    - fetch_cover: bool (default True for artist/work)
    """
    mode = str(params.get("mode") or "work").strip().lower()
    query = str(params.get("query") or "Bach Cello Suites").strip()
    aulos_work_id = str(params.get("aulos_work_id") or "")
    composer_id = str(params.get("composer_id") or "")
    fetch_cover = bool(params.get("fetch_cover", True))
    settings = get_settings()

    with httpx.Client(timeout=45.0, headers={"User-Agent": UA, "Accept": "application/json"}) as client:
        if mode == "artist":
            data = _mb_get(client, "artist", {"query": query, "limit": 5})
        elif mode == "recording":
            data = _mb_get(client, "recording", {"query": query, "limit": 10})
        else:
            data = _mb_get(client, "work", {"query": query, "limit": 5})

        # Secondary: release-group for cover art + recording file info when artist known
        release_groups: list[dict[str, Any]] = []
        recordings: list[dict[str, Any]] = []
        if mode == "artist" and (data.get("artists") or []):
            top = data["artists"][0]
            artist_id = str(top.get("id") or "")
            if artist_id:
                rg = _mb_get(
                    client,
                    "release-group",
                    {"artist": artist_id, "limit": 5, "type": "album"},
                )
                release_groups = list(rg.get("release-groups") or [])
                rec = _mb_get(
                    client,
                    "recording",
                    {"query": f'arid:{artist_id} AND recording:"{top.get("name") or ""}"', "limit": 8},
                )
                # Prefer a simpler recording query by artist name
                if not rec.get("recordings"):
                    rec = _mb_get(
                        client,
                        "recording",
                        {"query": f'artist:"{top.get("name")}"', "limit": 8},
                    )
                recordings = list(rec.get("recordings") or [])
        elif mode == "work" and fetch_cover:
            # Try release-group search from work title
            title = ""
            works = data.get("works") or []
            if works:
                title = str(works[0].get("title") or "")
            if title:
                rg = _mb_get(client, "release-group", {"query": f'releasegroup:"{title}"', "limit": 3})
                release_groups = list(rg.get("release-groups") or [])

    bundle = {
        "mode": mode,
        "query": query,
        "response": data,
        "release_groups": release_groups,
        "recordings": recordings,
    }
    payload = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
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
        source_url=f"https://musicbrainz.org/ws/2/{mode}?query={query}",
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()

    if mode == "artist":
        for artist in data.get("artists") or []:
            mbid = str(artist.get("id") or "")
            name = str(artist.get("name") or mbid)
            score = artist.get("score")
            life = artist.get("life-span") or {}
            body = (
                f"MusicBrainz artist {mbid}: {name} (score={score})\n"
                f"Type: {artist.get('type')}\n"
                f"Country: {artist.get('country') or ''}\n"
                f"Disambiguation: {artist.get('disambiguation') or ''}\n"
                f"Life: {life.get('begin') or ''} – {life.get('end') or ''}\n"
                f"License note: ODbL — derived DB share-alike may apply.\n"
                f"Query: {query}"
            )
            if composer_id:
                row = db.get(ComposerEntity, composer_id)
                if row is None:
                    row = ComposerEntity(id=composer_id, name_en=name)
                    db.add(row)
                elif not row.name_en:
                    row.name_en = name
                ext = {}
                try:
                    ext = json.loads(row.external_ids_json or "{}")
                except json.JSONDecodeError:
                    ext = {}
                ext["musicbrainz"] = mbid
                row.external_ids_json = json.dumps(ext, ensure_ascii=False)
                begin, end = life.get("begin") or "", life.get("end") or ""
                if begin or end:
                    row.lifespan = f"{str(begin)[:4]}–{str(end)[:4]}".strip("–")

            doc = KnowledgeDocument(
                title=f"MusicBrainz artist — {name}",
                entity_type="composer",
                entity_id=composer_id or mbid,
                aulos_work_id="",
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
                    section="musicbrainz-artist",
                    text=body,
                    aulos_work_id="",
                )
            )
    elif mode == "recording":
        for rec in data.get("recordings") or []:
            mbid = str(rec.get("id") or "")
            title = str(rec.get("title") or mbid)
            length_ms = rec.get("length")
            body = (
                f"MusicBrainz recording {mbid}: {title}\n"
                f"Length_ms: {length_ms}\n"
                f"Disambiguation: {rec.get('disambiguation') or ''}\n"
                f"Score: {rec.get('score')}\n"
                f"License note: ODbL metadata — audio binaries not scraped from commercial stores.\n"
            )
            doc = KnowledgeDocument(
                title=f"MusicBrainz recording — {title}",
                entity_type="recording",
                entity_id=mbid,
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
                    section="musicbrainz-recording",
                    text=body,
                    aulos_work_id=aulos_work_id,
                )
            )
    else:
        for work in data.get("works") or []:
            mbid = str(work.get("id") or "")
            title = str(work.get("title") or mbid)
            score = work.get("score")
            body = (
                f"MusicBrainz work {mbid}: {title} (score={score})\n"
                f"Type: {work.get('type')}\n"
                f"Disambiguation: {work.get('disambiguation') or ''}\n"
                f"License note: ODbL — derived DB share-alike may apply.\n"
                f"Query: {query}"
            )
            doc = KnowledgeDocument(
                title=f"MusicBrainz — {title}",
                entity_type="work",
                entity_id=mbid,
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
                    section="musicbrainz",
                    text=body,
                    aulos_work_id=aulos_work_id,
                )
            )

    # Persist music-file information (recording metadata JSON) on durable disk
    if recordings:
        persist_meta_json(
            db,
            source=source,
            job=job,
            entity_type="composer" if composer_id else "recording-set",
            entity_id=composer_id or f"mb-recordings-{job.id}",
            title=f"MusicBrainz recordings for {composer_id or query}",
            payload={
                "query": query,
                "count": len(recordings),
                "recordings": [
                    {
                        "id": r.get("id"),
                        "title": r.get("title"),
                        "length_ms": r.get("length"),
                        "score": r.get("score"),
                        "disambiguation": r.get("disambiguation"),
                        "video": r.get("video"),
                        "first-release-date": r.get("first-release-date"),
                    }
                    for r in recordings
                ],
            },
            aulos_work_id=aulos_work_id,
            source_url="https://musicbrainz.org/ws/2/recording",
        )

    if release_groups:
        persist_meta_json(
            db,
            source=source,
            job=job,
            entity_type="release-group-set",
            entity_id=composer_id or f"mb-rg-{job.id}",
            title=f"MusicBrainz release-groups for {composer_id or query}",
            payload={
                "count": len(release_groups),
                "release_groups": [
                    {
                        "id": rg.get("id"),
                        "title": rg.get("title"),
                        "primary-type": rg.get("primary-type"),
                        "first-release-date": rg.get("first-release-date"),
                    }
                    for rg in release_groups
                ],
            },
            aulos_work_id=aulos_work_id,
            source_url="https://musicbrainz.org/ws/2/release-group",
        )

    # Cover Art Archive images (not commercial audio masters)
    if fetch_cover:
        for rg in release_groups[:3]:
            rgid = str(rg.get("id") or "")
            if not rgid:
                continue
            fetch_cover_art(
                db,
                source=source,
                job=job,
                release_group_mbid=rgid,
                entity_id=composer_id or rgid,
                title=str(rg.get("title") or rgid),
                aulos_work_id=aulos_work_id,
            )

    db.commit()
