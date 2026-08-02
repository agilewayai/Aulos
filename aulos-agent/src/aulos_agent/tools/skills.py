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
    "listening.external_review",
    "listening.revise",
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
    _attach_review_llms(context)
    runtime = _runtime()
    step = runtime.run_trigger(trigger, context, disabled_skill_ids=disabled)
    versions = dict(context.get("skill_versions") or {})
    versions[step.skill_id] = step.skill_version
    context["skill_versions"] = versions
    steps = list(context.get("_agent_steps") or [])
    steps.append(_step_payload(step))
    review = runtime._review_milestone_step(trigger, context)
    if review is not None:
        steps.append(_step_payload(review))
        versions[review.skill_id] = review.skill_version
        context["skill_versions"] = versions
    context["_agent_steps"] = steps
    return json.dumps(
        {
            "step": _step_payload(step),
            "context": _jsonable_context(context),
            "review_step": _step_payload(review) if review is not None else None,
        },
        ensure_ascii=False,
    )


def _jsonable_context(context: dict[str, Any]) -> dict[str, Any]:
    """Drop callables so context survives tool JSON round-trips."""
    return {k: v for k, v in context.items() if not callable(v)}


def _ensure_aulos_api_path() -> None:
    """Allow agent process to import aulos_api from the monorepo sibling."""
    try:
        import aulos_api  # noqa: F401
        return
    except ImportError:
        pass
    sibling = Path(__file__).resolve().parents[4] / "aulos-api" / "src"
    if sibling.is_dir() and str(sibling) not in sys.path:
        sys.path.insert(0, str(sibling))


def _ops_llm_complete(system_prompt: str, *, role: str = "review"):
    """Sync completer via aulos-api ops LLM when agent provider is fake.

    role='review' → Ops review_provider (Grok by default; may be AI Code Mirror /
    Codex Responses). Must not silently fall back onto the draft author model.
    role='draft' → Ops draft_provider (DeepSeek by default) for revise repairs.

    Uses ``invoke_provider`` so chat Completions *and* Responses (Codex relay)
    wires both work when the operator switches Review → AI Code Mirror.
    """

    def complete(prompt: str) -> str | None:
        try:
            import asyncio

            _ensure_aulos_api_path()
            from aulos_api.db.session import SessionLocal, get_engine, init_db
            from aulos_api.services.llm_providers import invoke_provider, load_llm_config

            init_db()
            get_engine()
            assert SessionLocal is not None
            db = SessionLocal()
            try:
                cfg = load_llm_config(db)
                name = cfg.resolve_role_provider(role)
                if not name:
                    return None
                creds = cfg.provider_creds(name)
                if creds is None or not creds.complete:
                    return None

                # Codex Responses relays often need a longer budget than chat.
                timeout = 150.0 if (creds.wire_api or "").lower() == "responses" else 120.0

                async def _run() -> str:
                    return await invoke_provider(
                        provider=name,
                        creds=creds,
                        message=prompt,
                        system_prompt=system_prompt,
                        timeout=timeout,
                    )

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                if loop and loop.is_running():
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        return pool.submit(lambda: asyncio.run(_run())).result(
                            timeout=timeout + 30.0
                        )
                return asyncio.run(_run())
            finally:
                db.close()
        except Exception:  # noqa: BLE001
            return None

    return complete


def _attach_intent_critic(context: dict[str, Any]) -> None:
    """Re-attach LLM Critic completer each tool call (callables cannot travel in JSON)."""
    if context.get("review_llm_enabled") is False:
        return
    if callable(context.get("llm_critic_complete")):
        return
    system = (
        "You are Aulos Intent Critic. Review ONLY; never write a guide. "
        "Return ONLY JSON with verdict PASS|FAIL."
    )
    # Ops role routing: review_provider (Grok or AI Code Mirror) ≠ draft author.
    context["llm_critic_complete"] = _ops_llm_complete(system, role="review")


def _attach_external_review_expert(context: dict[str, Any]) -> None:
    """Music-guide + music-analysis expert completer for SPEC-022 hard-flaw review."""
    if context.get("review_llm_enabled") is False:
        return
    if callable(context.get("llm_external_review_complete")):
        return
    system = (
        "You are a senior music appreciation-guide expert and music-analysis "
        "expert for Aulos. Find hard flaws (硬伤) in the finished listening "
        "guide: wrong work/composer/portrait, foreign chambers, form/movement "
        "errors, missing listening map/anatomy, weak ear cues, factual mistakes. "
        "Do NOT hunt or score web sources. Be critical and specific. "
        "Review ONLY; never rewrite the full guide. Return ONLY JSON."
    )
    context["llm_external_review_complete"] = _ops_llm_complete(system, role="review")


def _attach_revise_proofreader(context: dict[str, Any]) -> None:
    """Proofread/repair completer that rewrites dossier fields from the review report."""
    if context.get("review_llm_enabled") is False:
        return
    if callable(context.get("llm_revise_complete")):
        return
    system = (
        "You are Aulos revise proofreader: a music-guide editor who repairs "
        "dossier fields to clear expert hard-flaw findings. Return ONLY JSON "
        "patches (thesis, points, listening_map, caveats). Do not emit full HTML."
    )
    # Author-side repair uses the draft provider, not the review critic.
    context["llm_revise_complete"] = _ops_llm_complete(system, role="draft")


def _attach_review_llms(context: dict[str, Any]) -> None:
    _attach_intent_critic(context)
    _attach_external_review_expert(context)
    _attach_revise_proofreader(context)


@tool
def finalize_listening_guide(context_json: str) -> str:
    """Build the final listening report fields from accumulated context after compose+eval."""
    context = _parse_context(context_json)
    # Ensure guide exists if compose was skipped — run compose trigger via public API
    if not context.get("guide_html") and context.get("work_title"):
        _attach_review_llms(context)
        runtime = _runtime()
        step = runtime.run_trigger("listening.compose", context)
        versions = dict(context.get("skill_versions") or {})
        versions[step.skill_id] = step.skill_version
        context["skill_versions"] = versions
        steps = list(context.get("_agent_steps") or [])
        steps.append(_step_payload(step))
        review = runtime._review_milestone_step("listening.compose", context)
        if review is not None:
            steps.append(_step_payload(review))
        context["_agent_steps"] = steps
    eval_pass = bool(context.get("pass", True))
    eval_score = int(context.get("eval_score") or 0)
    steps = list(context.get("_agent_steps") or [])
    if not any(s.get("id") == "eval" and s.get("status") == "completed" for s in steps):
        eval_pass = bool(context.get("guide_html"))
        eval_score = eval_score or (8 if eval_pass else 0)
    if context.get("review_failed"):
        eval_pass = False
        eval_score = min(eval_score, 7)
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
        "context": {
            k: v
            for k, v in _jsonable_context(context).items()
            if k != "_agent_steps"
        },
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
