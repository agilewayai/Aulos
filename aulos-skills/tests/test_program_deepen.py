"""SPEC-034Δ — iterative program deepen loop (not single-layer synthesize)."""

from __future__ import annotations

from aulos_skills.program_deepen import (
    finalize_program_dossier,
    fold_program_iterations,
    iter_program_works,
    strip_generic_family_map,
)
from aulos_skills.guide_render import render_bilingual_guide_html
from aulos_skills.release_structure import build_release_structure


def _multi_raw() -> dict:
    return {
        "id": 3796623,
        "title": "Violin Concertos BWV 1041 • 1042 / Double Concertos BWV 1060 • 1043",
        "tracklist": [
            {"title": "Concerto In A Minor (BWV 1041)", "type_": "track"},
            {"title": "Concerto In E Major (BWV 1042)", "type_": "track"},
            {"title": "Concerto In D Minor (BWV 1060) For Oboe, Violin", "type_": "track"},
            {"title": "Concerto In D Minor (BWV 1043) For Two Violins", "type_": "track"},
        ],
        "labels": [{"name": "Philips", "catno": "9500 098"}],
    }


def test_iter_program_works_caps_and_orders() -> None:
    st = build_release_structure(_multi_raw()).to_dict()
    works = iter_program_works(st, composer="Johann Sebastian Bach", max_works=3)
    assert len(works) == 3
    assert any("1041" in " ".join(w.get("catalog_numbers") or []) for w in works)
    assert all(w.get("search_query") and "=" not in w["search_query"] for w in works)


def test_fold_filters_junk_bio_hits() -> None:
    st = build_release_structure(_multi_raw()).to_dict()
    iterations = [
        {
            "title": "Concerto In A Minor (BWV 1041)",
            "catalog_numbers": ["bwv1041"],
            "web_hits": [
                "[web:wikipedia] Johann Sebastian Bachlava the Doctor: Markdown Content: joke",
                "[web:wikipedia] Bach: Johann Sebastian Bach biography only",
                "[web:brave] BWV 1041: A-minor ritornello concerto with solo flight",
            ],
            "web_source_count": 3,
            "web_dossier": {
                "listening_thesis": "Research notes for x gathered from open sources.",
                "width_points": ["BWV 1041 ritornello bite before the solo episode"],
            },
        }
    ]
    d = fold_program_iterations(st, iterations, composer="Johann Sebastian Bach")
    cues = " ".join(d["variation_deepdives"][0]["ear_cues"]).lower()
    assert "bachlava" not in cues
    assert "1041" in cues or "ritornello" in cues
    assert d["listening_map"][0]["label"] in {"BWV 1041", "bwv1041"} or "1041" in d["listening_map"][0]["label"]


def test_fold_iterations_replaces_scaffold_deepdives() -> None:
    st = build_release_structure(_multi_raw()).to_dict()
    iterations = [
        {
            "title": "Concerto In A Minor (BWV 1041)",
            "catalog_numbers": ["bwv1041"],
            "llm_dossier": {
                "listening_thesis": "Lock the A-minor ritornello bite before the solo flight.",
                "form": "Ritornello concerto",
            },
            "web_hits": ["[web:brave] BWV 1041: Vivaldi-influenced…"],
            "web_source_count": 3,
            "llm_source": "agent-skills+deepseek",
        },
        {
            "title": "Concerto In E Major (BWV 1042)",
            "catalog_numbers": ["bwv1042"],
            "llm_note": "E-major brilliance with dance-finale pulse.",
            "web_source_count": 2,
        },
    ]
    d = fold_program_iterations(
        st,
        iterations,
        composer="Johann Sebastian Bach",
        work_title=st["release_title"],
    )
    assert d["raw_format"] == "release-program-loop"
    assert d["_provenance"]["program_loop"] == "iterative"
    assert len(d["variation_deepdives"]) == 2
    assert "ritornello" in d["variation_deepdives"][0]["ear_cues"][0].lower()
    assert all(
        str(x.get("label") or "").lower() not in {"orchestral thesis", "solo dialogue"}
        for x in d["listening_map"]
    )


def test_strip_generic_family_map() -> None:
    d = strip_generic_family_map(
        {
            "listening_map": [
                {"label": "Orchestral thesis", "cue": "generic"},
                {"label": "BWV 1041", "cue": "specific"},
                {"label": "Close", "cue": "generic"},
            ]
        }
    )
    labels = [x["label"] for x in d["listening_map"]]
    assert labels == ["BWV 1041"]


