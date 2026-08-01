"""SPEC-024 Work Resolver + chamber contracts."""

from __future__ import annotations

from aulos_skills.chamber_contracts import (
    audit_chamber_contracts,
    ensure_chamber_floor,
)
from aulos_skills.work_resolver import resolve_listening_work


def test_resolver_maps_songs_without_words_packaging() -> None:
    resolved = resolve_listening_work(
        raw_message="/discogs #2694192 listening guide",
        work_hint="Felix Mendelssohn — Lieder ohne Worte (Songs Without Words)",
        kb_dossier={
            "_provenance": {"source": "discogs"},
            "composer": "Felix Mendelssohn",
            "work_title": (
                "Bartholdy Lieder Ohne Worte = Songs Without Words / "
                "Romances Sans Paroles / Ges"
            ),
        },
    )
    assert resolved.work_id == "mendelssohn.lieder-ohne-worte"
    assert resolved.family_id == "lyric-piano-miniatures"
    assert "Bartholdy" not in resolved.work_title
    assert resolved.status == "work"


def test_chamber_audit_flags_thin_identity_shelf() -> None:
    gaps = audit_chamber_contracts(
        {"listening_thesis": "short", "listening_map": [], "width_points": []},
        identity_resolved=True,
    )
    codes = {g["code"] for g in gaps}
    assert "contract_thesis" in codes
    assert "contract_map" in codes


def test_ensure_floor_fills_from_family_with_zh() -> None:
    family = {
        "listening_thesis": "Hear a singing line over a keyboard gait first — lyric rooms.",
        "width_points": ["a", "b", "c", "d"],
        "depth_points": ["d1", "d2", "d3"],
        "listening_map": [
            {"label": "A", "cue": "1"},
            {"label": "B", "cue": "2"},
            {"label": "C", "cue": "3"},
        ],
        "genesis": {"year": "1830s", "place": "salon"},
        "sound_world": {"ensemble_notes": "solo piano"},
        "zh": {
            "listening_thesis": "先听见歌唱声部与左手步态——抒情之室。",
            "width_points": ["甲", "乙", "丙"],
            "listening_map": [
                {"label": "开", "cue": "一"},
                {"label": "中", "cue": "二"},
                {"label": "收", "cue": "三"},
            ],
        },
    }
    out = ensure_chamber_floor({}, family)
    assert len(out["listening_map"]) >= 3
    assert out["genesis"]
    assert out["sound_world"]
    zh = out.get("zh") or {}
    assert "歌唱" in str(zh.get("listening_thesis") or "")
    gaps = audit_chamber_contracts(out, identity_resolved=True)
    high = [g for g in gaps if g["severity"] == "high"]
    assert high == []
