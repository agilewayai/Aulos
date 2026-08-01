"""Listening guide API — classical art-agent MVP + public share + recompose."""

from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import get_current_user
from aulos_api.db.models import ListeningGuide, User
from aulos_api.db.session import get_db
from aulos_api.services.knowledge_base import knowledge_stats, retrieve as kb_retrieve
from aulos_api.services.discogs import DiscogsError
from aulos_api.services.listening_guide import (
    create_queued_guide,
    delete_owned_guide,
    enqueue_recompose_guide,
    get_owned_guide,
    get_owned_guide_by_share_slug,
    get_published_guide_by_slug,
    guide_to_dict,
    guide_trace_dict,
    iter_guide_job_events,
    list_owned_guides,
    publish_guide,
    retry_listening_guide_job,
    run_listening_guide_workflow,
    set_guide_favorite,
    set_guide_tags,
    unpublish_guide,
    update_publish_guide,
)
from aulos_api.security_headers import PUBLIC_GUIDE_CSP, SECURITY_HEADERS
from aulos_api.services.guide_html_security import prepare_public_guide_html
from aulos_api.timefmt import to_utc_iso_optional

router = APIRouter(tags=["listening-guides"])
private = APIRouter(prefix="/v1/listening-guides", tags=["listening-guides"])
public = APIRouter(prefix="/v1/public/guides", tags=["public-guides"])
knowledge = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])




class ListeningGuideRequest(BaseModel):
    message: str = Field(min_length=3, max_length=2000)
    work_hint: str | None = Field(default=None, max_length=255)


class RecomposeRequest(BaseModel):
    message: str | None = Field(default=None, max_length=2000)
    work_hint: str | None = Field(default=None, max_length=255)


class WorkflowStepOut(BaseModel):
    id: str
    title: str
    status: str
    thinking: str = ""
    detail: str = ""
    skill_id: str | None = None
    skill_version: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    index: int | None = None
    total: int | None = None


class ListeningGuideOut(BaseModel):
    id: int
    work_title: str
    composer: str
    status: str
    source: str
    summary: str
    guide_html: str
    steps: list[WorkflowStepOut]
    skill_versions: dict[str, str] = {}
    eval_pass: bool | None = None
    eval_score: int | None = None
    process_scorecard: dict | None = None
    generation_rounds: dict | None = None
    external_review_report: dict | None = None
    created_at: datetime | str | None = None
    updated_at: datetime | str | None = None
    published: bool = False
    share_slug: str | None = None
    share_path: str | None = None
    published_at: datetime | str | None = None
    message: str = ""
    error_detail: str = ""
    favorited: bool = False
    favorited_at: datetime | str | None = None
    tags: list[str] = []


class TagsUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=12)


class PublicGuideMeta(BaseModel):
    work_title: str
    composer: str
    summary: str
    share_slug: str
    share_path: str
    published_at: datetime | str | None = None


class ShareOwnershipOut(BaseModel):
    id: int
    work_title: str
    composer: str
    published: bool
    share_slug: str | None = None
    share_path: str | None = None
    owner: bool = True


def _sse(event_iter):
    async def event_gen():
        async for item in event_iter:
            event = item.get("event", "message")
            data = json.dumps(item.get("data") or {}, ensure_ascii=False)
            yield f"event: {event}\ndata: {data}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@private.post("", response_model=ListeningGuideOut, status_code=status.HTTP_201_CREATED)
