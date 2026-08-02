"""Web research loop: search → LLM verify → KB persist (generic, no composer branches).

Decision policy (not “thin forever”):
1. **cold_fill** — local RAG/dossier below richness floor → full gather+verify+upsert
2. **refresh** — dossier already rich but provenance/doc age past TTL → gather+verify,
   merge onto existing KB (so external updates are not frozen out)
3. **skip** — rich AND within TTL → reuse KB only

Richness is a *chamber coverage* score (portrait/profile/genesis/stature/sound/map/…),
not a claim that the outside world stopped changing.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import KnowledgeDocument, SystemSetting
from aulos_api.services.knowledge_base import normalize_work_key, upsert_document
from aulos_api.services.llm_providers import chat_with_ops_llm, load_llm_config
from aulos_api.services.web_search import gather_web_sources

logger = logging.getLogger("aulos_api.web_research")

WEB_RESEARCH_SETTING_KEY = "web.research"

# Default: re-check open web weekly even when local dossier looks complete.
DEFAULT_REFRESH_AFTER_HOURS = 168
DEFAULT_PROGRAM_DEEPEN_BUDGET_SECONDS = 120


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_iso() -> str:
    return _utcnow().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bool_setting(data: dict[str, Any], key: str, default: bool) -> bool:
    raw = data.get(key)
    if raw is None:
        return default
    if isinstance(raw, str):
        return raw.strip().lower() not in {"0", "false", "no", "off"}
    return bool(raw)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    raw = str(ts).strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_web_research_config(db: Session) -> dict[str, Any]:
    row = db.query(SystemSetting).filter(SystemSetting.key == WEB_RESEARCH_SETTING_KEY).one_or_none()
    data: dict[str, Any] = {}
    if row and row.value:
        try:
            parsed = json.loads(row.value)
            if isinstance(parsed, dict):
                data = parsed
        except json.JSONDecodeError:
            data = {}
    return {
        "enabled": _bool_setting(data, "enabled", True),
        "min_rag_hits": int(data.get("min_rag_hits") or 3),
        "min_dossier_richness": int(data.get("min_dossier_richness") or 5),
        "refresh_after_hours": int(
            data.get("refresh_after_hours")
            if data.get("refresh_after_hours") is not None
            else DEFAULT_REFRESH_AFTER_HOURS
        ),
        "brave_api_key": str(data.get("brave_api_key") or ""),
        "persist_global": _bool_setting(data, "persist_global", True),
        "max_sources": int(data.get("max_sources") or 10),
        # Agent Reach search enabler (Jina deepen); social/cookie paths remain denied.
        "agent_reach_enabled": _bool_setting(data, "agent_reach_enabled", True),
        # SPEC-034 latency defaults: multi-work program deepen is fast/budgeted.
        "program_deepen_mode": str(data.get("program_deepen_mode") or "fast").strip().lower(),
        "program_deepen_max_works": int(data.get("program_deepen_max_works") or 6),
        "program_deepen_max_sources": int(data.get("program_deepen_max_sources") or 4),
        "program_deepen_budget_seconds": int(
            data.get("program_deepen_budget_seconds") or DEFAULT_PROGRAM_DEEPEN_BUDGET_SECONDS
        ),
        "program_deepen_per_work_llm": _bool_setting(data, "program_deepen_per_work_llm", False),
        "program_deepen_album_llm": _bool_setting(data, "program_deepen_album_llm", False),
        "program_deepen_verify_sources": _bool_setting(data, "program_deepen_verify_sources", False),
        "program_deepen_agent_reach_enabled": _bool_setting(
            data,
            "program_deepen_agent_reach_enabled",
            False,
        ),
        "program_deepen_max_variants": int(data.get("program_deepen_max_variants") or 1),
        "program_deepen_wikipedia_limit": int(data.get("program_deepen_wikipedia_limit") or 1),
        "program_deepen_search_timeout": float(data.get("program_deepen_search_timeout") or 5.0),
    }


def save_web_research_config(
    db: Session,
    *,
    enabled: bool | None = None,
    min_rag_hits: int | None = None,
    min_dossier_richness: int | None = None,
    refresh_after_hours: int | None = None,
    brave_api_key: str | None = None,
    persist_global: bool | None = None,
    max_sources: int | None = None,
    agent_reach_enabled: bool | None = None,
    program_deepen_mode: str | None = None,
    program_deepen_max_works: int | None = None,
    program_deepen_max_sources: int | None = None,
    program_deepen_budget_seconds: int | None = None,
    program_deepen_per_work_llm: bool | None = None,
    program_deepen_album_llm: bool | None = None,
    program_deepen_verify_sources: bool | None = None,
    program_deepen_agent_reach_enabled: bool | None = None,
    program_deepen_max_variants: int | None = None,
    program_deepen_wikipedia_limit: int | None = None,
    program_deepen_search_timeout: float | None = None,
) -> dict[str, Any]:
    current = load_web_research_config(db)
    if enabled is not None:
        current["enabled"] = bool(enabled)
    if min_rag_hits is not None:
        current["min_rag_hits"] = max(0, int(min_rag_hits))
    if min_dossier_richness is not None:
        current["min_dossier_richness"] = max(0, int(min_dossier_richness))
    if refresh_after_hours is not None:
        # 0 = always refresh when not thin (still merges; never skip-forever)
        current["refresh_after_hours"] = max(0, int(refresh_after_hours))
    if brave_api_key is not None:
        current["brave_api_key"] = brave_api_key
    if persist_global is not None:
        current["persist_global"] = bool(persist_global)
    if max_sources is not None:
        current["max_sources"] = max(3, int(max_sources))
    if agent_reach_enabled is not None:
        current["agent_reach_enabled"] = bool(agent_reach_enabled)
    if program_deepen_mode is not None:
        mode = str(program_deepen_mode or "fast").strip().lower()
        current["program_deepen_mode"] = mode if mode in {"fast", "full"} else "fast"
    if program_deepen_max_works is not None:
        current["program_deepen_max_works"] = max(1, min(12, int(program_deepen_max_works)))
    if program_deepen_max_sources is not None:
        current["program_deepen_max_sources"] = max(1, min(12, int(program_deepen_max_sources)))
    if program_deepen_budget_seconds is not None:
        current["program_deepen_budget_seconds"] = max(20, min(900, int(program_deepen_budget_seconds)))
    if program_deepen_per_work_llm is not None:
        current["program_deepen_per_work_llm"] = bool(program_deepen_per_work_llm)
    if program_deepen_album_llm is not None:
        current["program_deepen_album_llm"] = bool(program_deepen_album_llm)
    if program_deepen_verify_sources is not None:
        current["program_deepen_verify_sources"] = bool(program_deepen_verify_sources)
    if program_deepen_agent_reach_enabled is not None:
        current["program_deepen_agent_reach_enabled"] = bool(program_deepen_agent_reach_enabled)
    if program_deepen_max_variants is not None:
        current["program_deepen_max_variants"] = max(1, min(4, int(program_deepen_max_variants)))
    if program_deepen_wikipedia_limit is not None:
        current["program_deepen_wikipedia_limit"] = max(1, min(3, int(program_deepen_wikipedia_limit)))
    if program_deepen_search_timeout is not None:
        current["program_deepen_search_timeout"] = max(2.0, min(12.0, float(program_deepen_search_timeout)))
    row = db.query(SystemSetting).filter(SystemSetting.key == WEB_RESEARCH_SETTING_KEY).one_or_none()
    payload = json.dumps(
        {
            "enabled": current["enabled"],
            "min_rag_hits": current["min_rag_hits"],
            "min_dossier_richness": current["min_dossier_richness"],
            "refresh_after_hours": current["refresh_after_hours"],
            "brave_api_key": current["brave_api_key"],
            "persist_global": current["persist_global"],
            "max_sources": current["max_sources"],
            "agent_reach_enabled": current["agent_reach_enabled"],
            "program_deepen_mode": current["program_deepen_mode"],
            "program_deepen_max_works": current["program_deepen_max_works"],
            "program_deepen_max_sources": current["program_deepen_max_sources"],
            "program_deepen_budget_seconds": current["program_deepen_budget_seconds"],
            "program_deepen_per_work_llm": current["program_deepen_per_work_llm"],
            "program_deepen_album_llm": current["program_deepen_album_llm"],
            "program_deepen_verify_sources": current["program_deepen_verify_sources"],
            "program_deepen_agent_reach_enabled": current["program_deepen_agent_reach_enabled"],
            "program_deepen_max_variants": current["program_deepen_max_variants"],
            "program_deepen_wikipedia_limit": current["program_deepen_wikipedia_limit"],
            "program_deepen_search_timeout": current["program_deepen_search_timeout"],
        },
        ensure_ascii=False,
    )
    if row is None:
        row = SystemSetting(key=WEB_RESEARCH_SETTING_KEY, value=payload)
        db.add(row)
    else:
        row.value = payload
    db.commit()
    return public_web_research_config(current)


def public_web_research_config(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    c = cfg or {}
    return {
        "enabled": bool(c.get("enabled", True)),
        "min_rag_hits": int(c.get("min_rag_hits") or 3),
        "min_dossier_richness": int(c.get("min_dossier_richness") or 5),
        "refresh_after_hours": int(
            c.get("refresh_after_hours")
            if c.get("refresh_after_hours") is not None
            else DEFAULT_REFRESH_AFTER_HOURS
        ),
        "brave_api_key_set": bool(c.get("brave_api_key")),
        "persist_global": bool(c.get("persist_global", True)),
        "max_sources": int(c.get("max_sources") or 10),
        "agent_reach_enabled": bool(c.get("agent_reach_enabled", True)),
        "program_deepen_mode": str(c.get("program_deepen_mode") or "fast"),
        "program_deepen_max_works": int(c.get("program_deepen_max_works") or 6),
        "program_deepen_max_sources": int(c.get("program_deepen_max_sources") or 4),
        "program_deepen_budget_seconds": int(
            c.get("program_deepen_budget_seconds") or DEFAULT_PROGRAM_DEEPEN_BUDGET_SECONDS
        ),
        "program_deepen_per_work_llm": bool(c.get("program_deepen_per_work_llm", False)),
        "program_deepen_album_llm": bool(c.get("program_deepen_album_llm", False)),
        "program_deepen_verify_sources": bool(c.get("program_deepen_verify_sources", False)),
        "program_deepen_agent_reach_enabled": bool(
            c.get("program_deepen_agent_reach_enabled", False)
        ),
        "program_deepen_max_variants": int(c.get("program_deepen_max_variants") or 1),
        "program_deepen_wikipedia_limit": int(c.get("program_deepen_wikipedia_limit") or 1),
        "program_deepen_search_timeout": float(c.get("program_deepen_search_timeout") or 5.0),
    }


def _dossier_richness(dossier: dict[str, Any] | None) -> int:
    try:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.salon_codex import dossier_richness

        return int(dossier_richness(dossier or {}))
    except Exception:  # noqa: BLE001
        d = dossier or {}
        score = 0
        if d.get("listening_thesis") or d.get("work_introduction"):
            score += 1
        if d.get("genesis"):
            score += 1
        if d.get("sound_world"):
            score += 1
        if len(d.get("depth_points") or []) >= 2:
            score += 1
        if d.get("interpretations"):
            score += 1
        return score


def rag_is_thin(rag: dict[str, Any], *, cfg: dict[str, Any] | None = None) -> bool:
    """Cold-fill floor: chamber coverage + hit count. Does NOT imply 'never refresh'."""
    c = cfg or {}
    min_hits = int(c.get("min_rag_hits") or 3)
    min_rich = int(c.get("min_dossier_richness") or 5)
    hits = [h for h in (rag.get("rag_hits") or []) if str(h).strip()]
    dossier = dict(rag.get("kb_dossier") or {})
    rich = _dossier_richness(dossier)
    if rich >= min_rich and len(hits) >= min_hits:
        return False
    if rich >= min_rich + 2:
        return False
    return True


def _kb_freshness_ts(
    db: Session,
    *,
    work_title: str,
    composer: str,
    user_id: int | None,
    rag_dossier: dict[str, Any] | None,
) -> datetime | None:
    """Best-effort last web-verify / doc update time for this work shelf."""
    candidates: list[datetime] = []
    prov = dict((rag_dossier or {}).get("_provenance") or {})
    for key in ("verified_at", "refreshed_at"):
        dt = _parse_iso(str(prov.get(key) or "") or None)
        if dt:
            candidates.append(dt)
    key = normalize_work_key(work_title, composer)
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.work_key == key).all()
    docs = sorted(
        docs,
        key=lambda d: (0 if user_id is not None and d.user_id == user_id else (1 if d.user_id is None else 2)),
    )
    for doc in docs[:3]:
        try:
            meta = json.loads(doc.dossier_json or "{}")
        except json.JSONDecodeError:
            meta = {}
        p = dict(meta.get("_provenance") or {})
        for k in ("verified_at", "refreshed_at"):
            dt = _parse_iso(str(p.get(k) or "") or None)
            if dt:
                candidates.append(dt)
    return max(candidates) if candidates else None


def decide_web_research(
    db: Session,
    *,
    work_title: str,
    composer: str = "",
    user_id: int | None = None,
    rag: dict[str, Any] | None = None,
    cfg: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return {action: cold_fill|refresh|skip, reason, richness, age_hours?}."""
    c = cfg or load_web_research_config(db)
    rag = rag or {}
    dossier = dict(rag.get("kb_dossier") or {})
    rich = _dossier_richness(dossier)
    thin = rag_is_thin(rag, cfg=c)
    if thin:
        return {
            "action": "cold_fill",
            "reason": "rag_thin",
            "richness": rich,
            "min_dossier_richness": int(c.get("min_dossier_richness") or 5),
        }

    ttl_h = int(
        c.get("refresh_after_hours")
        if c.get("refresh_after_hours") is not None
        else DEFAULT_REFRESH_AFTER_HOURS
    )
    stamp = _kb_freshness_ts(
        db,
        work_title=work_title,
        composer=composer,
        user_id=user_id,
        rag_dossier=dossier,
    )
    clock = now or _utcnow()
    if stamp is None:
        return {
            "action": "refresh",
            "reason": "no_web_provenance",
            "richness": rich,
            "refresh_after_hours": ttl_h,
        }
    age = clock - stamp
    age_hours = age.total_seconds() / 3600.0
    if ttl_h <= 0 or age >= timedelta(hours=ttl_h):
        return {
            "action": "refresh",
            "reason": "stale",
            "richness": rich,
            "age_hours": round(age_hours, 2),
            "refresh_after_hours": ttl_h,
            "last_verified_at": stamp.isoformat().replace("+00:00", "Z"),
        }
    return {
        "action": "skip",
        "reason": "fresh",
        "richness": rich,
        "age_hours": round(age_hours, 2),
        "refresh_after_hours": ttl_h,
        "last_verified_at": stamp.isoformat().replace("+00:00", "Z"),
    }


