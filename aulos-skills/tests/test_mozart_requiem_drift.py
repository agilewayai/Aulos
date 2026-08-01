"""Regression: Horowitz/Mozart Discogs release must not drift into Requiem/Dies irae.

Guide #47 root cause: diary message lacked Catalog work lock + empty composer card;
LLM free-associated Horowitz+Mozart → Requiem piano transcription (末日经),
while the pressing is Piano Concerto K.488 + Sonata K.333.
"""

from __future__ import annotations

import json
from pathlib import Path

from aulos_skills.decontam import resolve_scrub_markers, validate_node_outputs
from aulos_skills.identity import resolve_identity
from aulos_skills.intake_parse import guess_composer_and_title
from aulos_skills.runtime import SkillRuntime


HOROWITZ_MOZART_MSG = """/discogs #1654260
Write a professional classical listening guide (聆乐导赏) for "Horowitz Plays Mozart: Piano Concerto No. 23 K. 488 • Piano Sonata K. 333".
Aspect focus: 作品导赏.
Composers: Wolfgang Amadeus Mozart
Performers: Vladimir Horowitz, Carlo Maria Giulini
Ensembles: Orchestra Del Teatro Alla Scala
Release: year=1987 label=Deutsche Grammophon catno=423 287-1
Discogs: https://www.discogs.com/release/1654260
Produce a structured listening guide with historical context and how to listen.
"""

HINT = "Wolfgang Amadeus Mozart — Horowitz Plays Mozart: Piano Concerto No. 23 K. 488 • Piano Sonata K. 333"

REQUIEM_POLLUTION = {
    "work_title": "Horowitz P… Write a professional classical listening guide (聆乐导赏) for",
    "composer": "",
    "listening_thesis": (
        "Horowitz’s solo piano readings of Mozart’s Requiem movements distill "
        "liturgical polyphony into a personal confession."
    ),
    "form": "Sacred choral suite (Requiem mass) reimagined as solo piano",
    "work_introduction": "Dies irae and Lacrimosa transcriptions — 末日经与落泪之日。",
    "zh_hans": {
        "listening_thesis": "霍洛维茨以钢琴独奏演绎莫扎特《安魂曲》选段。",
        "work_introduction": "最著名的是末日经和落泪之日。",
    },
}


def test_mozart_composer_and_k488_resolve_from_diary_shape() -> None:
    from aulos_skills.identity import load_catalog

    load_catalog.cache_clear()
    cat = load_catalog()
    guessed = guess_composer_and_title(HOROWITZ_MOZART_MSG, catalog_composers=cat.composers)
    assert "Mozart" in (guessed.get("composer") or "")
    assert "488" in (guessed.get("work_title") or "") or "Concerto" in (guessed.get("work_title") or "")
    ident = resolve_identity(HOROWITZ_MOZART_MSG, work_hint=HINT)
    assert ident.status == "work"
    assert ident.work_id == "mozart.piano-concerto-23.k-488"
    assert "Mozart" in (ident.composer_name or "")


def test_requiem_pollution_fails_decontam_on_k488_shelf() -> None:
    context = {
        "work_title": "Piano Concerto No. 23 K. 488 • Piano Sonata K. 333",
        "composer": "Wolfgang Amadeus Mozart",
        "composer_id": "wolfgang-amadeus-mozart",
        "work_id": "mozart.piano-concerto-23.k-488",
        "raw_message": HOROWITZ_MOZART_MSG,
        "work_hint": HINT,
    }
    markers = resolve_scrub_markers(context)
    assert any("requiem" in m or "安魂" in m or "末日" in m or "dies irae" in m for m in markers)
    report = validate_node_outputs(
        "listening.synthesize",
        context,
        {"corpus_dossier": REQUIEM_POLLUTION, "synthesize_source": "llm"},
    )
    assert not report.ok
    assert report.findings


def test_runtime_scrubs_requiem_when_kb_seed_is_k488() -> None:
    from aulos_skills.identity import load_catalog

    load_catalog.cache_clear()
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    seed = {
        "work_title": "Piano Concerto No. 23 K. 488 • Piano Sonata K. 333",
        "composer": "Wolfgang Amadeus Mozart",
        "interpretations": [
            {
                "artist": "Vladimir Horowitz, Carlo Maria Giulini",
                "year": "1987",
                "why_listen": "Primary Discogs pressing",
                "discogs_url": "https://www.discogs.com/release/1654260",
            }
        ],
        "_provenance": {"source": "discogs", "discogs": {"release_id": 1654260}},
        # Simulate LLM inventing Requiem into a prior KB layer
        "listening_thesis": REQUIEM_POLLUTION["listening_thesis"],
        "form": REQUIEM_POLLUTION["form"],
        "work_introduction": REQUIEM_POLLUTION["work_introduction"],
        "zh_hans": REQUIEM_POLLUTION["zh_hans"],
    }
    report = runtime.run_listening_chain(
        message=HOROWITZ_MOZART_MSG,
        work_hint=HINT,
        kb_dossier=seed,
        rag_hits=[
            "Discogs release #1654260: Horowitz Plays Mozart",
            "Composer credits: Wolfgang Amadeus Mozart",
            "Performers: Vladimir Horowitz, Carlo Maria Giulini",
        ],
        rag_mode="discogs",
    )
    assert "Mozart" in (report.composer or "")
    html = report.guide_html
    for banned in (
        "Requiem",
        "安魂曲",
        "安魂",
        "末日经",
        "末日經",
        "Dies irae",
        "Dies Irae",
        "Lacrimosa",
        "落泪之日",
        "落淚之日",
    ):
        assert banned not in html, f"Requiem drift marker present: {banned}"
    assert "488" in html or "Concerto" in html or "协奏" in html or "協奏" in html
    dossier = (report.context or {}).get("corpus_dossier") or {}
    blob = json.dumps(dossier, ensure_ascii=False)
    assert "Requiem" not in blob
    assert "安魂" not in blob
    assert "末日" not in blob
