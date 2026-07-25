"""SkillRuntime unit tests for listening chain."""

from pathlib import Path

from aulos_skills.runtime import SkillRuntime


def test_listening_chain_goldberg() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    report = runtime.run_listening_chain(
        message="I'm listening to Bach Goldberg Variations to learn the masterwork"
    )
    assert "Goldberg" in report.work_title
    assert report.guide_html.startswith("<!DOCTYPE html>")
    assert report.eval_pass is True
    assert report.eval_score >= 8
    ids = [s.id for s in report.steps]
    assert "intake" in ids
    assert "corpus" in ids
    assert "width" in ids
    assert "depth" in ids
    assert "compose" in ids
    assert "eval" in ids
    assert all(s.skill_id for s in report.steps)
    assert "aulos-listening-corpus" in report.skill_versions
    assert report.skill_versions["aulos-listening-compose"].startswith("0.3")
    corpus_step = next(s for s in report.steps if s.id == "corpus")
    assert "Corpus hit" in corpus_step.detail
    html = report.guide_html
    for needle in (
        "Salon Codex",
        "Composer",
        "Genesis",
        "Why it endures",
        "Anatomy of the work",
        "Sound world",
        "Famous interpretations",
        "Glenn Gould",
        "Discogs",
        "YouTube",
        "upload.wikimedia.org",
        "Myths",
        'loading="eager"',
        'data-lang="zh"',
        'data-lang="en"',
        "作曲家",
        "何以传世",
        "作品解剖",
        "哥德堡",
        "主题",
        'id="aulos-ambient"',
        "ambient-why",
        "Kimiko_Ishizaka_-_01_-_Aria",
        "ambient-playlist",
        "data-ambient-mode=\"playlist\"",
        "aulos-ambient-playlist",
        "ambient-track",
        "Variatio 25",
        "Aria da capo",
        "/v1/media/audio",
        "data-cache-src",
        "data-proxy-src",
        "data-ambient-player",
        "ambient-mini",
        "is-collapsed",
        "说明",
    ):
        assert needle in html, f"missing Salon Codex chamber marker: {needle}"
    assert "composer-zh" in html and "introduction-zh" in html
    assert html.index("composer-zh") < html.index("introduction-zh")
    assert '<aside class="ambient' in html
    assert html.index('<aside class="ambient') < html.index('<nav class="lang-switch"')
    assert "aulos-owner-bar" not in html
    assert "Re-compose" not in html
    assert "bass architecture" in report.summary.lower() or "低音" in report.summary or "Hold the Aria" in report.summary
    assert "aulos-listening-synthesize" in report.skill_versions
    ambient = (report.context.get("corpus_dossier") or {}).get("ambient_audio") or {}
    assert ambient.get("mode") == "playlist"
    assert len(ambient.get("tracks") or []) == 32
    assert ambient.get("url") and "Kimiko_Ishizaka" in str(ambient["url"])


def test_listening_chain_beethoven_cello_zh_approaches_salon_parity() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    report = runtime.run_listening_chain(
        message="我准备开始欣赏贝多芬的大提琴、钢琴奏鸣曲和变奏曲。你帮我写一份详细的欣赏导赏"
    )
    assert "Beethoven" in report.work_title
    assert "Cello" in report.work_title
    assert report.composer == "Ludwig van Beethoven"
    assert report.context.get("synthesize_hit") is True
    assert report.eval_pass is True
    html = report.guide_html
    assert len(html) > 12000
    for needle in (
        "Salon Codex",
        "Composer",
        "upload.wikimedia.org",
        "Sound world",
        "Famous interpretations",
        "Discogs",
        "Anatomy of the work",
        "Op. 69",
        'data-lang="zh"',
        "作曲家",
        "大提琴",
        "作品69",
        "何以传世",
        'id="aulos-ambient"',
        "ambient-why",
        "BWV 1007",
        "data-cache-src",
        "position: fixed",
        "data-ambient-player",
    ):
        assert needle in html, f"missing chamber marker: {needle}"
    assert "我准备开始欣赏" not in report.work_title
    assert "SkillRuntime" not in html.split('data-lang="zh"')[1].split('data-lang="en"')[0]
    assert "Goldberg" not in html
    assert "Aria bass" not in html
    assert "哥德堡" not in html
    assert report.skill_versions["aulos-listening-synthesize"].startswith("0.2")