def _merge_dossiers(base: dict[str, Any], newer: dict[str, Any]) -> dict[str, Any]:
    """Merge refresh onto existing shelf — prefer skills merge when available."""
    try:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.salon_codex import merge_dossiers

        merged = merge_dossiers(base or {}, newer or {})
    except Exception:  # noqa: BLE001
        merged = dict(base or {})
        for k, v in (newer or {}).items():
            if v in (None, "", [], {}):
                continue
            if isinstance(v, dict) and isinstance(merged.get(k), dict):
                cur = dict(merged[k])
                cur.update(v)
                merged[k] = cur
            elif isinstance(v, list) and isinstance(merged.get(k), list):
                seen = {json.dumps(x, sort_keys=True, default=str) for x in merged[k]}
                out = list(merged[k])
                for item in v:
                    key = json.dumps(item, sort_keys=True, default=str)
                    if key not in seen:
                        out.append(item)
                        seen.add(key)
                merged[k] = out
            else:
                merged[k] = v
    old_prov = dict((base or {}).get("_provenance") or {})
    new_prov = dict((newer or {}).get("_provenance") or {})
    prior = list(old_prov.get("prior_refreshes") or [])
    if old_prov.get("verified_at") or old_prov.get("refreshed_at"):
        prior.append(
            {
                "verified_at": old_prov.get("verified_at") or old_prov.get("refreshed_at"),
                "method": old_prov.get("method"),
                "source_count": len(old_prov.get("sources") or []),
            }
        )
    new_prov["prior_refreshes"] = prior[-5:]
    new_prov["refreshed_at"] = new_prov.get("verified_at") or _utcnow_iso()
    new_prov["refresh_of"] = old_prov.get("verified_at") or old_prov.get("refreshed_at")
    merged["_provenance"] = new_prov
    return merged


