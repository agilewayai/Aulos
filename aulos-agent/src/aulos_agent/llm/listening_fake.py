"""Offline fake chat model that plays the listening skill tool playbook."""

from __future__ import annotations

import json
import uuid
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from aulos_agent.tools.skills import LISTENING_PLAYBOOK_TRIGGERS


def _latest_context(messages: list[BaseMessage]) -> dict[str, Any]:
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            try:
                payload = json.loads(str(msg.content))
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and isinstance(payload.get("context"), dict):
                return dict(payload["context"])
            if isinstance(payload, dict) and payload.get("guide_html") is not None:
                # finalize result — treat as done context carrier
                return dict(payload.get("context") or payload)
        if isinstance(msg, HumanMessage):
            text = str(msg.content)
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "message" in data:
                    return {
                        "raw_message": data.get("message") or "",
                        "work_hint": data.get("work_hint") or "",
                        "llm_enrichment": data.get("llm_enrichment") or "",
                        "llm_dossier": dict(data.get("llm_dossier") or {}),
                        "kb_dossier": dict(data.get("kb_dossier") or {}),
                        "rag_hits": list(data.get("rag_hits") or []),
                        "rag_mode": data.get("rag_mode") or "",
                        "disabled_skill_ids": list(data.get("disabled_skill_ids") or []),
                        "review_llm_enabled": data.get("review_llm_enabled", True),
                        "ambient_fallback_mode": data.get("ambient_fallback_mode") or "embed",
                        "external_review_sources": list(data.get("external_review_sources") or []),
                        "skill_versions": {},
                        "_agent_steps": [],
                    }
            except json.JSONDecodeError:
                return {
                    "raw_message": text,
                    "work_hint": "",
                    "llm_enrichment": "",
                    "llm_dossier": {},
                    "kb_dossier": {},
                    "rag_hits": [],
                    "rag_mode": "",
                    "disabled_skill_ids": [],
                    "skill_versions": {},
                    "_agent_steps": [],
                }
    return {
        "raw_message": "",
        "work_hint": "",
        "skill_versions": {},
        "_agent_steps": [],
    }


def _completed_triggers(messages: list[BaseMessage]) -> set[str]:
    done: set[str] = set()
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        try:
            payload = json.loads(str(msg.content))
        except json.JSONDecodeError:
            continue
        step = payload.get("step") if isinstance(payload, dict) else None
        if isinstance(step, dict) and step.get("id"):
            # map step id back to trigger prefix
            sid = str(step["id"])
            done.add(f"listening.{sid}")
    return done


class ListeningPlaybookFakeModel(BaseChatModel):
    """Emit tool_calls for each listening playbook trigger, then finalize."""

    _bound: bool = PrivateAttr(default=False)

    @property
    def _llm_type(self) -> str:
        return "listening-playbook-fake"

    def bind_tools(self, tools: Any, **kwargs: Any) -> ListeningPlaybookFakeModel:
        self._bound = True
        return self

    def _generate(
        self,
        messages: list[Any],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        done = _completed_triggers(messages)
        context = _latest_context(messages)
        context_json = json.dumps(context, ensure_ascii=False)

        for trigger in LISTENING_PLAYBOOK_TRIGGERS:
            if trigger not in done:
                call_id = f"call_{uuid.uuid4().hex[:12]}"
                message = AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "run_listening_skill",
                            "args": {
                                "trigger": trigger,
                                "context_json": context_json,
                            },
                            "id": call_id,
                            "type": "tool_call",
                        }
                    ],
                )
                return ChatResult(generations=[ChatGeneration(message=message)])

        # All triggers done — finalize if not already
        finalized = any(
            isinstance(m, ToolMessage)
            and "guide_html" in str(m.content)
            and '"eval_pass"' in str(m.content)
            for m in messages
        )
        if not finalized:
            call_id = f"call_{uuid.uuid4().hex[:12]}"
            message = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "finalize_listening_guide",
                        "args": {"context_json": context_json},
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            )
            return ChatResult(generations=[ChatGeneration(message=message)])

        message = AIMessage(content="Listening guide complete via skill harness.")
        return ChatResult(generations=[ChatGeneration(message=message)])
