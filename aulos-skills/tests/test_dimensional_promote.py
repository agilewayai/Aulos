"""SPEC-031 dimensional templates + generic promote-to-production (anti-case)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from aulos_skills.dimension_templates import build_dimension_template
from aulos_skills.facet_classifier import classify_facets
from aulos_skills.promote_candidate import build_promote_candidate
from aulos_skills.promote_production import promote_staged_to_production
from aulos_skills.promote_staging import materialize_craft_pack, write_staging_craft
from aulos_skills.unknown_case_thicken import build_archetype_floor


CASES = [
    {
        "composer": "Clara Schumann",
        "title": "Clara Schumann — Nocturne in F major",
        "message": "Clara Schumann nocturne listening guide",
    },
    {
        "composer": "Béla Bartók",
        "title": "Béla Bartók — String Quartet No. 4",
        "message": "Bartok string quartet No. 4 listening",
    },
]


def test_dimension_template_is_facet_driven_not_work_named() -> None:
    """Same builder must thicken unrelated titles — no work_id branches."""
    floors = []
    for case in CASES:
        clf = classify_facets(
            work_title=case["title"],
            composer=case["composer"],
            raw_message=case["message"],
        )
        floor = build_dimension_template(
            case["title"],
            case["composer"],
            classification=clf,
        )
        assert floor["_provenance"]["dimension_template"] is True
        assert str(floor["dossier_id"]).startswith("dimension:")
        assert len(str(floor["listening_thesis"])) >= 40
        assert len(floor.get("listening_map") or []) >= 3
        assert str((floor.get("zh") or {}).get("listening_thesis") or "").strip()
        # Must not embed Catalog work_ids or sibling famous titles as identity
        blob = yaml.safe_dump(floor)
        assert "chopin.nocturne" not in blob
        assert "mendelssohn.lieder" not in blob
        floors.append(floor)
    # Distinct dimension ids across different facet sets
    assert floors[0]["dossier_id"] != floors[1]["dossier_id"]


def test_archetype_floor_falls_back_to_dimension_when_no_family() -> None:
    clf = classify_facets(
        work_title="Béla Bartók — String Quartet No. 4",
        composer="Béla Bartók",
        raw_message="string quartet listening",
    )
    assert clf["archetype_id"] == "chamber-generic"
    floor = build_archetype_floor(
        "Béla Bartók — String Quartet No. 4",
        "Béla Bartók",
        classification=clf,
    )
    # Dimension path (or archetype) — not empty generic scaffold
    assert floor.get("dossier_id")
    assert len(str(floor.get("listening_thesis") or "")) >= 40
    assert floor["_provenance"].get("dimension_template") or floor["_provenance"].get(
        "unknown_case_thicken"
    )


def test_promote_production_pipeline_is_case_agnostic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalog_root = tmp_path / "catalog"
    craft_root = tmp_path / "craft"
    staging_root = craft_root / "staging"
    (catalog_root / "composers").mkdir(parents=True)
    (catalog_root / "works").mkdir(parents=True)
    (catalog_root / "index.yaml").write_text(
        "composers: []\nworks: []\n", encoding="utf-8"
    )
    staging_root.mkdir(parents=True)

    monkeypatch.setattr(
        "aulos_skills.promote_staging.staging_craft_root",
        lambda: staging_root,
    )
    monkeypatch.setattr(
        "aulos_skills.promote_production.default_catalog_root",
        lambda: catalog_root,
    )
    monkeypatch.setattr(
        "aulos_skills.promote_production.craft_packs_root",
        lambda: craft_root,
    )

    reports = []
    for case in CASES:
        clf = classify_facets(
            work_title=case["title"],
            composer=case["composer"],
            raw_message=case["message"],
        )
        floor = build_archetype_floor(
            case["title"], case["composer"], classification=clf
        )
        cand = build_promote_candidate(
            work_title=case["title"],
            composer=case["composer"],
            classification=clf,
            dossier=floor,
        )
        assert cand is not None
        pack = materialize_craft_pack(
            cand,
            dossier=floor,
            composer=case["composer"],
            work_title=case["title"],
        )
        write_staging_craft(cand["suggested_work_id"], pack, overwrite=True)
        report = promote_staged_to_production(
            candidate=cand,
            composer=case["composer"],
            work_title=case["title"],
            overwrite=True,
        )
        reports.append(report)
        wid = cand["suggested_work_id"]
        assert report["work_id"] == wid
        assert (catalog_root / "works" / f"{wid}.yaml").is_file()
        assert (craft_root / f"{wid}.yaml").is_file()
        work = yaml.safe_load(
            (catalog_root / "works" / f"{wid}.yaml").read_text(encoding="utf-8")
        )
        assert work["work_id"] == wid
        assert work["facets"]["instruments"] or work["facets"]["forms"]
        assert work["family_id"]
        # Production craft must not be the only known Catalog celebrities
        assert wid not in {
            "chopin.nocturne-op9-no2",
            "mendelssohn.lieder-ohne-worte",
        }

    index = yaml.safe_load((catalog_root / "index.yaml").read_text(encoding="utf-8"))
    work_ids = {w["id"] for w in index.get("works") or []}
    assert reports[0]["work_id"] in work_ids
    assert reports[1]["work_id"] in work_ids
    assert reports[0]["work_id"] != reports[1]["work_id"]
