"""Agent tools that load/run Aulos domain skills."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from langchain_core.tools import tool


def _runtime():
    try:
        from aulos_skills.runtime import SkillRuntime
    except ImportError:
        sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
        if sibling.is_dir() and str(sibling) not in sys.path:
            sys.path.insert(0, str(sibling))
        from aulos_skills.runtime import SkillRuntime
    return SkillRuntime()


@tool
def list_aulos_skills(layer: str = "domain-runtime") -> str:
    """List Aulos skill packs. Default layer=domain-runtime for listening 导赏."""
    rows = _runtime().list_skills(layer=layer or None)
    return json.dumps(rows, ensure_ascii=False, indent=2)


@tool
def run_listening_skill_chain(message: str) -> str:
    """Run the full classical listening-guide skill chain for a listener message."""
    from aulos_skills.runtime import run_report_to_dict

    report = _runtime().run_listening_chain(message=message)
    payload = run_report_to_dict(report)
    payload.pop("guide_html", None)
    payload["guide_html_chars"] = len(report.guide_html or "")
    return json.dumps(payload, ensure_ascii=False, indent=2)