async def create_listening_guide(
    body: ListeningGuideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    try:
        row = await run_listening_guide_workflow(
            db=db,
            user_id=user.id,
            message=body.message.strip(),
            work_hint=(body.work_hint or "").strip() or None,
        )
    except DiscogsError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/jobs", response_model=ListeningGuideOut, status_code=status.HTTP_202_ACCEPTED)
def enqueue_listening_guide_job(
    body: ListeningGuideRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = create_queued_guide(
        db,
        user_id=user.id,
        message=body.message.strip(),
        work_hint=(body.work_hint or "").strip() or None,
    )
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/stream")
async def stream_listening_guide(
    body: ListeningGuideRequest,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    # SPEC-013: enqueue durable job, then attach reconnect-safe events.
    # Avoid Depends(get_db) so the request session is not held for the SSE lifetime.
    from aulos_api.db import session as db_session

    db_session.get_engine()
    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        row = create_queued_guide(
            db,
            user_id=user.id,
            message=body.message.strip(),
            work_hint=(body.work_hint or "").strip() or None,
        )
        guide_id = row.id
    finally:
        db.close()
    return _sse(iter_guide_job_events(user_id=user.id, guide_id=guide_id))


@private.get("", response_model=list[ListeningGuideOut])
def list_listening_guides(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, max_length=200),
    status_filter: str | None = Query(default=None, alias="status", max_length=32),
    published: bool | None = Query(default=None),
    favorited: bool | None = Query(default=None),
    tag: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ListeningGuideOut]:
    rows = list_owned_guides(
        db,
        user_id=user.id,
        q=q,
        status=status_filter,
        published=published,
        favorited=favorited,
        tag=tag,
        limit=limit,
        offset=offset,
    )
    return [ListeningGuideOut(**guide_to_dict(r)) for r in rows]


@private.get("/by-share/{slug}", response_model=ShareOwnershipOut)
def get_guide_by_share_slug(
    slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ShareOwnershipOut:
    row = get_owned_guide_by_share_slug(db, user_id=user.id, slug=slug)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found for this account")
    published = bool(row.share_slug and row.published_at)
    return ShareOwnershipOut(
        id=row.id,
        work_title=row.work_title,
        composer=row.composer or "",
        published=published,
        share_slug=row.share_slug if published else row.share_slug,
        share_path=f"/g/{row.share_slug}" if row.share_slug else None,
        owner=True,
    )


@private.get("/{guide_id}", response_model=ListeningGuideOut)
def get_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = get_owned_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.delete("/{guide_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not delete_owned_guide(db, user_id=user.id, guide_id=guide_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")


@private.post("/{guide_id}/favorite", response_model=ListeningGuideOut)
def favorite_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = set_guide_favorite(db, user_id=user.id, guide_id=guide_id, favorited=True)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.delete("/{guide_id}/favorite", response_model=ListeningGuideOut)
def unfavorite_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = set_guide_favorite(db, user_id=user.id, guide_id=guide_id, favorited=False)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.patch("/{guide_id}/tags", response_model=ListeningGuideOut)
def patch_listening_guide_tags(
    guide_id: int,
    body: TagsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = set_guide_tags(db, user_id=user.id, guide_id=guide_id, tags=body.tags)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.get("/{guide_id}/events")
async def stream_guide_job_events(
    guide_id: int,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    from aulos_api.db import session as db_session

    db_session.get_engine()
    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        row = get_owned_guide(db, user_id=user.id, guide_id=guide_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    finally:
        db.close()
    return _sse(iter_guide_job_events(user_id=user.id, guide_id=guide_id))


@private.post("/{guide_id}/retry", response_model=ListeningGuideOut, status_code=status.HTTP_202_ACCEPTED)
def retry_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    """Re-queue failed or stale-running jobs (SPEC-013 robust recovery)."""
    row = retry_listening_guide_job(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Guide cannot be retried (missing or already completed)",
        )
    return ListeningGuideOut(**guide_to_dict(row))


@private.get("/{guide_id}/trace")
def get_listening_guide_trace(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """SPEC-012: owner diagnostic chain_trace for 复盘."""
    row = get_owned_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return guide_trace_dict(row)


@private.post("/{guide_id}/recompose/jobs", response_model=ListeningGuideOut, status_code=status.HTTP_202_ACCEPTED)
def enqueue_recompose_job(
    guide_id: int,
    body: RecomposeRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    body = body or RecomposeRequest()
    row = enqueue_recompose_guide(
        db,
        user_id=user.id,
        guide_id=guide_id,
        message=(body.message or "").strip() or None,
        work_hint=(body.work_hint or "").strip() or None,
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/{guide_id}/recompose/stream")
async def stream_recompose_guide(
    guide_id: int,
    body: RecomposeRequest | None = None,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    body = body or RecomposeRequest()
    from aulos_api.db import session as db_session

    db_session.get_engine()
    assert db_session.SessionLocal is not None
    db = db_session.SessionLocal()
    try:
        row = enqueue_recompose_guide(
            db,
            user_id=user.id,
            guide_id=guide_id,
            message=(body.message or "").strip() or None,
            work_hint=(body.work_hint or "").strip() or None,
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    finally:
        db.close()
    return _sse(iter_guide_job_events(user_id=user.id, guide_id=guide_id))


@private.post("/{guide_id}/update-publish", response_model=ListeningGuideOut)
def update_publish_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = update_publish_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/{guide_id}/publish", response_model=ListeningGuideOut)
def publish_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = publish_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@private.post("/{guide_id}/unpublish", response_model=ListeningGuideOut)
def unpublish_listening_guide(
    guide_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListeningGuideOut:
    row = unpublish_guide(db, user_id=user.id, guide_id=guide_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Guide not found")
    return ListeningGuideOut(**guide_to_dict(row))


@public.get("/{slug}", response_class=HTMLResponse)
def public_guide_page(slug: str, db: Session = Depends(get_db)) -> HTMLResponse:
    """Public share page — no authentication. Serves the composed guide HTML only."""
    row = get_published_guide_by_slug(db, slug)
    if row is None or not (row.guide_html or "").strip():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared guide not found")
    html = prepare_public_guide_html(row.guide_html)
    headers = {
        **SECURITY_HEADERS,
        "Cache-Control": "public, max-age=60",
        "X-Robots-Tag": "noindex",
        "Content-Security-Policy": PUBLIC_GUIDE_CSP,
    }
    return HTMLResponse(content=html, headers=headers)


@public.get("/{slug}/meta", response_model=PublicGuideMeta)
def public_guide_meta(slug: str, db: Session = Depends(get_db)) -> PublicGuideMeta:
    row = get_published_guide_by_slug(db, slug)
    if row is None or not row.share_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shared guide not found")
    return PublicGuideMeta(
        work_title=row.work_title,
        composer=row.composer or "",
        summary=row.summary or "",
        share_slug=row.share_slug,
        share_path=f"/g/{row.share_slug}",
        published_at=to_utc_iso_optional(row.published_at),
    )


@knowledge.get("/search")
def knowledge_search(
    q: str = Query(min_length=1, max_length=500),
    work_hint: str = Query(default="", max_length=255),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    result = kb_retrieve(
        db,
        query=q,
        work_hint=work_hint,
        user_id=user.id,
        k=6,
    )
    # Don't dump full dossier in search preview
    dossier = result.get("kb_dossier") or {}
    return {
        "rag_mode": result.get("rag_mode"),
        "hits": result.get("hits") or [],
        "matched_title": dossier.get("work_title"),
        "matched_composer": dossier.get("composer"),
        "stats": knowledge_stats(db),
    }


@knowledge.get("/stats")
def get_knowledge_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return knowledge_stats(db)


discogs_api = APIRouter(prefix="/v1/discogs", tags=["discogs"])


@discogs_api.get("/search")
def discogs_search(
    q: str = Query("", min_length=0, max_length=200),
    limit: int = Query(10, ge=1, le=25),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """AJAX autocomplete for Discogs releases (catalog / title / artist)."""
    _ = user
    from aulos_api.services.discogs import DiscogsError, suggest_discogs_releases

    try:
        results = suggest_discogs_releases(q, db=db, limit=limit)
    except DiscogsError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return {"query": q.strip(), "results": results}


router.include_router(private)
router.include_router(public)
router.include_router(knowledge)
router.include_router(discogs_api)