def test_synthesize_scrubs_goldberg_pollution_from_llm() -> None:
    """LLM/RAG must not smuggle Goldberg chambers into Beethoven cello guides."""
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    report = runtime.run_listening_chain(
        message="我准备开始欣赏贝多芬的大提琴、钢琴奏鸣曲和变奏曲",
        llm_dossier={
            "listening_thesis": "polluted",
            "work_introduction": "polluted",
            "depth_points": [
                "Lock the ear on the Aria bass before chasing surface figuration.",
                "Cello motto ownership",
            ],
            "interpretations": [
                {"artist": "Glenn Gould", "year": "1955", "why_listen": "Goldberg monument"},
                {"artist": "Maisky", "year": "1990", "why_listen": "cello fire"},
            ],
            "zh": {
                "listening_thesis": "污染",
                "work_introduction": "污染",
                "depth_points": ["哥德堡咏叹调低音", "大提琴座右铭"],
            },
        },
    )
    html = report.guide_html
    assert report.eval_pass is True
    assert "Goldberg" not in html
    assert "Aria bass" not in html
    assert "哥德堡" not in html
    assert "BWV 1007" in html or "aulos-ambient" in html
    depth = (report.context.get("depth_dossier") or {}).get("depth_points") or []
    assert depth
    assert all("Aria bass" not in str(p) for p in depth)


def test_eval_hard_fails_without_ambient() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    result = runtime.run_trigger(
        "listening.eval",
        {
            "guide_html": "<!DOCTYPE html><html><body><h1>Test</h1><p>Composer Anatomy practice listening map</p></body></html>",
            "depth_dossier": {
                "depth_points": ["Listen for the motto", "Notice the return", "Track the silence"],
                "listening_map": [{"label": "Open", "cue": "Hear the motto"}],
            },
            "corpus_hit": True,
        },
    )
    assert result.outputs.get("pass") is False
    notes = str(result.outputs.get("eval_notes") or "")
    assert "ambient" in notes.lower()


def test_listening_chain_does_not_collapse_to_goldberg() -> None:
    """Regression: wrong RAG/corpus must not rename unrelated works to Goldberg."""
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    goldberg_dossier = {
        "work_title": "J.S. Bach — Goldberg Variations, BWV 988",
        "composer": "Johann Sebastian Bach",
        "listening_thesis": "Hold the Aria bass.",
        "ambient_audio": {"url": "https://example.com/goldberg.ogg"},
    }
    report = runtime.run_listening_chain(
        message="I'm listening to Mozart Symphony No. 40",
        kb_dossier=goldberg_dossier,
        rag_hits=["Hold the Aria bass architecture."],
        rag_mode="vector",
    )
    assert "Mozart" in report.work_title
    assert "Goldberg" not in report.work_title
    assert "Bach" not in (report.composer or "")

    mass = runtime.run_trigger(
        "listening.intake",
        {"raw_message": "Bach Mass in B minor", "work_hint": ""},
    ).outputs
    assert mass.get("corpus_keys") == []
    assert "Goldberg" not in str(mass.get("work_title"))

    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    rows = runtime.list_skills(layer="domain-runtime")
    ids = {r["id"] for r in rows}
    assert "aulos-listening" in ids
    assert "aulos-listening-depth" in ids
    assert "aulos-listening-synthesize" in ids


def test_disabled_skill_is_skipped() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    report = runtime.run_listening_chain(
        message="I'm listening to Bach Goldberg Variations",
        disabled_skill_ids={"aulos-listening-eval"},
    )
    eval_step = next(s for s in report.steps if s.id == "eval")
    assert eval_step.status == "skipped"
    assert report.guide_html.startswith("<!DOCTYPE html>")


def test_iter_listening_chain_yields_steps_then_report() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    from aulos_skills.runtime import SkillRunReport, SkillStepResult

    items = list(
        runtime.iter_listening_chain(message="Bach Goldberg Variations listening guide")
    )
    assert len(items) >= 2
    assert all(isinstance(i, (SkillStepResult, SkillRunReport)) for i in items)
    assert isinstance(items[-1], SkillRunReport)
    assert any(isinstance(i, SkillStepResult) and i.id == "corpus" for i in items)
