"""Class gate: sibling-work drift without per-work Python branches."""

from __future__ import annotations

from aulos_skills.identity_lock import (
    build_identity_lock,
    dossier_betrays_identity_lock,
    extract_catalog_numbers,
    load_form_lock_policy,
    normalize_catalog_number,
)


def test_form_lock_policy_loads_without_mozart_hardcode() -> None:
    load_form_lock_policy.cache_clear()
    pol = load_form_lock_policy()
    assert "concerto" in (pol.get("families") or {})
    assert "sacred_mass" in (pol.get("families") or {})
    # Policy must not be a single-work patch list
    blob = str(pol).lower()
    assert "k.488" not in blob and "k488" not in blob.replace(".", "")


def test_any_piano_concerto_locks_out_requiem_aliens() -> None:
    """Beethoven / any concerto title — not only Mozart K.488."""
    lock = build_identity_lock(
        work_title="Beethoven — Piano Concerto No. 5 in E-flat major, Op. 73",
        raw_message="Listening guide for Emperor Concerto",
    )
    assert "concerto" in lock.form_families
    assert any("requiem" in m or "安魂" in m for m in lock.alien_markers)
    assert normalize_catalog_number("Op. 73") in lock.catalog_numbers or "op73" in lock.catalog_numbers


def test_betrays_when_concerto_dossier_becomes_requiem_without_catalog_work() -> None:
    """No Catalog work_id required — form + number lock alone catches the swap."""
    title = "Brahms — Violin Concerto in D major, Op. 77"
    dossier = {
        "work_title": title,
        "listening_thesis": "A piano reading of the Requiem Dies irae — 末日经.",
        "form": "Sacred Requiem mass transcription",
        "work_introduction": "安魂曲选段与落泪之日。",
    }
    assert dossier_betrays_identity_lock(dossier, work_title=title)


def test_catalog_number_swap_is_betrayal() -> None:
    title = "Mozart — Piano Concerto No. 23, K. 488"
    dossier = {
        "work_title": "Mozart Requiem",
        "listening_thesis": "Focus on K. 626 Lacrimosa architecture.",
        "form": "Requiem mass",
        "work_introduction": "Köchel 626.",
    }
    assert extract_catalog_numbers(title)
    assert dossier_betrays_identity_lock(dossier, work_title=title)


def test_honest_concerto_dossier_does_not_betray() -> None:
    title = "Mozart — Piano Concerto No. 23 in A major, K. 488"
    dossier = {
        "work_title": title,
        "listening_thesis": "Listen for the Siciliano slow movement of K. 488.",
        "form": "Piano concerto",
        "work_introduction": "Orchestra and piano dialogue in A major.",
        "related_works": [{"title": "Mozart Requiem", "why": "Same composer, different form"}],
    }
    assert not dossier_betrays_identity_lock(dossier, work_title=title)


def test_masked_foreign_catalog_still_betrays() -> None:
    """Force-copied lock numbers must not mask a foreign catalog in thesis/ZH.

    Regen class: polluted dossier keeps BWV/K. in work_title while ZH thesis
    still narrates another work's Op./catalog — recompose/review must refuse it.
    """
    title = "Bach — Concerto in D minor, BWV 1060"
    dossier = {
        "work_title": title,
        "composer": "Johann Sebastian Bach",
        "listening_thesis": "Hear the concerto dialogue; remember BWV 1060.",
        "form": "Concerto",
        "work_introduction": "Oboe and violin with strings.",
        "zh_hant": {
            "listening_thesis": "欣德米特中提琴奏鸣曲 Op.11 No.5 的复调之路。",
        },
        "width_points": ["欣德米特本人是杰出的中提琴家"],
    }
    assert dossier_betrays_identity_lock(dossier, work_title=title)
