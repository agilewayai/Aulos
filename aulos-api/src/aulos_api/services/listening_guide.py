"""Classical listening-guide workflow — API gateway delegates to aulos-agent tools."""

from __future__ import annotations

import json
import logging
import re
import secrets
import sys
import time
from collections.abc import AsyncIterator, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from aulos_api.config import get_settings
from aulos_api.db.models import ListeningGuide
from aulos_api.services.agent_proxy import AgentProxy
from aulos_api.services.chain_trace import ChainTraceBuilder, extract_chain_trace
from aulos_api.services.discogs import DiscogsError, resolve_discogs_message
from aulos_api.services.knowledge_base import retrieve as kb_retrieve
from aulos_api.services.knowledge_base import upsert_from_report
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config
from aulos_api.services.listening_review import load_review_llm_enabled
from aulos_api.services.listening_ambient import load_ambient_fallback_mode
from aulos_api.services.share_slug import new_share_slug
from aulos_api.services.skills_ops import _load_disabled
from aulos_api.services.listening_plan import (
    coalesce_plan_steps,
    initial_plan_steps,
    mark_stage,
    progress_counts,
    upsert_step,
)
from aulos_api.timefmt import to_utc_iso_optional

logger = logging.getLogger("aulos_api.listening")

MAX_TAGS = 12
MAX_TAG_LEN = 32
STALE_RUNNING_SECONDS = 20 * 60


class _ChainProgress:
    """Emit countable plan updates through on_step during the gateway + agent run."""

    def __init__(self, on_step: Callable[[dict[str, Any]], None] | None) -> None:
        self.on_step = on_step
        self.steps = initial_plan_steps()
        # Do not blast every pending row — jobs already seed the plan in steps_json.

    def mark(self, sid: str, status: str, detail: str = "", thinking: str | None = None) -> None:
        self.steps = mark_stage(self.steps, sid, status=status, detail=detail, thinking=thinking)
        if self.on_step is None:
            return
        for step in self.steps:
            if step.get("id") == sid:
                self.on_step(dict(step))
                break

    def ingest_agent_step(self, step: dict[str, Any]) -> None:
        from aulos_api.services.listening_plan import canonicalize_step_id

        payload = dict(step)
        # Normalize skill completion statuses for the progress counter.
        status = str(payload.get("status") or "").lower()
        if status in {"ok", "success", "completed"}:
            payload["status"] = "done"
        elif status in {"skipped"}:
            payload["status"] = "skip"
        # Skill runtime emits short ids (route); map onto listening.route placeholders.
        if payload.get("id"):
            payload["id"] = canonicalize_step_id(str(payload["id"]))
        self.steps = upsert_step(self.steps, payload)
        if self.on_step is not None:
            for row in self.steps:
                if row.get("id") == payload.get("id"):
                    self.on_step(dict(row))
                    return
            self.on_step(payload)

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    return to_utc_iso_optional(dt)


def _new_share_slug() -> str:
    return new_share_slug()


