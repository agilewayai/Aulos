"""Countable listening-chain plan (SPEC-013 delta — progress + recoverability)."""

from __future__ import annotations

from typing import Any

# Fixed gateway stages (API). Agent skill steps append after g.agent starts.
GATEWAY_STAGES: tuple[tuple[str, str, str], ...] = (
    ("g.discogs", "Discogs", "Resolve /discogs release or skip when absent"),
    ("g.identity", "Identity", "Catalog identity lock for the work"),
    ("g.rag", "Knowledge", "Retrieve corpus, KB, and knowledge-plane hits"),
    ("g.web", "Web research", "Open-web gather when the shelf is cold"),
    ("g.extweb", "Review web", "Networked sources for external review Agent"),
    ("g.llm", "LLM enrich", "Bilingual Salon Codex enrichment"),
    ("g.agent", "Agent atelier", "Run listening skill playbook"),
    ("g.persist", "Persist", "Save guide HTML and evaluation"),
)

# Expected agent skill triggers (countable placeholders until tools report).
AGENT_STAGES: tuple[tuple[str, str, str], ...] = (
    ("listening.route", "Route", "Choose listening playbook path"),
    ("listening.intake", "Intake", "Parse listener intent and shelf"),
    ("listening.corpus", "Corpus", "Load curated listening corpus"),
    ("listening.synthesize", "Synthesize", "Merge research into dossier"),
    ("listening.width", "Width", "Wide cultural / historical frame"),
    ("listening.depth", "Depth", "Deep listening anatomy"),
    ("listening.compose", "Compose", "Render bilingual listening guide (draft v1)"),
    ("listening.external_review", "External review", "Expert music-guide / analysis hard-flaw review"),
    ("listening.revise", "Revise", "Targeted chamber patch from review intents"),
    ("listening.eval", "Eval", "Acceptance checks + dual-draft scores"),
)

PLAN_TOTAL = len(GATEWAY_STAGES) + len(AGENT_STAGES)

_PLAN_IDS = frozenset(sid for sid, _t, _th in GATEWAY_STAGES + AGENT_STAGES)
_AGENT_SHORT_TO_ID = {sid.split(".", 1)[-1]: sid for sid, _t, _th in AGENT_STAGES}

DONE_STATUSES = frozenset({"done", "completed", "ok"})
SKIP_STATUSES = frozenset({"skip", "skipped"})
FAIL_STATUSES = frozenset({"failed"})
TERMINAL_STATUSES = DONE_STATUSES | SKIP_STATUSES | FAIL_STATUSES


def canonicalize_step_id(sid: str | None) -> str:
    """Map skill short ids (route) onto plan placeholders (listening.route)."""
    raw = str(sid or "").strip()
    if not raw:
        return raw
    if raw in _PLAN_IDS:
        return raw
    mapped = _AGENT_SHORT_TO_ID.get(raw)
    if mapped:
        return mapped
    return raw


def _step(
    *,
    sid: str,
    title: str,
    thinking: str,
    index: int,
    total: int = PLAN_TOTAL,
    status: str = "pending",
    detail: str = "",
) -> dict[str, Any]:
    return {
        "id": sid,
        "title": title,
        "status": status,
        "thinking": thinking,
        "detail": detail,
        "index": index,
        "total": total,
        "skill_id": sid if sid.startswith("listening.") else None,
        "skill_version": None,
        "countable": True,
    }


def initial_plan_steps() -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for i, (sid, title, thinking) in enumerate(GATEWAY_STAGES, start=1):
        steps.append(_step(sid=sid, title=title, thinking=thinking, index=i))
    base = len(GATEWAY_STAGES)
    for j, (sid, title, thinking) in enumerate(AGENT_STAGES, start=1):
        steps.append(_step(sid=sid, title=title, thinking=thinking, index=base + j))
    return steps


def _is_countable(step: dict[str, Any]) -> bool:
    return step.get("countable", True) is not False


def progress_counts(steps: list[dict[str, Any]]) -> dict[str, int]:
    """Return completed / skipped / failed breakdown.

    `done` stays the finished count (completed+skipped+failed) for progress bars.
    """
    total = 0
    completed = 0
    skipped = 0
    failed = 0
    for step in steps:
        if not isinstance(step, dict) or not _is_countable(step):
            continue
        total += 1
        status = str(step.get("status") or "").lower()
        if status in DONE_STATUSES:
            completed += 1
        elif status in SKIP_STATUSES:
            skipped += 1
        elif status in FAIL_STATUSES:
            failed += 1
    if total <= 0:
        total = PLAN_TOTAL
    finished = completed + skipped + failed
    return {
        "completed": completed,
        "skipped": skipped,
        "failed": failed,
        "done": finished,
        "total": total,
    }


