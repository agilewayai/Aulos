"""SPEC-032 / REQ-022 — identity freeze, catalog number hygiene, facet hardening.

Cross-identity regressions only — no per-work craft patches.
"""

from __future__ import annotations

from pathlib import Path

from aulos_skills.facet_classifier import classify_facets
from aulos_skills.identity import resolve_identity
from aulos_skills.identity_lock import build_identity_lock
from aulos_skills.product_scorecard import score_product
from aulos_skills.promote_candidate import build_promote_candidate
from aulos_skills.registry import discover_skills
from aulos_skills.runtime import SkillRuntime


def test_composer_card_not_unlocked_by_performer_surname_substring() -> None:
    """Class: performer surname containing a composer alias must not load that card.

    Probe A: Eschenbach ⊂ bach. Probe B: unrelated — Schumann pianist vs Bach.
    """
    rt = SkillRuntime()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]

    mozart_blob = (
        "Wolfgang Amadeus Mozart Sonaten A-Dur KV 331 "
        "Performers: Christoph Eschenbach Deutsche Grammophon"
    )
    card_a = rt._match_composer_card(synth, mozart_blob, "Wolfgang Amadeus Mozart")
    assert not card_a or str(card_a.get("composer") or "").lower().find("bach") < 0
    assert (card_a or {}).get("composer") in {
        None,
        "",
        "Wolfgang Amadeus Mozart",
    } or "mozart" in str((card_a or {}).get("composer") or "").lower()

    # Unrelated identity: Clara Schumann nocturne must not become Bach via "Eschenbach"
    clara_blob = "Clara Schumann Nocturne Performers: Christoph Eschenbach"
    card_b = rt._match_composer_card(synth, clara_blob, "Clara Schumann")
    assert "bach" not in str((card_b or {}).get("composer") or "").lower()


def test_intent_lock_composer_wins_over_mismatched_card_in_synthesize() -> None:
    rt = SkillRuntime()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]
    out = rt._run_synthesize(
        synth,
        {
            "work_title": "Sonaten A-Dur KV 331 • C-Dur KV 330",
            "composer_guess": "Wolfgang Amadeus Mozart",
            "composer": "Wolfgang Amadeus Mozart",
            "raw_message": (
                "Mozart Sonaten Performers: Christoph Eschenbach "
                "listening guide piano sonatas"
            ),
            "intent_lock": {
                "composer": "Wolfgang Amadeus Mozart",
                "work_title": "Sonaten A-Dur KV 331 • C-Dur KV 330",
                "catalog_numbers": ["k330", "k331"],
            },
        },
    )
    dossier = out.get("corpus_dossier") or {}
    assert dossier.get("composer") == "Wolfgang Amadeus Mozart"
    assert out.get("composer") == "Wolfgang Amadeus Mozart"


def test_multi_catalog_numbers_not_false_ambiguous_tie() -> None:
    """Multiple Köchel numbers matching no Catalog work → not fake concerto/requiem tie."""
    msg = (
        '/discogs #1131988 Write a guide for "Sonaten A-Dur KV 331 • C-Dur KV 330 '
        '/ Rondo D-Dur KV 485 • A-Moll KV 511". Composers: Wolfgang Amadeus Mozart '
        "Performers: Christoph Eschenbach"
    )
    r = resolve_identity(msg)
    assert r.work_id is None
    assert r.status in {"composer_only", "multi_work", "unknown"}
    assert r.status != "ambiguous" or "k-488" not in (r.reason or "")
    assert "k-488" not in (r.reason or "")
    assert "k-626" not in (r.reason or "")
    if r.composer_name:
        assert "Mozart" in r.composer_name

    # Unrelated multi-Op pressing class: Chopin ops that are not Catalog singles
    chopin_msg = "Chopin Mazurka Op. 67 No. 4 and Waltz Op. 64 No. 1 listening guide"
    r2 = resolve_identity(chopin_msg)
    # Must not invent a false ambiguous tie to unrelated Catalog works via bare "op"
    assert "tie" not in (r2.reason or "") or r2.status == "work"


def test_bare_kv_prefix_does_not_score_catalog_works() -> None:
    r = resolve_identity(
        "Wolfgang Amadeus Mozart KV 330 piano sonata listening guide Eschenbach"
    )
    assert r.work_id not in {
        "mozart.piano-concerto-23.k-488",
        "mozart.requiem.k-626",
    }


def test_facet_solo_piano_sonata_not_cello_duo() -> None:
    en = classify_facets(
        work_title="Piano Sonata in C major",
        composer="Wolfgang Amadeus Mozart",
        raw_message="solo piano sonata listening",
    )
    assert "sonata" in en["forms"]
    assert "piano" in en["instruments"]
    assert en["archetype_id"] != "duo-cello-piano"
    assert en["archetype_id"] in {"solo-piano-sonata", "chamber-generic"}
    assert en["confidence"] >= 0.4

    de = classify_facets(
        work_title="Sonaten A-Dur KV 331 • C-Dur KV 330 / Rondo D-Dur KV 485",
        composer="Wolfgang Amadeus Mozart",
        raw_message="Sonaten Rondo piano Christoph Eschenbach",
    )
    assert "sonata" in de["forms"] or "rondo" in de["forms"]
    assert de["archetype_id"] != "duo-cello-piano"
    assert de["archetype_id"] in {"solo-piano-sonata", "chamber-generic"}

    # Unrelated: real cello sonata still maps to duo
    cello = classify_facets(
        work_title="Cello Sonata in A major",
        composer="César Franck",
        raw_message="cello and piano sonata",
    )
    assert cello["archetype_id"] == "duo-cello-piano"


