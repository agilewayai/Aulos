"""IdentityResolver + Work Catalog contract tests (SPEC-008)."""

from pathlib import Path

from aulos_skills.identity import IdentityResolver, WorkCatalog, default_catalog_root, resolve_identity


def _catalog() -> WorkCatalog:
    return WorkCatalog(default_catalog_root())


def test_catalog_loads_five_works() -> None:
    cat = _catalog()
    assert "bach.goldberg.bwv-988" in cat.works
    assert "bach.cello-suites.bwv-1007-1012" in cat.works
    assert "beethoven.cello-sonatas-variations" in cat.works
    assert "chopin.nocturne-op9-no2" in cat.works
    assert "chopin.mazurkas" in cat.works
    assert "mahler.symphony-5" in cat.works
    assert "dvorak.dumky-trio" in cat.works
    assert "antonin-dvorak" in cat.composers
    assert cat.weak_tokens


def test_chopin_mazurkas_resolves_to_dance_family() -> None:
    r = resolve_identity("我准备开始欣赏肖邦的玛祖卡。你帮我写一份详细的欣赏导赏")
    assert r.status == "work"
    assert r.work_id == "chopin.mazurkas"
    assert r.family_id == "character-dance-piano"
    assert r.composer_id == "frederic-chopin"
    markers = " ".join(r.conflict_markers).lower()
    assert "nocturne" in markers or "夜曲" in markers or "9" in markers


def test_bach_cello_suites_not_goldberg() -> None:
    r = resolve_identity("我准备开始欣赏巴赫的大提琴无伴奏组曲。你帮我写一份详细的欣赏导赏")
    assert r.status == "work"
    assert r.work_id == "bach.cello-suites.bwv-1007-1012"
    assert r.family_id == "solo-cello-suites"
    assert "goldberg" not in (r.work_title or "").lower()
    markers = " ".join(r.conflict_markers).lower()
    assert "goldberg" in markers or "哥德堡" in markers or "988" in markers


def test_goldberg_resolves() -> None:
    r = resolve_identity("I'm listening to Bach Goldberg Variations BWV 988")
    assert r.status == "work"
    assert r.work_id == "bach.goldberg.bwv-988"
    assert r.corpus_keys == ["bwv-988"]


def test_beethoven_cello_duo() -> None:
    r = resolve_identity("我准备开始欣赏贝多芬的大提琴、钢琴奏鸣曲和变奏曲")
    assert r.status == "work"
    assert r.work_id == "beethoven.cello-sonatas-variations"
    assert r.family_id == "duo-cello-piano"


def test_chopin_slot_without_code_branch() -> None:
    r = resolve_identity("我想听肖邦的夜曲作品9之2")
    assert r.status == "work"
    assert r.work_id == "chopin.nocturne-op9-no2"
    assert r.composer_id == "frederic-chopin"


def test_mahler_slot_without_code_branch() -> None:
    r = resolve_identity("Help me with Mahler Symphony No. 5 listening guide")
    assert r.status == "work"
    assert r.work_id == "mahler.symphony-5"


def test_dvorak_dumky_from_chinese_book_title() -> None:
    r = resolve_identity("帮我写一份德沃夏克《杜姆卡》三重奏的导赏")
    assert r.status == "work"
    assert r.work_id == "dvorak.dumky-trio"
    assert r.composer_id == "antonin-dvorak"
    assert "Dvořák" in r.composer_name or "Dvorak" in r.composer_name or "德沃" in r.composer_name


def test_bach_alone_is_composer_only() -> None:
    r = resolve_identity("Bach")
    assert r.status in {"composer_only", "ambiguous", "unknown"}
    assert r.work_id is None or r.status != "work"


def test_bwv_alone_does_not_force_goldberg() -> None:
    r = resolve_identity("BWV")
    assert r.work_id != "bach.goldberg.bwv-988" or r.status != "work"
    if r.status == "work":
        assert r.work_id != "bach.goldberg.bwv-988"
