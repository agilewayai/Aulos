"""SPEC-019 process scorecard unit tests."""

from __future__ import annotations

from pathlib import Path

from aulos_skills.process_scorecard import (
    SCHEMA,
    band_for_pct,
    record_node_scorecard,
    rollup_process,
    score_node,
)
from aulos_skills.runtime import SkillRuntime


ROOT = Path(__file__).resolve().parents[1]


def test_band_thresholds() -> None:
    assert band_for_pct(90) == "strong"
    assert band_for_pct(70) == "solid"
    assert band_for_pct(55) == "developing"
    assert band_for_pct(10) == "weak"


def test_na_dims_excluded_from_max() -> None:
    card = score_node(
        "listening.intake",
        {
            "intent_lock": {
                "work_title": "Piano Concerto No. 23 K. 488",
                "composer": "Wolfgang Amadeus Mozart",
                "catalog_numbers": ["k488"],
                "work_id": "mozart.piano-concerto-23.k-488",
            },
            "work_title": "Piano Concerto No. 23 K. 488",
            "composer": "Wolfgang Amadeus Mozart",
            "work_id": "mozart.piano-concerto-23.k-488",
        },
        {},
    )
    assert card is not None
    assert "ambient" in card.na_dims
    assert "richness" in card.na_dims
    assert card.max_possible == 3  # only identity
    assert card.earned == 3
    assert card.pct == 100.0


def test_route_unscored() -> None:
    assert score_node("listening.route", {}, {}) is None


def test_fidelity_hard_fail_on_review_failed() -> None:
    card = score_node(
        "listening.synthesize",
        {
            "intent_lock": {"work_title": "K.488", "composer": "Mozart", "catalog_numbers": ["k488"]},
            "work_title": "K.488",
            "composer": "Mozart",
            "review_failed": True,
            "corpus_dossier": {"listening_thesis": "x", "myths_and_caveats": ["y"]},
        },
        {"corpus_dossier": {"listening_thesis": "x", "myths_and_caveats": ["y"]}},
    )
    assert card is not None
    assert card.scores["fidelity"] == 0
    assert card.hard_fail is True


def test_clean_chain_writes_process_scorecard() -> None:
    rt = SkillRuntime(roots=[ROOT / "skills"])
    report = rt.run_listening_chain(
        message=(
            "Listening guide for Mozart Piano Concerto No. 23 in A major K. 488. "
            "Composers: Wolfgang Amadeus Mozart"
        ),
        work_hint="Mozart Piano Concerto No. 23 K. 488",
    )
    cards = list((report.context or {}).get("node_scorecards") or [])
    assert cards
    triggers = {c.get("trigger") for c in cards}
    assert "listening.intake" in triggers
    assert "listening.synthesize" in triggers
    process = (report.context or {}).get("process_scorecard") or {}
    assert process.get("schema") == SCHEMA
    assert "rollup" in process
    assert process["rollup"]["pct"] >= 0
    # Clean path should not hard-fail fidelity mid-chain
    synth = next(c for c in cards if c.get("trigger") == "listening.synthesize")
    assert synth.get("scores", {}).get("fidelity", 0) >= 2


def test_rollup_includes_product_and_nodes() -> None:
    context: dict = {
        "work_title": "Goldberg Variations",
        "composer": "Bach",
        "intent_lock": {
            "work_title": "Goldberg Variations",
            "composer": "Bach",
            "catalog_numbers": ["bwv988"],
            "work_id": "bach.goldberg",
        },
        "work_id": "bach.goldberg",
        "guide_html": (
            "<!DOCTYPE html><html><body>"
            '<div data-lang="en">en</div><div data-lang="zh-Hans">中</div>'
            "<div id=\"aulos-ambient\" data-ambient-player></div>"
            "<section id='composer-x'>作曲家</section>"
            "<section id='genesis-x'>创作背景与时代</section>"
            "<section id='stature-x'>何以传世</section>"
            "<section id='sound-x'>声响世界</section>"
            "<section id='interpretations-x'>名家演绎</section>"
            "<section id='media-x'>聆听室</section>"
            "listening map practice anatomy Fraunces"
            "</body></html>"
        ),
        "depth_dossier": {
            "depth_points": [
                "Listen for the aria return",
                "Hear the bass ground",
                "Notice variation contrast",
            ],
            "listening_map": [
                {"label": "Aria", "cue": "lock the bass"},
                {"label": "Mid", "cue": "hear intensification"},
            ],
        },
        "pass": True,
    }
    record_node_scorecard(context, "listening.intake", {})
    record_node_scorecard(
        context,
        "listening.synthesize",
        {
            "corpus_dossier": {
                "listening_thesis": "Ground bass as memory",
                "myths_and_caveats": ["Legend vs fact"],
                "depth_points": ["a", "b", "c"],
                "listening_map": [{}, {}],
                "interpretations": [{"artist": "x"}],
                "genesis": {"era": "baroque"},
                "historical_stature": {"reasons": ["r"]},
                "sound_world": {"texture": "keyboard"},
                "work_introduction": "intro",
            }
        },
    )
    process = rollup_process(context)
    assert process["schema"] == SCHEMA
    assert process["rollup"]["earned"] > 0
    assert process["product"]["scores"]["ambient"] == 3
    assert process["gates"]["ambient_ok"] is True
    assert process["rollup"]["band"] in {"solid", "strong", "developing", "weak"}