def test_finalize_prefers_loop_chambers() -> None:
    merged = {
        "listening_map": [{"label": "Orchestral thesis", "cue": "family"}],
        "variation_deepdives": [],
    }
    ctx = {
        "program_loop_applied": True,
        "program_loop_dossier": {
            "listening_map": [{"label": "BWV 1041", "cue": "lock ritornello"}],
            "variation_deepdives": [
                {"title": "BWV 1041", "focus": "x", "ear_cues": ["a"], "catalog": "bwv1041"}
            ],
            "raw_format": "release-program-loop",
            "_provenance": {"program_loop": "iterative", "iterations": 1},
            "zh": {"listening_map": [{"label": "BWV 1041", "cue": "利都奈罗"}]},
        },
    }
    out = finalize_program_dossier(merged, ctx)
    assert out["listening_map"][0]["label"] == "BWV 1041"
    assert out["raw_format"] == "release-program-loop"
    assert len(out["variation_deepdives"]) == 1


def test_fold_iterations_builds_program_subject_scalars() -> None:
    st = build_release_structure(
        {
            "title": "Trios Für Klavier, Flöte Und Violoncello",
            "tracklist": [
                {"title": "Trio In E Major, Op. 78", "type_": "track"},
                {"title": "Trio In G Minor, Op. 63", "type_": "track"},
                {"title": "Trio In D Major, Hob. XV:16", "type_": "track"},
            ],
        }
    ).to_dict()
    for row, composer in zip(
        st["program"],
        ["Johann Nepomuk Hummel", "Carl Maria von Weber", "Joseph Haydn"],
    ):
        row["composers"] = [composer]

    iterations = [
        {
            "title": "Trio In E Major, Op. 78",
            "composer": "Johann Nepomuk Hummel",
            "catalog_numbers": ["op78"],
            "llm_dossier": {
                "listening_thesis": "Hummel Op. 78 balances salon brilliance with chamber give-and-take.",
                "work_introduction": "A piano, flute and cello trio with poised early-Romantic rhetoric.",
                "sound_world": {"ensemble_notes": "piano, flute and cello as conversational equals"},
            },
        },
        {
            "title": "Trio In G Minor, Op. 63",
            "composer": "Carl Maria von Weber",
            "catalog_numbers": ["op63"],
            "llm_dossier": {
                "listening_thesis": "Weber Op. 63 brings darker theatrical contrast to the trio shelf.",
            },
        },
        {
            "title": "Trio In D Major, Hob. XV:16",
            "composer": "Joseph Haydn",
            "catalog_numbers": ["hob15"],
            "llm_dossier": {
                "listening_thesis": "Haydn Hob. XV:16 restores Classical poise and motivic wit.",
            },
        },
    ]
    d = fold_program_iterations(st, iterations, composer="", work_title=st["release_title"])
    assert d["composer"] == "Johann Nepomuk Hummel / Carl Maria von Weber / Joseph Haydn"
    assert "Unknown composer" not in d["work_introduction"]
    assert "Hummel" in d["listening_thesis"]
    assert "Weber" in d["listening_thesis"]
    assert "Haydn" in d["listening_thesis"]
    assert "anonymous" not in d["listening_thesis"].lower()
    assert {x["title"] for x in d["related_works"]} == {
        "Johann Nepomuk Hummel — Trio In E Major, Op. 78",
        "Carl Maria von Weber — Trio In G Minor, Op. 63",
        "Joseph Haydn — Trio In D Major, Hob. XV:16",
    }
    assert "piano" in str(d.get("sound_world") or {}).lower()
    assert "flute" in str(d.get("sound_world") or {}).lower()
    assert "cello" in str(d.get("sound_world") or {}).lower()


