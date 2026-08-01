from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_knowledge.auth import require_admin_token
from aulos_knowledge.config import get_settings
from aulos_knowledge.db import (
    ComposerEntity,
    FetchArtifact,
    FetchJob,
    KnowledgeChunk,
    KnowledgeDocument,
    MediaAsset,
    SourceAuthority,
    SourceDiscoveryRun,
    WorkEntity,
    get_session,
    utcnow,
)
from aulos_knowledge.connectors import connector_registered
from aulos_knowledge.jobs import enqueue_and_maybe_run
from aulos_knowledge.retrieve import retrieve as kb_retrieve
from aulos_knowledge.benchmark import (
    build_dashboard_report,
    benchmark_run_summary,
    get_benchmark_run,
    list_benchmark_runs,
    load_benchmark_suite,
    run_benchmark,
)
from aulos_knowledge.benchmark_queue import enqueue_and_maybe_run as enqueue_benchmark_run
from aulos_knowledge.explore_seeds import list_explore_seeds, prepare_famous_seed_crawls
from aulos_knowledge.source_discovery import (
    discovery_run_dict,
    enqueue_discovery_crawl,
    execute_discovery_run,
    register_discovery_candidates,
)

router = APIRouter()
admin_router = APIRouter(prefix="/v1/admin", dependencies=[Depends(require_admin_token)])


def _source_dict(r: SourceAuthority) -> dict[str, Any]:
    return {
        "id": r.id,
        "name": r.name,
        "tier": r.tier,
        "connector": r.connector,
        "base_urls": json.loads(r.base_urls_json or "[]"),
        "license_class": r.license_class,
        "rate_limit_qps": r.rate_limit_qps,
        "enabled": r.enabled,
        "notes": r.notes,
        "verification_status": r.verification_status or "candidate",
        "verified_by": r.verified_by or "",
        "verified_at": r.verified_at.isoformat() if r.verified_at else None,
        "tos_notes": r.tos_notes or "",
        "attribution_template": r.attribution_template or "",
        "allowed_path_prefixes": json.loads(r.allowed_path_prefixes_json or "[]"),
        "connector_semver": r.connector_semver or "",
        "origin_class": r.origin_class or "encyclopedia",
        "registry_revision": r.registry_revision or "",
        "connector_registered": connector_registered(r.connector or ""),
    }


class SourceIn(BaseModel):
    id: str
    name: str = ""
    tier: str = "A"
    connector: str = ""
    base_urls: list[str] = Field(default_factory=list)
    license_class: str = "unknown"
    rate_limit_qps: float = 1.0
    enabled: bool = False
    notes: str = ""
    origin_class: str = "encyclopedia"
    tos_notes: str = ""
    attribution_template: str = ""
    allowed_path_prefixes: list[str] = Field(default_factory=list)
    connector_semver: str = ""


class VerifyIn(BaseModel):
    by: str = "ops"


class JobIn(BaseModel):
    source_id: str
    params: dict[str, Any] = Field(default_factory=dict)


class ExploreIn(BaseModel):
    composer_id: str = ""
    wikidata_qid: str = ""
    wikipedia_title: str = ""
    max_depth: int = 2
    max_breadth: int = 24
    trigger: str = "ops"
    enqueue_crawl: bool = True


class RegisterCandidatesIn(BaseModel):
    candidate_ids: list[str] = Field(default_factory=list)
    min_score: float = 10.0


class EnqueueCrawlIn(BaseModel):
    sync: bool | None = None


class PrepareSeedsIn(BaseModel):
    limit: int = 8
    sync: bool | None = None
    featured_only: bool = True


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
        "sources_verified": db.query(SourceAuthority)
        .filter(SourceAuthority.verification_status == "verified")
        .count(),
        "jobs": db.query(FetchJob).count(),
        "artifacts": db.query(FetchArtifact).count(),
        "chunks": db.query(KnowledgeChunk).count(),
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


@router.get("/v1/kb/benchmark/suite")
def benchmark_suite() -> dict[str, Any]:
    suite = load_benchmark_suite()
    cases = [c for c in list(suite.get("cases") or []) if isinstance(c, dict)]
    return {
        "revision": suite.get("revision") or "",
        "case_count": len(cases),
        "required_case_count": sum(1 for c in cases if not c.get("optional")),
        "cases": [
            {
                "id": c.get("id"),
                "label": c.get("label"),
                "optional": bool(c.get("optional")),
            }
            for c in cases
        ],
    }