def _parse_llm_json(text: str) -> dict[str, Any]:
    try:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.salon_codex import parse_llm_dossier_json

        return parse_llm_dossier_json(text) or {}
    except Exception:  # noqa: BLE001
        raw = (text or "").strip()
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
                return data if isinstance(data, dict) else {}
            except json.JSONDecodeError:
                return {}
        return {}


def _raw_web_dossier(
    *,
    work_title: str,
    composer: str,
    work_id: str,
    sources: list[dict[str, Any]],
    reason: str = "llm_unavailable",
) -> dict[str, Any]:
    """META-001 §4.1: LLM verify is enrich — gather must still yield a usable floor."""
    width = [str(s.get("snippet") or "")[:280] for s in sources[:6] if s.get("snippet")]
    titles = [str(s.get("title") or "").strip() for s in sources[:6] if s.get("title")]
    thesis_bits = [t for t in titles if t][:2]
    thesis = (
        "; ".join(thesis_bits)[:240]
        if thesis_bits
        else f"Research notes for {work_title} gathered from open sources."
    )
    return {
        "work_title": work_title,
        "composer": composer,
        "work_id": work_id or None,
        "listening_thesis": thesis,
        "width_points": width,
        "myths_and_caveats": [
            "Web extracts not LLM-verified — treat as leads; confirm before stating as fact.",
            f"Degraded verify path: {reason}",
        ],
        "zh": {
            "listening_thesis": f"《{work_title}》公开来源摘录（未经模型核验，仅作线索）。",
            "width_points": width,
            "myths_and_caveats": ["公开网页摘录未经模型核验——陈述前请再确认。"],
        },
        "_provenance": {
            "method": "web_search_raw",
            "verified": False,
            "verified_at": _utcnow_iso(),
            "degrade_reason": reason,
            "sources": sources,
        },
    }


