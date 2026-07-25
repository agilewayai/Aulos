from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_knowledge.config import get_settings
from aulos_knowledge.db import (
    ComposerEntity,
    FetchArtifact,
    FetchJob,
    KnowledgeDocument,
    MediaAsset,
    SourceAuthority,
    WorkEntity,
    get_session,
)
from aulos_knowledge.jobs import enqueue_and_maybe_run
from aulos_knowledge.retrieve import retrieve as kb_retrieve

router = APIRouter()


class SourceIn(BaseModel):
    id: str
    name: str = ""
    tier: str = "A"
    connector: str = ""
    base_urls: list[str] = Field(default_factory=list)
    license_class: str = "unknown"
    rate_limit_qps: float = 1.0
    enabled: bool = True
    notes: str = ""


class JobIn(BaseModel):
    source_id: str
    params: dict[str, Any] = Field(default_factory=dict)


class RetrieveIn(BaseModel):
    query: str
    work_id: str = ""
    composer_id: str = ""
    k: int = 6


def _db():
    yield from get_session()


@router.get("/health")
def health() -> dict[str, str]:
    s = get_settings()
    return {"status": "ok", "service": s.app_name, "version": s.app_version}


@router.get("/v1/kb/stats")
def stats(db: Session = Depends(_db)) -> dict[str, Any]:
    return {
        "sources": db.query(SourceAuthority).count(),
        "sources_enabled": db.query(SourceAuthority).filter(SourceAuthority.enabled.is_(True)).count(),
        "jobs": db.query(FetchJob).count(),
        "artifacts": db.query(FetchArtifact).count(),
        "composers": db.query(ComposerEntity).count(),
        "works": db.query(WorkEntity).count(),
        "documents": db.query(KnowledgeDocument).count(),
        "documents_published": db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.status == "published")
        .count(),
        "documents_quarantine": db.query(KnowledgeDocument)
        .filter(KnowledgeDocument.status == "quarantine")
        .count(),
        "media_assets": db.query(MediaAsset).count(),
        "media_images": db.query(MediaAsset).filter(MediaAsset.kind == "image").count(),
        "media_audio": db.query(MediaAsset).filter(MediaAsset.kind == "audio").count(),
        "media_meta": db.query(MediaAsset).filter(MediaAsset.kind == "meta").count(),
    }


@router.post("/v1/kb/retrieve")
def retrieve(body: RetrieveIn, db: Session = Depends(_db)) -> dict[str, Any]:
    return kb_retrieve(
        db,
        query=body.query,
        work_id=body.work_id,
        composer_id=body.composer_id,
        k=body.k,
    )


@router.get("/v1/admin/sources")
def list_sources(db: Session = Depends(_db)) -> list[dict[str, Any]]:
    rows = db.query(SourceAuthority).order_by(SourceAuthority.id).all()
    out = []
    for r in rows:
        out.append(
            {
                "id": r.id,
                "name": r.name,
                "tier": r.tier,
                "connector": r.connector,
                "base_urls": json.loads(r.base_urls_json or "[]"),
                "license_class": r.license_class,
                "rate_limit_qps": r.rate_limit_qps,
                "enabled": r.enabled,
                "notes": r.notes,
            }
        )
    return out


@router.post("/v1/admin/sources")
def create_source(body: SourceIn, db: Session = Depends(_db)) -> dict[str, Any]:
    if db.get(SourceAuthority, body.id):
        raise HTTPException(400, f"source exists: {body.id}")
    row = SourceAuthority(
        id=body.id,
        name=body.name or body.id,
        tier=body.tier,
        connector=body.connector,
        base_urls_json=json.dumps(body.base_urls, ensure_ascii=False),
        license_class=body.license_class,
        rate_limit_qps=body.rate_limit_qps,
        enabled=body.enabled,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id}


@router.patch("/v1/admin/sources/{source_id}")
def patch_source(source_id: str, body: dict[str, Any], db: Session = Depends(_db)) -> dict[str, Any]:
    row = db.get(SourceAuthority, source_id)
    if not row:
        raise HTTPException(404, "source not found")
    if "enabled" in body:
        row.enabled = bool(body["enabled"])
    if "notes" in body:
        row.notes = str(body["notes"])
    if "rate_limit_qps" in body:
        row.rate_limit_qps = float(body["rate_limit_qps"])
    db.commit()
    return {"ok": True, "id": source_id, "enabled": row.enabled}


@router.get("/v1/admin/jobs")
def list_jobs(db: Session = Depends(_db), limit: int = 50) -> list[dict[str, Any]]:
    rows = db.query(FetchJob).order_by(FetchJob.id.desc()).limit(limit).all()
    return [
        {
            "id": j.id,
            "source_id": j.source_id,
            "status": j.status,
            "params": json.loads(j.params_json or "{}"),
            "error": j.error,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "finished_at": j.finished_at.isoformat() if j.finished_at else None,
        }
        for j in rows
    ]


@router.post("/v1/admin/jobs")
def create_job(body: JobIn, db: Session = Depends(_db)) -> dict[str, Any]:
    settings = get_settings()
    try:
        job = enqueue_and_maybe_run(
            db,
            source_id=body.source_id,
            params=body.params,
            sync=settings.sync_jobs,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "id": job.id,
        "source_id": job.source_id,
        "status": job.status,
        "error": job.error,
    }


