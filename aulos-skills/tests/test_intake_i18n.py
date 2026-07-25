"""Intake title/composer parsing + Hans/Hant localization."""

from aulos_skills.guide_render import render_bilingual_guide_html
from aulos_skills.i18n import LANG_ZH_HANS, to_traditional
from aulos_skills.intake_parse import guess_composer_and_title
from aulos_skills.identity import load_catalog
from aulos_skills.runtime import SkillRuntime


def test_guess_composer_from_chinese_book_title() -> None:
    cat = load_catalog()
    g = guess_composer_and_title(
        "帮我写一份德沃夏克《杜姆卡》三重奏的导赏",
        catalog_composers=cat.composers,
    )
    assert "杜姆卡" in g["work_title"]
    assert "一份" not in g["work_title"]
    assert "导赏" not in g["work_title"]
    assert "Dvořák" in g["composer"] or "德沃" in g["composer"]


def test_dumky_chain_not_unknown_composer() -> None:
    report = SkillRuntime().run_listening_chain(
        message="帮我写一份德沃夏克《杜姆卡》三重奏的导赏"
    )
    assert report.context.get("composer")
    assert "Unknown" not in str(report.context.get("composer"))
    html = str(report.context.get("guide_html") or "")
    assert "Unknown composer" not in html
    assert "Dvořák" in html or "Dvorak" in html or "德沃" in html or "德弗" in html


def test_guide_has_simplified_and_traditional_panes() -> None:
    html = render_bilingual_guide_html(
        dossier={
            "work_title": "Dumky",
            "composer": "Antonín Dvořák",
            "listening_thesis": "Hear the dumka gait.",
            "zh": {
                "listening_thesis": "先听杜姆卡的步态。",
                "work_introduction": "德沃夏克钢琴三重奏。",
                "composer": "安东宁·德沃夏克",
            },
        },
        work_title="Dumky",
        composer="Antonín Dvořák",
        default_lang=LANG_ZH_HANS,
    )
    assert 'data-lang="zh-Hans"' in html
    assert 'data-lang="zh-Hant"' in html
    assert 'data-lang="en"' in html
    assert "简体" in html and "繁体" in html
    import re

    hant = re.search(
        r'<article class="lang-pane" data-lang="zh-Hant"[^>]*>(.*?)</article>',
        html,
        re.S,
    )
    assert hant
    body = hant.group(1)
    assert "德弗札克" in body or "導" in body or "聽" in body


def test_hant_phrase_conventions() -> None:
    assert "蕭邦" in to_traditional("肖邦玛祖卡导赏")
    assert "導賞" in to_traditional("肖邦玛祖卡导赏")
    assert "德弗札克" in to_traditional("德沃夏克杜姆卡")
