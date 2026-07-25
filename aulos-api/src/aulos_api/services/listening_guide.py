"""Classical listening-guide workflow — API gateway delegates to aulos-agent tools."""

from __future__ import annotations

import json
import logging
import secrets
import sys
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.config import get_settings
from aulos_api.db.models import ListeningGuide
from aulos_api.services.agent_proxy import AgentProxy
from aulos_api.services.knowledge_base import retrieve as kb_retrieve
from aulos_api.services.knowledge_base import upsert_from_report
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config
from aulos_api.services.skills_ops import _load_disabled
from aulos_api.timefmt import to_utc_iso_optional

logger = logging.getLogger("aulos_api.listening")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return to_utc_iso_optional(dt)


def _new_share_slug() -> str:
    return secrets.token_urlsafe(12).replace("-", "").replace("_", "")[:16]


def _research_payload(report: Any) -> dict[str, Any]:
    ctx = getattr(report, "context", None) or {}
    dossier = dict(ctx.get("corpus_dossier") or {})
    if not dossier:
        width = dict(ctx.get("width_dossier") or {})
        dossier = dict(width.get("salon_dossier") or {})
    return {
        "eval_pass": report.eval_pass,
        "eval_score": report.eval_score,
        "skill_versions": report.skill_versions,
        "corpus_hit": bool(ctx.get("corpus_hit")),
        "synthesize_hit": bool(ctx.get("synthesize_hit")),
        "synthesize_source": ctx.get("synthesize_source"),
        "rag_mode": ctx.get("rag_mode"),
        "rag_hit_count": len(ctx.get("rag_hits") or []),
        "web_research": ctx.get("web_research") or ctx.get("web_research_meta"),
        "corpus_dossier": dossier,
        "work_title": report.work_title,
        "composer": report.composer,
        "summary": report.summary,
    }