def test_form_lock_solo_keyboard_anchors() -> None:
    lock = build_identity_lock(
        work_title="Sonaten A-Dur KV 331",
        raw_message="Mozart piano sonatas Rondo KV 485",
    )
    assert lock.catalog_numbers
    assert "solo_keyboard" in lock.form_families or "piano_sonata" in lock.form_families

    # Duo cello shelves must not inherit solo_keyboard aliens (cross-identity).
    duo = build_identity_lock(
        work_title="Cello Sonatas & Variations",
        raw_message="我准备开始欣赏贝多芬的大提琴、钢琴奏鸣曲和变奏曲",
    )
    assert "duo_cello_piano" in duo.form_families
    assert "solo_keyboard" not in duo.form_families
    aliens = " ".join(duo.alien_markers).lower()
    assert "violoncello" not in aliens


def test_promote_candidate_refuses_composer_drift_and_hard_fail() -> None:
    dossier = {
        "listening_thesis": "A" * 50,
        "listening_map": [{"label": "a", "cue": "b"}] * 3,
        "width_points": ["w"] * 3,
        "depth_points": ["d"] * 3,
        "work_introduction": "intro " * 10,
        "zh": {"listening_thesis": "中文论题足够长了吧"},
        "composer": "Johann Sebastian Bach",
    }
    clf = {"archetype_id": "solo-piano-sonata", "instruments": ["piano"], "forms": ["sonata"], "confidence": 0.8}
    assert (
        build_promote_candidate(
            work_title="Sonaten KV 331",
            composer="Johann Sebastian Bach",
            classification=clf,
            dossier=dossier,
            locked_composer="Wolfgang Amadeus Mozart",
        )
        is None
    )
    assert (
        build_promote_candidate(
            work_title="Clara Schumann — Nocturne",
            composer="Clara Schumann",
            classification=clf,
            dossier={**dossier, "composer": "Clara Schumann"},
            allow=False,
        )
        is None
    )
    ok = build_promote_candidate(
        work_title="Clara Schumann — Nocturne",
        composer="Clara Schumann",
        classification=clf,
        dossier={**dossier, "composer": "Clara Schumann"},
        locked_composer="Clara Schumann",
        allow=True,
    )
    assert ok is not None
    assert ok["suggested_work_id"].startswith("schumann.")


def test_product_scorecard_fails_on_composer_drift() -> None:
    card = score_product(
        html='<div data-lang="en">x</div><div data-lang="zh-Hans">y</div>',
        context={
            "work_title": "Sonaten KV 331",
            "composer": "Johann Sebastian Bach",
            "intent_lock": {"composer": "Wolfgang Amadeus Mozart", "work_title": "Sonaten KV 331"},
            "corpus_dossier": {
                "composer": "Johann Sebastian Bach",
                "work_title": "Sonaten KV 331",
                "listening_thesis": "A focused listening room under one identity; lock the opening character before chasing ornament.",
                "zh": {"listening_thesis": "同一身份下的专注聆听房间；先锁住开场性格。"},
                "listening_map": [1, 2, 3],
                "width_points": [1, 2, 3],
            },
        },
    )
    assert card.dimensions.get("identity_clarity", 3) == 0
    assert any(f.code == "product_composer_drift" for f in card.findings)
    assert card.pass_ is False

    # Unrelated clean identity still can pass identity dimension
    clean = score_product(
        html='<div data-lang="en">x</div><div data-lang="zh-Hans">y</div>'
        + "composer- genesis- sound- interpretations- anatomy- practice-",
        context={
            "work_title": "Nocturne in F major",
            "composer": "Clara Schumann",
            "intent_lock": {"composer": "Clara Schumann", "work_title": "Nocturne in F major"},
            "corpus_dossier": {
                "composer": "Clara Schumann",
                "work_title": "Nocturne in F major",
                "listening_thesis": "Hear the nocturne's cantabile line and the left-hand murmur before chasing legend.",
                "zh": {"listening_thesis": "先听夜曲的如歌旋律与左手低语。"},
                "listening_map": [1, 2, 3],
                "width_points": [1, 2, 3],
                "depth_points": [1, 2, 3],
                "_provenance": {"unknown_case_thicken": True},
                "dossier_id": "archetype:lyric-piano-miniatures",
            },
            "synthesize_source": "archetype:lyric-piano-miniatures",
        },
    )
    assert clean.dimensions.get("identity_clarity", 0) >= 2
    assert not any(f.code == "product_composer_drift" for f in clean.findings)
