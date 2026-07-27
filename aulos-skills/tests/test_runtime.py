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
        'data-lang="zh-Hans"',
        'data-lang="zh-Hant"',
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
    assert "composer-zh-Hans" in html or "composer-zh" in html
    assert "introduction-zh-Hans" in html or "introduction-zh" in html
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
        'data-lang="zh-Hans"',
        'data-lang="zh-Hant"',
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
    zh_pane = html.split('data-lang="zh-Hans"')[1].split("data-lang=")[0]
    assert "SkillRuntime" not in zh_pane
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


def test_listening_chain_bach_cello_suites_identity() -> None:
    """Solo cello suites must not inherit Goldberg keyboard or Beethoven duo shelves."""
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    polluted_kb = {
        "work_title": "J.S. Bach — Goldberg Variations, BWV 988",
        "composer": "Johann Sebastian Bach",
        "listening_thesis": "Hold the Aria bass before chasing surface figuration.",
        "work_introduction": "Open Goldberg / Ishizaka keyboard cycle.",
        "depth_points": ["Lock the Aria bass", "Glenn Gould monument"],
        "ambient_audio": {"playlist_id": "open-goldberg-ishizaka"},
        "zh": {"listening_thesis": "哥德堡咏叹调低音"},
    }
    report = runtime.run_listening_chain(
        message="我准备开始欣赏巴赫的大提琴无伴奏组曲。你帮我写一份详细的欣赏导赏",
        kb_dossier=polluted_kb,
        rag_hits=["Hold the Aria bass architecture from Goldberg BWV 988."],
        rag_mode="vector",
    )
    assert "Cello" in report.work_title or "大提琴" in report.work_title
    assert "Goldberg" not in report.work_title
    assert report.composer == "Johann Sebastian Bach"
    assert report.context.get("work_id") == "bach.cello-suites.bwv-1007-1012"
    assert "solo-cello-suites" in (report.context.get("family_hints") or [])
    html = report.guide_html
    for banned in (
        "Goldberg",
        "Aria bass",
        "哥德堡",
        "Glenn Gould",
        "Ishizaka",
        "Op. 69",
        "作品69",
        "duo citizenship",
        "二重公民权",
        "Maisky",
    ):
        assert banned not in html, f"pollution marker leaked: {banned}"
    # Explicit keyboard catalog may appear only as a negative caveat, not as identity
    assert "Hold the Aria" not in html
    assert "open-goldberg" not in html.lower()
    assert "BWV 1007" in html or "组曲" in html
    ambient = (report.context.get("corpus_dossier") or {}).get("ambient_audio") or {}
    amb_blob = str(ambient).lower()
    assert "ishizaka" not in amb_blob
    assert "goldberg" not in amb_blob
    assert "1007" in amb_blob or "cello" in amb_blob or "prelude" in amb_blob


def test_intake_solo_cello_suites_family() -> None:
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    out = runtime.run_trigger(
        "listening.intake",
        {"raw_message": "Bach unaccompanied cello suites BWV 1007-1012", "work_hint": ""},
    ).outputs
    assert out.get("work_id") == "bach.cello-suites.bwv-1007-1012"
    assert "solo-cello-suites" in (out.get("family_hints") or [])
    assert "keyboard-variations" not in (out.get("family_hints") or [])
    assert "duo-cello-piano" not in (out.get("family_hints") or [])
    assert "Goldberg" not in str(out.get("work_title"))
    assert out.get("conflict_markers")


def test_intake_chopin_and_mahler_from_catalog() -> None:
    """Productization proof: new composers resolve from catalog YAML alone."""
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    chopin = runtime.run_trigger(
        "listening.intake",
        {"raw_message": "Chopin Nocturne Op. 9 No. 2 listening guide", "work_hint": ""},
    ).outputs
    assert chopin.get("work_id") == "chopin.nocturne-op9-no2"
    mazurka = runtime.run_trigger(
        "listening.intake",
        {"raw_message": "肖邦玛祖卡详细导赏", "work_hint": ""},
    ).outputs
    assert mazurka.get("work_id") == "chopin.mazurkas"
    assert "character-dance-piano" in (mazurka.get("family_hints") or [])
    mahler = runtime.run_trigger(
        "listening.intake",
        {"raw_message": "马勒第五交响曲导赏", "work_hint": ""},
    ).outputs
    assert mahler.get("work_id") == "mahler.symphony-5"


def test_mazurka_chain_approaches_goldberg_atelier_coverage() -> None:
    """Evo bar: dance-character family ships full atelier chambers (no case hardcode)."""
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    report = runtime.run_listening_chain(
        message="我准备开始欣赏肖邦的玛祖卡。你帮我写一份详细的欣赏导赏",
    )
    assert report.context.get("work_id") == "chopin.mazurkas"
    assert "character-dance-piano" in (report.context.get("family_hints") or [])
    assert report.eval_pass
    assert report.eval_score >= 8
    html = report.guide_html
    for marker in (
        "作曲家",
        "创作背景与时代",
        "何以传世",
        "声响世界",
        "名家演绎",
        "聆听室",
        "id='composer-zh-Hans'",
        "id='genesis-zh-Hans'",
        "id='stature-zh-Hans'",
        "id='sound-zh-Hans'",
        "id='interpretations-zh-Hans'",
        "id='media-zh-Hans'",
    ):
        assert marker in html, f"missing atelier marker: {marker}"
    # No Goldberg pollution
    for banned in ("Goldberg", "哥德堡", "Glenn Gould", "Hold the Aria"):
        assert banned not in html
    # Honest Chopin peer ambient (catalog-ref), not Goldberg/Beethoven pollution
    assert "aulos-ambient" in html
    assert "Chopin" in html or "肖邦" in html
    assert "Nocturne" in html or "夜曲" in html
    assert "Goldberg" not in html
    assert "Moonlight" not in html
    assert "月光" not in html