def test_fold_iterations_builds_work_sheets_and_synthesis() -> None:
    st = build_release_structure(
        {
            "title": "Trios Für Klavier, Flöte Und Violoncello",
            "tracklist": [
                {"title": "Trio In E Major, Op. 78", "type_": "track"},
                {"title": "Trio In G Minor, Op. 63", "type_": "track"},
                {"title": "Trio In D Major, Hob. XV:16", "type_": "track"},
            ],
        }
    ).to_dict()
    for row, composer in zip(
        st["program"],
        ["Johann Nepomuk Hummel", "Carl Maria von Weber", "Joseph Haydn"],
    ):
        row["composers"] = [composer]

    iterations = [
        {
            "index": 0,
            "title": "Trio In E Major, Op. 78",
            "composer": "Johann Nepomuk Hummel",
            "catalog_numbers": ["op78"],
            "llm_dossier": {
                "listening_thesis": "Hummel Op. 78 balances salon brilliance with chamber give-and-take.",
                "sound_world": {"ensemble_notes": "piano, flute and cello as conversational equals"},
            },
            "web_hits": ["Hummel Op. 78 piano flute cello trio chamber dialogue"],
            "web_source_count": 3,
            "llm_source": "agent-skills+deepseek",
        },
        {
            "index": 1,
            "title": "Trio In G Minor, Op. 63",
            "composer": "Carl Maria von Weber",
            "catalog_numbers": ["op63"],
            "llm_dossier": {
                "listening_thesis": "Weber Op. 63 brings darker theatrical contrast to the trio shelf.",
                "sound_world": {"ensemble_notes": "stormier piano, flute and cello exchange"},
            },
            "web_hits": ["Weber Op. 63 trio for piano flute cello in G minor"],
            "web_source_count": 2,
            "llm_source": "web-floor",
        },
        {
            "index": 2,
            "title": "Trio In D Major, Hob. XV:16",
            "composer": "Joseph Haydn",
            "catalog_numbers": ["hob15"],
            "llm_dossier": {
                "listening_thesis": "Haydn Hob. XV:16 restores Classical poise and motivic wit.",
                "sound_world": {"ensemble_notes": "Classical balance across piano, flute and cello"},
            },
            "web_hits": ["Haydn Hob. XV:16 trio D major chamber writing"],
            "web_source_count": 2,
            "llm_source": "agent-skills+deepseek",
        },
    ]
    dossier = fold_program_iterations(st, iterations, composer="", work_title=st["release_title"])
    sheets = dossier.get("guide_sheets") or []
    assert [s.get("kind") for s in sheets] == ["work", "work", "work", "synthesis"]
    assert [s.get("composer") for s in sheets[:3]] == [
        "Johann Nepomuk Hummel",
        "Carl Maria von Weber",
        "Joseph Haydn",
    ]
    assert all(s.get("listening_map") for s in sheets[:3])
    assert all(s.get("deepdives") for s in sheets[:3])
    assert "Hummel" in str(sheets[-1].get("summary") or "")
    assert "Weber" in str(sheets[-1].get("summary") or "")
    assert "Haydn" in str(sheets[-1].get("summary") or "")
    plan = dossier.get("program_parallel_plan") or {}
    assert plan.get("fan_in") == "synthesis_sheet"
    assert [unit.get("composer") for unit in plan.get("fan_out") or []] == [
        "Johann Nepomuk Hummel",
        "Carl Maria von Weber",
        "Joseph Haydn",
    ]


def test_render_multi_work_sheets_as_accessible_tabs() -> None:
    dossier = {
        "work_title": "Trios Für Klavier, Flöte Und Violoncello",
        "composer": "Johann Nepomuk Hummel / Carl Maria von Weber / Joseph Haydn",
        "listening_thesis": "Hear the pressing as three locked program works.",
        "guide_sheets": [
            {
                "id": "work-1",
                "kind": "work",
                "index": 0,
                "title": "Trio In E Major, Op. 78",
                "composer": "Johann Nepomuk Hummel",
                "catalog": "Op. 78",
                "summary": "Hummel balances salon brilliance with chamber give-and-take.",
                "listening_map": [{"label": "Opening", "cue": "Catch the piano-flute-cello contract."}],
                "deepdives": [{"title": "Texture", "ear_cues": ["Listen for conversational equality."]}],
                "sound_world": "Piano, flute and cello as conversational equals.",
            },
            {
                "id": "work-2",
                "kind": "work",
                "index": 1,
                "title": "Trio In G Minor, Op. 63",
                "composer": "Carl Maria von Weber",
                "catalog": "Op. 63",
                "summary": "Weber darkens the shelf with theatrical contrast.",
                "listening_map": [{"label": "Contrast", "cue": "Track the minor-key rhetoric."}],
                "deepdives": [{"title": "Drama", "ear_cues": ["Notice the stage-like pacing."]}],
                "sound_world": "Stormier chamber exchange.",
            },
            {
                "id": "synthesis",
                "kind": "synthesis",
                "title": "Program synthesis",
                "summary": "Across Hummel and Weber, the same forces become different rooms.",
                "listening_map": [{"label": "Compare", "cue": "Move from salon poise to theatre."}],
                "deepdives": [{"title": "Shelf", "ear_cues": ["Compare balance across works."]}],
            },
        ],
    }
    html = render_bilingual_guide_html(
        dossier=dossier,
        work_title=str(dossier["work_title"]),
        composer=str(dossier["composer"]),
        default_lang="en",
    )
    assert 'class="sheet-tabs"' in html
    assert 'role="tablist"' in html
    assert 'role="tab"' in html
    assert 'role="tabpanel"' in html
    assert 'aria-selected="true"' in html
    assert 'data-sheet-kind="synthesis"' in html
    assert "Trio In E Major, Op. 78" in html
    assert "Program synthesis" in html
    assert "ArrowRight" in html
    assert "Home" in html and "End" in html