def upsert_step(steps: list[dict[str, Any]], step: dict[str, Any]) -> list[dict[str, Any]]:
    """Replace by id or append; keep countable index/total when possible."""
    out = [dict(s) for s in steps if isinstance(s, dict)]
    enriched = dict(step)
    raw_id = enriched.get("id")
    sid = canonicalize_step_id(str(raw_id) if raw_id is not None else None)
    if sid:
        enriched["id"] = sid

    # Intent-critic milestones are atelier-visible but do not inflate the plan total.
    if str(sid).startswith("review-"):
        enriched.setdefault("countable", False)

    if sid:
        for i, existing in enumerate(out):
            if existing.get("id") == sid:
                merged = {**existing, **enriched}
                if "index" not in enriched and existing.get("index") is not None:
                    merged["index"] = existing["index"]
                if "total" not in enriched and existing.get("total") is not None:
                    merged["total"] = existing["total"]
                if "countable" not in enriched and "countable" in existing:
                    merged["countable"] = existing["countable"]
                out[i] = merged
                return out

    # Unknown agent/extra step: append with next index
    countable = enriched.get("countable", True) is not False
    if "index" not in enriched:
        enriched["index"] = len(out) + 1
    if countable:
        if "total" not in enriched:
            enriched["total"] = max(PLAN_TOTAL, len([s for s in out if _is_countable(s)]) + 1)
            for row in out:
                if _is_countable(row):
                    row["total"] = enriched["total"]
    else:
        # Keep plan total unchanged for non-countable milestones.
        plan_total = next(
            (int(row["total"]) for row in out if row.get("total") is not None),
            PLAN_TOTAL,
        )
        enriched.setdefault("total", plan_total)
    out.append(enriched)
    return out


def coalesce_plan_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge legacy short-id agent steps onto listening.* placeholders.

    Older runs appended ``route`` beside a still-pending ``listening.route``,
    which left ghost「等待」rows and inflated totals (e.g. 21/31).
    """
    rank = {
        "failed": 5,
        "done": 4,
        "completed": 4,
        "ok": 4,
        "skip": 4,
        "skipped": 4,
        "running": 3,
        "pending": 1,
        "": 0,
    }
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []

    for raw in steps:
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        sid = canonicalize_step_id(str(row.get("id") or ""))
        if not sid:
            continue
        row["id"] = sid
        status = str(row.get("status") or "").lower()
        if status in {"ok", "success", "completed"}:
            row["status"] = "done"
            status = "done"
        elif status == "skipped":
            row["status"] = "skip"
            status = "skip"
        if sid.startswith("review-"):
            row["countable"] = False

        if sid not in merged:
            merged[sid] = row
            order.append(sid)
            continue

        prev = merged[sid]
        prev_status = str(prev.get("status") or "").lower()
        if rank.get(status, 0) >= rank.get(prev_status, 0):
            keep = {**prev, **row}
            # Prefer richer detail/thinking when overwriting with equal-or-better status.
            if not keep.get("detail") and prev.get("detail"):
                keep["detail"] = prev["detail"]
            if not keep.get("thinking") and prev.get("thinking"):
                keep["thinking"] = prev["thinking"]
            if keep.get("index") is None and prev.get("index") is not None:
                keep["index"] = prev["index"]
            merged[sid] = keep

    out = [merged[sid] for sid in order]
    countable_n = sum(1 for s in out if _is_countable(s))
    total = max(PLAN_TOTAL, countable_n)
    for i, row in enumerate(out, start=1):
        if row.get("index") is None:
            row["index"] = i
        if _is_countable(row):
            row["total"] = total
        else:
            row.setdefault("total", total)
    return out


def mark_stage(
    steps: list[dict[str, Any]],
    sid: str,
    *,
    status: str,
    detail: str = "",
    thinking: str | None = None,
) -> list[dict[str, Any]]:
    patch: dict[str, Any] = {"id": sid, "status": status, "detail": detail}
    if thinking is not None:
        patch["thinking"] = thinking
    # Ensure title exists for late marks
    for gid, title, default_thinking in GATEWAY_STAGES + AGENT_STAGES:
        if gid == sid:
            patch.setdefault("title", title)
            patch.setdefault("thinking", thinking or default_thinking)
            break
    return upsert_step(steps, patch)