async def _optional_llm_dossier(
    db: Session,
    work_title: str,
    composer: str,
    *,
    rag_hits: list[str] | None = None,
    facets: dict[str, Any] | None = None,
    family_id: str | None = None,
) -> tuple[dict | None, str | None, str]:
    """Generic Salon Codex enricher — no composer/work branches; KB hits as evidence."""
    cfg = load_llm_config(db)
    if not cfg.ready_for_live:
        return None, None, "agent-skills"
    facet_bits = []
    for key in ("instruments", "forms", "era", "ensemble"):
        vals = list((facets or {}).get(key) or [])
        if vals:
            facet_bits.append(f"{key}: {', '.join(str(v) for v in vals)}")
    evidence = [str(h).strip() for h in (rag_hits or []) if str(h).strip()][:8]
    evidence_block = "\n".join(f"- {h[:280]}" for h in evidence) if evidence else "- (none yet — rely on established musicology; label uncertainty)"
    prompt = (
        "You are Aulos, a classical listening-guide research agent.\n"
        "Fill a bilingual Salon Codex dossier for ANY identified work. "
        "Do not specialize by composer name in procedure — use form/instrument/era facets and evidence.\n"
        f"Work: {work_title}\n"
        f"Composer: {composer or 'unknown'}\n"
        f"Family hint (optional scaffold id): {family_id or 'none'}\n"
        f"Facets: {'; '.join(facet_bits) if facet_bits else 'none'}\n\n"
        "KB / prior-research evidence (may be partial; never invent citations beyond search URLs):\n"
        f"{evidence_block}\n\n"
        "Return ONLY a compact JSON object (no markdown) with:\n"
        "listening_thesis, work_introduction, era, form,\n"
        "composer_profile {{lifespan, summary, temperament, place_in_oeuvre, place_in_history}},\n"
        "genesis {{year, place, publication, patronage, background, instrument_culture}},\n"
        "historical_stature {{reasons: [], reception_arc}},\n"
        "width_points, depth_points,\n"
        "listening_map ([{{label,cue}}]), variation_deepdives ([{{title,note}}]),\n"
        "sound_world {{original_instrument, ensemble_notes, modern_modes: []}},\n"
        "related_works ([{{title,why}}]),\n"
        "interpretations ([{{artist,year,instrument,era_note,why_listen}}] — named traditions OK; "
        "youtube_url/discogs_url only as https://www.youtube.com/results?search_query=... or "
        "https://www.discogs.com/search/?q=... search links),\n"
        "appreciation_videos ([{{title,url,why}}] search links only),\n"
        "vinyl_and_discography ([{{label,url,note}}] Discogs search links only),\n"
        "practice_notes, myths_and_caveats,\n"
        "and nested zh_hans with the SAME chambers in Simplified Chinese 导赏 prose "
        "(简体：肖邦/德沃夏克/导赏/录音; no Chinglish; no skill jargon),\n"
        "and nested zh_hant with the SAME chambers in Traditional Chinese "
        "(繁体：蕭邦/德弗札克/導賞/錄音; 繁体字形与用词).\n"
        "Also include legacy nested zh equal to zh_hans for compatibility.\n"
        "Rules: ear-actionable; label legends; no invented Discogs/YouTube item IDs; "
        "no copying unrelated flagship works; keep JSON under 2200 words.\n"
        "CRITICAL: zh_hans and zh_hant required — omit neither English nor Chinese layers."
    )
    try:
        live = await chat_with_ops_llm(db=db, message=prompt, timeout=90.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_dossier_failed work=%s err=%s", work_title, exc)
        return None, None, "agent-skills"
    if live is None:
        return None, None, "agent-skills"
    text, provider = live
    try:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.salon_codex import parse_llm_dossier_json
    except ImportError:
        return None, text[:400], f"agent-skills+{provider}"
    dossier = parse_llm_dossier_json(text)
    note = None if dossier else text[:400]
    return (dossier or None), note, f"agent-skills+{provider}"


async def _optional_llm_note(db: Session, work_title: str) -> tuple[str | None, str]:
    cfg = load_llm_config(db)
    if not cfg.ready_for_live:
        return None, "agent-skills"
    prompt = (
        "You are Aulos, a classical-music research agent. "
        f"Give a compact enrichment note (max 80 words) for listening to: {work_title}."
    )
    try:
        live = await chat_with_ops_llm(db=db, message=prompt, timeout=45.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("llm_note_failed work=%s err=%s", work_title, exc)
        return None, "agent-skills"
    if live is None:
        return None, "agent-skills"
    text, provider = live
    return text, f"agent-skills+{provider}"


def _steps_as_dicts(report: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in report.steps or []:
        if hasattr(s, "to_workflow_dict"):
            out.append(s.to_workflow_dict())
        elif isinstance(s, dict):
            out.append(s)
    return out


def _apply_report_to_row(row: ListeningGuide, *, report: Any, source: str) -> ListeningGuide:
    steps = _steps_as_dicts(report)
    row.work_title = report.work_title
    row.composer = report.composer
    row.status = "completed"
    row.source = source
    row.summary = report.summary
    row.guide_html = report.guide_html
    row.steps_json = json.dumps(steps)
    row.research_json = json.dumps(_research_payload(report), ensure_ascii=False)
    row.skill_versions_json = json.dumps(report.skill_versions)
    return row


def _persist_report(
    *,
    db: Session,
    user_id: int,
    report: Any,
    source: str,
    existing: ListeningGuide | None = None,
) -> ListeningGuide:
    if existing is not None:
        row = _apply_report_to_row(existing, report=report, source=source)
        db.add(row)
    else:
        row = ListeningGuide(user_id=user_id)
        _apply_report_to_row(row, report=report, source=source)
        db.add(row)
    db.commit()
    db.refresh(row)
    try:
        upsert_from_report(db, report=report, guide_id=row.id, user_id=user_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("kb_index_failed guide=%s err=%s", row.id, exc)
    logger.info(
        "listening_guide_ok id=%s user=%s work=%s source=%s skills=%s recompose=%s",
        row.id,
        user_id,
        report.work_title,
        source,
        list(report.skill_versions.keys()),
        existing is not None,
    )
    return row


def _rag_context(db: Session, *, message: str, work_hint: str, composer: str, user_id: int) -> dict[str, Any]:
    try:
        local = kb_retrieve(
            db,
            query=message,
            work_hint=work_hint,
            composer=composer,
            user_id=user_id,
            k=6,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("kb_retrieve_failed err=%s", exc)
        local = {"rag_mode": "error", "hits": [], "kb_dossier": {}, "rag_hits": []}

    # Professional plane (aulos-knowledge) — feature-flagged; filter by Catalog work_id
    try:
        from aulos_api.services.knowledge_proxy import knowledge_enabled, retrieve_sync

        if knowledge_enabled():
            work_id = ""
            composer_id = ""
            try:
                from aulos_skills.identity import resolve_identity

                ident = resolve_identity(message, work_hint=work_hint or "")
                if ident.status == "work" and ident.work_id:
                    work_id = ident.work_id
                if ident.composer_id:
                    composer_id = ident.composer_id
            except Exception as exc:  # noqa: BLE001
                logger.warning("identity_resolve_for_rag_failed err=%s", exc)

            plane = retrieve_sync(
                query=message,
                work_id=work_id,
                composer_id=composer_id if not work_id else "",
                k=6,
            )
            if plane.get("hits"):
                # Hard filter: if we know work_id, drop any hit that names a different aulos_work_id
                hits_plane = list(plane.get("hits") or [])
                if work_id:
                    hits_plane = [
                        h
                        for h in hits_plane
                        if not h.get("aulos_work_id") or h.get("aulos_work_id") == work_id
                    ]
                hits = list(local.get("hits") or []) + hits_plane
                rag_hits = list(local.get("rag_hits") or []) + [
                    str(h.get("text") or "") for h in hits_plane
                ]
                local = {
                    **local,
                    "hits": hits,
                    "rag_hits": [t for t in rag_hits if t][:12],
                    "rag_mode": f"{local.get('rag_mode')}+knowledge-plane",
                    "knowledge_plane": True,
                    "knowledge_work_id": work_id,
                }
    except Exception as exc:  # noqa: BLE001
        logger.warning("knowledge_plane_retrieve_failed err=%s", exc)
    return local


async def _run_chain_core(
    *,
    db: Session,
    user_id: int,
    message: str,
    work_hint: str | None = None,
    on_step: Callable[[dict[str, Any]], None] | None = None,
    yield_steps: bool = False,
) -> AsyncIterator[dict[str, Any] | Any]:
    """Gateway: identity → RAG/KB → generic LLM enrich → skill tools (no composer branches)."""
    disabled = _load_disabled(db)
    work_guess = (work_hint or message)[:120]
    # Identity first so KB + copilot enrich the resolved shelf, not the raw utterance.
    work_title = work_guess
    composer_name = ""
    family_id: str | None = None
    work_id = ""
    facets: dict[str, Any] = {}
    try:
        from aulos_skills.identity import resolve_identity

        ident = resolve_identity(message, work_hint=work_hint or "")
        if ident.work_title:
            work_title = ident.work_title
        if ident.composer_name:
            composer_name = ident.composer_name
        family_id = ident.family_id
        work_id = str(ident.work_id or "")
        facets = dict(ident.facets or {})
    except Exception as exc:  # noqa: BLE001
        logger.warning("identity_resolve_for_enrich_failed err=%s", exc)

    rag = _rag_context(
        db,
        message=message,
        work_hint=work_hint or work_title,
        composer=composer_name,
        user_id=user_id,
    )

    # Cold KB → open-web gather → LLM verify → persist so next RAG is stronger
    web_meta: dict[str, Any] = {}
    try:
        from aulos_api.services.web_research import run_web_research

        web = await run_web_research(
            db,
            work_title=work_title,
            composer=composer_name,
            work_id=work_id,
            facets=facets,
            user_id=user_id,
            rag=rag,
        )
        web_meta = {
            k: web.get(k)
            for k in ("skipped", "reason", "persisted_doc_ids", "rag_mode_suffix", "action", "decision")
            if k in web
        }
        if not web.get("skipped"):
            rag_hits = list(rag.get("rag_hits") or []) + list(web.get("rag_hits") or [])
            rag["rag_hits"] = [t for t in rag_hits if t][:16]
            web_dossier = dict(web.get("dossier") or {})
            if web_dossier:
                existing = dict(rag.get("kb_dossier") or {})
                if web.get("action") == "refresh" and existing:
                    rag["kb_dossier"] = web_dossier  # already merged in run_web_research
                elif not existing or len(json.dumps(web_dossier, ensure_ascii=False)) > len(
                    json.dumps(existing, ensure_ascii=False)
                ):
                    rag["kb_dossier"] = {**existing, **web_dossier} if existing else web_dossier
            suffix = str(web.get("rag_mode_suffix") or "web-research")
            rag["rag_mode"] = f"{rag.get('rag_mode') or 'none'}+{suffix}"
            rag["web_research"] = {
                "sources": len(web.get("sources") or []),
                "persisted_doc_ids": list(web.get("persisted_doc_ids") or []),
                "verified": bool((web_dossier.get("_provenance") or {}).get("verified")),
                "action": web.get("action"),
                "decision": web.get("decision"),
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("web_research_failed work=%s err=%s", work_title, exc)
        web_meta = {"skipped": True, "reason": f"error:{exc}"}

    llm_dossier, enrichment, source = await _optional_llm_dossier(
        db,
        work_title,
        composer_name,
        rag_hits=list(rag.get("rag_hits") or []),
        facets=facets,
        family_id=family_id,
    )
    if llm_dossier is None and enrichment is None:
        enrichment, source = await _optional_llm_note(db, work_title)

    emitted: list[dict[str, Any]] = []

    def _capture(step: dict[str, Any]) -> None:
        emitted.append(step)
        if on_step is not None:
            on_step(step)

    proxy = AgentProxy(get_settings())
    report = proxy.run_listening(
        message=message,
        work_hint=work_hint,
        llm_enrichment=enrichment,
        llm_dossier=llm_dossier,
        kb_dossier=dict(rag.get("kb_dossier") or {}),
        rag_hits=list(rag.get("rag_hits") or []),
        rag_mode=str(rag.get("rag_mode") or ""),
        disabled_skill_ids=disabled,
        on_step=_capture if (yield_steps or on_step) else None,
    )
    if source != "agent-skills":
        report.source = source
    report.context["rag_mode"] = rag.get("rag_mode")
    report.context["rag_hits"] = rag.get("rag_hits") or []
    if rag.get("web_research"):
        report.context["web_research"] = rag.get("web_research")
    if web_meta:
        report.context["web_research_meta"] = web_meta

    if yield_steps:
        for step in report.steps or emitted:
            yield {"event": "step", "data": step}
    yield report


async def run_listening_guide_workflow(
    *,
    db: Session,
    user_id: int,
    message: str,
    work_hint: str | None = None,
    on_step: Callable[[dict[str, Any]], None] | None = None,
) -> ListeningGuide:
    report: Any = None
    async for item in _run_chain_core(
        db=db,
        user_id=user_id,
        message=message,
        work_hint=work_hint,
        on_step=on_step,
        yield_steps=False,
    ):
        report = item
    assert report is not None
    return _persist_report(db=db, user_id=user_id, report=report, source=report.source)


async def iter_listening_guide_events(
    *,
    db: Session,
    user_id: int,
    message: str,
    work_hint: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    try:
        report: Any = None
        async for item in _run_chain_core(
            db=db,
            user_id=user_id,
            message=message,
            work_hint=work_hint,
            yield_steps=True,
        ):
            if isinstance(item, dict) and item.get("event") == "step":
                yield item
            else:
                report = item
        assert report is not None
        row = _persist_report(db=db, user_id=user_id, report=report, source=report.source)
        yield {"event": "done", "data": guide_to_dict(row)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("listening_guide_stream_failed")
        yield {"event": "error", "data": {"detail": str(exc)}}


async def iter_recompose_events(
    *,
    db: Session,
    user_id: int,
    guide_id: int,
    message: str | None = None,
    work_hint: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Re-run chain into an existing guide row; preserve share_slug / published_at."""
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        yield {"event": "error", "data": {"detail": "Guide not found"}}
        return
    text = (message or "").strip() or f"Listening guide for {row.work_title}"
    hint = (work_hint or "").strip() or row.work_title
    try:
        report: Any = None
        async for item in _run_chain_core(
            db=db,
            user_id=user_id,
            message=text,
            work_hint=hint,
            yield_steps=True,
        ):
            if isinstance(item, dict) and item.get("event") == "step":
                yield item
            else:
                report = item
        assert report is not None
        updated = _persist_report(
            db=db,
            user_id=user_id,
            report=report,
            source=report.source,
            existing=row,
        )
        yield {"event": "done", "data": guide_to_dict(updated)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("listening_guide_recompose_failed id=%s", guide_id)
        yield {"event": "error", "data": {"detail": str(exc)}}


def guide_to_dict(row: ListeningGuide) -> dict:
    try:
        steps = json.loads(row.steps_json or "[]")
    except json.JSONDecodeError:
        steps = []
    try:
        skill_versions = json.loads(row.skill_versions_json or "{}")
    except json.JSONDecodeError:
        skill_versions = {}
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    published = bool(row.share_slug and row.published_at)
    html = row.guide_html or ""
    html = html.replace('loading="lazy"', 'loading="eager"')
    return {
        "id": row.id,
        "work_title": row.work_title,
        "composer": row.composer,
        "status": row.status,
        "source": row.source,
        "summary": row.summary,
        "guide_html": html,
        "steps": steps,
        "skill_versions": skill_versions,
        "eval_pass": research.get("eval_pass"),
        "eval_score": research.get("eval_score"),
        "created_at": _iso(row.created_at),
        "published": published,
        "share_slug": row.share_slug if published else None,
        "share_path": f"/g/{row.share_slug}" if published and row.share_slug else None,
        "published_at": _iso(row.published_at) if published else None,
    }


def get_owned_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    return (
        db.query(ListeningGuide)
        .filter(ListeningGuide.id == guide_id, ListeningGuide.user_id == user_id)
        .one_or_none()
    )


def get_owned_guide_by_share_slug(db: Session, *, user_id: int, slug: str) -> ListeningGuide | None:
    slug = (slug or "").strip()
    if not slug:
        return None
    return (
        db.query(ListeningGuide)
        .filter(
            ListeningGuide.share_slug == slug,
            ListeningGuide.user_id == user_id,
        )
        .one_or_none()
    )


def publish_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    if not row.share_slug:
        for _ in range(8):
            candidate = _new_share_slug()
            exists = (
                db.query(ListeningGuide.id)
                .filter(ListeningGuide.share_slug == candidate)
                .one_or_none()
            )
            if exists is None:
                row.share_slug = candidate
                break
        else:
            row.share_slug = secrets.token_hex(12)
    row.published_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("listening_guide_published id=%s slug=%s", row.id, row.share_slug)
    return row


def unpublish_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    row.published_at = None
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("listening_guide_unpublished id=%s", row.id)
    return row


def update_publish_guide(db: Session, *, user_id: int, guide_id: int) -> ListeningGuide | None:
    """Ensure guide is published (same slug). Content already live if published."""
    return publish_guide(db, user_id=user_id, guide_id=guide_id)


def get_published_guide_by_slug(db: Session, slug: str) -> ListeningGuide | None:
    slug = (slug or "").strip()
    if not slug:
        return None
    return (
        db.query(ListeningGuide)
        .filter(
            ListeningGuide.share_slug == slug,
            ListeningGuide.published_at.isnot(None),
        )
        .one_or_none()
    )
