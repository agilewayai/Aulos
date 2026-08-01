"""Guide #48 class — identity hygiene + H1 title drift + scorecard self-improvement."""

from __future__ import annotations

import re

from aulos_skills.guide_render import render_bilingual_guide_html
from aulos_skills.identity_hygiene import (
    apply_identity_hygiene,
    html_title_matches_work,
    inspect_dossier_hygiene,
    portrait_betrays_composer,
)
from aulos_skills.process_scorecard import record_node_scorecard, score_node
from aulos_skills.decontam import validate_node_outputs


def test_portrait_betrays_when_beethoven_url_on_mozart() -> None:
    portrait = {
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Beethoven.jpg",
        "credit": "Portrait associated with Beethoven",
        "caption": "Beethoven — the face most listeners carry into the cello-and-piano room.",
    }
    assert portrait_betrays_composer(portrait, "Wolfgang Amadeus Mozart") is True
    assert portrait_betrays_composer(portrait, "Ludwig van Beethoven") is False


def test_foreign_family_dossier_id_on_piano_concerto() -> None:
    dossier = {
        "dossier_id": "family:duo-cello-piano",
        "work_title": "Concerto For Piano And Orchestra No. 23 In A Major, K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "composer_portrait": {
            "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Beethoven.jpg",
            "caption": "Beethoven — cello-and-piano room.",
            "credit": "Beethoven",
        },
        "depth_points": [
            "Lock ear on opening rhetoric — who states the motto, cello or piano?",
            "Emancipates the cello as a sonata equal — especially Op. 69.",
        ],
    }
    report = inspect_dossier_hygiene(
        dossier,
        composer="Wolfgang Amadeus Mozart",
        work_title=str(dossier["work_title"]),
    )
    codes = {f.code for f in report.findings}
    assert "portrait_composer_mismatch" in codes
    assert "foreign_family_dossier" in codes
    cleaned, _ = apply_identity_hygiene(
        dossier,
        composer="Wolfgang Amadeus Mozart",
        work_title=str(dossier["work_title"]),
    )
    assert cleaned.get("composer_portrait") == {}
    assert not str(cleaned.get("dossier_id") or "").startswith("family:")


def test_h1_not_stolen_by_appreciation_video_title() -> None:
    """Regression guide #48: video loop reused `title` and overwrote H1 with Bernstein."""
    dossier = {
        "work_title": "Concerto For Piano And Orchestra No. 23 In A Major, K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "listening_thesis": "Intimate conversation between soloist and orchestra.",
        "appreciation_videos": [
            {
                "title": "Inside the Score: Mozart K. 488",
                "url": "https://www.youtube.com/results?search_query=Mozart+K488",
                "why": "score walkthrough",
            },
            {
                "title": "Bernstein on Mozart’s Piano Concertos",
                "url": "https://www.youtube.com/results?search_query=Bernstein+Mozart",
                "why": "televised commentary",
            },
        ],
        "zh": {
            "work_title": "A大调第23钢琴协奏曲，K. 488",
            "composer": "莫扎特",
            "listening_thesis": "独奏与乐队的亲密对话。",
            "appreciation_videos": [
                {
                    "title": "伯恩斯坦谈莫扎特钢琴协奏曲",
                    "url": "https://www.youtube.com/results?search_query=Bernstein+Mozart",
                    "why": "电视解说",
                }
            ],
        },
    }
    html = render_bilingual_guide_html(
        dossier=dossier,
        work_title=str(dossier["work_title"]),
        composer="Wolfgang Amadeus Mozart",
    )
    h1s = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h)).strip() for h in re.findall(r"<h1>(.*?)</h1>", html)]
    assert h1s
    for h in h1s:
        assert "Bernstein" not in h
        assert "伯恩斯坦" not in h
    assert "Bernstein on Mozart" in html  # still in media section
    assert html_title_matches_work(html, str(dossier["work_title"]))


def test_decontam_flags_kb_family_dossier_without_family_source() -> None:
    context = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "raw_message": "Horowitz Plays Mozart K.488",
        "conflict_markers": [],
    }
    outputs = {
        "synthesize_source": "kb-rag+corpus+llm",  # no family: token — guide #48 shape
        "corpus_dossier": {
            "dossier_id": "family:duo-cello-piano",
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "composer_portrait": {
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Beethoven.jpg",
                "caption": "Beethoven — cello-and-piano room.",
                "credit": "Beethoven",
            },
            "depth_points": ["cello or piano?", "Op. 69 lyric architecture"],
        },
    }
    report = validate_node_outputs("listening.synthesize", context, outputs)
    assert report.ok is False
    assert report.foreign_family == "duo-cello-piano" or any(
        "duo-cello" in f.marker for f in report.findings
    )
    assert any("portrait" in f.marker or f.where == "composer_portrait" for f in report.findings)


def test_scorecard_hard_fail_feeds_critique_corrections() -> None:
    context: dict = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "composer": "Wolfgang Amadeus Mozart",
        "intent_lock": {
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "catalog_numbers": ["k488"],
        },
        "corpus_dossier": {
            "dossier_id": "family:duo-cello-piano",
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "composer_portrait": {
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Beethoven.jpg",
                "caption": "Beethoven — cello room.",
                "credit": "Beethoven",
            },
            "myths_and_caveats": ["verify anecdotes"],
            "listening_thesis": "operatic depth",
        },
    }
    card = record_node_scorecard(
        context,
        "listening.synthesize",
        {"corpus_dossier": context["corpus_dossier"]},
    )
    assert card is not None
    assert card.hard_fail is True
    assert context.get("critique_corrections")
    assert any("portrait" in c or "family" in c for c in context["critique_corrections"])
    # Direct score_node also hard-fails identity
    scored = score_node(
        "listening.synthesize",
        context,
        {"corpus_dossier": context["corpus_dossier"]},
    )
    assert scored is not None
    assert scored.scores.get("identity", 3) <= 1
