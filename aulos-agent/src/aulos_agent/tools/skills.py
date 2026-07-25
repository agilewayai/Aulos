"""Agent tools that load/run Aulos domain skills (tool adapters over SkillRuntime)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

LISTENING_PLAYBOOK_TRIGGERS: tuple[str, ...] = (
    "listening.route",
    "listening.intake",
    "listening.corpus",
    "listening.synthesize",
    "listening.width",
    "listening.depth",
    "listening.compose",
    "listening.eval",
)


def _runtime():
    try:
        from aulos_skills.runtime import SkillRuntime
    except ImportError:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.runtime import SkillRuntime
    return SkillRuntime()


def _parse_context(context_json: str) -> dict[str, Any]:
    if not context_json or not str(context_json).strip():
        return {}
    data = json.loads(context_json)
    if not isinstance(data, dict):
        raise ValueError("context_json must be a JSON object")
    return data


def _step_payload(step: Any) -> dict[str, Any]:
    return {
        "id": step.id,
        "title": step.title,
        "status": step.status,
        "thinking": step.thinking,
        "detail": step.detail,
        "skill_id": step.skill_id,
        "skill_version": step.skill_version,
        "started_at": step.started_at,
        "finished_at": step.finished_at,
    }


@tool
def list_aulos_skills(layer: str = "domain-runtime") -> str:
    """List Aulos skill packs. Default layer=domain-runtime for listening 导赏."""
    rows = _runtime().list_skills(layer=layer or None)
    return json.dumps(rows, ensure_ascii=False, indent=2)


@tool
def run_listening_skill(trigger: str, context_json: str) -> str:
    """Run one listening skill by trigger (e.g. listening.intake). Returns step + updated context JSON.

    Pass the full accumulated context_json from the previous tool result. Product agents
    should call this once per playbook trigger — never skip the harness skill packs.
    """
    context = _parse_context(context_json)
    disabled = set(str(x) for x in (context.get("disabled_skill_ids") or []))
    runtime = _runtime()
    step = runtime.run_trigger(trigger, context, disabled_skill_ids=disabled)
    versions = dict(context.get("skill_versions") or {})
    versions[step.skill_id] = step.skill_version
    context["skill_versions"] = versions
    steps = list(context.get("_agent_steps") or [])
    steps.append(_step_payload(step))
    context["_agent_steps"] = steps
    return json.dumps(
        {"step": _step_payload(step), "context": context},
        ensure_ascii=False,
    )


@tool
def finalize_listening_guide(context_json: str) -> str:
    """Build the final listening report fields from accumulated context after compose+eval."""
    context = _parse_context(context_json)
    # Ensure guide exists if compose was skipped — run compose trigger via public API
    if not context.get("guide_html") and context.get("work_title"):
        runtime = _runtime()
        step = runtime.run_trigger("listening.compose", context)
        versions = dict(context.get("skill_versions") or {})
        versions[step.skill_id] = step.skill_version
        context["skill_versions"] = versions
        steps = list(context.get("_agent_steps") or [])
        steps.append(_step_payload(step))
        context["_agent_steps"] = steps
    eval_pass = bool(context.get("pass", True))
    eval_score = int(context.get("eval_score") or 0)
    steps = list(context.get("_agent_steps") or [])
    if not any(s.get("id") == "eval" and s.get("status") == "completed" for s in steps):
        eval_pass = bool(context.get("guide_html"))
        eval_score = eval_score or (8 if eval_pass else 0)
    report = {
        "steps": steps,
        "guide_html": str(context.get("guide_html") or ""),
        "summary": str(context.get("summary") or ""),
        "work_title": str(context.get("work_title") or ""),
        "composer": str(
            context.get("composer") or context.get("composer_guess") or ""
        ),
        "eval_pass": eval_pass,
        "eval_score": eval_score,
        "skill_versions": dict(context.get("skill_versions") or {}),
        "context": {k: v for k, v in context.items() if k != "_agent_steps"},
        "source": "agent-skills",
    }
    return json.dumps(report, ensure_ascii=False)


def run_listening_skill_chain_for_tests(message: str) -> str:
    """Test helper only — one-shot chain. Not registered for product agent tooling."""
    from aulos_skills.runtime import run_report_to_dict

    report = _runtime().run_listening_chain(message=message)
    payload = run_report_to_dict(report)
    payload.pop("guide_html", None)
    payload["guide_html_chars"] = len(report.guide_html or "")
    return json.dumps(payload, ensure_ascii=False, indent=2)
