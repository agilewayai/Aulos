"""Product-prose hygiene — packaging titles, process locks, bilingual partition."""

from __future__ import annotations

from aulos_skills.prose_hygiene import (
    clean_packaging_work_title,
    infer_form_label,
    is_mostly_cjk,
    partition_dossier_languages,
    scrub_dossier_process_locks,
    strip_ambient_from_html,
    strip_process_locks,
)


def test_clean_packaging_title_mendelssohn_dump() -> None:
    raw = (
        "Bartholdy Lieder Ohne Worte = Songs Without Words / "
        "Romances Sans Paroles / Ges"
    )
    cleaned = clean_packaging_work_title(raw, composer="Felix Mendelssohn")
    assert "Bartholdy" not in cleaned
    assert "=" not in cleaned
    assert "/ Ges" not in cleaned
    assert "Songs Without Words" in cleaned or "Lieder ohne Worte" in cleaned


def test_clean_packaging_preserves_catalog_em_dash_and_form_noun() -> None:
    """SPEC-032: Catalog canonical titles and form nouns must survive surname peel."""
    beethoven = clean_packaging_work_title(
        "Ludwig van Beethoven — Cello Sonatas & Variations (with piano)",
        composer="Ludwig van Beethoven",
    )
    assert "Beethoven" in beethoven
    assert "Cello" in beethoven

    mozart = clean_packaging_work_title(
        "Mozart Symphony No. 40",
        composer="Wolfgang Amadeus Mozart",
    )
    assert "Symphony" in mozart
    assert "40" in mozart


def test_strip_critique_lock_from_thesis() -> None:
    dirty = (
        "CRITIQUE LOCK: richness_empty; missing_listening_map — "
        "Hear the singing line before chasing drama."
    )
    clean = strip_process_locks(dirty)
    assert "CRITIQUE LOCK" not in clean.upper()
    assert "richness_empty" not in clean
    assert "singing line" in clean


def test_partition_moves_cjk_thesis_to_zh() -> None:
    dossier = {
        "listening_thesis": "把无词歌当作一间抒情钢琴房间来听，先锁住歌唱声部与左手步态。",
        "work_introduction": "This should stay English.",
        "width_points": ["Hold the gait."],
    }
    out = partition_dossier_languages(dossier)
    assert not is_mostly_cjk(str(out.get("listening_thesis") or "") or "x")
    assert out.get("listening_thesis") == ""
    zh = out.get("zh") or {}
    assert "无词歌" in str(zh.get("listening_thesis") or "")
    assert "Hold the gait" in str((zh.get("width_points") or [""])[0])


def test_scrub_dossier_strips_review_repair() -> None:
    dossier = {
        "listening_thesis": "REVIEW REPAIR: fix map — A lyric path into Songs Without Words.",
        "myths_and_caveats": ["CRITIQUE LOCK: foo", "Keep nickname caveats."],
    }
    out = scrub_dossier_process_locks(dossier)
    assert "REVIEW REPAIR" not in str(out.get("listening_thesis") or "").upper()
    assert "lyric path" in str(out.get("listening_thesis") or "").lower()
    assert all("CRITIQUE LOCK" not in str(x).upper() for x in out["myths_and_caveats"])


def test_infer_form_rejects_large_scale_for_songs_without_words() -> None:
    form = infer_form_label(
        work_title="Lieder ohne Worte (Songs Without Words)",
        form="Large-scale work — form clarified in deep research",
    )
    assert "large-scale" not in form.lower()
    assert "miniature" in form.lower() or "songs without words" in form.lower()


def test_scrub_drops_packaging_rag_bullets() -> None:
    dossier = {
        "listening_thesis": "Hear the singing line.",
        "width_points": [
            "Hold the gait.",
            "From prior research cache: Lieder = Songs / Romances / Gesamtaufnahme = Complete Recording",
        ],
    }
    out = scrub_dossier_process_locks(dossier)
    assert len(out["width_points"]) == 1
    assert "Hold the gait" in out["width_points"][0]


def test_strip_ambient_aside() -> None:
    html = (
        '<aside class="ambient-player">noise</aside>'
        "<main><h1>Songs Without Words</h1><p>Body</p></main>"
        '<script id="aulos-ambient-boot">x</script>'
    )
    out = strip_ambient_from_html(html)
    assert "ambient-player" not in out
    assert "aulos-ambient" not in out
    assert "Songs Without Words" in out
