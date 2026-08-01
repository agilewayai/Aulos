"""SPEC-025 knowledge thicken + product scorecard."""

from __future__ import annotations

from aulos_skills.craft_packs import load_craft_pack
from aulos_skills.knowledge_thicken import (
    knowledge_dossier_to_chambers,
    merge_knowledge_thicken,
)
from aulos_skills.product_scorecard import score_product


def test_knowledge_dossier_maps_portrait_and_genesis() -> None:
    dossier = {
        "composer": {
            "id": "frederic-chopin",
            "name_en": "Frédéric Chopin",
            "name_zh": "肖邦",
            "lifespan": "1810–1849",
            "era": "Romantic",
            "summary_en": "Polish composer and pianist",
            "summary_zh": "波兰作曲家",
        },
        "portrait": {
            "source_url": "https://upload.wikimedia.org/wikipedia/commons/e/e8/Frederic_Chopin_photo.jpeg",
            "license_class": "Public domain",
            "title": "Chopin photo",
        },
        "timeline": [
            {
                "event_type": "birth",
                "title_en": "Born in Żelazowa Wola",
                "date_start": "1810-02-22",
                "place_label": "Żelazowa Wola",
                "significance": "major",
                "sort_key": "1810-02-22",
            }
        ],
    }
    patch = knowledge_dossier_to_chambers(dossier)
    assert patch["composer_portrait"]["image_url"].startswith("https://")
    assert "1810" in str(patch["composer_profile"].get("lifespan"))
    assert patch["genesis"].get("place") == "Żelazowa Wola"
    assert "肖邦" in str((patch.get("zh") or {}).get("composer") or "")

    merged = merge_knowledge_thicken(
        {"listening_thesis": "Keep me", "composer_portrait": {}},
        patch,
    )
    assert merged["listening_thesis"] == "Keep me"
    assert merged["composer_portrait"]["image_url"]


def test_craft_pack_absent_until_promote() -> None:
    pack = load_craft_pack("mendelssohn.lieder-ohne-worte")
    assert pack == {}


def test_reassert_craft_leads_noop_without_pack() -> None:
    from aulos_skills.craft_packs import reassert_craft_leads

    drifted = {
        "listening_thesis": "LLM poetic EN",
        "zh": {"listening_thesis": "这是一部抒情日记。"},
    }
    out = reassert_craft_leads(drifted, "mendelssohn.lieder-ohne-worte")
    assert out["listening_thesis"] == "LLM poetic EN"


def test_product_score_fails_on_process_lock() -> None:
    card = score_product(
        html="<h1>CRITIQUE LOCK: x</h1><p>body</p>",
        context={
            "work_title": "Lieder ohne Worte (Songs Without Words)",
            "composer": "Felix Mendelssohn",
            "work_id": "mendelssohn.lieder-ohne-worte",
            "corpus_dossier": {
                "listening_thesis": "CRITIQUE LOCK: empty — Hear the song line over a gait carefully.",
                "listening_map": [{"label": "a", "cue": "1"}, {"label": "b", "cue": "2"}, {"label": "c", "cue": "3"}],
                "width_points": ["1", "2", "3"],
                "depth_points": ["1", "2", "3"],
                "zh": {"listening_thesis": "先听见歌唱声部与左手步态，再比较性情。"},
            },
        },
    )
    assert card.pass_ is False
    assert any(f.code == "product_process_leak" for f in card.findings)


def test_product_score_passes_thick_bilingual_guide() -> None:
    html = (
        "<!DOCTYPE html><div id=\"composer-en\">c</div>"
        "<div id=\"genesis-en\">g</div><div id=\"sound-en\">s</div>"
        "<div id=\"interpretations-en\">i</div><div id=\"anatomy-en\">a</div>"
        "<div id=\"practice-en\">p</div>"
        "<div data-lang=\"en\">en</div><div data-lang=\"zh-Hans\">zh</div>"
    )
    dossier = {
        "dossier_id": "catalog-floor:mendelssohn.lieder-ohne-worte",
        "_provenance": {"catalog_craft_floor": True, "knowledge_thicken": True},
        "listening_thesis": (
            "Hear a singing line over a keyboard gait first — lyric rooms, not symphony drama."
        ),
        "work_introduction": "Songs Without Words are lyric piano rooms.",
        "listening_map": [
            {"label": "Opening", "cue": "Lock the song."},
            {"label": "Middle", "cue": "Tint."},
            {"label": "Close", "cue": "Return."},
        ],
        "width_points": ["a", "b", "c"],
        "depth_points": ["d1", "d2", "d3"],
        "genesis": {"year": "1830s", "place": "salon"},
        "sound_world": {"ensemble_notes": "solo piano"},
        "composer_portrait": {"image_url": "https://example.com/x.jpg"},
        "composer_profile": {"summary": "Early Romantic lyricist"},
        "interpretations": [{"artist": "Barenboim"}],
        "zh": {
            "listening_thesis": "先听见歌唱声部与左手步态——抒情之室，而非交响戏剧。",
            "listening_map": [
                {"label": "开", "cue": "一"},
                {"label": "中", "cue": "二"},
                {"label": "收", "cue": "三"},
            ],
            "width_points": ["甲", "乙", "丙"],
        },
    }
    card = score_product(
        html=html,
        context={
            "work_title": "Felix Mendelssohn — Lieder ohne Worte (Songs Without Words)",
            "composer": "Felix Mendelssohn",
            "work_id": "mendelssohn.lieder-ohne-worte",
            "guide_html": html,
            "synthesize_source": "catalog-floor:mendelssohn.lieder-ohne-worte+knowledge-plane",
            "corpus_dossier": dossier,
        },
        dossier=dossier,
    )
    assert card.pass_ is True
    assert card.band in {"solid", "strong"}
    # catalog floor + knowledge portrait → asset_depth 2 (craft optional)
    assert card.dimensions.get("asset_depth") >= 2
    assert card.pct >= 70
