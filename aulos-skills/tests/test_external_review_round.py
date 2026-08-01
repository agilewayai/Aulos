"""SPEC-022Δ expert hard-flaw external review — not a source hunt."""

from __future__ import annotations

from pathlib import Path

from aulos_skills.external_review import (
    PERSPECTIVE,
    ROUNDS_SCHEMA,
    SCHEMA,
    build_external_review_report,
)
from aulos_skills.runtime import SkillRuntime

ROOT = Path(__file__).resolve().parents[1]


def test_external_review_flags_beethoven_portrait_on_mozart() -> None:
    context = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "raw_message": "Horowitz Plays Mozart K.488",
        "guide_html": "<html><h1>Piano Concerto No. 23 K. 488</h1></html>",
        "corpus_dossier": {
            "dossier_id": "family:duo-cello-piano",
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "composer_portrait": {
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Beethoven.jpg",
                "caption": "Beethoven — cello-and-piano room.",
                "credit": "Beethoven",
            },
        },
        "generation_rounds": {
            "draft_v1": {
                "guide_html": "<html><h1>Piano Concerto No. 23 K. 488</h1></html>",
                "summary": "x",
            }
        },
    }
    report = build_external_review_report(context)
    assert report["schema"] == SCHEMA
    assert report["perspective"] == PERSPECTIVE
    assert report["verdict"] in {"REVISE", "FAIL"}
    codes = {f["code"] for f in report["findings"]}
    assert "portrait_composer_mismatch" in codes or "foreign_family_dossier" in codes
    assert report["required_corrections"]
    assert report["sources_used"] == []


def test_expert_review_flags_cello_chamber_in_piano_concerto_html() -> None:
    html = """
    <html><h1>Piano Concerto No. 23 K. 488</h1>
    <p>Listen for the steel-string cello and piano duo in Op. 69 chamber rhetoric.</p>
    <section>聆听地图</section><section>作品解剖</section>
    </html>
    """
    report = build_external_review_report(
        {
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "guide_html": html,
            "corpus_dossier": {"form": "piano concerto", "composer": "Wolfgang Amadeus Mozart"},
            "generation_rounds": {"draft_v1": {"guide_html": html}},
        }
    )
    codes = {f["code"] for f in report["findings"]}
    assert "foreign_chamber_in_guide" in codes
    assert report["verdict"] in {"REVISE", "FAIL"}
    assert report["required_corrections"]
    evid = next(
        str(f.get("evidence") or "")
        for f in report["findings"]
        if f.get("code") == "foreign_chamber_in_guide"
    )
    assert "cello" in evid.lower() or "duo" in evid.lower()


def test_expert_review_does_not_hunt_web_sources() -> None:
    html = """
    <html><h1>Piano Concerto No. 23 K. 488</h1>
    <p>Mozart piano concerto listening guide with map.</p>
    <h2>Listening Map</h2><h2>Anatomy</h2>
    </html>
    """
    report = build_external_review_report(
        {
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "guide_html": html,
            "corpus_dossier": {"form": "piano concerto"},
            # Irrelevant / wrong web sources must NOT become findings
            "external_review_sources": [
                {"title": "Mozart and scatology", "url": "https://example.com/x", "snippet": "x"},
            ],
            "generation_rounds": {"draft_v1": {"guide_html": html}},
        }
    )
    codes = {f["code"] for f in report["findings"]}
    assert "web_catalog_weak" not in codes
    assert "web_composer_weak" not in codes
    assert "web_sources_thin" not in codes
    assert report["sources_used"] == []


def test_expert_llm_corrections_feed_report() -> None:
    html = "<html><h1>Piano Concerto No. 23 K. 488</h1><h2>Listening Map</h2><h2>Anatomy</h2></html>"

    def fake_llm(_prompt: str) -> str:
        return (
            '{"verdict":"REVISE","summary":"movement count wrong",'
            '"findings":[{"severity":"high","code":"movement_error","note":'
            '"K.488 is three movements; guide invents a fourth","evidence":"mvt","kind":"hard_flaw"}],'
            '"required_corrections":["Rewrite movement map to three movements only"]}'
        )

    report = build_external_review_report(
        {
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "guide_html": html,
            "corpus_dossier": {"form": "piano concerto"},
            "generation_rounds": {"draft_v1": {"guide_html": html}},
        },
        llm_complete=fake_llm,
    )
    assert report["layer"] == "expert_llm"
    codes = {f["code"] for f in report["findings"]}
    assert "movement_error" in codes or "expert_correction" in codes
    assert any("three movements" in c.lower() or "movement" in c.lower() for c in report["required_corrections"])
    assert report["verdict"] in {"REVISE", "FAIL"}


