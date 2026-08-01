"""Product person entity resolve — multi-source aggregate + bilingual (REQ-012)."""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aulos_api.auth.deps import get_optional_user
from aulos_api.db.models import User
from aulos_api.db.session import get_db
from aulos_api.services.knowledge_proxy import knowledge_enabled, proxy_knowledge

logger = logging.getLogger("aulos_api.entities")

router = APIRouter(prefix="/v1/entities", tags=["entities"])

_CJK = re.compile(r"[\u4e00-\u9fff]")


class PersonResolveIn(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    kind: str = Field(default="person", max_length=32)
    enrich: bool = True
    locale: str = Field(default="zh", max_length=8)


@router.get("/person")
async def get_person_card(
    name: str = Query(min_length=1, max_length=255),
    kind: str = Query(default="person", max_length=32),
    enrich: bool = Query(default=True),
    locale: str = Query(default="zh", max_length=8),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    _ = user
    return await _resolve(name=name, kind=kind, enrich=enrich, locale=locale, db=db)


@router.post("/person/resolve")
async def post_person_card(
    body: PersonResolveIn,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> dict:
    _ = user
    return await _resolve(name=body.name, kind=body.kind, enrich=body.enrich, locale=body.locale, db=db)


def _has_cjk(s: str) -> bool:
    return bool(_CJK.search(s or ""))


def _usable_bio(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 12:
        return False
    low = t.lower()
    if low.startswith("please note") or t.startswith("请注意"):
        return False
    if t.rstrip().endswith("是。") and len(t) < 48:
        return False
    if t.rstrip().endswith(" is .") or t.rstrip().endswith(" is."):
        return False
    return True


def _bilingual_complete(card: dict[str, Any] | None) -> bool:
    if not isinstance(card, dict) or card.get("source") == "unresolved":
        return False
    en = (card.get("summary_en") or "").strip()
    zh = (card.get("summary_zh") or "").strip()
    if not _usable_bio(en):
        return False
    if not zh or zh.startswith("请注意") or (not _usable_bio(zh) and len(zh) < 24):
        return False
    ext = card.get("external_ids") or {}
    # Require structured identity or encyclopedia provenance — Discogs-only+translate is not "done"
    if ext.get("wikidata") or ext.get("enwiki") or ext.get("zhwiki"):
        return True
    origins = {str(card.get("summary_en_origin") or ""), str(card.get("summary_zh_origin") or "")}
    if "wikipedia" in origins:
        return True
    if card.get("sources"):
        return True
    if card.get("lifespan") and "translated" not in origins:
        return True
    return False


def _apply_locale(card: dict[str, Any], locale: str) -> dict[str, Any]:
    loc = (locale or "zh").lower()
    if loc.startswith("en"):
        card["locale_default"] = "en"
        card["display_name"] = card.get("display_name_en") or card.get("display_name_zh") or card.get("display_name") or card.get("name")
        card["summary"] = card.get("summary_en") or card.get("summary_zh") or card.get("summary") or ""
    else:
        card["locale_default"] = "zh"
        card["display_name"] = card.get("display_name_zh") or card.get("display_name_en") or card.get("display_name") or card.get("name")
        card["summary"] = card.get("summary_zh") or card.get("summary_en") or card.get("summary") or ""
    return card


async def _knowledge_post(path: str, body: dict[str, Any], *, timeout: float = 60.0) -> dict[str, Any]:
    code, data, _headers = await proxy_knowledge("POST", path, json_body=body, timeout=timeout)
    if code >= 400:
        detail = data.get("detail") if isinstance(data, dict) else "knowledge error"
        raise HTTPException(status_code=code if code < 600 else 502, detail=detail)
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="invalid knowledge response")
    return data


async def _translate_missing_locale(db: Session, card: dict[str, Any]) -> dict[str, Any]:
    """Fill missing summary_zh or summary_en via OPS LLM; persist patch."""
    en = (card.get("summary_en") or "").strip()
    zh = (card.get("summary_zh") or "").strip()
    need_zh = len(zh) < 20 and len(en) >= 40
    need_en = len(en) < 40 and len(zh) >= 20
    need_name_zh = not (card.get("display_name_zh") or "").strip() and bool((card.get("display_name_en") or "").strip())
    # Do not translate obvious Discogs stubs / truncated junk
    if need_zh and (
        en.lower().startswith("please note")
        or en.rstrip().endswith(" is .")
        or en.rstrip().endswith(" is.")
        or len(en.split()) < 8
    ):
        need_zh = False
    if not (need_zh or need_en or need_name_zh):
        return card

    try:
        from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config

        cfg = load_llm_config(db)
        if not getattr(cfg, "ready_for_live", False):
            return card
    except Exception as exc:  # noqa: BLE001
        logger.warning("person_translate_llm_unavailable err=%s", exc)
        return card

    patch: dict[str, Any] = {
        "person_id": card.get("person_id") or "",
        "name": card.get("name") or "",
        "kind": card.get("kind") or "person",
    }

    async def _llm(prompt: str) -> str:
        live = await chat_with_ops_llm(db=db, message=prompt, timeout=60.0)
        if not live:
            return ""
        if isinstance(live, tuple):
            return str(live[0] or "").strip().strip('"')
        if isinstance(live, dict):
            return str(live.get("reply") or live.get("text") or live.get("content") or "").strip().strip('"')
        return str(live).strip().strip('"')

    try:
        if need_zh:
            translated = await _llm(
                "你是古典音乐文献译者。将下列音乐家简介忠实译为简体中文，"
                "不要添加原文没有的事实，不要解释，只输出译文：\n\n" + en
            )
            if len(translated) >= 12:
                patch["summary_zh"] = translated
                patch["summary_zh_origin"] = "translated"
                card["summary_zh"] = translated
                card["summary_zh_origin"] = "translated"
        if need_en:
            translated = await _llm(
                "You are a classical-music translator. Faithfully translate the following "
                "musician biography into clear English. Do not invent facts. "
                "Output only the translation:\n\n" + zh
            )
            if len(translated) >= 12:
                patch["summary_en"] = translated
                patch["summary_en_origin"] = "translated"
                card["summary_en"] = translated
                card["summary_en_origin"] = "translated"
        if need_name_zh:
            dn = str(card.get("display_name_en") or "")
            translated = await _llm(
                "将下列古典音乐家姓名译为常用简体中文译名，只输出译名：\n" + dn
            )
            if 1 < len(translated) <= 40 and _has_cjk(translated):
                patch["display_name_zh"] = translated
                card["display_name_zh"] = translated
    except Exception as exc:  # noqa: BLE001
        logger.warning("person_translate_failed err=%s", exc)
        return card

    if len(patch) <= 3:
        return card
    try:
        patched = await _knowledge_post("/v1/kb/entities/person/patch-locale", patch, timeout=30.0)
        return patched
    except HTTPException:
        return card


async def _resolve(*, name: str, kind: str, enrich: bool, locale: str, db: Session) -> dict:
    if not knowledge_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="knowledge plane disabled",
        )
    clean = name.strip()

    local = await _knowledge_post(
        "/v1/kb/entities/person/resolve",
        {"name": clean, "kind": kind, "enrich": False},
        timeout=30.0,
    )
    if _bilingual_complete(local) or not enrich:
        return _apply_locale(local, locale)

    # Fan-in: Discogs fragment + knowledge aggregate (Wikidata/Wikipedia)
    discogs_frag: dict[str, Any] | None = None
    try:
        from aulos_api.services.discogs import resolve_discogs_artist_card

        discogs_frag = resolve_discogs_artist_card(clean, kind=kind, db=db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("discogs_person_fragment_err name=%s err=%s", clean, exc)

    fragments: list[dict[str, Any]] = []
    if discogs_frag:
        fragments.append({**discogs_frag, "source_id": "discogs", "authority": "discogs"})

    card = await _knowledge_post(
        "/v1/kb/entities/person/aggregate",
        {
            "name": clean,
            "kind": kind,
            "fragments": fragments,
            "fetch_remote": True,
            "persist": True,
        },
        timeout=60.0,
    )

    if card.get("source") == "unresolved" and local.get("source") != "unresolved":
        card = local

    card = await _translate_missing_locale(db, card)
    return _apply_locale(card, locale)
