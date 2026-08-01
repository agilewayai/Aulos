"""External review must not trust empty-body hallucinations when dossier is rich."""

from __future__ import annotations

from aulos_skills.external_review import build_external_review_report
from aulos_skills.revise_repair import scan_hard_flaws


def test_process_lock_is_hard_flaw() -> None:
    findings = scan_hard_flaws(
        html="<h1>CRITIQUE LOCK: richness_empty — Songs</h1><p>body</p>",
        context={
            "work_title": "Lieder ohne Worte (Songs Without Words)",
            "composer": "Felix Mendelssohn",
            "corpus_dossier": {
                "listening_thesis": "CRITIQUE LOCK: x — Hear the song.",
                "form": "Lyric piano miniatures",
            },
        },
    )
    codes = {f.get("code") for f in findings}
    assert "process_lock_in_product_prose" in codes


def test_packaging_title_is_hard_flaw() -> None:
    findings = scan_hard_flaws(
        html="<h1>Work</h1><div data-section=\"map\">Listening Map</div><div>anatomy</div>",
        context={
            "work_title": "Bartholdy Lieder = Songs / Romances / Ges",
            "composer": "Felix Mendelssohn",
            "corpus_dossier": {"listening_thesis": "Hear the line.", "form": "Lyric"},
        },
    )
    codes = {f.get("code") for f in findings}
    assert "packaging_title_pollution" in codes


def test_llm_empty_body_claim_dropped_when_dossier_rich() -> None:
    def fake_llm(_prompt: str) -> str:
        return (
            '{"verdict":"FAIL","summary":"empty",'
            '"findings":[{"severity":"high","code":"MISSING_GUIDE_CONTENT",'
            '"note":"Only ambient, no text","evidence":"html","kind":"hard_flaw"}],'
            '"required_corrections":["补齐正文，现在只有 ambient"]}'
        )

    report = build_external_review_report(
        {
            "work_title": "Lieder ohne Worte (Songs Without Words)",
            "composer": "Felix Mendelssohn",
            "guide_html": (
                "<aside class=\"ambient\">x</aside>"
                "<h1>Lieder ohne Worte</h1>"
                "<section data-section=\"map\">Listening Map</section>"
                "<p>anatomy landmarks here with enough body text for review.</p>"
            ),
            "corpus_dossier": {
                "listening_thesis": "Hear the singing line over a keyboard gait.",
                "work_introduction": "Lyric piano miniatures turn song speech into rooms.",
                "form": "Lyric piano miniatures (Songs Without Words)",
                "width_points": ["Hold the gait.", "Compare two rooms."],
                "listening_map": [
                    {"label": "Opening", "cue": "Lock the song."},
                    {"label": "Middle", "cue": "Tint."},
                ],
            },
        },
        llm_complete=fake_llm,
    )
    codes = {f.get("code") for f in report.get("findings") or []}
    assert "MISSING_GUIDE_CONTENT" not in codes
    assert "missing_guide_content" not in {str(c).lower() for c in codes}
    notes = " ".join(str(f.get("note") or "") for f in report.get("findings") or [])
    assert "only ambient" not in notes.lower()