def _titles_compatible(cat_title: str, discogs_title: str, cat_work: Any = None) -> bool:
    """True when Discogs title and Catalog work describe the same shelf (not substring-only)."""
    a = (cat_title or "").lower().strip()
    b = (discogs_title or "").lower().strip()
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    # Shared catalog numbers / distinctive tokens (K.488 vs album chrome)
    needles: list[str] = []
    if cat_work is not None:
        needles.extend(str(x).lower() for x in (getattr(cat_work, "catalog_numbers", None) or []) if x)
        needles.extend(str(x).lower() for x in (getattr(cat_work, "distinctive_tokens", None) or []) if x)
    for n in needles:
        n_compact = re.sub(r"[\s.\-]", "", n)
        b_compact = re.sub(r"[\s.\-]", "", b)
        if len(n) >= 4 and (n in b or (n_compact and n_compact in b_compact)):
            return True
    # Token overlap excluding weak surname/form words
    weak = {"mozart", "bach", "beethoven", "chopin", "piano", "the", "and", "major", "minor"}
    ta = {t for t in re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", a) if t not in weak}
    tb = {t for t in re.findall(r"[a-z0-9\u4e00-\u9fff]{3,}", b) if t not in weak}
    if ta and tb and len(ta & tb) >= 2:
        return True
    return False


def _dossier_betrays_lock(
    dossier: dict[str, Any] | None,
    *,
    work_title: str,
    work_hint: str = "",
    raw_message: str = "",
) -> bool:
    """Reject LLM dossiers that swapped the locked work for a sibling famous piece.

    Class gate via aulos_skills.identity_lock (form policy + catalog numbers) —
    not Mozart/K.488-specific branches.
    """
    if not dossier:
        return False
    try:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.identity_lock import dossier_betrays_identity_lock
    except ImportError:
        return False
    return dossier_betrays_identity_lock(
        dossier,
        work_title=work_title,
        work_hint=work_hint,
        raw_message=raw_message,
    )


def _research_payload(report: Any) -> dict[str, Any]:
    ctx = getattr(report, "context", None) or {}
    dossier = dict(ctx.get("corpus_dossier") or {})
    if not dossier:
        width = dict(ctx.get("width_dossier") or {})
        dossier = dict(width.get("salon_dossier") or {})
    payload = {
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
    if ctx.get("discogs"):
        payload["discogs"] = ctx.get("discogs")
    if isinstance(ctx.get("chain_trace"), dict):
        payload["chain_trace"] = ctx["chain_trace"]
    if ctx.get("intent_lock"):
        payload["intent_lock"] = ctx.get("intent_lock")
    if ctx.get("review_events"):
        payload["review_events"] = list(ctx.get("review_events") or [])
    if ctx.get("review_failed"):
        payload["review_failed"] = True
    if ctx.get("critique_corrections"):
        payload["critique_corrections"] = list(ctx.get("critique_corrections") or [])
    if ctx.get("process_scorecard"):
        payload["process_scorecard"] = ctx.get("process_scorecard")
    if ctx.get("product_scorecard"):
        payload["product_scorecard"] = ctx.get("product_scorecard")
    if ctx.get("promote_candidate"):
        payload["promote_candidate"] = ctx.get("promote_candidate")
    if ctx.get("facet_classification"):
        payload["facet_classification"] = ctx.get("facet_classification")
    if ctx.get("node_scorecards"):
        payload["node_scorecards"] = list(ctx.get("node_scorecards") or [])
    if ctx.get("generation_rounds"):
        payload["generation_rounds"] = ctx.get("generation_rounds")
    if ctx.get("external_review_report"):
        payload["external_review_report"] = ctx.get("external_review_report")
    return payload


def guide_trace_dict(row: ListeningGuide) -> dict[str, Any]:
    """Owner/ops diagnostic payload (SPEC-012)."""
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    out = {
        "guide_id": row.id,
        "work_title": row.work_title,
        "composer": row.composer,
        "status": row.status,
        "source": row.source,
        "created_at": _iso(row.created_at),
        "chain_trace": extract_chain_trace(research),
    }
    if isinstance(research.get("process_scorecard"), dict):
        out["process_scorecard"] = research["process_scorecard"]
    elif research.get("node_scorecards"):
        out["node_scorecards"] = research.get("node_scorecards")
    if isinstance(research.get("promote_candidate"), dict):
        out["promote_candidate"] = research["promote_candidate"]
    if isinstance(research.get("product_scorecard"), dict):
        out["product_scorecard"] = research["product_scorecard"]
    if research.get("synthesize_source"):
        out["synthesize_source"] = research.get("synthesize_source")
    if isinstance(research.get("facet_classification"), dict):
        out["facet_classification"] = research["facet_classification"]
    return out


def list_guide_scorecard_summaries(
    db: Session,
    *,
    limit: int = 40,
) -> list[dict[str, Any]]:
    """Ops board: recent guides with rollup scorecard summary (SPEC-019)."""
    limit = max(1, min(int(limit or 40), 100))
    rows = (
        db.query(ListeningGuide)
        .order_by(ListeningGuide.id.desc())
        .limit(limit)
        .all()
    )
    items: list[dict[str, Any]] = []
    for row in rows:
        try:
            research = json.loads(row.research_json or "{}")
        except json.JSONDecodeError:
            research = {}
        process = research.get("process_scorecard") if isinstance(research, dict) else None
        rollup = dict((process or {}).get("rollup") or {}) if isinstance(process, dict) else {}
        gates = dict((process or {}).get("gates") or {}) if isinstance(process, dict) else {}
        product = research.get("product_scorecard") if isinstance(research, dict) else None
        promote = research.get("promote_candidate") if isinstance(research, dict) else None
        items.append(
            {
                "guide_id": row.id,
                "work_title": row.work_title,
                "composer": row.composer,
                "status": row.status,
                "source": row.source,
                "created_at": _iso(row.created_at),
                "eval_pass": research.get("eval_pass") if isinstance(research, dict) else None,
                "eval_score": research.get("eval_score") if isinstance(research, dict) else None,
                "review_failed": bool(
                    (isinstance(research, dict) and research.get("review_failed"))
                    or gates.get("review_failed")
                ),
                "pct": rollup.get("pct"),
                "band": rollup.get("band") or ("unknown" if not process else "weak"),
                "hard_fail": bool(rollup.get("hard_fail")),
                "has_scorecard": bool(process),
                "has_promote_candidate": bool(isinstance(promote, dict) and promote),
                "promote_status": (
                    str(promote.get("status") or "candidate")
                    if isinstance(promote, dict)
                    else None
                ),
                "synthesize_source": (
                    research.get("synthesize_source") if isinstance(research, dict) else None
                ),
                "product_band": (
                    (product or {}).get("band") if isinstance(product, dict) else None
                ),
                "asset_depth": (
                    ((product or {}).get("dimensions") or {}).get("asset_depth")
                    if isinstance(product, dict)
                    else None
                ),
            }
        )
    return items


def list_promote_candidates(
    db: Session,
    *,
    limit: int = 40,
) -> list[dict[str, Any]]:
    """Guides whose research_json carries a promote_candidate (SPEC-030)."""
    limit = max(1, min(int(limit or 40), 100))
    rows = (
        db.query(ListeningGuide)
        .order_by(ListeningGuide.id.desc())
        .limit(max(limit * 5, 100))
        .all()
    )
    items: list[dict[str, Any]] = []
    for row in rows:
        try:
            research = json.loads(row.research_json or "{}")
        except json.JSONDecodeError:
            research = {}
        promote = research.get("promote_candidate") if isinstance(research, dict) else None
        if not isinstance(promote, dict) or not promote:
            continue
        items.append(
            {
                "guide_id": row.id,
                "work_title": row.work_title,
                "composer": row.composer,
                "created_at": _iso(row.created_at),
                "synthesize_source": research.get("synthesize_source"),
                "promote_candidate": promote,
                "facet_classification": research.get("facet_classification"),
            }
        )
        if len(items) >= limit:
            break
    return items


def stage_promote_candidate(
    db: Session,
    guide_id: int,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Write craft/staging YAML from guide promote_candidate; mark status=staged."""
    from aulos_skills.promote_staging import materialize_craft_pack, write_staging_craft

    row = db.get(ListeningGuide, guide_id)
    if row is None:
        raise LookupError("Guide not found")
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    cand = research.get("promote_candidate") if isinstance(research, dict) else None
    if not isinstance(cand, dict) or not cand:
        raise ValueError("Guide has no promote_candidate")
    dossier = research.get("corpus_dossier") if isinstance(research, dict) else None
    if not isinstance(dossier, dict):
        dossier = {}
    pack = materialize_craft_pack(
        cand,
        dossier=dossier,
        composer=str(row.composer or ""),
        work_title=str(row.work_title or ""),
    )
    wid = str(cand.get("suggested_work_id") or pack.get("work_id") or "")
    path = write_staging_craft(wid, pack, overwrite=overwrite)
    updated = dict(cand)
    updated["status"] = "staged"
    updated["staged_path"] = str(path)
    updated["staged_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    updated["dry_run"] = False  # staged to disk; still not production craft/
    research["promote_candidate"] = updated
    row.research_json = json.dumps(research, ensure_ascii=False)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "guide_id": row.id,
        "suggested_work_id": wid,
        "staged_path": str(path),
        "promote_candidate": updated,
    }


def promote_candidate_to_production(
    db: Session,
    guide_id: int,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """SPEC-031 — graduate staged promote_candidate via generic Catalog+craft pipeline."""
    from aulos_skills.promote_production import promote_staged_to_production

    row = db.get(ListeningGuide, guide_id)
    if row is None:
        raise LookupError("Guide not found")
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    cand = research.get("promote_candidate") if isinstance(research, dict) else None
    if not isinstance(cand, dict) or not cand:
        raise ValueError("Guide has no promote_candidate")
    status = str(cand.get("status") or "")
    if status not in {"staged", "production"} and not cand.get("staged_path"):
        raise ValueError("promote_candidate must be staged before production promote")

    report = promote_staged_to_production(
        candidate=cand,
        composer=str(row.composer or ""),
        work_title=str(row.work_title or ""),
        overwrite=overwrite,
    )
    updated = dict(cand)
    updated["status"] = "production"
    updated["dry_run"] = False
    updated["production_work_id"] = report.get("work_id")
    updated["production_craft_path"] = report.get("craft_path")
    updated["production_catalog_path"] = report.get("catalog_work_path")
    updated["promoted_at"] = report.get("promoted_at")
    research["promote_candidate"] = updated
    row.research_json = json.dumps(research, ensure_ascii=False)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "ok": True,
        "guide_id": row.id,
        "report": report,
        "promote_candidate": updated,
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
        f"LOCKED WORK TITLE (do not rename, truncate, or substitute): {work_title}\n"
        f"Composer: {composer or 'unknown'}\n"
        f"Family hint (optional scaffold id): {family_id or 'none'}\n"
        f"Facets: {'; '.join(facet_bits) if facet_bits else 'none'}\n\n"
        "KB / prior-research evidence (may be partial; never invent citations beyond search URLs):\n"
        f"{evidence_block}\n\n"
        "Return ONLY a compact JSON object (no markdown) with:\n"
        "work_title (MUST equal the LOCKED WORK TITLE above),\n"
        "listening_thesis, work_introduction, era, form,\n"
        "composer_profile {{lifespan, summary, temperament, place_in_oeuvre, place_in_history}},\n"
        "genesis {{year, place, publication, patronage, background, instrument_culture}},\n"
        "historical_stature {{reasons: [], reception_arc}},\n"
        "width_points, depth_points,\n"
        "listening_map ([{{label,cue}}]), variation_deepdives ([{{title,note}}]),\n"
        "sound_world {{original_instrument, ensemble_notes, modern_modes: []}},\n"
        "related_works ([{{title,why}}]),\n"
        "interpretations ([{{artist,year,instrument,era_note,why_listen}}] — named traditions OK; "
        "youtube_url/bilibili_url/discogs_url only as "
        "https://www.youtube.com/results?search_query=... or "
        "https://search.bilibili.com/all?keyword=... or "
        "https://www.discogs.com/search/?q=... search links),\n"
        "appreciation_videos ([{{title,url,bilibili_url,why}}] — url=YouTube search; "
        "bilibili_url=哔哩哔哩 search; search links only),\n"
        "vinyl_and_discography ([{{label,url,note}}] Discogs search links only),\n"
        "practice_notes, myths_and_caveats,\n"
        "and nested zh_hans with the SAME chambers in Simplified Chinese 导赏 prose "
        "(简体：肖邦/德沃夏克/导赏/录音; no Chinglish; no skill jargon),\n"
        "and nested zh_hant with the SAME chambers in Traditional Chinese "
        "(繁体：蕭邦/德弗札克/導賞/錄音; 繁体字形与用词).\n"
        "Also include legacy nested zh equal to zh_hans for compatibility.\n"
        "Rules: ear-actionable; label legends; no invented Discogs/YouTube/Bilibili item IDs; "
        "no copying unrelated flagship works; keep JSON under 2200 words.\n"
        "CRITICAL IDENTITY LOCK: Write about the LOCKED WORK TITLE only. "
        "Never substitute another famous work by the same composer or performer "
        "(e.g. if the lock is Piano Concerto K.488, do NOT write Mozart Requiem / Dies irae / 末日经 / 安魂曲 "
        "even if Horowitz is famous for a Requiem transcription). "
        "related_works may briefly mention siblings, but thesis/form/introduction must stay on the locked work.\n"
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
    if dossier and _dossier_betrays_lock(dossier, work_title=work_title):
        logger.warning(
            "llm_dossier_betrays_lock work=%s — discarding substituted sibling work",
            work_title[:120],
        )
        return None, text[:400], f"agent-skills+{provider}+lock-reject"
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
    row.error_detail = ""
    row.updated_at = utcnow()
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
    original_message = message
    original_hint = (work_hint or "").strip()
    trace = ChainTraceBuilder(message=original_message, work_hint=original_hint)
    progress = _ChainProgress(on_step)

    # SPEC-008: /discogs #release-id → fetch Discogs → rewrite intent + seed dossier
    discog: dict[str, Any] | None = None
    progress.mark("g.discogs", "running", "Resolving Discogs intent…")
    try:
        discog = resolve_discogs_message(message, db=db)
    except DiscogsError:
        progress.mark("g.discogs", "failed", "Discogs resolve failed")
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("discogs_resolve_failed err=%s", exc)
        discog = None
        trace.milestone(
            "discogs.resolve",
            status="fail",
            summary=f"Discogs resolve error: {exc}",
            signals=["discogs_error"],
        )
        progress.mark("g.discogs", "failed", str(exc)[:240])
    if discog:
        message = str(discog.get("listening_intent") or message)
        work_hint = str(discog.get("work_hint") or work_hint or "")
        trace.milestone(
            "discogs.resolve",
            status="ok",
            summary=(
                f"Discogs #{discog.get('release_id')} → "
                f"{discog.get('composer') or '?'} — {str(discog.get('work_title') or '')[:80]}"
            ),
            facts={
                "release_id": discog.get("release_id"),
                "master_id": discog.get("master_id"),
                "composer": discog.get("composer"),
                "work_title": discog.get("work_title"),
                "catno_query": discog.get("catno_query"),
                "uri": discog.get("uri"),
                "performers": list(discog.get("performers") or [])[:6],
            },
        )
        trace.note_identity(
            stage="discogs",
            composer=str(discog.get("composer") or ""),
            work_title=str(discog.get("work_title") or ""),
            extra={"release_id": discog.get("release_id")},
        )
        progress.mark(
            "g.discogs",
            "done",
            f"#{discog.get('release_id')} · {discog.get('composer') or '?'} — {str(discog.get('work_title') or '')[:80]}",
        )
    else:
        if not any(m["id"] == "discogs.resolve" for m in trace.milestones):
            trace.milestone(
                "discogs.resolve",
                status="skip",
                summary="No /discogs command in message",
            )
        if progress.steps[0].get("status") == "running":
            progress.mark("g.discogs", "skip", "No /discogs command")

    work_guess = (work_hint or message)[:120]
    # Identity first so KB + copilot enrich the resolved shelf, not the raw utterance.
    work_title = work_guess
    composer_name = ""
    family_id: str | None = None
    work_id = ""
    facets: dict[str, Any] = {}
    ident_status = "unknown"
    ident_reason = ""
    progress.mark("g.identity", "running", "Resolving catalog identity…")
    try:
        from aulos_skills.identity import resolve_identity

        ident = resolve_identity(message, work_hint=work_hint or "")
        ident_status = ident.status
        ident_reason = ident.reason
        if ident.work_title:
            work_title = ident.work_title
        if ident.composer_name:
            composer_name = ident.composer_name
        family_id = ident.family_id
        work_id = str(ident.work_id or "")
        facets = dict(ident.facets or {})
        trace.milestone(
            "identity.resolve",
            status="ok" if ident.status == "work" else ("warn" if ident.status != "unknown" else "skip"),
            summary=f"Catalog identity={ident.status} work_id={work_id or 'none'} ({ident.reason})",
            facts={
                "status": ident.status,
                "work_id": work_id or None,
                "composer_id": ident.composer_id,
                "composer": composer_name,
                "work_title": work_title,
                "family_id": family_id,
                "score": ident.score,
                "confidence": ident.confidence,
                "reason": ident.reason,
            },
        )
        trace.note_identity(
            stage="catalog",
            composer=composer_name,
            work_title=work_title,
            work_id=work_id or None,
            extra={"status": ident.status, "reason": ident.reason},
        )
        progress.mark(
            "g.identity",
            "done" if ident.status == "work" else "skip",
            f"{ident.status}: {composer_name or '?'} — {work_title[:80]}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("identity_resolve_for_enrich_failed err=%s", exc)
        trace.milestone(
            "identity.resolve",
            status="fail",
            summary=f"Identity resolve error: {exc}",
            signals=["identity_error"],
        )
        progress.mark("g.identity", "failed", str(exc)[:240])

    # Discogs seed is listener-authoritative for title/composer facts, but Catalog
    # work_id should still lock when packaging-cleaned titles match (SPEC-024).
    cleared_catalog = False
    if discog:
        from aulos_skills.prose_hygiene import clean_packaging_work_title
        from aulos_skills.work_resolver import resolve_listening_work

        if discog.get("composer"):
            composer_name = str(discog["composer"])
        raw_discogs_title = str(discog.get("work_title") or work_title or "")
        work_title = clean_packaging_work_title(raw_discogs_title, composer=composer_name) or raw_discogs_title
        # Re-resolve on cleaned Discogs title — do not wipe Catalog on packaging mismatch alone.
        resolved = resolve_listening_work(
            raw_message=str(discog.get("listening_intent") or message),
            work_hint=f"{composer_name} — {work_title}".strip(" —"),
            kb_dossier={
                "_provenance": {"source": "discogs"},
                "composer": composer_name,
                "work_title": work_title,
            },
        )
        if resolved.status == "work" and resolved.work_id:
            work_id = str(resolved.work_id)
            family_id = resolved.family_id
            work_title = resolved.work_title or work_title
            composer_name = resolved.composer or composer_name
            if resolved.identity and resolved.identity.facets:
                facets = dict(resolved.identity.facets or {})
            cleared_catalog = False
        elif work_id:
            try:
                from aulos_skills.identity import load_catalog

                cat_work = load_catalog().works.get(work_id)
                cat_title = (cat_work.canonical_title if cat_work else "") or ""
                if cat_title and work_title and not _titles_compatible(cat_title, work_title, cat_work):
                    work_id = ""
                    family_id = None
                    facets = {}
                    cleared_catalog = True
            except Exception:  # noqa: BLE001
                work_id = ""
                family_id = None
                facets = {}
                cleared_catalog = True
        # Em-dash hint so intake dash-parse cannot split hyphenated surnames
        work_hint = str(
            discog.get("work_hint")
            or (f"{composer_name} — {work_title}".strip(" —") if composer_name else work_title)
        )
        message = str(discog.get("listening_intent") or message)
        trace.milestone(
            "identity.lock",
            status="ok",
            summary=(
                "Discogs title/composer locked"
                + (" (cleared conflicting Catalog work_id)" if cleared_catalog else "")
                + (f"; resolver={resolved.status}:{resolved.work_id}" if resolved else "")
            ),
            facts={
                "composer": composer_name,
                "work_title": work_title,
                "work_id": work_id or None,
                "family_id": family_id,
                "cleared_catalog_work": cleared_catalog,
                "resolver_status": resolved.status if resolved else None,
            },
            signals=["discogs_authoritative"] + (["cleared_catalog_work"] if cleared_catalog else []),
        )
        trace.note_identity(
            stage="locked",
            composer=composer_name,
            work_title=work_title,
            work_id=work_id or None,
        )
        progress.mark(
            "g.identity",
            "done",
            f"Discogs lock: {composer_name or '?'} — {work_title[:80]}",
        )

    # SPEC-025: knowledge-plane composer dossier → Salon thicken patch (applied after RAG)
    kn_bag: dict[str, Any] = {}
    composer_id_for_kn = ""
    try:
        from aulos_skills.identity import load_catalog

        if work_id:
            w = load_catalog().works.get(work_id)
            if w and w.composer_id:
                composer_id_for_kn = str(w.composer_id)
    except Exception:  # noqa: BLE001
        composer_id_for_kn = ""
    if not composer_id_for_kn:
        try:
            from aulos_skills.identity import resolve_identity

            ident_kn = resolve_identity(message, work_hint=work_hint or work_title)
            composer_id_for_kn = str(ident_kn.composer_id or "")
        except Exception:  # noqa: BLE001
            composer_id_for_kn = ""
    if composer_id_for_kn:
        try:
            from aulos_api.services.knowledge_proxy import (
                fetch_composer_dossier_sync,
                knowledge_enabled,
            )
            from aulos_skills.knowledge_thicken import knowledge_dossier_to_chambers

            if knowledge_enabled():
                kn = fetch_composer_dossier_sync(composer_id_for_kn)
                if kn:
                    kn_bag = {
                        "_knowledge_composer": kn,
                        "_knowledge_thicken": knowledge_dossier_to_chambers(kn),
                    }
                from aulos_api.services.knowledge_proxy import (
                    dossier_is_thin,
                    enqueue_composer_dossier_build_sync,
                )

                # SPEC-026: thin dossier → async build for next compose (never block)
                if dossier_is_thin(kn if isinstance(kn, dict) else {}):
                    enq = enqueue_composer_dossier_build_sync(composer_id_for_kn)
                    if enq.get("ok"):
                        kn_bag = dict(kn_bag)
                        kn_bag["_knowledge_dossier_enqueued"] = True
                        kn_bag["_knowledge_dossier_enqueue"] = {
                            "job_id": enq.get("job_id"),
                            "status": enq.get("status"),
                        }
        except Exception as exc:  # noqa: BLE001
            logger.warning("knowledge_thicken_failed err=%s", exc)

    progress.mark("g.rag", "running", "Retrieving knowledge…")
    rag = _rag_context(
        db,
        message=message,
        work_hint=work_hint or work_title,
        composer=composer_name,
        user_id=user_id,
    )
    if discog:
        seed = dict(discog.get("kb_seed") or {})
        if seed:
            existing = dict(rag.get("kb_dossier") or {})
            # Discogs seed wins for vinyl/interpretations; keep other KB chambers.
            merged = {**existing, **{k: v for k, v in seed.items() if k != "_provenance"}}
            prov = dict(existing.get("_provenance") or {})
            prov.update(dict(seed.get("_provenance") or {}))
            merged["_provenance"] = prov
            if work_title:
                merged["work_title"] = work_title
            if composer_name:
                merged["composer"] = composer_name
            if work_id:
                merged["work_id"] = work_id
            if family_id:
                merged["family_id"] = family_id
            rag["kb_dossier"] = merged
        snippets = list(discog.get("rag_snippets") or [])
        if snippets:
            rag["rag_hits"] = list(snippets) + list(rag.get("rag_hits") or [])
            rag["rag_hits"] = [t for t in rag["rag_hits"] if t][:16]
            rag["rag_mode"] = f"{rag.get('rag_mode') or 'none'}+discogs"

    if kn_bag:
        kb_merged = dict(rag.get("kb_dossier") or {})
        kb_merged.update(kn_bag)
        from aulos_skills.knowledge_thicken import merge_knowledge_thicken

        kb_merged = merge_knowledge_thicken(
            kb_merged, dict(kn_bag.get("_knowledge_thicken") or {})
        )
        rag["kb_dossier"] = kb_merged
        rag["knowledge_thicken"] = True
        rag["knowledge_composer_id"] = composer_id_for_kn
        if kn_bag.get("_knowledge_dossier_enqueued"):
            rag["knowledge_dossier_enqueued"] = True
            rag["knowledge_dossier_enqueue"] = kn_bag.get("_knowledge_dossier_enqueue")

    trace.milestone(
        "rag",
        status="ok",
        summary=f"RAG mode={rag.get('rag_mode') or 'none'} hits={len(rag.get('rag_hits') or [])}",
        facts={
            "rag_mode": rag.get("rag_mode"),
            "hit_count": len(rag.get("rag_hits") or []),
            "kb_dossier_keys": list((rag.get("kb_dossier") or {}).keys())[:20],
            "knowledge_work_id": rag.get("knowledge_work_id"),
        },
    )
    progress.mark(
        "g.rag",
        "done",
        f"mode={rag.get('rag_mode') or 'none'} · hits={len(rag.get('rag_hits') or [])}",
    )

    # Cold KB → open-web gather → LLM verify → persist so next RAG is stronger
    web_meta: dict[str, Any] = {}
    progress.mark("g.web", "running", "Web research…")
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
            trace.milestone(
                "web_research",
                status="ok",
                summary=f"Web research action={web.get('action')} sources={len(web.get('sources') or [])}",
                facts=web_meta,
            )
            progress.mark(
                "g.web",
                "done",
                f"action={web.get('action')} · sources={len(web.get('sources') or [])}",
            )
        else:
            trace.milestone(
                "web_research",
                status="skip",
                summary=f"Web research skipped: {web.get('reason') or 'n/a'}",
                facts=web_meta,
            )
            progress.mark("g.web", "skip", str(web.get("reason") or "skipped")[:240])
    except Exception as exc:  # noqa: BLE001
        logger.warning("web_research_failed work=%s err=%s", work_title, exc)
        web_meta = {"skipped": True, "reason": f"error:{exc}"}
        trace.milestone(
            "web_research",
            status="fail",
            summary=f"Web research error: {exc}",
            signals=["web_research_error"],
        )
        progress.mark("g.web", "failed", str(exc)[:240])

    progress.mark("g.llm", "running", "LLM dossier enrichment…")
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
    trace.milestone(
        "llm_enrich",
        status="ok" if (llm_dossier or enrichment) else "skip",
        summary=f"LLM enrich source={source}",
        facts={
            "source": source,
            "has_dossier": bool(llm_dossier),
            "has_note": bool(enrichment),
            "family_id": family_id,
            "identity_status": ident_status,
            "identity_reason": ident_reason,
        },
    )
    progress.mark(
        "g.llm",
        "done" if (llm_dossier or enrichment) else "skip",
        f"source={source}",
    )

    emitted: list[dict[str, Any]] = []

    def _capture(step: dict[str, Any]) -> None:
        emitted.append(step)
        progress.ingest_agent_step(step)

    progress.mark("g.agent", "running", "Agent skill playbook…")
    # SPEC-022: always gather open-web sources for the external review Agent (do not skip-on-fresh).
    external_review_sources: list[dict[str, Any]] = []
    try:
        from aulos_api.services.web_search import gather_web_sources

        external_review_sources = gather_web_sources(
            work_title=work_title or message[:120],
            composer=composer_name or "",
        )
        progress.mark(
            "g.extweb",
            "done",
            f"External-review sources={len(external_review_sources)}",
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("external_review_sources_failed err=%s", exc)
        progress.mark("g.extweb", "skip", str(exc)[:120])

    proxy = AgentProxy(get_settings())
    review_llm = load_review_llm_enabled(db)
    ambient_fallback_mode = load_ambient_fallback_mode(db)
    try:
        report = proxy.run_listening(
            message=message,
            work_hint=work_hint,
            llm_enrichment=enrichment,
            llm_dossier=llm_dossier,
            kb_dossier=dict(rag.get("kb_dossier") or {}),
            rag_hits=list(rag.get("rag_hits") or []),
            rag_mode=str(rag.get("rag_mode") or ""),
            disabled_skill_ids=disabled,
            review_llm_enabled=review_llm,
            ambient_fallback_mode=ambient_fallback_mode,
            external_review_sources=external_review_sources,
            on_step=_capture if (yield_steps or on_step) else None,
        )
    except Exception as exc:  # noqa: BLE001
        progress.mark("g.agent", "failed", str(exc)[:240])
        raise
    progress.mark("g.agent", "done", f"skills={len(emitted or report.steps or [])}")
    progress.mark("g.persist", "running", "Persisting guide…")
    if source != "agent-skills":
        report.source = source
    report.context["rag_mode"] = rag.get("rag_mode")
    report.context["rag_hits"] = rag.get("rag_hits") or []
    if rag.get("web_research"):
        report.context["web_research"] = rag.get("web_research")
    if web_meta:
        report.context["web_research_meta"] = web_meta
    if discog:
        report.context["discogs"] = {
            "release_id": discog.get("release_id"),
            "master_id": discog.get("master_id"),
            "uri": discog.get("uri"),
            "performers": list(discog.get("performers") or []),
            "composers": list(discog.get("composers") or []),
            "work_title": discog.get("work_title"),
            "composer": discog.get("composer"),
            "catno_query": discog.get("catno_query"),
            "command": discog.get("command"),
        }

    # Skill-side diagnostics + identity arc close
    skill_ctx = dict(report.context or {})
    if not skill_ctx.get("work_id") and work_id:
        skill_ctx["work_id"] = work_id
    trace.ingest_skill_context(skill_ctx)
    # Prefer skill-reported shelf for final, fall back to gateway lock
    final_composer = str(report.composer or composer_name or "")
    final_title = str(report.work_title or work_title or "")
    final_work_id = str(skill_ctx.get("work_id") or work_id or "") or None
    report.context["chain_trace"] = trace.finalize(
        work_title=final_title,
        composer=final_composer,
        work_id=final_work_id,
        eval_pass=getattr(report, "eval_pass", None),
        eval_score=getattr(report, "eval_score", None),
    )
    # Prefer countable plan steps for persistence when progress was tracked.
    if progress.steps and (on_step is not None or yield_steps):
        report.steps = coalesce_plan_steps(list(progress.steps))
    progress.mark("g.persist", "done", "Guide ready to save")
    # Persist coalesced view (drop ghost short-id duplicates).
    if progress.steps:
        progress.steps = coalesce_plan_steps(list(progress.steps))
        if report.steps:
            report.steps = list(progress.steps)

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
    except DiscogsError as exc:
        yield {
            "event": "error",
            "data": {"detail": str(exc), "status_code": exc.status_code, "code": "discogs"},
        }
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
    if isinstance(steps, list):
        steps = coalesce_plan_steps([s for s in steps if isinstance(s, dict)])
    else:
        steps = []
    try:
        skill_versions = json.loads(row.skill_versions_json or "{}")
    except json.JSONDecodeError:
        skill_versions = {}
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    try:
        tags = json.loads(row.tags_json or "[]")
        if not isinstance(tags, list):
            tags = []
    except json.JSONDecodeError:
        tags = []
    published = bool(row.share_slug and row.published_at)
    html = row.guide_html or ""
    html = html.replace('loading="lazy"', 'loading="eager"')
    favorited_at = getattr(row, "favorited_at", None)
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
        "process_scorecard": research.get("process_scorecard")
        if isinstance(research.get("process_scorecard"), dict)
        else None,
        "generation_rounds": research.get("generation_rounds")
        if isinstance(research.get("generation_rounds"), dict)
        else None,
        "external_review_report": research.get("external_review_report")
        if isinstance(research.get("external_review_report"), dict)
        else (
            (research.get("generation_rounds") or {}).get("review_report")
            if isinstance(research.get("generation_rounds"), dict)
            else None
        ),
        "created_at": _iso(row.created_at),
        "updated_at": _iso(getattr(row, "updated_at", None) or row.created_at),
        "published": published,
        "share_slug": row.share_slug if published else None,
        "share_path": f"/g/{row.share_slug}" if published and row.share_slug else None,
        "published_at": _iso(row.published_at) if published else None,
        "message": getattr(row, "message", "") or "",
        "error_detail": getattr(row, "error_detail", "") or "",
        "favorited": bool(favorited_at),
        "favorited_at": _iso(favorited_at) if favorited_at else None,
        "tags": [str(t) for t in tags if str(t).strip()],
    }


def normalize_tags(raw: list[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in raw or []:
        tag = " ".join(str(item).strip().lower().split())
        if not tag or tag in seen:
            continue
        if len(tag) > MAX_TAG_LEN:
            tag = tag[:MAX_TAG_LEN]
        seen.add(tag)
        out.append(tag)
        if len(out) >= MAX_TAGS:
            break
    return out


def list_owned_guides(
    db: Session,
    *,
    user_id: int,
    q: str | None = None,
    status: str | None = None,
    published: bool | None = None,
    favorited: bool | None = None,
    tag: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[ListeningGuide]:
    query = db.query(ListeningGuide).filter(ListeningGuide.user_id == user_id)
    needle = (q or "").strip()
    if needle:
        like = f"%{needle}%"
        query = query.filter(
            or_(
                ListeningGuide.work_title.ilike(like),
                ListeningGuide.composer.ilike(like),
                ListeningGuide.summary.ilike(like),
                ListeningGuide.message.ilike(like),
            )
        )
    if status:
        query = query.filter(ListeningGuide.status == status.strip())
    if published is True:
        query = query.filter(
            ListeningGuide.published_at.isnot(None),
            ListeningGuide.share_slug.isnot(None),
        )
    elif published is False:
        query = query.filter(
            or_(ListeningGuide.published_at.is_(None), ListeningGuide.share_slug.is_(None))
        )
    if favorited is True:
        query = query.filter(ListeningGuide.favorited_at.isnot(None))
    elif favorited is False:
        query = query.filter(ListeningGuide.favorited_at.is_(None))
    tag_n = (tag or "").strip().lower()
    if tag_n:
        # SQLite/JSON text: match normalized quoted token
        query = query.filter(ListeningGuide.tags_json.ilike(f'%"{tag_n}"%'))
    limit = max(1, min(int(limit or 50), 100))
    offset = max(0, int(offset or 0))
    return query.order_by(ListeningGuide.id.desc()).offset(offset).limit(limit).all()


def delete_owned_guide(db: Session, *, user_id: int, guide_id: int) -> bool:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def set_guide_favorite(db: Session, *, user_id: int, guide_id: int, favorited: bool) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    row.favorited_at = utcnow() if favorited else None
    row.updated_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def set_guide_tags(db: Session, *, user_id: int, guide_id: int, tags: list[str]) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    row.tags_json = json.dumps(normalize_tags(tags), ensure_ascii=False)
    row.updated_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def placeholder_title(message: str) -> str:
    text = " ".join((message or "").strip().split())
    if not text:
        return "Composing…"
    if len(text) > 72:
        return text[:69] + "…"
    return text


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


def create_queued_guide(
    db: Session,
    *,
    user_id: int,
    message: str,
    work_hint: str | None = None,
) -> ListeningGuide:
    text = (message or "").strip()
    row = ListeningGuide(
        user_id=user_id,
        work_title=placeholder_title(text),
        composer="",
        status="queued",
        source="pending",
        summary="",
        guide_html="",
        steps_json=json.dumps(initial_plan_steps(), ensure_ascii=False),
        research_json="{}",
        skill_versions_json="{}",
        message=text,
        error_detail="",
        tags_json="[]",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    from aulos_api.services.listening_queue import enqueue_listening_job

    enqueue_listening_job(
        guide_id=row.id,
        user_id=user_id,
        kind="compose",
        work_hint=work_hint,
    )
    return row


def enqueue_recompose_guide(
    db: Session,
    *,
    user_id: int,
    guide_id: int,
    message: str | None = None,
    work_hint: str | None = None,
) -> ListeningGuide | None:
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    text = (message or "").strip() or (row.message or "").strip() or f"Listening guide for {row.work_title}"
    row.message = text
    row.status = "queued"
    row.error_detail = ""
    row.steps_json = json.dumps(initial_plan_steps(), ensure_ascii=False)
    row.updated_at = utcnow()
    if row.work_title.startswith("Composing") or not row.guide_html:
        row.work_title = placeholder_title(text)
    db.add(row)
    db.commit()
    db.refresh(row)
    from aulos_api.services.listening_queue import enqueue_listening_job

    enqueue_listening_job(
        guide_id=row.id,
        user_id=user_id,
        kind="recompose",
        work_hint=work_hint or row.work_title,
    )
    return row


def enqueue_targeted_revise_guide(
    db: Session,
    *,
    user_id: int,
    guide_id: int,
    review_notes: str,
    work_hint: str | None = None,
) -> ListeningGuide | None:
    """Queue SPEC-022Δ targeted chamber refresh (no full listening chain)."""
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    notes = (review_notes or "").strip()
    if not notes:
        return None
    try:
        research = json.loads(row.research_json or "{}")
    except json.JSONDecodeError:
        research = {}
    if not isinstance(research, dict):
        research = {}
    research["pending_review_notes"] = notes
    research["revise_mode"] = "targeted"
    row.research_json = json.dumps(research, ensure_ascii=False)
    row.status = "queued"
    row.error_detail = ""
    # Compact plan for reconnect UI
    row.steps_json = json.dumps(
        [
            {
                "id": "targeted.locate",
                "title": "Locate review targets",
                "status": "queued",
                "thinking": "Map review notes to chambers",
                "detail": "",
            },
            {
                "id": "targeted.patch",
                "title": "Patch chambers",
                "status": "queued",
                "thinking": "Rewrite only targeted sections",
                "detail": "",
            },
            {
                "id": "targeted.render",
                "title": "Re-render + score",
                "status": "queued",
                "thinking": "Render HTML and update generation_rounds",
                "detail": "",
            },
        ],
        ensure_ascii=False,
    )
    row.updated_at = utcnow()
    db.add(row)
    db.commit()
    db.refresh(row)
    from aulos_api.services.listening_queue import enqueue_listening_job

    enqueue_listening_job(
        guide_id=row.id,
        user_id=user_id,
        kind="targeted_revise",
        work_hint=work_hint or row.work_title,
        review_notes=notes,
    )
    return row


def retry_listening_guide_job(
    db: Session,
    *,
    user_id: int,
    guide_id: int,
) -> ListeningGuide | None:
    """Re-queue a failed or stale-running job with a fresh countable plan."""
    row = get_owned_guide(db, user_id=user_id, guide_id=guide_id)
    if row is None:
        return None
    status = (row.status or "").strip()
    stale = False
    if status == "running" and row.updated_at is not None:
        updated = row.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=timezone.utc)
        age = (utcnow() - updated).total_seconds()
        stale = age >= STALE_RUNNING_SECONDS
    if status == "completed":
        return None
    if status == "running" and not stale:
        return row  # still working — client should keep watching
    if status not in {"failed", "queued"} and not stale:
        return None
    return enqueue_recompose_guide(
        db,
        user_id=user_id,
        guide_id=guide_id,
        message=row.message or None,
        work_hint=row.work_title or None,
    )


async def iter_guide_job_events(
    *,
    user_id: int,
    guide_id: int,
    poll_seconds: float = 0.35,
    timeout_seconds: float = 900.0,
    db: Session | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Reconnect-safe SSE: poll persisted steps/status until terminal.

    Emits `progress` snapshots whenever steps/status change so in-place stage
    updates (pending→running→done) are visible after reconnect.
    """
    import asyncio

    from aulos_api.db import session as db_session

    last_sig = ""
    started = time.monotonic()
    while True:
        own_session = db is None
        session = db
        if session is None:
            db_session.get_engine()
            if db_session.SessionLocal is None:
                yield {"event": "error", "data": {"detail": "Database unavailable"}}
                return
            session = db_session.SessionLocal()
        try:
            row = get_owned_guide(session, user_id=user_id, guide_id=guide_id)
            if row is None:
                yield {"event": "error", "data": {"detail": "Guide not found"}}
                return
            try:
                steps = json.loads(row.steps_json or "[]")
                if not isinstance(steps, list):
                    steps = []
            except json.JSONDecodeError:
                steps = []
            steps = coalesce_plan_steps([s for s in steps if isinstance(s, dict)])
            counts = progress_counts(steps)
            sig = json.dumps(
                {"status": row.status, "steps": steps, "error": row.error_detail or ""},
                ensure_ascii=False,
                sort_keys=True,
            )
            if sig != last_sig:
                last_sig = sig
                yield {
                    "event": "progress",
                    "data": {
                        "guide_id": row.id,
                        "status": row.status,
                        "done": counts["done"],
                        "completed": counts.get("completed", counts["done"]),
                        "skipped": counts.get("skipped", 0),
                        "failed": counts.get("failed", 0),
                        "total": counts["total"],
                        "steps": steps,
                        "error_detail": row.error_detail or "",
                    },
                }
                for step in steps:
                    if isinstance(step, dict):
                        yield {"event": "step", "data": step}
            if row.status == "completed":
                yield {"event": "done", "data": guide_to_dict(row)}
                return
            if row.status == "failed":
                yield {
                    "event": "error",
                    "data": {
                        "detail": row.error_detail or "Guide job failed",
                        "guide_id": row.id,
                        "status": "failed",
                        "retryable": True,
                    },
                }
                return
        finally:
            if own_session and session is not None:
                session.close()
            elif session is not None:
                session.expire_all()

        if time.monotonic() - started > timeout_seconds:
            yield {
                "event": "error",
                "data": {
                    "detail": "Timed out waiting for guide job",
                    "guide_id": guide_id,
                    "retryable": True,
                },
            }
            return
        await asyncio.sleep(poll_seconds)
