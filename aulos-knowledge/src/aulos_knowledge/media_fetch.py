"""Allowlisted media download helpers (Wikimedia Commons / Cover Art Archive)."""

from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from aulos_knowledge.artifacts import write_media_file
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import FetchArtifact, FetchJob, MediaAsset, SourceAuthority

logger = logging.getLogger("aulos_knowledge.media")

UA = "AulosKnowledge/0.1 (https://aulos.purezen.ai; knowledge-plane)"

# Only these hosts may be fetched for binary media (ADR-006 allowlist spirit).
ALLOWED_MEDIA_HOSTS = {
    "commons.wikimedia.org",
    "upload.wikimedia.org",
    "coverartarchive.org",
    "archive.org",
    "ia800000.us.archive.org",
}

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_AUDIO_BYTES = 32 * 1024 * 1024
MAX_META_BYTES = 2 * 1024 * 1024


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return False
    if host in ALLOWED_MEDIA_HOSTS:
        return True
    # Cover Art Archive / IA CDN subdomains
    return host.endswith(".archive.org") or host.endswith(".wikimedia.org")


def _suffix_for_mime(mime: str, fallback: str) -> str:
    mime = (mime or "").split(";")[0].strip().lower()
    mapping = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
        "audio/mpeg": "mp3",
        "audio/ogg": "ogg",
        "audio/flac": "flac",
        "audio/wav": "wav",
        "application/json": "json",
    }
    return mapping.get(mime, fallback)


