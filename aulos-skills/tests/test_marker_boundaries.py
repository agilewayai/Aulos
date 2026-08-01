"""Alien marker matching — digit tokens must not fire inside years (SPEC-025)."""

from __future__ import annotations

from aulos_skills.decontam import _blob_hits, marker_in_text
from aulos_skills.process_scorecard import _score_source_hygiene


def test_bare_988_does_not_match_year_1988() -> None:
    html = "<h3>Daniel Barenboim · 1988</h3><p>Deutsche Grammophon complete Songs Without Words</p>"
    assert marker_in_text("988", html) is False
    assert marker_in_text("1988", html) is True
    assert marker_in_text("goldberg", html) is False
    assert marker_in_text("bwv 988", "see BWV 988 variations") is True
    assert marker_in_text("988", "BWV 988 — Goldberg") is True


def test_blob_hits_skips_year_substring() -> None:
    hits = _blob_hits(
        "Barenboim 1988 DG Songs Without Words",
        ["988", "goldberg", "bwv 988", "songs without words"],
    )
    assert "988" not in hits
    assert "songs without words" in hits


def test_process_hygiene_ignores_1988_vs_988() -> None:
    score, findings = _score_source_hygiene(
        {
            "conflict_markers": ["988", "goldberg", "bwv 988"],
            "corpus_dossier": {
                "listening_thesis": "Lyric rooms of Songs Without Words.",
                "myths_and_caveats": ["Nicknames are editorial."],
            },
        },
        {"guide_html": "<h3>Daniel Barenboim · 1988</h3>"},
    )
    assert score >= 2
    assert not any(f.code == "hygiene_alien" for f in findings)
