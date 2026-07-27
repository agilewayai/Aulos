from __future__ import annotations

from urllib.parse import unquote

from aulos_skills.guide_render import render_bilingual_guide_html
from aulos_skills.media_search import (
    bilibili_search_url,
    enrich_appreciation_video,
    query_from_youtube_search_url,
)


def test_bilibili_search_url_encodes_query() -> None:
    url = bilibili_search_url("Goldberg Variations Schiff")
    assert url.startswith("https://search.bilibili.com/all?keyword=")
    assert "Goldberg" in unquote(url)


def test_query_from_youtube_search_url() -> None:
    src = "https://www.youtube.com/results?search_query=Glenn+Gould+Goldberg"
    assert "Glenn Gould Goldberg" in query_from_youtube_search_url(src).replace("+", " ")


def test_enrich_video_adds_bilibili_from_youtube_query() -> None:
    row = enrich_appreciation_video(
        {
            "title": "Gould 1981",
            "url": "https://www.youtube.com/results?search_query=Glenn+Gould+Goldberg+Variations+1981",
            "why": "benchmark reading",
        }
    )
    assert "bilibili_url" in row
    assert "search.bilibili.com" in row["bilibili_url"]
    assert "Glenn" in unquote(row["bilibili_url"])


def test_guide_html_includes_bilibili_link_for_videos() -> None:
    dossier = {
        "work_title": "Demo Work",
        "composer": "Demo Composer",
        "listening_thesis": "Listen closely.",
        "appreciation_videos": [
            {
                "title": "Lecture demo",
                "url": "https://www.youtube.com/results?search_query=Demo+Work+lecture",
                "why": "guided listening",
            }
        ],
        "zh_hans": {
            "work_title": "示范作品",
            "composer": "示范作曲家",
            "listening_thesis": "细听。",
            "appreciation_videos": [
                {
                    "title": "示范讲座",
                    "url": "https://www.youtube.com/results?search_query=Demo+Work+lecture",
                    "why": "导赏",
                }
            ],
        },
    }
    html = render_bilingual_guide_html(dossier=dossier, work_title="Demo Work", composer="Demo Composer")
    assert "search.bilibili.com" in html
    assert "哔哩哔哩" in html or "Bilibili" in html
