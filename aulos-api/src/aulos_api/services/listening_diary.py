"""Listening diary domain service (SPEC-019 / SPEC-020)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import (
    DiaryGuideLink,
    ListeningDiaryComment,
    ListeningDiaryLike,
    ListeningDiaryPost,
    ListeningGuide,
    User,
    UserFollow,
    utcnow,
)
from aulos_api.services.discogs import DiscogsError, build_diary_snapshot, fetch_discogs_entity
from aulos_api.services.share_slug import new_share_slug
from aulos_api.timefmt import to_utc_iso, to_utc_iso_optional

SUPPORTED_PROVIDERS = frozenset({"discogs"})
NOTE_MAX = 500
COMMENT_MAX = 1000


class DiaryError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _parse_listened_on(value: str | date | None) -> date:
    if value is None or value == "":
        return datetime.now(timezone.utc).date()
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise DiaryError("Invalid listened_on; expected YYYY-MM-DD", status_code=400) from exc


def _clamp_note(note: str | None) -> str:
    text = (note or "").strip()
    if len(text) > NOTE_MAX:
        raise DiaryError(f"listening_note max {NOTE_MAX} characters", status_code=400)
    return text


def diary_to_dict(
    row: ListeningDiaryPost,
    *,
    author: User | None = None,
    include_snapshot: bool = True,
) -> dict[str, Any]:
    published = row.status == "published" and bool(row.published_at)
    snap: dict[str, Any] = {}
    if include_snapshot and row.snapshot_json:
        try:
            parsed = json.loads(row.snapshot_json)
            if isinstance(parsed, dict):
                snap = parsed
        except json.JSONDecodeError:
            snap = {}
    out: dict[str, Any] = {
        "id": row.id,
        "user_id": row.user_id,
        "status": row.status,
        "source_provider": row.source_provider,
        "source_external_id": row.source_external_id,
        "source_kind": row.source_kind,
        "title": row.title,
        "cover_image_url": row.cover_image_url,
        "listening_note": row.listening_note,
        "listened_on": row.listened_on.isoformat() if row.listened_on else None,
        "share_slug": row.share_slug if published or row.share_slug else None,
        "share_path": f"/p/{row.share_slug}" if published and row.share_slug else None,
        "published": published,
        "published_at": to_utc_iso_optional(row.published_at),
        "like_count": int(row.like_count or 0),
        "comment_count": int(row.comment_count or 0),
        "created_at": to_utc_iso(row.created_at) if row.created_at else None,
        "updated_at": to_utc_iso(row.updated_at) if row.updated_at else None,
        "snapshot": snap if include_snapshot else None,
    }
    if author is not None:
        out["author"] = {
            "id": author.id,
            "display_name": author.display_name or author.email.split("@")[0],
        }
    return out


def attach_guides_to_diary_dict(
    db: Session,
    payload: dict[str, Any],
    *,
    post_id: int,
    public_only: bool = False,
) -> dict[str, Any]:
    payload["guides"] = list_diary_guides(db, post_id=post_id, public_only=public_only)
    return payload


def build_guide_message_from_diary(row: ListeningDiaryPost, *, aspect: str) -> tuple[str, str]:
    """Return (message, work_hint) for listening-guide queue."""
    snap: dict[str, Any] = {}
    try:
        parsed = json.loads(row.snapshot_json or "{}")
        if isinstance(parsed, dict):
            snap = parsed
    except json.JSONDecodeError:
        snap = {}
    title = (row.title or snap.get("title") or "Untitled release").strip()
    composers = snap.get("composers") or []
    performers = snap.get("performers") or []
    ensembles = snap.get("ensembles") or []
    year = snap.get("year") or ""
    label = snap.get("label") or ""
    catno = snap.get("catno") or ""
    uri = snap.get("uri") or ""
    note = (row.listening_note or "").strip()
    aspect_clean = (aspect or "作品导赏").strip() or "作品导赏"
    lines = [
        f'Write a professional classical listening guide (聆乐导赏) for "{title}".',
        f"Aspect focus: {aspect_clean}.",
    ]
    # Prefer Discogs command so the atelier chain locks identity via release id.
    if (row.source_provider or "").strip().lower() == "discogs" and (row.source_external_id or "").strip():
        lines.insert(0, f"/discogs #{str(row.source_external_id).strip()}")
    if composers:
        lines.append("Composers: " + ", ".join(str(c) for c in composers))
    if performers:
        lines.append("Performers: " + ", ".join(str(p) for p in performers))
    if ensembles:
        lines.append("Ensembles: " + ", ".join(str(e) for e in ensembles))
    if year or label or catno:
        lines.append(f"Release: year={year} label={label} catno={catno}".strip())
    if uri:
        lines.append(f"Discogs: {uri}")
    if note:
        lines.append(f"Listener note: {note}")
    lines.append("Produce a structured listening guide with historical context and how to listen.")
    composer_hint = str(composers[0]) if composers else ""
    work_hint = f"{composer_hint} — {title}".strip(" —") if composer_hint else title
    return "\n".join(lines), work_hint


def _derive_link_status(link: DiaryGuideLink, guide: ListeningGuide | None) -> str:
    stored = (link.status or "").strip() or "queued"
    if stored in {"published", "dismissed"}:
        return stored
    if guide is None:
        return "failed" if stored == "failed" else stored
    gs = (guide.status or "").strip()
    if gs in {"queued", "running"}:
        return "queued"
    if gs == "failed":
        return "failed"
    if gs == "completed":
        if guide.published_at and guide.share_slug:
            return "published"
        return "ready_for_review"
    return stored


def _link_actions(status: str) -> dict[str, bool]:
    return {
        "can_publish": status == "ready_for_review",
        "can_revise": status in {"ready_for_review", "failed", "published"},
        "can_unpublish": status == "published",
        "can_dismiss": status in {"ready_for_review", "published", "failed"},
        "can_delete": status in {"ready_for_review", "dismissed", "failed"},
    }


def guide_link_to_dict(link: DiaryGuideLink, guide: ListeningGuide | None) -> dict[str, Any]:
    status = _derive_link_status(link, guide)
    # Persist derived ready/failed when stale
    out: dict[str, Any] = {
        "id": link.id,
        "diary_post_id": link.diary_post_id,
        "guide_id": link.guide_id,
        "aspect": link.aspect or "",
        "status": status,
        "review_notes": getattr(link, "review_notes", None) or "",
        "revised_at": to_utc_iso_optional(getattr(link, "revised_at", None)),
        "notified_at": to_utc_iso_optional(link.notified_at),
        "published_at": to_utc_iso_optional(link.published_at),
        "created_at": to_utc_iso(link.created_at) if link.created_at else None,
        "actions": _link_actions(status),
        "guide": None,
    }
    if guide is not None:
        from aulos_api.services.listening_guide import guide_to_dict

        g = guide_to_dict(guide)
        # Keep payload lighter for lists
        out["guide"] = {
            "id": g["id"],
            "work_title": g.get("work_title"),
            "composer": g.get("composer"),
            "status": g.get("status"),
            "summary": g.get("summary"),
            "published": g.get("published"),
            "share_slug": g.get("share_slug"),
            "share_path": g.get("share_path"),
            "error_detail": g.get("error_detail"),
            "updated_at": g.get("updated_at"),
            "steps": g.get("steps") or [],
            "guide_html": g.get("guide_html") if status in {"ready_for_review", "published"} else "",
            "process_scorecard": g.get("process_scorecard"),
            "generation_rounds": g.get("generation_rounds")
            if status in {"ready_for_review", "published", "failed"}
            else None,
            "external_review_report": g.get("external_review_report")
            if status in {"ready_for_review", "published", "failed"}
            else None,
            "eval_pass": g.get("eval_pass"),
            "eval_score": g.get("eval_score"),
        }
    return out


def list_diary_guides(
    db: Session,
    *,
    post_id: int,
    public_only: bool = False,
) -> list[dict[str, Any]]:
    links = (
        db.query(DiaryGuideLink)
        .filter(DiaryGuideLink.diary_post_id == post_id)
        .order_by(DiaryGuideLink.id.desc())
        .all()
    )
    out: list[dict[str, Any]] = []
    for link in links:
        guide = db.get(ListeningGuide, link.guide_id) if link.guide_id else None
        item = guide_link_to_dict(link, guide)
        if public_only and item["status"] != "published":
            continue
        out.append(item)
    return out


def list_user_guide_tasks(db: Session, *, user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    rows = (
        db.query(DiaryGuideLink, ListeningDiaryPost)
        .join(ListeningDiaryPost, ListeningDiaryPost.id == DiaryGuideLink.diary_post_id)
        .filter(ListeningDiaryPost.user_id == user_id)
        .order_by(DiaryGuideLink.id.desc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    out: list[dict[str, Any]] = []
    for link, post in rows:
        guide = db.get(ListeningGuide, link.guide_id) if link.guide_id else None
        item = guide_link_to_dict(link, guide)
        item["diary_title"] = post.title
        item["diary_cover_image_url"] = post.cover_image_url
        item["needs_attention"] = item["status"] == "ready_for_review" and link.notified_at is None
        out.append(item)
    return out


def enqueue_diary_guide(
    db: Session,
    *,
    user_id: int,
    post_id: int,
    aspect: str = "作品导赏",
) -> dict[str, Any]:
    post = (
        db.query(ListeningDiaryPost)
        .filter(ListeningDiaryPost.id == post_id, ListeningDiaryPost.user_id == user_id)
        .one_or_none()
    )
    if post is None:
        raise DiaryError("Diary post not found", status_code=404)
    aspect_clean = (aspect or "作品导赏").strip()[:255] or "作品导赏"
    message, work_hint = build_guide_message_from_diary(post, aspect=aspect_clean)
    from aulos_api.services.listening_guide import create_queued_guide

    guide = create_queued_guide(db, user_id=user_id, message=message, work_hint=work_hint)
    link = DiaryGuideLink(
        diary_post_id=post.id,
        guide_id=guide.id,
        aspect=aspect_clean,
        status="queued",
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return guide_link_to_dict(link, guide)


def publish_diary_guide_link(db: Session, *, user_id: int, link_id: int) -> dict[str, Any]:
    link, post = _owned_link(db, user_id=user_id, link_id=link_id)
    if not link.guide_id:
        raise DiaryError("Guide missing on link", status_code=400)
    from aulos_api.services.listening_guide import get_owned_guide, publish_guide

    guide = get_owned_guide(db, user_id=user_id, guide_id=link.guide_id)
    if guide is None:
        raise DiaryError("Guide not found", status_code=404)
    if guide.status != "completed" or not (guide.guide_html or "").strip():
        raise DiaryError("Guide is not ready for review yet", status_code=409)
    published = publish_guide(db, user_id=user_id, guide_id=guide.id)
    if published is None:
        raise DiaryError("Failed to publish guide", status_code=400)
    link.status = "published"
    link.published_at = utcnow()
    if link.notified_at is None:
        link.notified_at = utcnow()
    db.add(link)
    db.commit()
    db.refresh(link)
    db.refresh(published)
    return guide_link_to_dict(link, published)


def dismiss_diary_guide_link(db: Session, *, user_id: int, link_id: int) -> dict[str, Any]:
    link, _post = _owned_link(db, user_id=user_id, link_id=link_id)
    status = _derive_link_status(
        link, db.get(ListeningGuide, link.guide_id) if link.guide_id else None
    )
    if status == "published" and link.guide_id:
        from aulos_api.services.listening_guide import unpublish_guide

        unpublish_guide(db, user_id=user_id, guide_id=link.guide_id)
        link.published_at = None
    link.status = "dismissed"
    if link.notified_at is None:
        link.notified_at = utcnow()
    db.add(link)
    db.commit()
    db.refresh(link)
    guide = db.get(ListeningGuide, link.guide_id) if link.guide_id else None
    return guide_link_to_dict(link, guide)


def unpublish_diary_guide_link(db: Session, *, user_id: int, link_id: int) -> dict[str, Any]:
    link, _post = _owned_link(db, user_id=user_id, link_id=link_id)
    if not link.guide_id:
        raise DiaryError("Guide missing on link", status_code=400)
    from aulos_api.services.listening_guide import get_owned_guide, unpublish_guide

    guide = get_owned_guide(db, user_id=user_id, guide_id=link.guide_id)
    if guide is None:
        raise DiaryError("Guide not found", status_code=404)
    unpublished = unpublish_guide(db, user_id=user_id, guide_id=guide.id)
    if unpublished is None:
        raise DiaryError("Failed to unpublish guide", status_code=400)
    link.status = "ready_for_review"
    link.published_at = None
    db.add(link)
    db.commit()
    db.refresh(link)
    db.refresh(unpublished)
    return guide_link_to_dict(link, unpublished)


def revise_diary_guide_link(
    db: Session,
    *,
    user_id: int,
    link_id: int,
    notes: str,
) -> dict[str, Any]:
    notes_clean = (notes or "").strip()
    if not notes_clean:
        raise DiaryError("Review notes are required", status_code=400)
    if len(notes_clean) > 4000:
        raise DiaryError("Review notes too long", status_code=400)
    link, _post = _owned_link(db, user_id=user_id, link_id=link_id)
    if not link.guide_id:
        raise DiaryError("Guide missing on link", status_code=400)
    from aulos_api.services.listening_guide import (
        enqueue_targeted_revise_guide,
        get_owned_guide,
        unpublish_guide,
    )

    guide = get_owned_guide(db, user_id=user_id, guide_id=link.guide_id)
    if guide is None:
        raise DiaryError("Guide not found", status_code=404)
    status = _derive_link_status(link, guide)
    if status not in {"ready_for_review", "failed", "published"}:
        raise DiaryError(f"Cannot revise from status={status}", status_code=409)
    if status == "published" or (guide.published_at and guide.share_slug):
        unpublish_guide(db, user_id=user_id, guide_id=guide.id)
        link.published_at = None

    work_hint = guide.work_title or None

    link.review_notes = notes_clean
    link.revised_at = utcnow()
    link.status = "queued"
    db.add(link)
    db.commit()

    # Identity-polluted guides cannot be cured by chamber patches — full recompose.
    escalate = False
    try:
        research = json.loads(guide.research_json or "{}")
        dossier = dict(research.get("corpus_dossier") or {}) if isinstance(research, dict) else {}
        from aulos_skills.identity_lock import dossier_betrays_identity_lock

        escalate = bool(
            dossier
            and dossier_betrays_identity_lock(
                dossier,
                work_title=guide.work_title or "",
                raw_message=guide.message or "",
            )
        )
    except Exception:  # noqa: BLE001
        escalate = False

    if escalate:
        from aulos_api.services.listening_guide import enqueue_recompose_guide

        recomposed = enqueue_recompose_guide(
            db,
            user_id=user_id,
            guide_id=guide.id,
            message=guide.message or None,
            work_hint=work_hint,
        )
    else:
        recomposed = enqueue_targeted_revise_guide(
            db,
            user_id=user_id,
            guide_id=guide.id,
            review_notes=notes_clean,
            work_hint=work_hint,
        )
    if recomposed is None:
        raise DiaryError("Failed to enqueue targeted revise", status_code=400)
    db.refresh(link)
    return guide_link_to_dict(link, recomposed)


def delete_diary_guide_link(db: Session, *, user_id: int, link_id: int) -> None:
    link, _post = _owned_link(db, user_id=user_id, link_id=link_id)
    guide = db.get(ListeningGuide, link.guide_id) if link.guide_id else None
    status = _derive_link_status(link, guide)
    if status == "published":
        raise DiaryError("Unpublish before deleting a published guide link", status_code=409)
    if status == "queued":
        raise DiaryError("Cannot delete while generation is in progress", status_code=409)
    guide_id = link.guide_id
    db.delete(link)
    db.commit()
    if guide_id:
        other = (
            db.query(DiaryGuideLink.id)
            .filter(DiaryGuideLink.guide_id == guide_id)
            .one_or_none()
        )
        if other is None:
            from aulos_api.services.listening_guide import delete_owned_guide, get_owned_guide

            g = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
            if g is not None and not (g.published_at and g.share_slug):
                delete_owned_guide(db, user_id=user_id, guide_id=guide_id)


def ack_diary_guide_link(db: Session, *, user_id: int, link_id: int) -> dict[str, Any]:
    link, _post = _owned_link(db, user_id=user_id, link_id=link_id)
    if link.notified_at is None:
        link.notified_at = utcnow()
        db.add(link)
        db.commit()
        db.refresh(link)
    guide = db.get(ListeningGuide, link.guide_id) if link.guide_id else None
    return guide_link_to_dict(link, guide)


def _owned_link(db: Session, *, user_id: int, link_id: int) -> tuple[DiaryGuideLink, ListeningDiaryPost]:
    row = (
        db.query(DiaryGuideLink, ListeningDiaryPost)
        .join(ListeningDiaryPost, ListeningDiaryPost.id == DiaryGuideLink.diary_post_id)
        .filter(DiaryGuideLink.id == link_id, ListeningDiaryPost.user_id == user_id)
        .one_or_none()
    )
    if row is None:
        raise DiaryError("Guide link not found", status_code=404)
    return row[0], row[1]


def create_diary_post(
    db: Session,
    *,
    user_id: int,
    provider: str,
    external_id: str,
    listening_note: str | None = None,
    listened_on: str | date | None = None,
    source_kind: str | None = None,
    client: Any = None,
) -> ListeningDiaryPost:
    prov = (provider or "").strip().lower()
    if prov not in SUPPORTED_PROVIDERS:
        raise DiaryError(f"Unsupported provider: {provider}", status_code=400)
    ext = str(external_id or "").strip()
    if not ext:
        raise DiaryError("external_id required", status_code=400)

    if prov == "discogs":
        try:
            payload = fetch_discogs_entity(ext, client=client, db=db)
        except DiscogsError as exc:
            raise DiaryError(str(exc), status_code=exc.status_code) from exc
        snap = build_diary_snapshot(payload)
    else:  # pragma: no cover — guarded by SUPPORTED_PROVIDERS
        raise DiaryError(f"Unsupported provider: {provider}", status_code=400)

    kind = (source_kind or snap.get("source_kind") or "release").strip() or "release"
    row = ListeningDiaryPost(
        user_id=user_id,
        status="draft",
        source_provider=prov,
        source_external_id=str(snap.get("external_id") or ext),
        source_kind=kind,
        title=str(snap.get("title") or "")[:512],
        cover_image_url=str(snap.get("cover_image_url") or "")[:1024],
        listening_note=_clamp_note(listening_note),
        listened_on=_parse_listened_on(listened_on),
        snapshot_json=json.dumps(snap, ensure_ascii=False),
        like_count=0,
        comment_count=0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_owned_diary(db: Session, *, user_id: int, post_id: int) -> ListeningDiaryPost | None:
    return (
        db.query(ListeningDiaryPost)
        .filter(ListeningDiaryPost.id == post_id, ListeningDiaryPost.user_id == user_id)
        .one_or_none()
    )


def list_owned_diaries(
    db: Session,
    *,
    user_id: int,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ListeningDiaryPost]:
    q = db.query(ListeningDiaryPost).filter(ListeningDiaryPost.user_id == user_id)
    if status_filter:
        q = q.filter(ListeningDiaryPost.status == status_filter)
    return (
        q.order_by(ListeningDiaryPost.created_at.desc())
        .offset(max(0, offset))
        .limit(min(100, max(1, limit)))
        .all()
    )


def patch_diary(
    db: Session,
    *,
    user_id: int,
    post_id: int,
    listening_note: str | None = None,
    listened_on: str | date | None = None,
) -> ListeningDiaryPost:
    row = get_owned_diary(db, user_id=user_id, post_id=post_id)
    if row is None:
        raise DiaryError("Diary post not found", status_code=404)
    if listening_note is not None:
        row.listening_note = _clamp_note(listening_note)
    if listened_on is not None:
        row.listened_on = _parse_listened_on(listened_on)
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def publish_diary(db: Session, *, user_id: int, post_id: int) -> ListeningDiaryPost:
    row = get_owned_diary(db, user_id=user_id, post_id=post_id)
    if row is None:
        raise DiaryError("Diary post not found", status_code=404)
    if not row.share_slug:
        row.share_slug = new_share_slug()
    row.status = "published"
    row.published_at = utcnow()
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def unpublish_diary(db: Session, *, user_id: int, post_id: int) -> ListeningDiaryPost:
    row = get_owned_diary(db, user_id=user_id, post_id=post_id)
    if row is None:
        raise DiaryError("Diary post not found", status_code=404)
    row.status = "draft"
    row.published_at = None
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_diary(db: Session, *, user_id: int, post_id: int) -> None:
    row = get_owned_diary(db, user_id=user_id, post_id=post_id)
    if row is None:
        raise DiaryError("Diary post not found", status_code=404)
    db.delete(row)
    db.commit()


def get_published_by_slug(db: Session, *, slug: str) -> ListeningDiaryPost | None:
    return (
        db.query(ListeningDiaryPost)
        .filter(
            ListeningDiaryPost.share_slug == slug,
            ListeningDiaryPost.status == "published",
            ListeningDiaryPost.published_at.isnot(None),
        )
        .one_or_none()
    )


def list_plaza_feed(db: Session, *, limit: int = 30, offset: int = 0) -> list[tuple[ListeningDiaryPost, User]]:
    rows = (
        db.query(ListeningDiaryPost, User)
        .join(User, User.id == ListeningDiaryPost.user_id)
        .filter(
            ListeningDiaryPost.status == "published",
            ListeningDiaryPost.published_at.isnot(None),
        )
        .order_by(ListeningDiaryPost.published_at.desc())
        .offset(max(0, offset))
        .limit(min(100, max(1, limit)))
        .all()
    )
    return list(rows)


def list_home_feed(
    db: Session,
    *,
    user_id: int,
    limit: int = 30,
    offset: int = 0,
) -> list[tuple[ListeningDiaryPost, User]]:
    followee_ids = [
        r[0]
        for r in db.query(UserFollow.followee_id).filter(UserFollow.follower_id == user_id).all()
    ]
    if not followee_ids:
        return []
    rows = (
        db.query(ListeningDiaryPost, User)
        .join(User, User.id == ListeningDiaryPost.user_id)
        .filter(
            ListeningDiaryPost.user_id.in_(followee_ids),
            ListeningDiaryPost.status == "published",
            ListeningDiaryPost.published_at.isnot(None),
        )
        .order_by(ListeningDiaryPost.published_at.desc())
        .offset(max(0, offset))
        .limit(min(100, max(1, limit)))
        .all()
    )
    return list(rows)


def follow_user(db: Session, *, follower_id: int, followee_id: int) -> UserFollow:
    if follower_id == followee_id:
        raise DiaryError("Cannot follow yourself", status_code=400)
    target = db.get(User, followee_id)
    if target is None or not target.is_active:
        raise DiaryError("User not found", status_code=404)
    existing = (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == follower_id, UserFollow.followee_id == followee_id)
        .one_or_none()
    )
    if existing is not None:
        return existing
    row = UserFollow(follower_id=follower_id, followee_id=followee_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def unfollow_user(db: Session, *, follower_id: int, followee_id: int) -> None:
    row = (
        db.query(UserFollow)
        .filter(UserFollow.follower_id == follower_id, UserFollow.followee_id == followee_id)
        .one_or_none()
    )
    if row is not None:
        db.delete(row)
        db.commit()


def get_user_public_blog(db: Session, *, user_id: int, limit: int = 30) -> tuple[User, list[ListeningDiaryPost]] | None:
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    posts = (
        db.query(ListeningDiaryPost)
        .filter(
            ListeningDiaryPost.user_id == user_id,
            ListeningDiaryPost.status == "published",
            ListeningDiaryPost.published_at.isnot(None),
        )
        .order_by(ListeningDiaryPost.published_at.desc())
        .limit(min(100, max(1, limit)))
        .all()
    )
    return user, posts


def _published_post(db: Session, post_id: int) -> ListeningDiaryPost:
    row = db.get(ListeningDiaryPost, post_id)
    if row is None or row.status != "published" or not row.published_at:
        raise DiaryError("Published diary post not found", status_code=404)
    return row


def like_post(db: Session, *, user_id: int, post_id: int) -> ListeningDiaryPost:
    row = _published_post(db, post_id)
    existing = (
        db.query(ListeningDiaryLike)
        .filter(ListeningDiaryLike.post_id == post_id, ListeningDiaryLike.user_id == user_id)
        .one_or_none()
    )
    if existing is None:
        db.add(ListeningDiaryLike(post_id=post_id, user_id=user_id))
        row.like_count = int(row.like_count or 0) + 1
        db.commit()
        db.refresh(row)
    return row


def unlike_post(db: Session, *, user_id: int, post_id: int) -> ListeningDiaryPost:
    row = _published_post(db, post_id)
    existing = (
        db.query(ListeningDiaryLike)
        .filter(ListeningDiaryLike.post_id == post_id, ListeningDiaryLike.user_id == user_id)
        .one_or_none()
    )
    if existing is not None:
        db.delete(existing)
        row.like_count = max(0, int(row.like_count or 0) - 1)
        db.commit()
        db.refresh(row)
    return row


def list_comments(db: Session, *, post_id: int, limit: int = 50) -> list[tuple[ListeningDiaryComment, User]]:
    _published_post(db, post_id)
    rows = (
        db.query(ListeningDiaryComment, User)
        .join(User, User.id == ListeningDiaryComment.user_id)
        .filter(
            ListeningDiaryComment.post_id == post_id,
            ListeningDiaryComment.deleted_at.is_(None),
        )
        .order_by(ListeningDiaryComment.created_at.asc())
        .limit(min(200, max(1, limit)))
        .all()
    )
    return list(rows)


def add_comment(db: Session, *, user_id: int, post_id: int, body: str) -> ListeningDiaryComment:
    row = _published_post(db, post_id)
    text = (body or "").strip()
    if not text:
        raise DiaryError("Comment body required", status_code=400)
    if len(text) > COMMENT_MAX:
        raise DiaryError(f"Comment max {COMMENT_MAX} characters", status_code=400)
    comment = ListeningDiaryComment(post_id=post_id, user_id=user_id, body=text)
    db.add(comment)
    row.comment_count = int(row.comment_count or 0) + 1
    db.commit()
    db.refresh(comment)
    return comment