def test_mozart_piano_concerto_discogs_path_not_beethoven_cello_family() -> None:
    """Discogs Mozart piano release must not inherit duo-cello-piano (Beethoven) chambers.

    Regression: family match scored piano+sonata=2 without composer gate → whole
    Beethoven cello pack polluted Mozart K.488/K.333 guides.
    """
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    intent = (
        "I'm listening to Wolfgang Amadeus Mozart — Piano Concerto No. 23 K. 488 "
        "• Piano Sonata K. 333 performed by Vladimir Horowitz, "
        "Orchestra Del Teatro Alla Scala, Carlo Maria Giulini "
        "(Discogs release 6280908). Write a professional listening guide."
    )
    hint = "Wolfgang Amadeus Mozart Piano Concerto No. 23 K. 488 • Piano Sonata K. 333"
    seed = {
        "work_title": "Piano Concerto No. 23 K. 488 • Piano Sonata K. 333",
        "composer": "Wolfgang Amadeus Mozart",
        "interpretations": [
            {
                "artist": "Vladimir Horowitz, Carlo Maria Giulini",
                "year": "1987",
                "why_listen": "Primary Discogs pressing",
                "discogs_url": "https://www.discogs.com/release/6280908",
            }
        ],
        "vinyl_and_discography": [
            {
                "label": "Deutsche Grammophon · 423 287-1 · 1987",
                "url": "https://www.discogs.com/release/6280908",
                "note": "Source release #6280908",
            }
        ],
        "_provenance": {"source": "discogs", "discogs": {"release_id": 6280908}},
    }
    report = runtime.run_listening_chain(
        message=intent,
        work_hint=hint,
        kb_dossier=seed,
        rag_hits=[
            "Discogs release #6280908: Horowitz Plays Mozart",
            "Composer credits: Wolfgang Amadeus Mozart",
            "Performers: Vladimir Horowitz, Carlo Maria Giulini",
        ],
        rag_mode="discogs",
    )
    assert "Mozart" in (report.composer or "") or "Mozart" in report.work_title
    assert "Beethoven" not in (report.composer or "")
    html = report.guide_html
    for banned in (
        "Op. 69",
        "Op. 102",
        "Fournier",
        "Maisky",
        "大提琴与钢琴奏鸣曲",
        "duo citizenship",
        "Cello Sonatas & Variations",
    ):
        assert banned not in html, f"pollution marker present: {banned}"
    assert "Mozart" in html or "莫扎特" in html
    synth = next(s for s in report.steps if s.id == "synthesize")
    assert "duo-cello-piano" not in (synth.detail or "")
    assert "family:duo-cello-piano" not in str(report.context.get("synthesize_source") or "")


def test_brahms_violin_concerto_not_duo_cello_family() -> None:
    """Discogs Brahms Violin Concerto Op.77 must not inherit Beethoven cello-duo pack.

    Regression (guide #44): family match scored composer brahms=+2 with zero
    instrument/form evidence → family:duo-cello-piano + Bach Suite ambient pollution.
    """
    root = Path(__file__).resolve().parents[1]
    runtime = SkillRuntime(roots=[root / "skills"])
    intent = (
        "I'm listening to Johannes Brahms — Concerto En Ré Majeur Pour Violon Et "
        "Orchestre, Op. 77 performed by Leonide Kogan "
        "(Discogs release 1830948). Write a professional listening guide."
    )
    hint = "Johannes Brahms Concerto En Ré Majeur Pour Violon Et Orchestre, Op. 77"
    seed = {
        "work_title": "Concerto En Ré Majeur Pour Violon Et Orchestre, Op. 77",
        "composer": "Johannes Brahms",
        "interpretations": [
            {
                "artist": "Leonide Kogan",
                "year": "1950s",
                "why_listen": "Primary Discogs pressing",
                "discogs_url": "https://www.discogs.com/release/1830948",
            }
        ],
        "vinyl_and_discography": [
            {
                "label": "Discogs · 1830948",
                "url": "https://www.discogs.com/release/1830948",
                "note": "Source release #1830948",
            }
        ],
        "_provenance": {"source": "discogs", "discogs": {"release_id": 1830948}},
    }
    report = runtime.run_listening_chain(
        message=intent,
        work_hint=hint,
        kb_dossier=seed,
        rag_hits=[
            "Discogs release #1830948: Brahms Violin Concerto Op.77",
            "Composer credits: Johannes Brahms",
            "Performers: Leonide Kogan",
        ],
        rag_mode="discogs",
    )
    assert "Brahms" in (report.composer or "") or "Brahms" in report.work_title
    assert "Beethoven" not in (report.composer or "")
    html = report.guide_html
    for banned in (
        "Op. 69",
        "Op. 102",
        "Fournier",
        "Maisky",
        "duo citizenship",
        "Cello Sonatas & Variations",
        "BWV 1007",
        "Cello Suite No. 1",
        "无伴奏大提琴组曲第一号",
        "大提琴与钢琴奏鸣曲",
        "Moonlight",
        "月光",
    ):
        assert banned not in html, f"pollution marker present: {banned}"
    # Bare "Beethoven" may appear only as Classical peer ambient for Mozart — not for Brahms.
    assert "Beethoven" not in html and "贝多芬" not in html
    synth = next(s for s in report.steps if s.id == "synthesize")
    assert "duo-cello-piano" not in (synth.detail or "")
    assert "family:duo-cello-piano" not in str(report.context.get("synthesize_source") or "")


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