async def verify_sources_to_dossier(
    db: Session,
    *,
    work_title: str,
    composer: str,
    work_id: str,
    facets: dict[str, Any],
    sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """LLM extracts Salon Codex fields only when supported by provided sources."""
    if not sources:
        return {}
    cfg = load_llm_config(db)
    evidence = "\n".join(
        f"- [{i+1}] {s.get('title')}: {s.get('snippet')} (url: {s.get('url')})"
        for i, s in enumerate(sources)
    )
    facet_bits = []
    for key in ("instruments", "forms", "era", "ensemble"):
        vals = list((facets or {}).get(key) or [])
        if vals:
            facet_bits.append(f"{key}: {', '.join(str(v) for v in vals)}")

    if not cfg.ready_for_live:
        return _raw_web_dossier(
            work_title=work_title,
            composer=composer,
            work_id=work_id,
            sources=sources,
            reason="llm_not_ready",
        )

    prompt = (
        "You are Aulos research verifier. Using ONLY the numbered sources below, "
        "fill a compact Salon Codex JSON for the identified work. "
        "Do not invent Discogs/YouTube item IDs; search URLs are OK. "
        "If a fact is not in the sources, omit it or put it under myths_and_caveats as uncertain.\n"
        f"Work: {work_title}\nComposer: {composer or 'unknown'}\n"
        f"Catalog work_id: {work_id or 'none'}\n"
        f"Facets: {'; '.join(facet_bits) if facet_bits else 'none'}\n\n"
        f"Sources:\n{evidence}\n\n"
        "Return ONLY JSON with: listening_thesis, work_introduction, era, form, "
        "composer_profile, genesis, historical_stature, width_points, depth_points, "
        "listening_map, sound_world, related_works, interpretations, practice_notes, "
        "myths_and_caveats, nested zh_hans (简体导赏), nested zh_hant (繁体导赏), "
        "and legacy zh (= zh_hans). "
        "Also include supported_source_indexes: [1-based ints you actually used]."
    )
    try:
        live = await chat_with_ops_llm(db=db, message=prompt, timeout=90.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("web_verify_llm_failed work=%s err=%s", work_title, exc)
        return _raw_web_dossier(
            work_title=work_title,
            composer=composer,
            work_id=work_id,
            sources=sources,
            reason=f"llm_error:{type(exc).__name__}",
        )
    if live is None:
        return _raw_web_dossier(
            work_title=work_title,
            composer=composer,
            work_id=work_id,
            sources=sources,
            reason="llm_empty",
        )
    text, _provider = live
    dossier = _parse_llm_json(text)
    if not dossier:
        return _raw_web_dossier(
            work_title=work_title,
            composer=composer,
            work_id=work_id,
            sources=sources,
            reason="llm_parse_failed",
        )
    dossier["work_title"] = work_title
    if composer:
        dossier["composer"] = composer
    if work_id:
        dossier["work_id"] = work_id
    used = dossier.pop("supported_source_indexes", None)
    kept_sources = sources
    if isinstance(used, list) and used:
        idxs = []
        for u in used:
            try:
                idxs.append(int(u) - 1)
            except (TypeError, ValueError):
                continue
        filtered = [sources[i] for i in idxs if 0 <= i < len(sources)]
        if filtered:
            kept_sources = filtered
    dossier["_provenance"] = {
        "method": "web_search+llm",
        "verified": True,
        "verified_at": _utcnow_iso(),
        "sources": kept_sources,
    }
    return dossier


def persist_web_dossier(
    db: Session,
    *,
    dossier: dict[str, Any],
    user_id: int | None,
    persist_global: bool = True,
    source_guide_id: int | None = None,
    merge_existing: bool = False,
) -> list[int]:
    """Upsert verified web research into KB (user scope + optional global)."""
    title = str(dossier.get("work_title") or "")
    composer = str(dossier.get("composer") or "")
    if not title:
        return []
    key = normalize_work_key(title, composer)
    ids: list[int] = []
    targets: list[int | None] = []
    if user_id is not None:
        targets.append(user_id)
    if persist_global:
        targets.append(None)
    seen: set[str] = set()
    for uid in targets:
        mark = "global" if uid is None else f"u{uid}"
        if mark in seen:
            continue
        seen.add(mark)
        payload = dict(dossier)
        if merge_existing:
            q = db.query(KnowledgeDocument).filter(KnowledgeDocument.work_key == key)
            if uid is None:
                q = q.filter(KnowledgeDocument.user_id.is_(None))
            else:
                q = q.filter(KnowledgeDocument.user_id == uid)
            prior = q.one_or_none()
            if prior and prior.dossier_json:
                try:
                    old = json.loads(prior.dossier_json)
                except json.JSONDecodeError:
                    old = {}
                if isinstance(old, dict) and old:
                    payload = _merge_dossiers(old, dossier)
        doc = upsert_document(
            db,
            work_key=key,
            title=title,
            composer=composer,
            dossier=payload,
            source_guide_id=source_guide_id,
            user_id=uid,
        )
        ids.append(doc.id)
        logger.info(
            "web_research_persisted work_key=%s user=%s doc=%s verified=%s merge=%s",
            key,
            uid,
            doc.id,
            bool((payload.get("_provenance") or {}).get("verified")),
            merge_existing,
        )
    return ids


async def run_web_research(
    db: Session,
    *,
    work_title: str,
    composer: str = "",
    work_id: str = "",
    facets: dict[str, Any] | None = None,
    user_id: int | None = None,
    rag: dict[str, Any] | None = None,
    force_action: str | None = None,
    verify_sources: bool = True,
    agent_reach_enabled: bool | None = None,
    max_sources: int | None = None,
    max_variants: int | None = None,
    wikipedia_limit: int | None = None,
    search_timeout: float | None = None,
) -> dict[str, Any]:
    """Full loop. Returns skipped dict when fresh; otherwise cold_fill or refresh.

    force_action: when ``cold_fill`` or ``refresh``, bypass freshness skip
    (SPEC-034 program deepen loop — each program work must gather evidence).
    """
    cfg = load_web_research_config(db)
    if not cfg.get("enabled"):
        return {"skipped": True, "reason": "disabled", "action": "skip"}
    if not work_title.strip():
        return {"skipped": True, "reason": "no_work_title", "action": "skip"}

    forced = str(force_action or "").strip().lower()
    if forced in {"cold_fill", "refresh"}:
        decision = {
            "action": forced,
            "reason": "forced_program_iteration",
            "richness": _dossier_richness(dict((rag or {}).get("kb_dossier") or {})),
        }
    else:
        decision = decide_web_research(
            db,
            work_title=work_title,
            composer=composer,
            user_id=user_id,
            rag=rag,
            cfg=cfg,
        )
    action = str(decision.get("action") or "skip")
    if action == "skip":
        return {
            "skipped": True,
            "reason": decision.get("reason") or "fresh",
            "action": "skip",
            "decision": decision,
        }

    sources = gather_web_sources(
        work_title=work_title,
        composer=composer,
        brave_api_key=str(cfg.get("brave_api_key") or ""),
        max_sources=int(max_sources if max_sources is not None else (cfg.get("max_sources") or 10)),
        agent_reach_enabled=(
            bool(cfg.get("agent_reach_enabled", True))
            if agent_reach_enabled is None
            else bool(agent_reach_enabled)
        ),
        max_variants=max_variants,
        wikipedia_limit=int(wikipedia_limit if wikipedia_limit is not None else 3),
        search_timeout=float(search_timeout if search_timeout is not None else 12.0),
    )
    if not sources:
        return {
            "skipped": True,
            "reason": "no_sources",
            "action": action,
            "decision": decision,
        }

    if not verify_sources:
        dossier = _raw_web_dossier(
            work_title=work_title,
            composer=composer,
            work_id=work_id,
            sources=sources,
            reason="web_search_raw_unverified",
        )
        rag_hits = [
            f"[web:{s.get('provider')}] {s.get('title')}: {str(s.get('snippet') or '')[:220]}"
            for s in sources
            if s.get("snippet")
        ]
        doc_ids = persist_web_dossier(
            db,
            dossier=dossier,
            user_id=user_id,
            persist_global=bool(cfg.get("persist_global", True)),
            merge_existing=False,
        )
        return {
            "skipped": False,
            "partial": True,
            "reason": "web_search_raw_unverified",
            "action": action,
            "decision": decision,
            "sources": sources,
            "dossier": dossier,
            "rag_hits": rag_hits,
            "persisted_doc_ids": doc_ids,
            "rag_mode_suffix": "web-fast-raw",
        }

    dossier = await verify_sources_to_dossier(
        db,
        work_title=work_title,
        composer=composer,
        work_id=work_id,
        facets=dict(facets or {}),
        sources=sources,
    )
    if not dossier:
        rag_hits = [
            f"[web:{s.get('provider')}] {s.get('title')}: {str(s.get('snippet') or '')[:220]}"
            for s in sources
            if s.get("snippet")
        ]
        return {
            "skipped": False,
            "partial": True,
            "reason": "verify_failed",
            "action": action,
            "decision": decision,
            "sources": sources,
            "dossier": {},
            "rag_hits": rag_hits,
            "persisted_doc_ids": [],
            "rag_mode_suffix": "web-partial",
        }
    # Raw floor still counts as usable evidence (META §4.1 — LLM is enrich, not gate)
    is_raw = str((dossier.get("_provenance") or {}).get("method") or "") == "web_search_raw"
    if is_raw:
        rag_hits = [
            f"[web:{s.get('provider')}] {s.get('title')}: {str(s.get('snippet') or '')[:220]}"
            for s in sources
            if s.get("snippet")
        ]
        # Persist raw floor so next RAG is warmer even without LLM verify
        doc_ids = persist_web_dossier(
            db,
            dossier=dossier,
            user_id=user_id,
            persist_global=bool(cfg.get("persist_global", True)),
            merge_existing=False,
        )
        return {
            "skipped": False,
            "partial": True,
            "reason": str((dossier.get("_provenance") or {}).get("degrade_reason") or "web_search_raw"),
            "action": action,
            "decision": decision,
            "sources": sources,
            "dossier": dossier,
            "rag_hits": rag_hits,
            "persisted_doc_ids": doc_ids,
            "rag_mode_suffix": "web-partial",
        }

    merge_existing = action == "refresh"
    existing = dict((rag or {}).get("kb_dossier") or {})
    if merge_existing and existing:
        dossier = _merge_dossiers(existing, dossier)

    doc_ids = persist_web_dossier(
        db,
        dossier=dossier,
        user_id=user_id,
        persist_global=bool(cfg.get("persist_global", True)),
        merge_existing=merge_existing,
    )
    rag_hits = [
        f"[web:{s.get('provider')}] {s.get('title')}: {str(s.get('snippet') or '')[:220]}"
        for s in sources
        if s.get("snippet")
    ]
    suffix = "web-refresh" if action == "refresh" else "web-research"
    return {
        "skipped": False,
        "action": action,
        "decision": decision,
        "dossier": dossier,
        "rag_hits": rag_hits,
        "sources": sources,
        "persisted_doc_ids": doc_ids,
        "rag_mode_suffix": suffix,
    }
