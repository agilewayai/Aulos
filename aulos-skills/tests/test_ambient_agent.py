"""Adaptive ambient agent selection tests."""

from pathlib import Path

from aulos_skills.ambient_agent import select_ambient
from aulos_skills.guide_render import _ambient_bar
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
        allow_video_search=False,
    )
    assert amb.get("selection_source") == "curated"
    assert len(amb.get("tracks") or []) == 32


def test_library_related_disabled_without_curated() -> None:
    amb = select_ambient(
        work_title="French Suite No. 5",
        composer="Johann Sebastian Bach",
        era="Baroque",
        form="french suite",
        facets={"instruments": ["keyboard", "harpsichord"]},
        corpus_dir=_corpus(),
        allow_video_search=False,
    )
    assert amb == {}


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
        allow_video_search=False,
    )
    assert amb.get("selection_source") == "catalog-ref"
    blob = str(amb).lower()
    assert "ishizaka" not in blob
    assert "1007" in blob or "cello" in blob or amb.get("selection_id") == "cello-as-speaker-bach-suite1"


def test_mozart_does_not_get_moonlight_standin() -> None:
    amb = select_ambient(
        work_title="Piano Concerto No. 23 K.488",
        composer="Wolfgang Amadeus Mozart",
        era="Classical",
        form="concerto",
        existing={
            "title": "Beethoven — Moonlight Sonata (I)",
            "url": "https://example.com/moonlight.ogg",
            "why": "Stand-in from open library rotation (peer classical piano).",
            "why_zh": "公开授权库轮换 stand-in",
        },
        corpus_dir=_corpus(),
        allow_video_search=False,
    )
    assert amb == {}
    assert "moonlight" not in str(amb).lower()


def test_mozart_no_defaults_rotation() -> None:
    amb = select_ambient(
        work_title="Symphony No. 40",
        composer="Wolfgang Amadeus Mozart",
        era="Classical",
        form="symphony",
        corpus_dir=_corpus(),
        allow_video_search=False,
    )
    assert amb == {}


def test_video_embed_fallback_from_concrete_url() -> None:
    amb = select_ambient(
        work_title="Piano Concerto No. 23",
        composer="Mozart",
        corpus_dir=_corpus(),
        fallback_mode="embed",
        appreciation_videos=[
            {
                "title": "K.488 performance",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            }
        ],
        allow_video_search=False,
    )
    assert amb.get("selection_source") == "video-embed"
    assert amb.get("mode") == "embed"
    assert "youtube.com/embed/dQw4w9WgXcQ" in str(amb.get("embed_src") or "")
    html = _ambient_bar(amb, default_lang="en")
    assert 'data-ambient-player="v2-embed"' in html
    assert 'id="aulos-ambient"' in html
    assert "iframe" in html


def test_video_stream_fallback_uses_extract() -> None:
    def fake_extract(url: str) -> dict | None:
        return {
            "platform": "youtube",
            "video_id": "dQw4w9WgXcQ",
            "watch_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Streamed",
            "audio_stream_url": "https://cdn.example/a.m4a",
        }

    amb = select_ambient(
        work_title="Piano Concerto No. 23",
        composer="Mozart",
        corpus_dir=_corpus(),
        fallback_mode="stream",
        appreciation_videos=[
            {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        ],
        video_extract_fn=fake_extract,
        allow_video_search=False,
    )
    assert amb.get("selection_source") == "video-stream"
    assert amb.get("url")
    assert amb.get("cache_src") or amb.get("proxy_src")


def test_compose_injects_ambient_for_catalog_work() -> None:
    runtime = SkillRuntime()
    context: dict = {
        "raw_message": "Goldberg Variations BWV 988",
        "work_title": "Goldberg Variations",
        "composer": "Johann Sebastian Bach",
        "ambient_ref": "bach-open-goldberg-full",
        "width_dossier": {},
        "depth_dossier": {},
        "corpus_dossier": {
            "work_title": "Goldberg Variations",
            "composer": "Johann Sebastian Bach",
            "ambient_audio": {"playlist_id": "open-goldberg-ishizaka"},
            "listening_thesis": "Hold the ground.",
            "zh": {"listening_thesis": "抓住低音"},
        },
    }
    runtime.run_trigger("listening.compose", context)
    html = str(context.get("guide_html") or "")
    assert "aulos-ambient" in html or "data-ambient-player" in html
