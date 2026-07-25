"""Built-in MCP tool implementations (pure, offline-safe)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def echo_message(message: str) -> str:
    return f"echo: {message}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def aulos_status() -> dict[str, str]:
    return {
        "project": "aulos-mcp",
        "role": "agents integration via Model Context Protocol",
        "status": "ready",
    }


def _skills_runtime():
    try:
        from aulos_skills.runtime import SkillRuntime
    except ImportError:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        # builtin.py -> tools -> aulos_mcp -> src -> aulos-mcp -> aulos
        if sibling.is_dir():
            sys.path.insert(0, str(sibling))
        from aulos_skills.runtime import SkillRuntime
    return SkillRuntime()


def skills_list(layer: str | None = None) -> list[dict[str, Any]]:
    runtime = _skills_runtime()
    return runtime.list_skills(layer=layer or None)


def skills_run(trigger: str, message: str = "", work_hint: str = "") -> dict[str, Any]:
    runtime = _skills_runtime()
    if trigger == "listening.chain" or trigger == "listening.route":
        report = runtime.run_listening_chain(message=message or "listening guide", work_hint=work_hint or None)
        from aulos_skills.runtime import run_report_to_dict

        return run_report_to_dict(report)
    context: dict[str, Any] = {"raw_message": message, "work_hint": work_hint}
    result = runtime.run_trigger(trigger, context)
    return {
        "step": result.to_workflow_dict(),
        "outputs": result.outputs,
        "context_keys": sorted(context.keys()),
    }
