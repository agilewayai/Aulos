"""Prompt templates for the agent graph."""

from __future__ import annotations

from pathlib import Path

from langchain_core.messages import SystemMessage

from aulos_agent.config.settings import Settings, get_settings
from aulos_agent.tools.skills import LISTENING_PLAYBOOK_TRIGGERS


def build_system_message(settings: Settings | None = None) -> SystemMessage:
    cfg = settings or get_settings()
    return SystemMessage(content=cfg.system_prompt)


def _listening_skill_body() -> str:
    try:
        from aulos_agent.tools.skills import _runtime

        rt = _runtime()
        skill = rt.skills.get("aulos-listening")
        if skill is None:
            return ""
        from aulos_skills.registry import skill_body

        return skill_body(skill)[:4000]
    except Exception:  # noqa: BLE001
        # Fallback: sibling path read
        root = Path(__file__).resolve().parents[4] / "aulos-skills" / "skills" / "aulos-listening" / "SKILL.md"
        if root.is_file():
            return root.read_text(encoding="utf-8")[:4000]
        return ""


def build_listening_system_message(settings: Settings | None = None) -> SystemMessage:
    """System prompt that forces skill-tool playbook for 导赏 jobs."""
    cfg = settings or get_settings()
    triggers = ", ".join(LISTENING_PLAYBOOK_TRIGGERS)
    body = _listening_skill_body()
    content = f"""{cfg.system_prompt}

You are executing a classical listening-guide (导赏) job for Aulos.
The product core is Agent + Skill Harness + tools. You MUST complete the job by calling tools — never invent the guide HTML yourself.

Playbook (call `run_listening_skill` once per trigger, in order, passing the latest context_json):
{triggers}

After all triggers complete, call `finalize_listening_guide` with the accumulated context_json.

Harness guidance (from aulos-listening skill):
{body}
"""
    return SystemMessage(content=content)
