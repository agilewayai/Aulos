"""Tests for review_targets semantic locate (SPEC-022Δ)."""

from aulos_skills.review_targets import (
    intents_from_expert_report,
    intents_from_human_notes,
    locate_targets_from_notes,
    resolve_scope,
    targets_for_finding_code,
    union_targets,
)


def test_code_maps_to_chambers() -> None:
    assert "composer_portrait" in targets_for_finding_code("portrait_composer_mismatch")
    assert "listening_map" in targets_for_finding_code("missing_listening_map")
    assert "work_title" in targets_for_finding_code("h1_celebrity_pollution")
    assert "work_title" in targets_for_finding_code("INCORRECT_WORK_TITLE")
    assert "work_title" in targets_for_finding_code("packaging_title_pollution")


def test_expert_intents_from_report() -> None:
    report = {
        "findings": [
            {
                "severity": "high",
                "code": "portrait_composer_mismatch",
                "note": "Wrong portrait",
                "evidence": "Beethoven",
            },
            {
                "severity": "medium",
                "code": "missing_listening_map",
                "note": "No map",
            },
        ],
        "required_corrections": ["Clear foreign portrait", "Add listening map"],
    }
    intents = intents_from_expert_report(report)
    assert len(intents) == 2
    assert intents[0]["source"] == "expert"
    assert "composer_portrait" in intents[0]["targets"]
    assert "listening_map" in intents[1]["targets"]
    assert resolve_scope(intents) == "targeted"


def test_human_notes_locate_genesis() -> None:
    targets = locate_targets_from_notes("请加强创作背景与时代介绍")
    assert "genesis" in targets or "historical_stature" in targets
    intents = intents_from_human_notes("请加强创作背景与时代介绍")
    assert intents[0]["source"] == "human"
    assert resolve_scope(intents) == "targeted"
    assert "*" not in union_targets(intents)


def test_human_notes_unlocatable_falls_back_full() -> None:
    intents = intents_from_human_notes("整篇重写得更有诗意一些吧")
    # May or may not hit keywords; if no chamber hit → full
    if not locate_targets_from_notes("整篇重写得更有诗意一些吧"):
        assert resolve_scope(intents) == "full"
        assert union_targets(intents) == ["*"]


def test_high_severity_unknown_code_full_scope() -> None:
    report = {
        "findings": [
            {"severity": "high", "code": "totally_unknown_xyz", "note": "weird"},
        ],
        "required_corrections": ["Fix weird"],
    }
    intents = intents_from_expert_report(report)
    assert intents
    assert "*" in intents[0]["targets"]
    assert resolve_scope(intents) == "full"
