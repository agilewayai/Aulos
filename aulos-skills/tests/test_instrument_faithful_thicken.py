"""SPEC-033 / REQ-023 — instrument-faithful thicken + multi-work intake (anti-case)."""

from __future__ import annotations

from pathlib import Path

from aulos_skills.facet_classifier import classify_facets
from aulos_skills.identity_hygiene import family_instruments_miss_title, foreign_family_id
from aulos_skills.identity_lock import build_identity_lock, extract_catalog_numbers
from aulos_skills.product_scorecard import score_product
from aulos_skills.registry import discover_skills
from aulos_skills.runtime import SkillRuntime


def test_chained_catalog_numbers_extract_siblings() -> None:
    """Prefix once, siblings after separators — not a single-work parser."""
    bwv = extract_catalog_numbers(
        "Violin Concertos BWV 1041 • 1042 / Double Concertos BWV 1060 • 1043"
    )
    assert {"bwv1041", "bwv1042", "bwv1060", "bwv1043"} <= bwv

    koch = extract_catalog_numbers("Sonaten K. 330 / 331 • 332")
    assert {"k330", "k331", "k332"} <= koch


def test_piano_concerto_family_refuses_orchestra_plus_concerto_without_piano() -> None:
    """Ensemble+form must not unlock a soloist-scoped family pack."""
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]
    rt = SkillRuntime()
    # Unrelated identity A: violin / oboe double concerto shelf
    family = rt._match_family(
        synth,
        "Concerto In D Minor BWV 1060 For Oboe, Violin, Strings — New Philharmonia Orchestra",
        family_hints=[],
        composer_guess="Johann Sebastian Bach",
    )
    assert str(family.get("family_id") or "") != "piano-concerto"

    # Unrelated identity B: honest piano concerto still unlocks
    family_ok = rt._match_family(
        synth,
        "Piano Concerto No. 23 in A major, K. 488 — Orchestra Del Teatro Alla Scala",
        family_hints=[],
        composer_guess="Wolfgang Amadeus Mozart",
    )
    assert str(family_ok.get("family_id") or "") == "piano-concerto"


def test_family_hint_piano_concerto_refused_on_violin_title() -> None:
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]
    rt = SkillRuntime()
    family = rt._match_family(
        synth,
        "Brahms — Violin Concerto in D major, Op. 77 with orchestra",
        family_hints=["piano-concerto"],
        composer_guess="Johannes Brahms",
    )
    assert str(family.get("family_id") or "") != "piano-concerto"


def test_foreign_family_piano_pack_on_violin_title() -> None:
    title = "Brahms — Violin Concerto in D major, Op. 77"
    pack = {"dossier_id": "family:piano-concerto"}
    assert foreign_family_id(pack, title, composer="Johannes Brahms") == "piano-concerto"
    # Orchestra in blob must not excuse missing piano soloist
    assert family_instruments_miss_title(
        {
            "match": {
                "instruments": ["piano", "orchestra", "钢琴", "管弦乐"],
                "forms": ["concerto"],
            }
        },
        "Violin Concerto with New Philharmonia Orchestra",
    )


def test_facet_violin_concerto_not_piano_soft_unlock() -> None:
    clf = classify_facets(
        work_title="Violin Concerto in D major, Op. 77",
        composer="Johannes Brahms",
        raw_message="with orchestra listening guide",
    )
    assert "violin" in (clf.get("instruments") or [])
    assert clf.get("archetype_id") != "piano-concerto"


def test_non_piano_concerto_locks_piano_rhetoric_aliens() -> None:
    from aulos_skills.identity_lock import load_form_lock_policy

    load_form_lock_policy.cache_clear()
    lock = build_identity_lock(
        work_title="Concerto for Oboe, Violin, Strings and Continuo",
        raw_message="Double concerto listening guide",
    )
    aliens = " ".join(lock.alien_markers).lower()
    assert "piano concerto" in aliens or "钢琴协奏" in aliens


def test_product_scorecard_flags_solo_instrument_betrayal() -> None:
    html = (
        '<section data-lang="en">Piano concerto cadenza dialogue with fortepiano.</section>'
        '<section data-lang="zh">钢琴协奏曲华彩与乐队对话。</section>'
    )
    card = score_product(
        html=html,
        context={
            "work_title": "Brahms — Violin Concerto in D major, Op. 77",
            "composer": "Johannes Brahms",
            "intent_lock": {"composer": "Johannes Brahms"},
            "synthesize_source": "family:piano-concerto",
        },
        dossier={
            "composer": "Johannes Brahms",
            "work_title": "Brahms — Violin Concerto in D major, Op. 77",
            "listening_thesis": (
                "Hear the piano concerto as a conversation — lock the orchestral thesis "
                "and the soloist's cadenza memory before bravura."
            ),
            "form": "Piano concerto — ritornello / sonata dialogue",
            "zh": {"listening_thesis": "把钢琴协奏曲当作一场对话来听，关注华彩。"},
        },
    )
    assert any(f.code == "product_solo_instrument_drift" for f in card.findings)
    assert card.dimensions.get("identity_clarity", 3) == 0
