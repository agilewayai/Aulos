"""SPEC-030 promote staging craft write."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from aulos_skills.facet_classifier import classify_facets
from aulos_skills.promote_candidate import build_promote_candidate
from aulos_skills.promote_staging import (
    materialize_craft_pack,
    staging_craft_root,
    validate_work_id,
    write_staging_craft,
)
from aulos_skills.unknown_case_thicken import build_archetype_floor


def test_validate_work_id_rejects_traversal() -> None:
    assert validate_work_id("schumann.nocturne-in-f") is True
    assert validate_work_id("../etc/passwd") is False
    assert validate_work_id("Schumann.Nocturne") is False
    assert validate_work_id("") is False


def test_write_staging_craft_under_staging_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "aulos_skills.promote_staging.staging_craft_root",
        lambda: tmp_path / "staging",
    )
    pack = {
        "work_id": "schumann.nocturne-in-f",
        "composer": "Clara Schumann",
        "listening_thesis": "Hear the nocturne as one lyric piano room — lock cantabile first.",
        "listening_map": [
            {"label": "Opening", "cue": "a"},
            {"label": "Middle", "cue": "b"},
            {"label": "Close", "cue": "c"},
        ],
        "zh": {"listening_thesis": "把夜曲当作抒情之室。"},
    }
    path = write_staging_craft("schumann.nocturne-in-f", pack)
    assert path.parent == tmp_path / "staging"
    assert path.is_file()
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert loaded["work_id"] == "schumann.nocturne-in-f"
    assert loaded["_provenance"]["promote_staged"] is True


def test_materialize_from_promote_candidate() -> None:
    clf = classify_facets(
        work_title="Clara Schumann — Nocturne in F major",
        composer="Clara Schumann",
        raw_message="Clara Schumann nocturne",
    )
    floor = build_archetype_floor(
        "Clara Schumann — Nocturne in F major",
        "Clara Schumann",
        classification=clf,
    )
    cand = build_promote_candidate(
        work_title="Clara Schumann — Nocturne in F major",
        composer="Clara Schumann",
        classification=clf,
        dossier=floor,
    )
    assert cand is not None
    pack = materialize_craft_pack(
        cand,
        dossier=floor,
        composer="Clara Schumann",
        work_title="Clara Schumann — Nocturne in F major",
    )
    assert pack["work_id"] == cand["suggested_work_id"]
    assert pack["family_id"] == "lyric-piano-miniatures"
    assert len(str(pack["listening_thesis"])) >= 40
    assert len(pack.get("listening_map") or []) >= 3


def test_classifier_prelude_and_string_quartet() -> None:
    prelude = classify_facets(
        work_title="Alexander Scriabin — Prelude Op. 11 No. 1",
        composer="Alexander Scriabin",
        raw_message="Scriabin prelude listening guide",
    )
    assert prelude["archetype_id"] == "lyric-piano-miniatures"
    assert any("prelude" in f for f in prelude["forms"])
    assert prelude["confidence"] >= 0.4

    quartet = classify_facets(
        work_title="Béla Bartók — String Quartet No. 4",
        composer="Béla Bartók",
        raw_message="Bartok string quartet listening",
    )
    assert "quartet" in quartet["forms"] or "strings" in quartet["instruments"]
    assert quartet["archetype_id"] == "chamber-generic"
    assert quartet["confidence"] >= 0.4


def test_staging_root_is_under_craft() -> None:
    root = staging_craft_root()
    assert root.name == "staging"
    assert root.parent.name == "craft"
