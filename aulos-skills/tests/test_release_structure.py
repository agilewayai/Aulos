"""SPEC-034 / META-001 §4.1 — Discogs release structure before deepen."""

from __future__ import annotations

from aulos_skills.release_structure import (
    assert_structure_ready,
    build_release_structure,
    expansion_plan,
)


def _bach_violin_program_raw() -> dict:
    """Multi-BWV pressing (anti-case class: program must be recognized first)."""
    return {
        "id": 3796623,
        "title": "Violin Concertos BWV 1041 • 1042 / Double Concertos BWV 1060 • 1043",
        "artists": [{"name": "Arthur Grumiaux"}],
        "extraartists": [
            {"name": "Johann Sebastian Bach", "role": "Composed By"},
            {"name": "Arthur Grumiaux", "role": "Violin"},
        ],
        "tracklist": [
            {
                "position": "1",
                "title": "Concerto In A Minor (BWV 1041) For Violin, Strings, And Continuo",
                "type_": "track",
            },
            {
                "position": "2",
                "title": (
                    "Concerto In E Major (BWV 1042) For Violin, Strings, And Continuo"
                ),
                "type_": "track",
            },
            {
                "position": "3",
                "title": (
                    "Concerto In D Minor (BWV 1060) For Oboe, Violin, Strings, "
                    "And Continuo"
                ),
                "type_": "track",
            },
            {
                "position": "4",
                "title": (
                    "Concerto In D Minor (BWV 1043) For Two Violins, Strings, "
                    "And Continuo"
                ),
                "type_": "track",
            },
        ],
        "labels": [{"name": "Philips", "catno": "9500 098"}],
        "year": 1970,
        "genres": ["Classical"],
        "formats": [{"name": "Vinyl"}],
    }


def _mozart_dual_raw() -> dict:
    """Unrelated multi-work identity (Horowitz Mozart pressing class)."""
    return {
        "id": 4084139,
        "title": "Horowitz Plays Mozart",
        "tracklist": [
            {"position": "A1", "title": "Piano Concerto No. 23 In A Major, K. 488", "type_": "track"},
            {"position": "B1", "title": "Piano Sonata In B Flat Major, K. 333", "type_": "track"},
        ],
        "labels": [{"name": "Deutsche Grammophon", "catno": "423 287-1"}],
        "year": 1987,
        "genres": ["Classical"],
    }


def _hummel_weber_haydn_raw() -> dict:
    """Guide #59 class: release artists are composers, extraartists are performers."""
    return {
        "id": 7083684,
        "title": "Trios Für Klavier, Flöte Und Violoncello",
        "artists": [
            {"name": "Johann Nepomuk Hummel"},
            {"name": "Carl Maria von Weber"},
            {"name": "Joseph Haydn"},
            {"name": "Trio Parnassus"},
        ],
        "extraartists": [
            {"name": "Trio Parnassus", "role": "Piano Trio"},
            {"name": "Michael Faust", "role": "Flute"},
            {"name": "Stanislav Apolín", "role": "Cello"},
        ],
        "tracklist": [
            {"position": "1", "title": "Trio In E Major, Op. 78", "type_": "track"},
            {"position": "2", "title": "Trio In G Minor, Op. 63", "type_": "track"},
            {"position": "3", "title": "Trio In D Major, Hob. XV:16", "type_": "track"},
        ],
        "labels": [{"name": "MDG", "catno": "MDG 303 0434-2"}],
        "genres": ["Classical"],
    }


def test_canonical_discogs_title_strips_polyglot() -> None:
    from aulos_skills.release_structure import canonical_discogs_title, program_search_query

    poly = (
        "Violin Concerto In A Minor, BWV 1041 = Violinkonzert A-Moll = "
        "Concerto Pour Violon Et Orchestre En La"
    )
    canon = canonical_discogs_title(poly)
    assert "=" not in canon
    assert "1041" in canon
    assert "Violinkonzert" not in canon
    q = program_search_query(
        composer="Johann Sebastian Bach",
        title=poly,
        catalog_numbers=["bwv1041"],
    )
    assert "BWV 1041" in q
    assert "=" not in q
    assert "Pour Violon" not in q
    # Composer is attached by gather — query itself stays work-scoped
    assert "Johann Sebastian" not in q