@router.get("/v1/admin/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    job = db.get(FetchJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return {
        "id": job.id,
        "source_id": job.source_id,
        "status": job.status,
        "params": json.loads(job.params_json or "{}"),
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


def _doc_summary(d: KnowledgeDocument) -> dict[str, Any]:
    return {
        "id": d.id,
        "title": d.title,
        "entity_type": d.entity_type,
        "entity_id": d.entity_id,
        "aulos_work_id": d.aulos_work_id,
        "status": d.status,
        "source_id": d.source_id,
        "artifact_id": d.artifact_id,
        "job_id": d.job_id,
        "extractor_version": d.extractor_version,
        "license_class": d.license_class,
        "body_preview": (d.body or "")[:240],
    }


@router.get("/v1/admin/composers")
def list_composers(db: Session = Depends(_db), limit: int = 100) -> list[dict[str, Any]]:
    rows = db.query(ComposerEntity).order_by(ComposerEntity.name_en, ComposerEntity.id).limit(limit).all()
    return [
        {
            "id": c.id,
            "name_en": c.name_en,
            "name_zh": c.name_zh,
            "lifespan": c.lifespan,
            "external_ids": json.loads(c.external_ids_json or "{}"),
        }
        for c in rows
    ]


@router.get("/v1/admin/documents")
def list_documents(
    db: Session = Depends(_db),
    status: str = "",
    entity_type: str = "",
    source_id: str = "",
    q: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    query = db.query(KnowledgeDocument).order_by(KnowledgeDocument.id.desc())
    if status:
        query = query.filter(KnowledgeDocument.status == status)
    if entity_type:
        query = query.filter(KnowledgeDocument.entity_type == entity_type)
    if source_id:
        query = query.filter(KnowledgeDocument.source_id == source_id)
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(
            (KnowledgeDocument.title.ilike(like))
            | (KnowledgeDocument.body.ilike(like))
            | (KnowledgeDocument.entity_id.ilike(like))
            | (KnowledgeDocument.aulos_work_id.ilike(like))
        )
    rows = query.limit(min(limit, 200)).all()
    return [_doc_summary(d) for d in rows]


@router.get("/v1/admin/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    out = _doc_summary(doc)
    out["body"] = doc.body or ""
    return out


@router.post("/v1/admin/documents/{doc_id}/quarantine")
def quarantine_doc(doc_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    doc.status = "quarantine"
    db.commit()
    return {"ok": True, "id": doc_id, "status": "quarantine"}


@router.post("/v1/admin/documents/{doc_id}/publish")
def publish_doc(doc_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    """Restore a quarantined (or draft) document to published — proofreading accept."""
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    doc.status = "published"
    db.commit()
    return {"ok": True, "id": doc_id, "status": "published"}


@router.get("/v1/admin/provenance/{document_id}")
def provenance(document_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    doc = db.get(KnowledgeDocument, document_id)
    if not doc:
        raise HTTPException(404, "document not found")
    src = db.get(SourceAuthority, doc.source_id) if doc.source_id else None
    art = db.get(FetchArtifact, doc.artifact_id) if doc.artifact_id else None
    job = db.get(FetchJob, doc.job_id) if doc.job_id else None
    return {
        "document": {
            "id": doc.id,
            "title": doc.title,
            "entity_type": doc.entity_type,
            "entity_id": doc.entity_id,
            "aulos_work_id": doc.aulos_work_id,
            "status": doc.status,
            "body": doc.body or "",
            "extractor_version": doc.extractor_version,
            "license_class": doc.license_class,
        },
        "source": None
        if not src
        else {
            "id": src.id,
            "name": src.name,
            "tier": src.tier,
            "connector": src.connector,
            "license_class": src.license_class,
        },
        "artifact": None
        if not art
        else {
            "id": art.id,
            "content_hash": art.content_hash,
            "storage_path": art.storage_path,
            "source_url": art.source_url,
            "byte_size": art.byte_size,
            "fetched_at": art.fetched_at.isoformat() if art.fetched_at else None,
        },
        "job": None
        if not job
        else {
            "id": job.id,
            "status": job.status,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        },
    }


@router.get("/v1/admin/artifacts/{artifact_id}")
def get_artifact(artifact_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    art = db.get(FetchArtifact, artifact_id)
    if not art:
        raise HTTPException(404, "artifact not found")
    settings = get_settings()
    path = Path(settings.artifact_root) / art.storage_path
    preview = ""
    if path.is_file() and art.byte_size < 200_000 and (art.content_type or "").startswith(("text/", "application/json")):
        try:
            preview = path.read_text(encoding="utf-8")[:4000]
        except Exception:  # noqa: BLE001
            preview = "<binary>"
    return {
        "id": art.id,
        "content_hash": art.content_hash,
        "storage_path": art.storage_path,
        "source_url": art.source_url,
        "exists": path.is_file(),
        "preview": preview,
    }


@router.get("/v1/admin/media")
def list_media(
    db: Session = Depends(_db),
    kind: str = "",
    entity_id: str = "",
    limit: int = 50,
) -> list[dict[str, Any]]:
    q = db.query(MediaAsset).order_by(MediaAsset.id.desc())
    if kind:
        q = q.filter(MediaAsset.kind == kind)
    if entity_id:
        q = q.filter(MediaAsset.entity_id == entity_id)
    rows = q.limit(min(limit, 200)).all()
    settings = get_settings()
    root = Path(settings.artifact_root)
    out = []
    for m in rows:
        abs_path = root / m.storage_path if m.storage_path else None
        out.append(
            {
                "id": m.id,
                "kind": m.kind,
                "title": m.title,
                "entity_type": m.entity_type,
                "entity_id": m.entity_id,
                "aulos_work_id": m.aulos_work_id,
                "source_id": m.source_id,
                "source_url": m.source_url,
                "storage_path": m.storage_path,
                "content_hash": m.content_hash,
                "content_type": m.content_type,
                "byte_size": m.byte_size,
                "license_class": m.license_class,
                "exists_on_disk": bool(abs_path and abs_path.is_file()),
                "job_id": m.job_id,
                "artifact_id": m.artifact_id,
            }
        )
    return out
