"""Adaptive ambient agent selection tests."""

from pathlib import Path

from aulos_skills.ambient_agent import select_ambient
from aulos_skills.identity import resolve_identity
from aulos_skills.runtime import SkillRuntime


def _corpus() -> Path:
    return Path(__file__).resolve().parents[1] / "skills" / "aulos-listening-corpus" / "assets" / "corpus"


def test_curated_goldberg_wins() -> None:
    existing = {"playlist_id": "open-goldberg-ishizaka"}
    amb = select_ambient(
        work_title="Goldberg Variations",
        composer="Bach",
        existing=existing,
        corpus_dir=_corpus(),
    )
    assert amb.get("selection_source") == "curated"
    assert len(amb.get("tracks") or []) == 32


def test_related_bach_suite_without_curated() -> None:
    amb = select_ambient(
        work_title="French Suite No. 5",
        composer="Johann Sebastian Bach",
        era="Baroque",
        form="french suite",
        facets={"instruments": ["keyboard", "harpsichord"]},
        corpus_dir=_corpus(),
    )
    assert amb.get("url") or amb.get("tracks")
    assert amb.get("selection_source") == "related"
    assert "why_zh" in amb and amb["why_zh"]
    assert "1007" not in str(amb.get("url") or "")
    assert "Cello Suite" not in str(amb.get("title") or "")


def test_solo_cello_suites_reject_goldberg_curated() -> None:
    ident = resolve_identity("巴赫大提琴无伴奏组曲")
    amb = select_ambient(
        work_title=ident.work_title,
        composer=ident.composer_name,
        family_hints=[ident.family_id] if ident.family_id else [],
        facets=ident.facets,
        ambient_ref=ident.ambient_ref,
        conflict_markers=ident.conflict_markers,
        existing={"playlist_id": "open-goldberg-ishizaka"},
        corpus_dir=_corpus(),
    )
    assert amb.get("selection_source") in {"related", "default", "catalog-ref"}
    blob = str(amb).lower()
    assert "ishizaka" not in blob
    assert "1007" in blob or "cello" in blob or amb.get("selection_id") == "cello-as-speaker-bach-suite1"


def test_mozart_gets_classical_peer_or_default() -> None:
    amb = select_ambient(
        work_title="Symphony No. 40",
        composer="Wolfgang Amadeus Mozart",
        era="Classical",
        form="symphony",
        corpus_dir=_corpus(),
    )
    assert amb.get("url")
    assert amb.get("selection_source") in {"related", "default"}
    assert amb.get("why") and amb.get("why_zh")


def test_default_rotation_is_stable_per_work() -> None:
    a = select_ambient(work_title="Unknown Lyric Poem", composer="", corpus_dir=_corpus())
    b = select_ambient(work_title="Unknown Lyric Poem", composer="", corpus_dir=_corpus())
    assert a.get("selection_id") == b.get("selection_id")
    assert a.get("selection_source") == "default"


def test_compose_injects_ambient_why_for_cold_work() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    report = runtime.run_listening_chain(message="I'm listening to Mozart Symphony No. 40")
    assert "Mozart" in report.work_title
    html = report.guide_html
    assert "ambient-why" in html
    assert "aulos-ambient" in html
