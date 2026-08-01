"""SPEC-018 adversarial process review — IntentLock + hybrid Critic."""

from __future__ import annotations

import json
from pathlib import Path

from aulos_skills.adversarial_review import (
    apply_critique_to_context,
    deterministic_review,
    freeze_intent_lock_dict,
    intent_critic_review,
)
from aulos_skills.runtime import SkillRuntime


ROOT = Path(__file__).resolve().parents[1]


def _runtime() -> SkillRuntime:
    return SkillRuntime(roots=[ROOT / "skills"])


def test_freeze_intent_lock_for_concerto() -> None:
    lock = freeze_intent_lock_dict(
        work_title="Piano Concerto No. 23 K. 488",
        composer="Wolfgang Amadeus Mozart",
        work_hint="Mozart K.488",
        raw_message="Horowitz Plays Mozart Piano Concerto K.488",
        source="discogs",
    )
    assert lock["work_title"]
    assert "488" in " ".join(lock["catalog_numbers"]) or lock["catalog_numbers"]
    assert lock["alien_markers"]
    assert any("requiem" in m or "安魂" in m or "末日" in m for m in lock["alien_markers"])


def test_intake_freezes_intent_lock_into_context() -> None:
    rt = _runtime()
    report = rt.run_listening_chain(
        message=(
            "Write a listening guide for Mozart Piano Concerto No. 23 K. 488. "
            "Composers: Wolfgang Amadeus Mozart"
        ),
        work_hint="Mozart — Piano Concerto No. 23 K. 488",
    )
    lock = (report.context or {}).get("intent_lock") or {}
    assert lock.get("work_title")
    assert "Mozart" in (lock.get("composer") or report.composer or "")
    assert report.context.get("review_events") is not None
    review_ids = [s.id for s in report.steps if str(s.id).startswith("review-")]
    assert "review-synthesize" in review_ids
    assert "review-compose" in review_ids


def test_deterministic_review_fails_requiem_vs_concerto_lock() -> None:
    lock = freeze_intent_lock_dict(
        work_title="Piano Concerto No. 23 K. 488",
        composer="Wolfgang Amadeus Mozart",
        work_hint="K.488 concerto",
        raw_message="Mozart piano concerto K.488",
        source="catalog",
    )
    context = {
        "intent_lock": lock,
        "work_title": lock["work_title"],
        "work_hint": "K.488 concerto",
        "raw_message": "Mozart piano concerto K.488",
        "conflict_markers": list(lock["conflict_markers"]),
    }
    polluted = {
        "corpus_dossier": {
            "work_title": lock["work_title"],
            "listening_thesis": "Dies irae and Requiem as piano confession",
            "form": "Requiem mass",
            "work_introduction": "安魂曲 · 末日经",
        }
    }
    report = deterministic_review("listening.synthesize", context, polluted)
    assert not report.ok
    assert any(d.code == "intent_betrayal" or d.code.startswith("decontam") for d in report.deviations)


def test_llm_critic_fail_injects_critique_and_rework() -> None:
    lock = freeze_intent_lock_dict(
        work_title="Violin Concerto in D major Op. 77",
        composer="Johannes Brahms",
        work_hint="Brahms violin concerto",
        raw_message="Brahms Violin Concerto Op.77",
        source="diary",
    )
    context = {
        "intent_lock": lock,
        "work_title": lock["work_title"],
        "composer": lock["composer"],
        "work_hint": "Brahms violin concerto",
        "raw_message": "Brahms Violin Concerto Op.77",
        "conflict_markers": list(lock["conflict_markers"]),
        "review_llm_enabled": True,
    }

    def fake_llm(_prompt: str) -> str:
        return json.dumps(
            {
                "verdict": "FAIL",
                "deviations": [
                    {
                        "code": "form_swap",
                        "summary": "Narrative drifted into German Requiem / Ein deutsches Requiem",
                    }
                ],
                "required_corrections": [
                    "Narrative must stay on Violin Concerto Op.77",
                    "Forbid Requiem as work body",
                ],
                "preserved_lock_check": "catalog Op.77 missing in thesis",
            }
        )

    outputs = {
        "corpus_dossier": {
            "work_title": lock["work_title"],
            "listening_thesis": "A serene Ein deutsches Requiem meditation",
            "form": "Sacred choral requiem",
        }
    }
    critic = intent_critic_review(
        "listening.synthesize", context, outputs, llm_complete=fake_llm
    )
    assert not critic.ok
    assert critic.layer == "llm_critic"
    apply_critique_to_context(context, critic)
    assert context.get("critique_corrections")
    assert any("Op.77" in c or "Concerto" in c for c in context["critique_corrections"])


def test_clean_k488_path_does_not_false_fail_review() -> None:
    rt = _runtime()
    report = rt.run_listening_chain(
        message=(
            "Listening guide for Mozart Piano Concerto No. 23 in A major K. 488. "
            "Composers: Wolfgang Amadeus Mozart"
        ),
        work_hint="Mozart Piano Concerto No. 23 K. 488",
        context_seed={"review_llm_enabled": True},
    )
    assert not report.context.get("review_failed")
    events = list(report.context.get("review_events") or [])
    synth = [e for e in events if e.get("trigger") == "listening.synthesize"]
    assert synth
    assert synth[-1].get("ok") is True or synth[-1].get("repaired") is True
    html = report.guide_html or ""
    assert "Requiem" not in html
    assert "安魂" not in html


def test_runtime_gate_records_review_events_on_pollution() -> None:
    rt = _runtime()
    polluted_llm = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "listening_thesis": "Horowitz plays Mozart Requiem Dies irae 末日经 as the work itself",
        "form": "Requiem",
        "work_introduction": "安魂曲",
        "zh_hans": {"listening_thesis": "安魂曲末日经"},
    }
    report = rt.run_listening_chain(
        message=(
            "Write a guide for Mozart Piano Concerto No. 23 K. 488. "
            "Composers: Wolfgang Amadeus Mozart"
        ),
        work_hint="Mozart — Piano Concerto No. 23 K. 488",
        llm_dossier=polluted_llm,
        context_seed={"review_llm_enabled": True},
    )
    events = list(report.context.get("review_events") or [])
    assert events
    html = report.guide_html or ""
    for banned in ("Requiem", "安魂曲", "末日经", "Dies irae"):
        assert banned not in html, f"still polluted: {banned}"
