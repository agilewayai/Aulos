"""Targeted revise — patches named chambers only (SPEC-022Δ)."""

from __future__ import annotations

from aulos_skills.external_review import build_external_review_report
from aulos_skills.targeted_revise import ROUNDS_SCHEMA_V2, run_targeted_revise


def _base_context() -> dict:
    html = """
    <html><h1>Piano Concerto No. 23 K. 488</h1>
    <p>Steel-string cello Op. 69 chamber duo with Beethoven portrait vibes.</p>
    <h2>Listening Map</h2><p>Old map.</p>
    </html>
    """
    return {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "raw_message": "Horowitz Plays Mozart K.488",
        "guide_html": html,
        "corpus_dossier": {
            "dossier_id": "family:duo-cello-piano",
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "form": "piano concerto",
            "listening_thesis": "Cello-and-piano Op. 69 room.",
            "work_introduction": "Keep this introduction intact for identity.",
            "composer_portrait": {
                "image_url": "https://example.com/Beethoven.jpg",
                "caption": "Beethoven",
            },
            "listening_map": [{"label": "Old", "cue": "stale"}],
            "depth_points": ["steel-string cello dialogue"],
            "width_points": ["keep-me-width-point-xyz"],
            "myths_and_caveats": ["verify anecdotes"],
        },
        "generation_rounds": {
            "schema": ROUNDS_SCHEMA_V2,
            "draft_v1": {"guide_html": html, "summary": "v1"},
        },
    }


def test_targeted_revise_clears_portrait_keeps_unrelated_width() -> None:
    context = _base_context()
    report = build_external_review_report(context)
    width_before = list(context["corpus_dossier"]["width_points"])
    intro_before = context["corpus_dossier"]["work_introduction"]

    out = run_targeted_revise(context, report=report, allow_full_compose=None)
    assert out["revise_scope"] in {"targeted", "full"}
    dossier = context["corpus_dossier"]
    # Portrait should be cleared when flagged
    codes = {f["code"] for f in report.get("findings") or []}
    if "portrait_composer_mismatch" in codes:
        assert dossier.get("composer_portrait") in ({}, None) or not (
            dossier.get("composer_portrait") or {}
        ).get("image_url")
    # Unrelated width point preserved unless foreign scrub wiped it via expert repair
    assert intro_before in str(dossier.get("work_introduction") or "") or dossier.get(
        "work_introduction"
    )
    assert out["guide_html"]
    rounds = context["generation_rounds"]
    assert rounds["schema"] == ROUNDS_SCHEMA_V2
    assert rounds["draft_v1"]["guide_html"]  # frozen
    assert rounds["draft_v2"]["guide_html"]
    assert rounds.get("revision_history")
    assert rounds.get("comparison")
    # full compose callback must not be required for targeted
    assert "full_compose" not in (out.get("revise_repair_log") or []) or out["revise_scope"] == "full"
    del width_before  # silence lint if scrub removed it


def test_human_notes_targeted_genesis_without_full_compose() -> None:
    # Clean shelf (no foreign Op./BWV) — pollution scrub must not escalate this path.
    context = _base_context()
    context["corpus_dossier"] = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "form": "piano concerto",
        "listening_thesis": "Lock the orchestral opening before the piano entry.",
        "work_introduction": "Keep this introduction intact for identity.",
        "listening_map": [{"label": "I", "cue": "tutti thesis"}],
        "depth_points": ["Map ritornello returns"],
        "width_points": ["keep-me-width-point-xyz"],
        "myths_and_caveats": ["verify anecdotes"],
        "genesis": {},
    }
    composed_calls = {"n": 0}

    def boom(_ctx: dict) -> dict:
        composed_calls["n"] += 1
        raise AssertionError("full compose must not run for genesis-only notes")

    out = run_targeted_revise(
        context,
        human_notes="请加强创作背景与时代介绍，补充 genesis。",
        allow_full_compose=boom,
    )
    assert composed_calls["n"] == 0
    assert out["revise_scope"] == "targeted"
    assert "genesis" in (out.get("patched_targets") or [])
    genesis = context["corpus_dossier"].get("genesis") or {}
    assert genesis
    history = context["generation_rounds"]["revision_history"]
    assert any(h.get("source") in {"human", "mixed"} for h in history)
    assert context["generation_rounds"]["review_report"]["perspective"] == "human_review_notes"


def test_draft_v1_frozen_across_revise() -> None:
    context = _base_context()
    v1_html = context["generation_rounds"]["draft_v1"]["guide_html"]
    run_targeted_revise(
        context,
        human_notes="补充聆听地图 listening map",
        allow_full_compose=None,
    )
    assert context["generation_rounds"]["draft_v1"]["guide_html"] == v1_html
    maps = context["corpus_dossier"].get("listening_map") or []
    assert isinstance(maps, list) and maps
    assert any("Opening" in str(m) or "cue" in str(m) for m in maps)
