"""Listening diary + plaza SNS routes (SPEC-019 / SPEC-020)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import get_current_user, get_optional_user
from aulos_api.db.models import User
from aulos_api.db.session import get_db
from aulos_api.services import listening_diary as diary
from aulos_api.timefmt import to_utc_iso

router = APIRouter(tags=["listening-diary"])
private = APIRouter(prefix="/v1/listening-diary", tags=["listening-diary"])
plaza = APIRouter(prefix="/v1/plaza", tags=["listening-plaza"])
social = APIRouter(prefix="/v1/social", tags=["listening-social"])


class DiaryCreateIn(BaseModel):
    provider: str = Field(min_length=1, max_length=32)
    external_id: str = Field(min_length=1, max_length=128)
    listening_note: str | None = Field(default=None, max_length=500)
    listened_on: str | None = None
    source_kind: str | None = Field(default=None, max_length=32)


class DiaryPatchIn(BaseModel):
    listening_note: str | None = Field(default=None, max_length=500)
    listened_on: str | None = None


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=1000)


class DiaryGuideEnqueueIn(BaseModel):
    aspect: str = Field(default="作品导赏", max_length=255)


class DiaryGuideReviseIn(BaseModel):
    notes: str = Field(min_length=1, max_length=4000)


def _raise(exc: diary.DiaryError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@private.get("/guide-tasks")
def list_guide_tasks(
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    items = diary.list_user_guide_tasks(db, user_id=user.id, limit=limit)
    ready = sum(1 for i in items if i.get("status") == "ready_for_review")
    queued = sum(1 for i in items if i.get("status") == "queued")
    return {
        "items": items,
        "ready_for_review_count": ready,
        "queued_count": queued,
    }


@private.post("/guides/{link_id}/publish")
def publish_guide_link(
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return diary.publish_diary_guide_link(db, user_id=user.id, link_id=link_id)
    except diary.DiaryError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@private.post("/guides/{link_id}/unpublish")
def unpublish_guide_link(
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return diary.unpublish_diary_guide_link(db, user_id=user.id, link_id=link_id)
    except diary.DiaryError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@private.post("/guides/{link_id}/revise", status_code=status.HTTP_202_ACCEPTED)
def revise_guide_link(
    link_id: int,
    body: DiaryGuideReviseIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return diary.revise_diary_guide_link(
            db, user_id=user.id, link_id=link_id, notes=body.notes
        )
    except diary.DiaryError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@private.post("/guides/{link_id}/dismiss")
def dismiss_guide_link(
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return diary.dismiss_diary_guide_link(db, user_id=user.id, link_id=link_id)
    except diary.DiaryError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@private.delete("/guides/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_guide_link(
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        diary.delete_diary_guide_link(db, user_id=user.id, link_id=link_id)
    except diary.DiaryError as exc:
        _raise(exc)


@private.post("/guides/{link_id}/ack")
def ack_guide_link(
    link_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return diary.ack_diary_guide_link(db, user_id=user.id, link_id=link_id)
    except diary.DiaryError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@private.post("/{post_id}/guides", status_code=status.HTTP_202_ACCEPTED)
def enqueue_guide_for_diary(
    post_id: int,
    body: DiaryGuideEnqueueIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        return diary.enqueue_diary_guide(
            db, user_id=user.id, post_id=post_id, aspect=body.aspect
        )
    except diary.DiaryError as exc:
        _raise(exc)
    raise AssertionError("unreachable")


@private.get("/{post_id}/guides")
def list_guides_for_diary(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = diary.get_owned_diary(db, user_id=user.id, post_id=post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Diary post not found")
    return {"items": diary.list_diary_guides(db, post_id=post_id, public_only=False)}


@private.post("", status_code=status.HTTP_201_CREATED)
def create_diary(
    body: DiaryCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.create_diary_post(
            db,
            user_id=user.id,
            provider=body.provider,
            external_id=body.external_id,
            listening_note=body.listening_note,
            listened_on=body.listened_on,
            source_kind=body.source_kind,
        )
    except diary.DiaryError as exc:
        _raise(exc)
    return diary.diary_to_dict(row, author=user)


@private.get("")
def list_my_diary(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    rows = diary.list_owned_diaries(
        db, user_id=user.id, status_filter=status_filter, limit=limit, offset=offset
    )
    return [diary.diary_to_dict(r, author=user, include_snapshot=True) for r in rows]


@private.get("/{post_id}")
def get_my_diary(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    row = diary.get_owned_diary(db, user_id=user.id, post_id=post_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Diary post not found")
    payload = diary.diary_to_dict(row, author=user)
    return diary.attach_guides_to_diary_dict(db, payload, post_id=post_id, public_only=False)


@private.patch("/{post_id}")
def patch_my_diary(
    post_id: int,
    body: DiaryPatchIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.patch_diary(
            db,
            user_id=user.id,
            post_id=post_id,
            listening_note=body.listening_note,
            listened_on=body.listened_on,
        )
    except diary.DiaryError as exc:
        _raise(exc)
    return diary.diary_to_dict(row, author=user)


@private.post("/{post_id}/publish")
def publish_my_diary(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.publish_diary(db, user_id=user.id, post_id=post_id)
    except diary.DiaryError as exc:
        _raise(exc)
    return diary.diary_to_dict(row, author=user)


@private.post("/{post_id}/unpublish")
def unpublish_my_diary(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.unpublish_diary(db, user_id=user.id, post_id=post_id)
    except diary.DiaryError as exc:
        _raise(exc)
    return diary.diary_to_dict(row, author=user)


@private.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_diary(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    try:
        diary.delete_diary(db, user_id=user.id, post_id=post_id)
    except diary.DiaryError as exc:
        _raise(exc)


@plaza.get("/feed")
def plaza_feed(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = diary.list_plaza_feed(db, limit=limit, offset=offset)
    return {
        "items": [diary.diary_to_dict(post, author=author, include_snapshot=False) for post, author in rows],
        "limit": limit,
        "offset": offset,
    }


@plaza.get("/home")
def plaza_home(
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = diary.list_home_feed(db, user_id=user.id, limit=limit, offset=offset)
    return {
        "items": [diary.diary_to_dict(post, author=author, include_snapshot=False) for post, author in rows],
        "limit": limit,
        "offset": offset,
    }


@plaza.get("/posts/{slug}")
def plaza_post_by_slug(
    slug: str,
    _user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    row = diary.get_published_by_slug(db, slug=slug)
    if row is None:
        raise HTTPException(status_code=404, detail="Published diary post not found")
    author = db.get(User, row.user_id)
    payload = diary.diary_to_dict(row, author=author)
    return diary.attach_guides_to_diary_dict(db, payload, post_id=row.id, public_only=True)


@plaza.post("/posts/{post_id}/likes")
def like_plaza_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.like_post(db, user_id=user.id, post_id=post_id)
    except diary.DiaryError as exc:
        _raise(exc)
    author = db.get(User, row.user_id)
    return diary.diary_to_dict(row, author=author, include_snapshot=False)


@plaza.delete("/posts/{post_id}/likes")
def unlike_plaza_post(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.unlike_post(db, user_id=user.id, post_id=post_id)
    except diary.DiaryError as exc:
        _raise(exc)
    author = db.get(User, row.user_id)
    return diary.diary_to_dict(row, author=author, include_snapshot=False)


@plaza.get("/posts/{post_id}/comments")
def list_plaza_comments(
    post_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    _user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        rows = diary.list_comments(db, post_id=post_id, limit=limit)
    except diary.DiaryError as exc:
        _raise(exc)
    return {
        "items": [
            {
                "id": c.id,
                "post_id": c.post_id,
                "body": c.body,
                "created_at": to_utc_iso(c.created_at) if c.created_at else None,
                "author": {
                    "id": u.id,
                    "display_name": u.display_name or u.email.split("@")[0],
                },
            }
            for c, u in rows
        ]
    }


@plaza.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def add_plaza_comment(
    post_id: int,
    body: CommentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        comment = diary.add_comment(db, user_id=user.id, post_id=post_id, body=body.body)
    except diary.DiaryError as exc:
        _raise(exc)
    return {
        "id": comment.id,
        "post_id": comment.post_id,
        "body": comment.body,
        "created_at": to_utc_iso(comment.created_at) if comment.created_at else None,
        "author": {
            "id": user.id,
            "display_name": user.display_name or user.email.split("@")[0],
        },
    }


@social.post("/follows/{user_id}")
def follow(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    try:
        row = diary.follow_user(db, follower_id=user.id, followee_id=user_id)
    except diary.DiaryError as exc:
        _raise(exc)
    return {"follower_id": row.follower_id, "followee_id": row.followee_id}


@social.delete("/follows/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    diary.unfollow_user(db, follower_id=user.id, followee_id=user_id)


@social.get("/users/{user_id}")
def public_user_blog(
    user_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    _viewer: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    packed = diary.get_user_public_blog(db, user_id=user_id, limit=limit)
    if packed is None:
        raise HTTPException(status_code=404, detail="User not found")
    author, posts = packed
    return {
        "user": {
            "id": author.id,
            "display_name": author.display_name or author.email.split("@")[0],
        },
        "posts": [diary.diary_to_dict(p, author=author, include_snapshot=False) for p in posts],
    }


router.include_router(private)
router.include_router(plaza)
router.include_router(social)
