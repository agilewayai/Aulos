"""SPEC-029 Unknown-Case Thicken Loop v1."""

from __future__ import annotations

from pathlib import Path

from aulos_skills.facet_classifier import classify_facets
from aulos_skills.promote_candidate import build_promote_candidate
from aulos_skills.registry import discover_skills
from aulos_skills.runtime import SkillRuntime
from aulos_skills.unknown_case_thicken import build_archetype_floor


def test_facet_classifier_nocturne_to_lyric_piano() -> None:
    hit = classify_facets(
        work_title="Clara Schumann — Nocturne in F major",
        composer="Clara Schumann",
        raw_message="listening guide for Clara Schumann nocturne",
    )
    assert hit["archetype_id"] == "lyric-piano-miniatures"
    assert "piano" in hit["instruments"]
    assert any("nocturne" in f for f in hit["forms"])
    assert hit["confidence"] >= 0.4


def test_facet_classifier_unknown_falls_to_chamber_generic() -> None:
    hit = classify_facets(
        work_title="An Obscure Chamber Fancy Op. 12",
        composer="Ada Lovelace",
        raw_message="please write a listening guide",
    )
    assert hit["archetype_id"] == "chamber-generic"
    assert hit["confidence"] >= 0.4


def test_archetype_floor_binds_title_and_zh() -> None:
    classification = classify_facets(
        work_title="Gabriel Fauré — Nocturne No. 6",
        composer="Gabriel Fauré",
        raw_message="Fauré nocturne listening",
    )
    floor = build_archetype_floor(
        "Gabriel Fauré — Nocturne No. 6",
        "Gabriel Fauré",
        classification=classification,
    )
    assert floor.get("dossier_id") == "archetype:lyric-piano-miniatures"
    assert floor["_provenance"]["unknown_case_thicken"] is True
    thesis = str(floor.get("listening_thesis") or "")
    assert len(thesis) >= 40
    assert "Nocturne" in thesis or "nocturne" in thesis.lower() or "Fauré" in thesis
    assert len(floor.get("listening_map") or []) >= 3
    zh = floor.get("zh") or {}
    assert str(zh.get("listening_thesis") or "").strip()


def test_synthesize_unknown_title_uses_archetype_not_generic_scaffold() -> None:
    """Non-Catalog title must still thicken via archetype: (REQ-019)."""
    rt = SkillRuntime()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills.get("aulos-listening-synthesize")
    assert synth is not None
    out = rt._run_synthesize(
        synth,
        {
            "work_title": "Clara Schumann — Nocturne in F major",
            "composer_guess": "Clara Schumann",
            "composer": "Clara Schumann",
            "raw_message": "Clara Schumann Nocturne in F major listening guide",
            # Explicitly no Catalog work_id
        },
    )
    src = str(out.get("synthesize_source") or "")
    assert "archetype:" in src
    assert "generic-scaffold" not in src
    dossier = out.get("corpus_dossier") or {}
    thesis = str(dossier.get("listening_thesis") or "")
    assert len(thesis) >= 40
    assert dossier.get("composer") == "Clara Schumann"


def test_promote_candidate_dry_run_schema() -> None:
    classification = classify_facets(
        work_title="Clara Schumann — Nocturne in F major",
        composer="Clara Schumann",
        raw_message="Clara Schumann nocturne",
    )
    floor = build_archetype_floor(
        "Clara Schumann — Nocturne in F major",
        "Clara Schumann",
        classification=classification,
    )
    cand = build_promote_candidate(
        work_title="Clara Schumann — Nocturne in F major",
        composer="Clara Schumann",
        classification=classification,
        dossier=floor,
    )
    assert cand is not None
    assert cand["schema"] == "aulos.promote_candidate/v1"
    assert cand["dry_run"] is True
    assert cand["family_id"] == "lyric-piano-miniatures"
    assert cand["suggested_work_id"]
    assert "nocturne" in cand["suggested_work_id"] or "schumann" in cand["suggested_work_id"]
    draft = cand["craft_draft"]
    assert len(str(draft.get("listening_thesis") or "")) >= 40
    assert cand["gates"]["chamber_floor"] is True


def test_synthesize_emits_promote_candidate_on_archetype_path() -> None:
    rt = SkillRuntime()
    root = Path(__file__).resolve().parents[1]
    skills = {s.skill_id: s for s in discover_skills([root / "skills"])}
    synth = skills.get("aulos-listening-synthesize")
    assert synth is not None
    out = rt._run_synthesize(
        synth,
        {
            "work_title": "Clara Schumann — Nocturne in F major",
            "composer_guess": "Clara Schumann",
            "composer": "Clara Schumann",
            "raw_message": "Clara Schumann Nocturne listening guide",
        },
    )
    assert "archetype:" in str(out.get("synthesize_source") or "")
    cand = out.get("promote_candidate")
    assert isinstance(cand, dict)
    assert cand.get("dry_run") is True
    assert cand.get("schema") == "aulos.promote_candidate/v1"
