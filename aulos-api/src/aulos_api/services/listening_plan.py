"""Countable listening-chain plan (SPEC-013 delta — progress + recoverability)."""

from __future__ import annotations

from typing import Any

# Fixed gateway stages (API). Agent skill steps append after g.agent starts.
GATEWAY_STAGES: tuple[tuple[str, str, str], ...] = (
    ("g.discogs", "Discogs", "Resolve /discogs release or skip when absent"),
    ("g.identity", "Identity", "Catalog identity lock for the work"),
    ("g.rag", "Knowledge", "Retrieve corpus, KB, and knowledge-plane hits"),
    ("g.web", "Web research", "Open-web gather when the shelf is cold"),
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
    ("listening.compose", "Compose", "Render bilingual listening guide"),
    ("listening.eval", "Eval", "Acceptance checks for the guide"),
)

PLAN_TOTAL = len(GATEWAY_STAGES) + len(AGENT_STAGES)


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
    }


def initial_plan_steps() -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for i, (sid, title, thinking) in enumerate(GATEWAY_STAGES, start=1):
        steps.append(_step(sid=sid, title=title, thinking=thinking, index=i))
    base = len(GATEWAY_STAGES)
    for j, (sid, title, thinking) in enumerate(AGENT_STAGES, start=1):
        steps.append(_step(sid=sid, title=title, thinking=thinking, index=base + j))
    return steps


def progress_counts(steps: list[dict[str, Any]]) -> dict[str, int]:
    total = 0
    done = 0
    for step in steps:
        if not isinstance(step, dict):
            continue
        total += 1
        if str(step.get("status") or "") in {"done", "completed", "ok", "skip", "skipped"}:
            done += 1
        elif str(step.get("status") or "") == "failed":
            done += 1
    if total <= 0:
        total = PLAN_TOTAL
    return {"done": done, "total": total}


def upsert_step(steps: list[dict[str, Any]], step: dict[str, Any]) -> list[dict[str, Any]]:
    """Replace by id or append; keep countable index/total when possible."""
    out = [dict(s) for s in steps if isinstance(s, dict)]
    sid = step.get("id")
    enriched = dict(step)
    if sid:
        for i, existing in enumerate(out):
            if existing.get("id") == sid:
                merged = {**existing, **enriched}
                if "index" not in enriched and existing.get("index") is not None:
                    merged["index"] = existing["index"]
                if "total" not in enriched and existing.get("total") is not None:
                    merged["total"] = existing["total"]
                out[i] = merged
                return out
    # Unknown agent/extra step: append with next index
    if "index" not in enriched:
        enriched["index"] = len(out) + 1
    if "total" not in enriched:
        enriched["total"] = max(PLAN_TOTAL, len(out) + 1)
        for row in out:
            row["total"] = enriched["total"]
    out.append(enriched)
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
