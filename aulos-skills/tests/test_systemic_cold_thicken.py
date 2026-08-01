"""SPEC-026 systemic cold-path thicken."""

from __future__ import annotations

import yaml

from aulos_skills.catalog_craft_floor import build_catalog_craft_floor
from aulos_skills.product_scorecard import score_product
from aulos_skills.runtime import SkillRuntime


def test_catalog_floor_binds_chopin_nocturne_without_craft_yaml() -> None:
    family = yaml.safe_load(
        (
            __import__("pathlib").Path(__file__).resolve().parents[1]
            / "skills/aulos-listening-synthesize/assets/families/lyric-piano-miniatures.yaml"
        ).read_text(encoding="utf-8")
    )
    floor = build_catalog_craft_floor(
        "chopin.nocturne-op9-no2",
        family=family,
    )
    assert floor.get("dossier_id") == "catalog-floor:chopin.nocturne-op9-no2"
    assert floor["_provenance"]["catalog_craft_floor"] is True
    assert "Op. 9" in str(floor.get("catalog") or "")
    assert "Nocturne" in str(floor.get("listening_thesis") or "")
    assert "夜曲" in str((floor.get("zh") or {}).get("listening_thesis") or "")
    assert floor.get("composer")


def test_catalog_floor_without_family_still_thickens_scaffold() -> None:
    floor = build_catalog_craft_floor("mozart.requiem.k-626", family=None)
    assert floor.get("dossier_id") == "catalog-floor:mozart.requiem.k-626"
    assert len(floor.get("listening_map") or []) >= 3
    assert "K. 626" in str(floor.get("catalog") or "") or "626" in str(floor.get("catalog") or "")
    assert (floor.get("zh") or {}).get("listening_thesis")


def test_product_family_only_cannot_be_strong() -> None:
    html = (
        '<!DOCTYPE html><div id="composer-en">c</div>'
        '<div id="genesis-en">g</div><div id="sound-en">s</div>'
        '<div id="interpretations-en">i</div><div id="anatomy-en">a</div>'
        '<div id="practice-en">p</div>'
        '<div data-lang="en">en</div><div data-lang="zh-Hans">zh</div>'
    )
    dossier = {
        "dossier_id": "family:lyric-piano-miniatures",
        "listening_thesis": (
            "Hear a singing line over a keyboard gait first — lyric rooms, not symphony drama."
        ),
        "listening_map": [
            {"label": "Opening", "cue": "Lock the song."},
            {"label": "Middle", "cue": "Tint."},
            {"label": "Close", "cue": "Return."},
        ],
        "width_points": ["a", "b", "c"],
        "depth_points": ["d1", "d2", "d3"],
        "genesis": {"year": "1830s"},
        "sound_world": {"ensemble_notes": "solo piano"},
        "zh": {"listening_thesis": "先听见歌唱声部与左手步态——抒情之室。"},
    }
    card = score_product(
        html=html,
        context={
            "work_title": "Some Nocturne",
            "composer": "Frédéric Chopin",
            "work_id": "chopin.nocturne-op9-no2",
            "synthesize_source": "family:lyric-piano-miniatures",
            "corpus_dossier": dossier,
        },
        dossier=dossier,
    )
    assert card.dimensions.get("asset_depth") == 1
    assert card.band != "strong"
    assert any(f.code == "product_asset_family_only" for f in card.findings)


def test_product_catalog_floor_reaches_asset_depth_two() -> None:
    html = (
        '<!DOCTYPE html><div id="composer-en">c</div>'
        '<div id="genesis-en">g</div><div id="sound-en">s</div>'
        '<div id="interpretations-en">i</div><div id="anatomy-en">a</div>'
        '<div id="practice-en">p</div>'
        '<div data-lang="en">en</div><div data-lang="zh-Hans">zh</div>'
    )
    dossier = {
        "dossier_id": "catalog-floor:chopin.nocturne-op9-no2",
        "_provenance": {"catalog_craft_floor": True},
        "listening_thesis": (
            "In Nocturne Op. 9 No. 2: hear a singing line over a keyboard gait first."
        ),
        "listening_map": [
            {"label": "Opening", "cue": "1"},
            {"label": "Middle", "cue": "2"},
            {"label": "Close", "cue": "3"},
        ],
        "width_points": ["a", "b", "c"],
        "depth_points": ["d1", "d2", "d3"],
        "genesis": {"year": "1830s", "place": "salon"},
        "sound_world": {"ensemble_notes": "solo piano"},
        "zh": {"listening_thesis": "就夜曲作品9之2而言：先听见歌唱声部。"},
    }
    card = score_product(
        html=html,
        context={
            "work_title": "Frédéric Chopin — Nocturne in E-flat major, Op. 9 No. 2",
            "composer": "Frédéric Chopin",
            "work_id": "chopin.nocturne-op9-no2",
            "synthesize_source": "family:x+catalog-floor:chopin.nocturne-op9-no2",
            "corpus_dossier": dossier,
        },
        dossier=dossier,
    )
    assert card.dimensions.get("asset_depth") == 2
    assert card.pass_ is True


def test_dossier_is_thin_helper() -> None:
    from aulos_skills.knowledge_thicken import dossier_is_thin

    assert dossier_is_thin({}) is True
    assert dossier_is_thin({"composer": {"id": "x"}, "timeline": [], "portrait": None}) is True
    assert (
        dossier_is_thin(
            {
                "composer": {"id": "x", "summary_en": "A" * 50},
                "timeline": [{"event_type": "birth"}],
                "events_count": 1,
                "portrait": {"source_url": "https://example.com/p.jpg"},
            }
        )
        is False
    )


def test_synthesize_includes_catalog_floor_for_catalog_work() -> None:
    from pathlib import Path

    from aulos_skills.registry import discover_skills

    rt = SkillRuntime()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills.get("aulos-listening-synthesize")
    assert synth is not None
    out = rt._run_synthesize(
        synth,
        {
            "work_id": "chopin.nocturne-op9-no2",
            "work_title": "Frédéric Chopin — Nocturne in E-flat major, Op. 9 No. 2",
            "composer_guess": "Frédéric Chopin",
            "composer": "Frédéric Chopin",
            "family_hints": ["lyric-piano-miniatures"],
            "raw_message": "Chopin Nocturne Op. 9 No. 2 listening guide",
        },
    )
    src = str(out.get("synthesize_source") or "")
    assert "catalog-floor:chopin.nocturne-op9-no2" in src
    dossier = out.get("corpus_dossier") or {}
    thesis = str(dossier.get("listening_thesis") or "")
    assert len(thesis) >= 40
    assert "9" in thesis or "Nocturne" in thesis or "nocturne" in thesis.lower()