def test_finalize_program_loop_overrides_album_family_scalars() -> None:
    merged = {
        "composer": "Unknown composer",
        "listening_thesis": "An anonymous trio collection in a generic piano-trio family.",
        "work_introduction": "A thin overview of an anonymous collection.",
        "related_works": [{"title": "Mozart Piano Concerto K.488", "why": "wrong carryover"}],
        "sound_world": {"ensemble_notes": "generic family scaffold"},
        "listening_map": [{"label": "Orchestral thesis", "cue": "family"}],
        "variation_deepdives": [],
    }
    ctx = {
        "program_loop_applied": True,
        "program_loop_dossier": {
            "composer": "Johann Nepomuk Hummel / Carl Maria von Weber / Joseph Haydn",
            "listening_thesis": "Three locked works: Hummel Op. 78, Weber Op. 63, and Haydn Hob. XV:16.",
            "work_introduction": "Program-level guide for the piano, flute and cello trio shelf.",
            "related_works": [{"title": "Johann Nepomuk Hummel — Trio In E Major, Op. 78"}],
            "sound_world": {"ensemble_notes": "piano, flute and cello"},
            "listening_map": [{"label": "Op. 78", "cue": "Hummel lock"}],
            "variation_deepdives": [
                {"title": "Op. 78", "focus": "x", "ear_cues": ["a"], "catalog": "op78"}
            ],
            "raw_format": "release-program-loop",
        },
    }
    out = finalize_program_dossier(merged, ctx)
    assert out["composer"].startswith("Johann Nepomuk Hummel")
    assert "Unknown composer" not in out["composer"]
    assert "anonymous" not in out["listening_thesis"].lower()
    assert "Mozart" not in str(out.get("related_works") or "")
    assert out["sound_world"]["ensemble_notes"] == "piano, flute and cello"


def test_synthesize_uses_program_iterations() -> None:
    from pathlib import Path

    from aulos_skills.registry import discover_skills
    from aulos_skills.runtime import SkillRuntime
    from aulos_skills.salon_codex import empty_dossier

    st = build_release_structure(_multi_raw(), composers=["Johann Sebastian Bach"]).to_dict()
    synth = next(
        s for s in discover_skills([Path(__file__).resolve().parents[1] / "skills"]) if "synthesize" in s.skill_id
    )
    ctx = {
        "work_title": st["release_title"],
        "composer": "Johann Sebastian Bach",
        "composer_guess": "Johann Sebastian Bach",
        "raw_message": "/discogs #3796623",
        "release_structure": st,
        "program_expand_required": True,
        "program_iterations": [
            {
                "title": "Concerto In A Minor (BWV 1041)",
                "catalog_numbers": ["bwv1041"],
                "llm_dossier": {"listening_thesis": "A-minor ritornello contract."},
                "web_hits": ["web note 1041"],
                "web_source_count": 2,
            },
            {
                "title": "Concerto In E Major (BWV 1042)",
                "catalog_numbers": ["bwv1042"],
                "llm_dossier": {"listening_thesis": "E-major brilliance."},
                "web_source_count": 1,
            },
        ],
        "kb_dossier": {
            "work_title": st["release_title"],
            "composer": "Johann Sebastian Bach",
            "release_structure": st,
            "_provenance": {"source": "discogs"},
        },
        "corpus_dossier": empty_dossier(),
        "discogs": {"performers": ["Arthur Grumiaux"]},
    }
    out = SkillRuntime()._run_synthesize(synth, ctx)
    src = str(out.get("synthesize_source") or "")
    assert "release-program-loop" in src
    assert out.get("guide_sheets")
    assert (out.get("program_parallel_plan") or {}).get("fan_in") == "synthesis_sheet"
    dossier = out["corpus_dossier"]
    assert dossier.get("raw_format") == "release-program-loop"
    assert len(dossier.get("variation_deepdives") or []) >= 2
    labels = [str(x.get("label") or "").lower() for x in (dossier.get("listening_map") or [])]
    assert "orchestral thesis" not in labels