def test_polyglot_tracklist_canonicalizes_program_titles() -> None:
    raw = _bach_violin_program_raw()
    raw["tracklist"] = [
        {
            "position": "1",
            "title": (
                "Violin Concerto In A Minor, BWV 1041 = Violinkonzert A-Moll = "
                "Concerto Pour Violon Et Orchestre En La"
            ),
            "type_": "track",
        },
        {
            "position": "2",
            "title": (
                "Violin Concerto In E, BWV 1042 = Violinkonzert E-Dur = "
                "Concerto Pour Violon Et Orchestre En Mi"
            ),
            "type_": "track",
        },
    ]
    st = build_release_structure(raw, composers=["Johann Sebastian Bach"])
    assert st.shape == "multi_work_program"
    for p in st.program:
        assert "=" not in p.title
        assert p.catalog_numbers


def test_multi_bwv_program_is_structure_ready() -> None:
    st = build_release_structure(
        _bach_violin_program_raw(),
        composers=["Johann Sebastian Bach"],
        performers=["Arthur Grumiaux"],
    )
    assert st.shape == "multi_work_program"
    assert st.structure_ready is True
    assert len(st.program) >= 3
    cats = {c for p in st.program for c in p.catalog_numbers}
    assert "bwv1041" in cats or any("1041" in c for c in cats)
    assert any("1060" in c for c in cats)
    assert assert_structure_ready(st) == []


def test_unrelated_mozart_program_also_clusters() -> None:
    st = build_release_structure(_mozart_dual_raw(), composers=["Wolfgang Amadeus Mozart"])
    assert st.shape == "multi_work_program"
    assert len(st.program) == 2
    joined = " ".join(p.title for p in st.program)
    assert "488" in joined and "333" in joined
    plan = expansion_plan(st)
    deepen = [x for x in plan if x["name"] == "work_deepen"]
    assert len(deepen) == 2


def test_release_artists_are_positionally_assigned_to_program_composers() -> None:
    from aulos_skills.program_deepen import iter_program_works

    st = build_release_structure(_hummel_weber_haydn_raw())
    assert st.shape == "multi_work_program"
    assert st.structure_ready is True
    assert [p.composers for p in st.program] == [
        ["Johann Nepomuk Hummel"],
        ["Carl Maria von Weber"],
        ["Joseph Haydn"],
    ]
    assert st.composers == [
        "Johann Nepomuk Hummel",
        "Carl Maria von Weber",
        "Joseph Haydn",
    ]
    plan = expansion_plan(st)
    assert [x.get("composer") for x in plan if x["name"] == "work_deepen"] == [
        "Johann Nepomuk Hummel",
        "Carl Maria von Weber",
        "Joseph Haydn",
    ]
    works = iter_program_works(st.to_dict(), composer="", max_works=3)
    assert [w.get("composer") for w in works] == [
        "Johann Nepomuk Hummel",
        "Carl Maria von Weber",
        "Joseph Haydn",
    ]


def test_empty_payload_not_ready() -> None:
    st = build_release_structure({})
    assert st.structure_ready is False
    fails = assert_structure_ready(st)
    assert "release_structure_not_ready" in fails


def test_single_work_goldberg_ready() -> None:
    st = build_release_structure(
        {
            "id": 700123,
            "title": "Glenn Gould - The Goldberg Variations",
            "tracklist": [
                {"position": "A1", "title": "Aria", "type_": "track"},
                {"position": "A2", "title": "Variation 1 a 1 Clav.", "type_": "track"},
            ],
            "labels": [{"name": "Columbia", "catno": "ML 5060"}],
        },
        composers=["Johann Sebastian Bach"],
    )
    assert st.shape in {"single_work", "shelf"}
    assert st.structure_ready is True
    assert st.track_count == 2