def test_chain_emits_generation_rounds_with_dual_drafts() -> None:
    rt = SkillRuntime(roots=[ROOT / "skills"])
    report = rt.run_listening_chain(
        message=(
            "Listening guide for Mozart Piano Concerto No. 23 in A major K. 488. "
            "Composers: Wolfgang Amadeus Mozart"
        ),
        work_hint="Mozart Piano Concerto No. 23 K. 488",
        context_seed={},
    )
    triggers = {s.id for s in report.steps}
    assert "external_review" in triggers
    assert "revise" in triggers
    rounds = (report.context or {}).get("generation_rounds") or {}
    assert rounds.get("schema") == ROUNDS_SCHEMA
    assert rounds.get("draft_v1", {}).get("guide_html")
    assert rounds.get("review_report")
    assert rounds.get("review_report", {}).get("perspective") == PERSPECTIVE
    assert rounds.get("draft_v2", {}).get("guide_html")
    assert rounds.get("comparison")
    assert "v1_hard_flaws" in rounds["comparison"]
    assert "v2_hard_flaws" in rounds["comparison"]
    assert isinstance(rounds.get("revision_history"), list)
    assert rounds["revision_history"]
    assert report.guide_html == rounds["draft_v2"]["guide_html"]


def test_revise_repairs_and_scorecards_diverge_on_hard_flaws() -> None:
    from aulos_skills.revise_repair import (
        apply_review_repairs,
        rescore_draft_v1_with_report,
        score_draft_with_hard_flaws,
    )

    polluted_html = """
    <html><h1>Piano Concerto No. 23 K. 488</h1>
    <p>Bernstein on Mozart — and a steel-string cello Op. 69 chamber duo.</p>
    </html>
    """
    clean_html = """
    <html><h1>Piano Concerto No. 23 K. 488</h1>
    <h2>Listening Map</h2><p>Opening motive in A major.</p>
    <h2>Anatomy</h2><p>Three-movement piano concerto form.</p>
    <section id='composer-en'>Mozart</section>
    </html>
    """
    context = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "raw_message": "Horowitz Plays Mozart K.488",
        "guide_html": polluted_html,
        "corpus_dossier": {
            "dossier_id": "family:duo-cello-piano",
            "form": "piano concerto",
            "listening_thesis": "Cello-and-piano Op. 69 room with steel-string cello.",
            "composer_portrait": {
                "image_url": "https://example.com/Beethoven.jpg",
                "caption": "Beethoven",
            },
            "depth_points": ["steel-string cello dialogue"],
        },
        "generation_rounds": {
            "draft_v1": {"guide_html": polluted_html, "summary": "v1"},
        },
    }
    report = build_external_review_report(context)
    assert report["verdict"] in {"REVISE", "FAIL"}
    rescore_draft_v1_with_report(context, report)
    v1_pct = context["generation_rounds"]["draft_v1"]["process_scorecard"]["rollup"]["pct"]
    v1_flaws = context["generation_rounds"]["draft_v1"]["process_scorecard"]["rollup"][
        "hard_flaws_remaining"
    ]
    assert v1_flaws >= 1

    repair = apply_review_repairs(context, report)
    assert repair["log"]
    assert context["corpus_dossier"].get("dossier_id") in {"", None}

    v2_card = score_draft_with_hard_flaws(html=clean_html, context=context, phase="revise")
    v2_pct = v2_card["rollup"]["pct"]
    v2_flaws = v2_card["rollup"]["hard_flaws_remaining"]
    assert v2_flaws < v1_flaws or v2_pct > v1_pct
