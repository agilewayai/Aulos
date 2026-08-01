"""Ambient video fallback unit tests."""

from aulos_skills.ambient_video import (
    embed_src_for,
    normalize_fallback_mode,
    parse_video_ref,
    resolve_ambient_video,
)


def test_normalize_fallback_default_embed() -> None:
    assert normalize_fallback_mode(None) == "embed"
    assert normalize_fallback_mode("STREAM") == "stream"
    assert normalize_fallback_mode("nope") == "embed"


def test_parse_youtube_and_bilibili() -> None:
    yt = parse_video_ref("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert yt and yt["video_id"] == "dQw4w9WgXcQ"
    assert parse_video_ref("https://www.youtube.com/results?search_query=Mozart") is None
    bili = parse_video_ref("https://www.bilibili.com/video/BV1xx411c7mD")
    assert bili and bili["video_id"].startswith("BV")
    assert parse_video_ref("https://search.bilibili.com/all?keyword=x") is None


def test_embed_src_urls() -> None:
    assert "embed/abc12345678" in embed_src_for(platform="youtube", video_id="abc12345678")
    assert "bvid=BV1xx411c7mD" in embed_src_for(platform="bilibili", video_id="BV1xx411c7mD")


def test_resolve_embed_without_search() -> None:
    out = resolve_ambient_video(
        composer="Mozart",
        work_title="K.488",
        appreciation_videos=[{"url": "https://youtu.be/dQw4w9WgXcQ"}],
        fallback_mode="embed",
        allow_search=False,
    )
    assert out["mode"] == "embed"
    assert out["selection_source"] == "video-embed"
    assert "embed/dQw4w9WgXcQ" in out["embed_src"]


def test_resolve_stream_degrades_to_embed_on_extract_fail() -> None:
    def fail(_url: str):
        return None

    out = resolve_ambient_video(
        composer="Mozart",
        work_title="K.488",
        appreciation_videos=[{"url": "https://www.youtube.com/watch?v=xxxxxxxxxxx"}],
        fallback_mode="stream",
        extract_fn=fail,
        allow_search=False,
    )
    assert out["mode"] == "embed"
    assert out["selection_source"] == "video-embed"


def test_prefer_zh_orders_bilibili_first() -> None:
    out = resolve_ambient_video(
        composer="Mozart",
        work_title="K.488",
        appreciation_videos=[
            {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            {"url": "https://www.bilibili.com/video/BV1xx411c7mD"},
        ],
        fallback_mode="embed",
        prefer_zh=True,
        allow_search=False,
    )
    assert out["platform"] == "bilibili"
