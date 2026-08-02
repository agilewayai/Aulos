"""SPEC-027 genre family coverage + Catalog family lock."""

from __future__ import annotations

from pathlib import Path

from aulos_skills.catalog_craft_floor import build_catalog_craft_floor
from aulos_skills.family_packs import catalog_family_id, load_family_pack
from aulos_skills.identity import load_catalog
from aulos_skills.registry import discover_skills
from aulos_skills.runtime import SkillRuntime


def test_every_catalog_work_has_registered_family() -> None:
    load_catalog.cache_clear()
    cat = load_catalog()
    missing = []
    for wid, work in cat.works.items():
        fid = work.family_id
        if not fid:
            missing.append(f"{wid}:null")
            continue
        pack = load_family_pack(fid)
        if not pack:
            missing.append(f"{wid}:{fid}:missing-pack")
        elif len(pack.get("listening_map") or []) < 3:
            missing.append(f"{wid}:{fid}:thin-map")
        elif not (pack.get("zh") or {}).get("listening_thesis"):
            missing.append(f"{wid}:{fid}:no-zh")
    assert missing == [], missing


def test_new_families_load_and_have_zh() -> None:
    for fid in (
        "piano-concerto",
        "violin-concerto",
        "sacred-requiem",
        "symphony-orchestra",
        "piano-trio",
    ):
        pack = load_family_pack(fid)
        assert pack.get("family_id") == fid
        assert len(pack.get("listening_thesis") or "") >= 40
        assert len(pack.get("listening_map") or []) >= 3
        assert (pack.get("zh") or {}).get("listening_thesis")


def test_catalog_floor_autoload_family_for_requiem() -> None:
    load_catalog.cache_clear()
    load_family_pack.cache_clear()
    floor = build_catalog_craft_floor("mozart.requiem.k-626", family=None)
    assert floor.get("dossier_id") == "catalog-floor:mozart.requiem.k-626"
    thesis = str(floor.get("listening_thesis") or "")
    assert "Requiem" in thesis or "requiem" in thesis.lower() or "ritual" in thesis.lower()
    assert "安魂" in str((floor.get("zh") or {}).get("listening_thesis") or "")
    assert catalog_family_id("mozart.requiem.k-626") == "sacred-requiem"


def test_synthesize_locks_catalog_family_for_concerto() -> None:
    load_catalog.cache_clear()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]
    out = SkillRuntime()._run_synthesize(
        synth,
        {
            "work_id": "mozart.piano-concerto-23.k-488",
            "work_title": "Wolfgang Amadeus Mozart — Piano Concerto No. 23 in A major, K. 488",
            "composer_guess": "Wolfgang Amadeus Mozart",
            "composer": "Wolfgang Amadeus Mozart",
            "raw_message": "Mozart Piano Concerto K.488 listening guide",
        },
    )
    src = str(out.get("synthesize_source") or "")
    assert "family:piano-concerto" in src
    assert "catalog-floor:mozart.piano-concerto-23.k-488" in src
    assert "composer-card" in src or "Mozart" in str(
        (out.get("corpus_dossier") or {}).get("composer") or ""
    )


def test_synthesize_symphony_and_trio_families() -> None:
    load_catalog.cache_clear()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills["aulos-listening-synthesize"]
    rt = SkillRuntime()
    for work_id, family, title, composer in (
        (
            "mahler.symphony-5",
            "symphony-orchestra",
            "Gustav Mahler — Symphony No. 5",
            "Gustav Mahler",
        ),
        (
            "dvorak.dumky-trio",
            "piano-trio",
            "Antonín Dvořák — Piano Trio No. 4 (Dumky), Op. 90",
            "Antonín Dvořák",
        ),
    ):
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
        assert f"family:{family}" in src, src
        assert f"catalog-floor:{work_id}" in src, src
