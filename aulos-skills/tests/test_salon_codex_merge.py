"""Regression: merge_dossiers must tolerate malformed zh_* layers from LLMs."""

from __future__ import annotations

from aulos_skills.salon_codex import coerce_dict, merge_dossiers, parse_llm_dossier_json


def test_coerce_dict_rejects_string_as_pairs() -> None:
    # Bare dict("ab") raises ValueError — coerce must not.
    assert coerce_dict("简体导赏散文")["listening_thesis"].startswith("简体")
    assert coerce_dict(["x"])["listening_thesis"] == "x"
    assert coerce_dict({"a": 1}) == {"a": 1}
    assert coerce_dict(None) == {}


def test_merge_dossiers_zh_hans_string_does_not_crash() -> None:
    """Root cause of Mozart piano-concerto job failure:

    ValueError: dictionary update sequence element #0 has length 1; 2 is required
    when LLM/web dossier sets zh_hans to a prose string (or list) instead of an object.
    """
    base = {
        "work_title": "Piano Concerto No. 23",
        "composer": "Wolfgang Amadeus Mozart",
        "listening_thesis": "Listen for the A-major glow.",
    }
    bad_llm = {
        "work_title": "Piano Concerto No. 23 K. 488",
        "zh_hans": "莫扎特第二十三钢琴协奏曲，留意A大调的光泽与歌唱性。",
        "zh_hant": ["莫扎特第二十三鋼琴協奏曲"],
        "zh": "legacy prose",
        "composer_profile": "should-be-object-but-string",
        "width_points": "one point as string",
    }
    merged = merge_dossiers(base, bad_llm)
    assert merged["work_title"].startswith("Piano Concerto")
    assert isinstance(merged.get("zh_hans"), dict)
    assert "莫扎特" in str(merged["zh_hans"].get("listening_thesis") or "")
    assert isinstance(merged.get("zh_hant"), dict)
    assert isinstance(merged.get("composer_profile"), dict)
    assert merged["width_points"] == ["one point as string"]


def test_parse_llm_dossier_normalizes_zh_string() -> None:
    raw = '{"listening_thesis":"Hello","zh_hans":"中文导赏","width_points":"solo"}'
    data = parse_llm_dossier_json(raw)
    assert isinstance(data["zh_hans"], dict)
    assert data["width_points"] == ["solo"]


def test_merge_mozart_family_and_llm_layers() -> None:
    family = {
        "form": "piano concerto",
        "zh_hans": {
            "listening_thesis": "家族骨架",
            "width_points": ["维也纳钢琴协奏曲传统"],
        },
    }
    llm = {
        "composer": "Wolfgang Amadeus Mozart",
        "work_title": "Piano Concerto No. 23 in A major, K. 488",
        "zh_hans": "K.488 慢乐章如歌。",  # malformed
        "listening_map": [{"label": "I", "cue": "A major"}],
    }
    merged = merge_dossiers(family, llm)
    assert "Mozart" in merged["composer"]
    assert isinstance(merged["zh_hans"], dict)
    assert merged["listening_map"]