def commons_file_info(client: httpx.Client, title: str) -> dict[str, Any] | None:
    """Resolve a Commons File: title to download URL + license metadata."""
    file_title = title if title.startswith("File:") else f"File:{title}"
    resp = client.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query",
            "titles": file_title,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata|sha1",
            "format": "json",
        },
    )
    resp.raise_for_status()
    pages = ((resp.json().get("query") or {}).get("pages") or {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if not infos:
            continue
        info = infos[0]
        ext = info.get("extmetadata") or {}
        license_short = ((ext.get("LicenseShortName") or {}).get("value")) or ""
        artist = ((ext.get("Artist") or {}).get("value")) or ""
        return {
            "title": file_title,
            "url": info.get("url") or "",
            "mime": info.get("mime") or "",
            "size": int(info.get("size") or 0),
            "sha1": info.get("sha1") or "",
            "license": license_short,
            "artist_html": artist,
        }
    return None


def download_bytes(client: httpx.Client, url: str, *, max_bytes: int) -> tuple[bytes, str]:
    if not _host_allowed(url):
        raise ValueError(f"media host not allowlisted: {urlparse(url).hostname}")
    with client.stream("GET", url) as resp:
        resp.raise_for_status()
        ctype = resp.headers.get("content-type") or "application/octet-stream"
        chunks: list[bytes] = []
        total = 0
        for chunk in resp.iter_bytes():
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"media exceeds max_bytes={max_bytes}")
            chunks.append(chunk)
    return b"".join(chunks), ctype


def persist_remote_media(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    kind: str,
    url: str,
    entity_type: str,
    entity_id: str,
    aulos_work_id: str = "",
    title: str = "",
    license_class: str = "",
    filename_hint: str = "",
    max_bytes: int | None = None,
) -> MediaAsset | None:
    """Download allowlisted media and register MediaAsset + FetchArtifact rows."""
    settings = get_settings()
    root = __import__("pathlib").Path(settings.artifact_root)
    limit = max_bytes or (
        MAX_IMAGE_BYTES if kind == "image" else MAX_AUDIO_BYTES if kind == "audio" else MAX_META_BYTES
    )
    with httpx.Client(timeout=60.0, headers={"User-Agent": UA}, follow_redirects=True) as client:
        payload, ctype = download_bytes(client, url, max_bytes=limit)
    suffix = _suffix_for_mime(ctype, "bin")
    fname = filename_hint or f"{entity_id or 'asset'}.{suffix}"
    digest, rel, _ = write_media_file(
        root=root,
        kind=kind,
        source_id=source.id,
        entity_id=entity_id,
        payload=payload,
        filename=fname,
    )
    art = FetchArtifact(
        job_id=job.id,
        source_id=source.id,
        content_hash=digest,
        content_type=ctype.split(";")[0].strip(),
        storage_path=rel,
        source_url=url,
        byte_size=len(payload),
    )
    db.add(art)
    db.flush()
    asset = MediaAsset(
        kind=kind,
        title=title or fname,
        entity_type=entity_type,
        entity_id=entity_id,
        aulos_work_id=aulos_work_id,
        source_id=source.id,
        artifact_id=art.id,
        job_id=job.id,
        source_url=url,
        storage_path=rel,
        content_hash=digest,
        content_type=ctype.split(";")[0].strip(),
        byte_size=len(payload),
        license_class=license_class or source.license_class,
        meta_json="{}",
    )
    db.add(asset)
    db.flush()
    return asset


def persist_meta_json(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    entity_type: str,
    entity_id: str,
    title: str,
    payload: dict[str, Any],
    aulos_work_id: str = "",
    source_url: str = "",
) -> MediaAsset:
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    settings = get_settings()
    digest, rel, _ = write_media_file(
        root=__import__("pathlib").Path(settings.artifact_root),
        kind="meta",
        source_id=source.id,
        entity_id=entity_id,
        payload=raw,
        filename=f"{entity_id or 'meta'}.json",
    )
    art = FetchArtifact(
        job_id=job.id,
        source_id=source.id,
        content_hash=digest,
        content_type="application/json",
        storage_path=rel,
        source_url=source_url,
        byte_size=len(raw),
    )
    db.add(art)
    db.flush()
    asset = MediaAsset(
        kind="meta",
        title=title,
        entity_type=entity_type,
        entity_id=entity_id,
        aulos_work_id=aulos_work_id,
        source_id=source.id,
        artifact_id=art.id,
        job_id=job.id,
        source_url=source_url,
        storage_path=rel,
        content_hash=digest,
        content_type="application/json",
        byte_size=len(raw),
        license_class=source.license_class,
        meta_json=json.dumps({"keys": list(payload.keys())}, ensure_ascii=False),
    )
    db.add(asset)
    db.flush()
    return asset


def fetch_wikidata_media_claims(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    qid: str,
    claims: dict[str, Any],
    composer_id: str = "",
    aulos_work_id: str = "",
) -> list[MediaAsset]:
    """Download P18 (image) and P51 (audio) Commons files linked from Wikidata."""
    out: list[MediaAsset] = []
    entity_id = composer_id or qid
    entity_type = "composer" if composer_id else "work" if aulos_work_id else "entity"
    with httpx.Client(timeout=60.0, headers={"User-Agent": UA}, follow_redirects=True) as client:
        for prop, kind in (("P18", "image"), ("P51", "audio")):
            for claim in (claims.get(prop) or [])[:3]:
                snak = (claim.get("mainsnak") or {}).get("datavalue") or {}
                filename = str((snak.get("value") or "")).strip()
                if not filename:
                    continue
                try:
                    info = commons_file_info(client, filename)
                    if not info or not info.get("url"):
                        continue
                    asset = persist_remote_media(
                        db,
                        source=source,
                        job=job,
                        kind=kind,
                        url=info["url"],
                        entity_type=entity_type,
                        entity_id=entity_id,
                        aulos_work_id=aulos_work_id,
                        title=info.get("title") or filename,
                        license_class=info.get("license") or source.license_class,
                        filename_hint=filename.replace(" ", "_"),
                        max_bytes=MAX_IMAGE_BYTES if kind == "image" else MAX_AUDIO_BYTES,
                    )
                    if asset:
                        asset.meta_json = json.dumps(
                            {"commons": info, "wikidata_prop": prop, "qid": qid},
                            ensure_ascii=False,
                        )
                        out.append(asset)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("wikidata_media_skip qid=%s file=%s err=%s", qid, filename, exc)
    return out


def fetch_cover_art(
    db: Session,
    *,
    source: SourceAuthority,
    job: FetchJob,
    release_group_mbid: str,
    entity_id: str,
    title: str = "",
    aulos_work_id: str = "",
) -> MediaAsset | None:
    """Cover Art Archive front cover (images only — not commercial audio)."""
    if not release_group_mbid:
        return None
    url = f"https://coverartarchive.org/release-group/{release_group_mbid}/front-500"
    try:
        return persist_remote_media(
            db,
            source=source,
            job=job,
            kind="image",
            url=url,
            entity_type="release-group",
            entity_id=entity_id or release_group_mbid,
            aulos_work_id=aulos_work_id,
            title=title or f"Cover {release_group_mbid}",
            license_class="CAA",
            filename_hint=f"{release_group_mbid}_front.jpg",
            max_bytes=MAX_IMAGE_BYTES,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("cover_art_skip mbid=%s err=%s", release_group_mbid, exc)
        return None