def test_program_expand_dossier_has_per_work_deepdives() -> None:
    from aulos_skills.release_structure import build_program_expand_dossier

    st = build_release_structure(
        _bach_violin_program_raw(),
        composers=["Johann Sebastian Bach"],
        performers=["Arthur Grumiaux"],
    )
    d = build_program_expand_dossier(
        st,
        composer="Johann Sebastian Bach",
        work_title=st.release_title,
        performers=["Arthur Grumiaux"],
    )
    assert d
    assert len(d["variation_deepdives"]) >= 3
    assert len(d["listening_map"]) >= 3
    assert "release-program-expand" == d.get("raw_format")
    assert (d.get("zh") or {}).get("listening_map")
    joined = " ".join(x["title"] for x in d["variation_deepdives"])
    assert "1041" in joined or "1042" in joined


def test_structure_gate_refuses_family_when_not_ready() -> None:
    from aulos_skills.release_structure import apply_structure_gate

    ctx = apply_structure_gate(
        {
            "release_structure": {
                "shape": "multi_work_program",
                "structure_ready": False,
                "gaps": ["missing_tracklist"],
                "program": [{"title": "A", "catalog_numbers": ["bwv1"]}],
            }
        }
    )
    assert ctx.get("refuse_families") is True
    assert ctx.get("structure_hard_fails")


def test_synthesize_applies_program_expand() -> None:
    """Slice C: multi-work ready context → synthesize_source includes program expand."""
    from aulos_skills.runtime import SkillRuntime
    from aulos_skills.salon_codex import empty_dossier

    st = build_release_structure(
        _bach_violin_program_raw(),
        composers=["Johann Sebastian Bach"],
        performers=["Arthur Grumiaux"],
    ).to_dict()
    st["expansion_plan"] = expansion_plan(st)
    rt = SkillRuntime()
    from pathlib import Path

    from aulos_skills.registry import discover_skills

    skills_root = Path(__file__).resolve().parents[1] / "skills"
    synth = None
    for s in discover_skills([skills_root]):
        if "synthesize" in s.skill_id:
            synth = s
            break
    assert synth is not None
    ctx = {
        "work_title": st["release_title"],
        "composer": "Johann Sebastian Bach",
        "composer_guess": "Johann Sebastian Bach",
        "raw_message": "/discogs #3796623",
        "kb_dossier": {
            "work_title": st["release_title"],
            "composer": "Johann Sebastian Bach",
            "release_structure": st,
            "_provenance": {"source": "discogs"},
        },
        "release_structure": st,
        "program_expand_required": True,
        "corpus_dossier": empty_dossier(),
        "discogs": {"performers": ["Arthur Grumiaux"]},
    }
    out = rt._run_synthesize(synth, ctx)
    assert out.get("synthesize_hit")
    src = str(out.get("synthesize_source") or "")
    assert "release-program-expand" in src
    dossier = out.get("corpus_dossier") or {}
    assert len(dossier.get("variation_deepdives") or []) >= 3
    assert len(dossier.get("listening_map") or []) >= 3


def test_intake_scorecard_hard_fails_unready_multi_work() -> None:
    from aulos_skills.process_scorecard import score_node

    card = score_node(
        "listening.intake",
        {
            "work_title": "Violin Concertos",
            "composer": "Johann Sebastian Bach",
            "intent_lock": {
                "work_title": "Violin Concertos",
                "composer": "Johann Sebastian Bach",
                "catalog_numbers": [],
            },
            "release_structure": {
                "shape": "multi_work_program",
                "structure_ready": False,
                "gaps": ["missing_tracklist"],
                "program": [],
            },
        },
        {},
    )
    assert card is not None
    assert card.hard_fail is True
    assert any(f.code == "release_structure_not_ready" for f in card.findings)
