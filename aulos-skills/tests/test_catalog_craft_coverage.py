"""Catalog thicken uses catalog-floor + family — craft packs are promote-only."""

from __future__ import annotations

from pathlib import Path

from aulos_skills.craft_packs import list_craft_work_ids, load_craft_pack
from aulos_skills.identity import load_catalog
from aulos_skills.registry import discover_skills
from aulos_skills.runtime import SkillRuntime


def test_hand_craft_packs_not_required_for_catalog() -> None:
    """Compression: no pre-authored per-work craft YAML in the repo."""
    load_catalog.cache_clear()
    load_craft_pack.cache_clear()
    # Staging dir may exist; production craft/*.yaml should be empty pre-promote
    assert list_craft_work_ids() == []


def test_synthesize_uses_catalog_floor_without_craft() -> None:
    load_catalog.cache_clear()
    load_craft_pack.cache_clear()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]
    rt = SkillRuntime()
    cases = (
        (
            "mozart.piano-concerto-23.k-488",
            "Mozart — Piano Concerto No. 23 in A major, K. 488",
            "Wolfgang Amadeus Mozart",
        ),
        (
            "mozart.requiem.k-626",
            "Mozart — Requiem in D minor, K. 626",
            "Wolfgang Amadeus Mozart",
        ),
        (
            "mahler.symphony-5",
            "Gustav Mahler — Symphony No. 5",
            "Gustav Mahler",
        ),
    )
    for work_id, title, composer in cases:
        out = rt._run_synthesize(
            synth,
            {
                "work_id": work_id,
                "work_title": title,
                "composer_guess": composer,
                "composer": composer,
                "raw_message": f"{title} listening guide",
            },
        )
        src = str(out.get("synthesize_source") or "")
        assert f"catalog-floor:{work_id}" in src, src
        assert f"craft:{work_id}" not in src, src
        dossier = out.get("corpus_dossier") or {}
        thesis = str(dossier.get("listening_thesis") or "")
        assert len(thesis) >= 40