@router.get("/v1/kb/benchmark/dashboard")
def benchmark_dashboard(db: Session = Depends(_db)) -> dict[str, Any]:
    return build_dashboard_report(db)


@admin_router.post("/benchmark/run", status_code=200)
def benchmark_run(
    response: Response,
    db: Session = Depends(_db),
    trigger: str = "ops",
    async_mode: bool = Query(False, alias="async"),
) -> dict[str, Any]:
    settings = get_settings()
    sync = settings.sync_jobs and not async_mode
    if sync:
        return run_benchmark(db, trigger=trigger, sync=True)
    row = enqueue_benchmark_run(db, trigger=trigger, sync=False)
    response.status_code = 202
    return benchmark_run_summary(row)


@admin_router.get("/benchmark/runs")
def benchmark_runs(db: Session = Depends(_db), limit: int = 20) -> list[dict[str, Any]]:
    return list_benchmark_runs(db, limit=limit)


@admin_router.get("/benchmark/runs/{run_id}")
def benchmark_run_detail(run_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    report = get_benchmark_run(db, run_id)
    if not report:
        raise HTTPException(404, "benchmark run not found")
    return report


@admin_router.get("/benchmark/runs/{run_id}/diagnosis")
def benchmark_run_diagnosis(run_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    from aulos_knowledge.diagnosis import diagnose_benchmark_run, get_diagnosis_for_run

    existing = get_diagnosis_for_run(db, run_id)
    if existing:
        return existing
    return diagnose_benchmark_run(db, run_id)


@admin_router.post("/benchmark/runs/{run_id}/diagnose")
def benchmark_run_diagnose(run_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    from aulos_knowledge.diagnosis import diagnose_benchmark_run

    return diagnose_benchmark_run(db, run_id)


@admin_router.post("/improvements/{action_id}/execute")
def improvement_execute(action_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    from aulos_knowledge.improvement import execute_improvement_action

    settings = get_settings()
    return execute_improvement_action(db, action_id, sync=settings.sync_jobs)


@admin_router.post("/improvements/execute-safe")
def improvements_execute_safe(
    diagnosis_id: int,
    db: Session = Depends(_db),
) -> list[dict[str, Any]]:
    from aulos_knowledge.improvement import execute_safe_actions

    settings = get_settings()
    return execute_safe_actions(db, diagnosis_id, sync=settings.sync_jobs)


@admin_router.post("/improve/cycle", status_code=200)
def improve_cycle(
    response: Response,
    db: Session = Depends(_db),
    benchmark_run_id: int | None = None,
    async_mode: bool = Query(False, alias="async"),
) -> dict[str, Any]:
    from aulos_knowledge.improvement import run_improvement_cycle

    settings = get_settings()
    sync = settings.sync_jobs and not async_mode
    result = run_improvement_cycle(db, benchmark_run_id=benchmark_run_id, sync=sync)
    if not sync:
        response.status_code = 202
    return result


@admin_router.get("/sources")
def list_sources(db: Session = Depends(_db)) -> list[dict[str, Any]]:
    rows = db.query(SourceAuthority).order_by(SourceAuthority.id).all()
    return [_source_dict(r) for r in rows]


@admin_router.post("/sources")
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
        enabled=False if body.enabled and not connector_registered(body.connector) else body.enabled,
        notes=body.notes,
        verification_status="candidate",
        origin_class=body.origin_class or "encyclopedia",
        tos_notes=body.tos_notes,
        attribution_template=body.attribution_template,
        allowed_path_prefixes_json=json.dumps(body.allowed_path_prefixes, ensure_ascii=False),
        connector_semver=body.connector_semver,
    )
    if row.enabled and row.verification_status != "verified":
        row.enabled = False
    db.add(row)
    db.commit()
    return {"ok": True, "id": row.id, **_source_dict(row)}


@admin_router.patch("/sources/{source_id}")
def patch_source(source_id: str, body: dict[str, Any], db: Session = Depends(_db)) -> dict[str, Any]:
    row = db.get(SourceAuthority, source_id)
    if not row:
        raise HTTPException(404, "source not found")
    if "enabled" in body:
        want = bool(body["enabled"])
        if want:
            if (row.verification_status or "") != "verified":
                raise HTTPException(400, "cannot enable: source not verified")
            if not connector_registered(row.connector or ""):
                raise HTTPException(400, "cannot enable: connector not registered")
        row.enabled = want
    if "notes" in body:
        row.notes = str(body["notes"])
    if "rate_limit_qps" in body:
        row.rate_limit_qps = float(body["rate_limit_qps"])
    if "tos_notes" in body:
        row.tos_notes = str(body["tos_notes"])
    if "attribution_template" in body:
        row.attribution_template = str(body["attribution_template"])
    db.commit()
    return {"ok": True, **_source_dict(row)}


@admin_router.post("/sources/{source_id}/verify")
def verify_source(source_id: str, body: VerifyIn | None = None, db: Session = Depends(_db)) -> dict[str, Any]:
    row = db.get(SourceAuthority, source_id)
    if not row:
        raise HTTPException(404, "source not found")
    if not connector_registered(row.connector or ""):
        raise HTTPException(400, "cannot verify: connector not registered")
    by = (body.by if body else "ops") or "ops"
    row.verification_status = "verified"
    row.verified_by = by
    row.verified_at = utcnow()
    db.commit()
    return {"ok": True, **_source_dict(row)}


@admin_router.post("/sources/{source_id}/reject")
def reject_source(source_id: str, db: Session = Depends(_db)) -> dict[str, Any]:
    row = db.get(SourceAuthority, source_id)
    if not row:
        raise HTTPException(404, "source not found")
    row.verification_status = "rejected"
    row.enabled = False
    db.commit()
    return {"ok": True, **_source_dict(row)}


@admin_router.post("/sources/{source_id}/suspend")
def suspend_source(source_id: str, db: Session = Depends(_db)) -> dict[str, Any]:
    row = db.get(SourceAuthority, source_id)
    if not row:
        raise HTTPException(404, "source not found")
    row.verification_status = "suspended"
    row.enabled = False
    db.commit()
    return {"ok": True, **_source_dict(row)}


@admin_router.post("/sources/explore")
def explore_sources(body: ExploreIn, db: Session = Depends(_db)) -> dict[str, Any]:
    """REQ-009 — depth+breadth graph search for authority source candidates."""
    row = execute_discovery_run(
        db,
        composer_id=body.composer_id.strip(),
        wikidata_qid=body.wikidata_qid.strip().upper(),
        wikipedia_title=body.wikipedia_title.strip(),
        max_depth=max(1, min(body.max_depth, 4)),
        max_breadth=max(4, min(body.max_breadth, 64)),
        trigger=body.trigger or "ops",
        enqueue_crawl=bool(body.enqueue_crawl),
    )
    return discovery_run_dict(row)


@admin_router.get("/sources/explore/seeds")
def explore_seeds(db: Session = Depends(_db)) -> dict[str, Any]:
    """Product catalog for Explore: A–Z composers, famous badges, portraits."""
    return list_explore_seeds(db)


@admin_router.post("/sources/explore/prepare-seeds")
def prepare_explore_seeds(body: PrepareSeedsIn | None = None, db: Session = Depends(_db)) -> dict[str, Any]:
    """Enqueue Wikidata/Wikipedia crawls for curated famous composers (portraits + dossier)."""
    payload = body or PrepareSeedsIn()
    return prepare_famous_seed_crawls(
        db,
        sync=payload.sync,
        limit=max(1, min(payload.limit, 64)),
        featured_only=bool(payload.featured_only),
    )


@admin_router.get("/sources/explore/runs")
def list_explore_runs(db: Session = Depends(_db), limit: int = 20) -> list[dict[str, Any]]:
    rows = (
        db.query(SourceDiscoveryRun)
        .order_by(SourceDiscoveryRun.id.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return [discovery_run_dict(r) for r in rows]


@admin_router.get("/sources/explore/runs/{run_id}")
def get_explore_run(run_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    row = db.get(SourceDiscoveryRun, run_id)
    if not row:
        raise HTTPException(404, "discovery run not found")
    return discovery_run_dict(row)


@admin_router.post("/sources/explore/runs/{run_id}/register-candidates")
def register_explore_candidates(
    run_id: int,
    body: RegisterCandidatesIn | None = None,
    db: Session = Depends(_db),
) -> dict[str, Any]:
    try:
        result = register_discovery_candidates(
            db,
            run_id,
            candidate_ids=(body.candidate_ids if body and body.candidate_ids else None),
            min_score=(body.min_score if body else 10.0),
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"ok": True, **result}


@admin_router.post("/sources/explore/runs/{run_id}/enqueue-crawl")
def enqueue_explore_crawl(
    run_id: int,
    body: EnqueueCrawlIn | None = None,
    db: Session = Depends(_db),
) -> dict[str, Any]:
    """Enqueue authority bundle crawl for the discovery seed (verified sources only)."""
    try:
        result = enqueue_discovery_crawl(
            db,
            run_id,
            sync=(body.sync if body else None),
        )
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {"ok": True, **result}


@admin_router.get("/jobs")
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


@admin_router.post("/jobs")
def create_job(
    body: JobIn,
    response: Response,
    db: Session = Depends(_db),
    async_mode: bool = Query(False, alias="async"),
) -> dict[str, Any]:
    """Enqueue crawl job. Async (202) by default when SYNC_JOBS=false or ?async=true."""
    settings = get_settings()
    run_sync = settings.sync_jobs and not async_mode
    try:
        job = enqueue_and_maybe_run(
            db,
            source_id=body.source_id,
            params=body.params,
            sync=run_sync,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not run_sync:
        response.status_code = 202
    return {
        "id": job.id,
        "source_id": job.source_id,
        "status": job.status,
        "error": job.error,
        "async": not run_sync,
    }


@admin_router.get("/jobs/{job_id}")
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


@admin_router.get("/composers")
def list_composers(db: Session = Depends(_db), limit: int = 100) -> list[dict[str, Any]]:
    rows = db.query(ComposerEntity).order_by(ComposerEntity.name_en, ComposerEntity.id).limit(limit).all()
    return [
        {
            "id": c.id,
            "name_en": c.name_en,
            "name_zh": c.name_zh,
            "lifespan": c.lifespan,
            "era": getattr(c, "era", "") or "",
            "summary_en": getattr(c, "summary_en", "") or "",
            "external_ids": json.loads(c.external_ids_json or "{}"),
        }
        for c in rows
    ]


class BuildDossierIn(BaseModel):
    qid: str = ""
    wikidata_qid: str = ""


@admin_router.get("/composers/{composer_id}/dossier")
def admin_composer_dossier(composer_id: str, db: Session = Depends(_db)) -> dict[str, Any]:
    from aulos_knowledge.composer_dossier import build_composer_dossier

    payload = build_composer_dossier(db, composer_id)
    if not payload:
        raise HTTPException(404, f"composer not found: {composer_id}")
    return payload


@admin_router.post("/composers/{composer_id}/build-dossier", status_code=200)
def admin_build_composer_dossier(
    composer_id: str,
    response: Response,
    body: BuildDossierIn | None = None,
    db: Session = Depends(_db),
) -> dict[str, Any]:
    """Enqueue Wikidata mode=composer_dossier (REQ-010). Returns 202 when async."""
    from aulos_knowledge.composer_dossier import resolve_composer_qid

    body = body or BuildDossierIn()
    qid = resolve_composer_qid(db, composer_id, body.qid or body.wikidata_qid)
    if not qid:
        raise HTTPException(400, f"no Wikidata QID for composer: {composer_id}")
    settings = get_settings()
    try:
        job = enqueue_and_maybe_run(
            db,
            source_id="wikidata",
            params={
                "mode": "composer_dossier",
                "composer_id": composer_id,
                "qid": qid,
                "qids": [qid],
            },
            sync=settings.sync_jobs,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if not settings.sync_jobs:
        response.status_code = 202
    return {
        "job_id": job.id,
        "status": job.status,
        "composer_id": composer_id,
        "qid": qid,
        "error": job.error or "",
    }


@router.get("/v1/kb/composers/{composer_id}/dossier")
def kb_composer_dossier(
    composer_id: str,
    db: Session = Depends(_db),
    _: None = Depends(require_admin_token),
) -> dict[str, Any]:
    """Read dossier for RAG/product (S1: same admin token gate)."""
    from aulos_knowledge.composer_dossier import build_composer_dossier

    payload = build_composer_dossier(db, composer_id)
    if not payload:
        raise HTTPException(404, f"composer not found: {composer_id}")
    return payload


@admin_router.get("/documents")
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


def _chunk_summary(c: KnowledgeChunk) -> dict[str, Any]:
    text = c.text or ""
    return {
        "id": c.id,
        "document_id": c.document_id,
        "section": c.section,
        "aulos_work_id": c.aulos_work_id,
        "text_preview": text[:240],
        "text_len": len(text),
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _provenance_bundle(
    db: Session,
    *,
    doc: KnowledgeDocument,
    chunk: KnowledgeChunk | None = None,
) -> dict[str, Any]:
    src = db.get(SourceAuthority, doc.source_id) if doc.source_id else None
    art = db.get(FetchArtifact, doc.artifact_id) if doc.artifact_id else None
    job = db.get(FetchJob, doc.job_id) if doc.job_id else None
    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.document_id == doc.id)
        .order_by(KnowledgeChunk.id.asc())
        .all()
    )
    out: dict[str, Any] = {
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
        "chunks": [_chunk_summary(c) for c in chunks],
        "source": None
        if not src
        else {
            "id": src.id,
            "name": src.name,
            "tier": src.tier,
            "connector": src.connector,
            "license_class": src.license_class,
            "verification_status": src.verification_status,
            "origin_class": src.origin_class,
            "attribution_template": src.attribution_template,
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
    if chunk is not None:
        out["chunk"] = {
            "id": chunk.id,
            "document_id": chunk.document_id,
            "section": chunk.section,
            "aulos_work_id": chunk.aulos_work_id,
            "text": chunk.text or "",
            "created_at": chunk.created_at.isoformat() if chunk.created_at else None,
        }
    return out


@admin_router.get("/documents/{doc_id}")
def get_document(doc_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    out = _doc_summary(doc)
    out["body"] = doc.body or ""
    chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.document_id == doc.id)
        .order_by(KnowledgeChunk.id.asc())
        .all()
    )
    out["chunks"] = [_chunk_summary(c) for c in chunks]
    return out


@admin_router.post("/documents/{doc_id}/quarantine")
def quarantine_doc(doc_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    doc.status = "quarantine"
    db.commit()
    return {"ok": True, "id": doc_id, "status": "quarantine"}


@admin_router.post("/documents/{doc_id}/publish")
def publish_doc(doc_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    """Restore a quarantined (or draft) document to published — proofreading accept."""
    doc = db.get(KnowledgeDocument, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    doc.status = "published"
    db.commit()
    return {"ok": True, "id": doc_id, "status": "published"}


@admin_router.get("/provenance/{document_id}")
def provenance(document_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    doc = db.get(KnowledgeDocument, document_id)
    if not doc:
        raise HTTPException(404, "document not found")
    return _provenance_bundle(db, doc=doc)


@admin_router.get("/chunks/{chunk_id}/provenance")
def chunk_provenance(chunk_id: int, db: Session = Depends(_db)) -> dict[str, Any]:
    """Chunk-level provenance: chunk → document → source + artifact + job (REQ-008 S2)."""
    chunk = db.get(KnowledgeChunk, chunk_id)
    if not chunk:
        raise HTTPException(404, "chunk not found")
    doc = db.get(KnowledgeDocument, chunk.document_id)
    if not doc:
        raise HTTPException(404, "document not found for chunk")
    return _provenance_bundle(db, doc=doc, chunk=chunk)


@admin_router.get("/artifacts/{artifact_id}")
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


@admin_router.get("/media")
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


@admin_router.get("/media/{media_id}/content")
def media_content(media_id: int, db: Session = Depends(_db)) -> Response:
    """Serve crawled media bytes (portraits) for OPS Explore avatars."""
    row = db.get(MediaAsset, media_id)
    if not row or not row.storage_path:
        raise HTTPException(404, "media not found")
    settings = get_settings()
    path = Path(settings.artifact_root) / row.storage_path
    if not path.is_file():
        raise HTTPException(404, "media file missing on disk")
    media_type = row.content_type or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)
