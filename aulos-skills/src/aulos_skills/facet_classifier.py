"""FacetClassifier — title/message → instruments/forms/era + archetype_id (SPEC-029)."""

from __future__ import annotations

from typing import Any

# Data-driven token tables — no work-name branches.
_INSTRUMENT_TOKENS: dict[str, tuple[str, ...]] = {
    "piano": ("piano", "pianoforte", "keyboard", "钢琴", "鍵盤", "键盘"),
    "cello": ("cello", "violoncello", "大提琴"),
    "violin": ("violin", "小提琴"),
    "viola": ("viola", "中提琴"),
    "oboe": ("oboe", "双簧管"),
    "strings": ("string quartet", "string trio", "弦乐四重奏", "弦乐", "strings"),
    "orchestra": ("orchestra", "symphony orchestra", "管弦", "乐团", "交響"),
    "voice": ("requiem", "mass", "choir", "chorus", "合唱", "弥撒", "安魂"),
}

_FORM_TOKENS: dict[str, tuple[str, ...]] = {
    "nocturne": ("nocturne", "nocturnes", "夜曲"),
    "songs-without-words": (
        "songs without words",
        "lieder ohne worte",
        "romances sans paroles",
        "无词歌",
        "无言歌",
    ),
    "character-piece": (
        "intermezzo",
        "intermezzi",
        "character piece",
        "lyric miniature",
        "小品",
    ),
    "prelude": ("prelude", "preludes", "prélude", "préludes", "前奏曲"),
    "etude": ("etude", "etudes", "étude", "études", "study", "studies", "练习曲"),
    "ballade": ("ballade", "ballades", "叙事曲"),
    "impromptu": ("impromptu", "impromptus", "即兴曲"),
    "fantasy": ("fantaisie", "fantasia", "fantasy", "幻想曲"),
    "mazurka": ("mazurka", "mazurkas", "玛祖卡"),
    "polonaise": ("polonaise", "polonaises", "波罗乃兹"),
    "waltz": ("waltz", "waltzes", "圆舞曲", "华尔兹"),
    "variation": ("variation", "variations", "变奏"),
    "suite": ("suite", "suites", "组曲"),
    "sonata": ("sonata", "sonatas", "sonate", "sonaten", "奏鸣曲"),
    "rondo": ("rondo", "rondos", "rondò", "rondòs", "回旋曲"),
    "concerto": ("concerto", "concerti", "协奏曲"),
    "symphony": ("symphony", "symphonies", "交响曲", "交響曲"),
    "requiem": ("requiem", "安魂曲"),
    "trio": ("trio", "piano trio", "三重奏"),
    "quartet": ("string quartet", "quartet", "quartets", "四重奏"),
    "duo": ("duo", "sonata for cello", "cello sonata", "二重奏"),
}

_ERA_TOKENS: dict[str, tuple[str, ...]] = {
    "baroque": ("baroque", "巴洛克"),
    "classical": ("classical", "古典"),
    "romantic": ("romantic", "浪漫"),
    "modern": ("modern", "20th", "contemporary", "现代"),
}

# (archetype_id, required_instrument_keys, required_form_keys, score_boost)
_ARCHETYPE_RULES: tuple[tuple[str, frozenset[str], frozenset[str], float], ...] = (
    ("sacred-requiem", frozenset(), frozenset({"requiem"}), 0.35),
    # Non-piano concertos must outrank piano-concerto soft unlock (SPEC-033).
    (
        "violin-concerto",
        frozenset({"violin"}),
        frozenset({"concerto"}),
        0.36,
    ),
    (
        "oboe-concerto",
        frozenset({"oboe"}),
        frozenset({"concerto"}),
        0.36,
    ),
    ("piano-concerto", frozenset({"piano"}), frozenset({"concerto"}), 0.35),
    ("symphony-orchestra", frozenset({"orchestra"}), frozenset({"symphony"}), 0.35),
    ("piano-trio", frozenset({"piano"}), frozenset({"trio"}), 0.3),
    # Solo keyboard sonata/rondo must outrank duo when cello is absent (SPEC-032).
    (
        "solo-piano-sonata",
        frozenset({"piano"}),
        frozenset({"sonata", "rondo"}),
        0.34,
    ),
    (
        "duo-cello-piano",
        frozenset({"cello", "piano"}),
        frozenset({"duo", "sonata"}),
        0.3,
    ),
    ("solo-cello-suites", frozenset({"cello"}), frozenset({"suite"}), 0.3),
    ("keyboard-variations", frozenset({"piano"}), frozenset({"variation"}), 0.3),
    (
        "character-dance-piano",
        frozenset({"piano"}),
        frozenset({"mazurka", "polonaise", "waltz"}),
        0.3,
    ),
    (
        "lyric-piano-miniatures",
        frozenset({"piano"}),
        frozenset(
            {
                "nocturne",
                "songs-without-words",
                "character-piece",
                "prelude",
                "etude",
                "ballade",
                "impromptu",
                "fantasy",
            }
        ),
        0.35,
    ),
)

_FALLBACK = "chamber-generic"


def _blob(*parts: str) -> str:
    return " ".join(p for p in parts if p).lower()


def _match_keys(table: dict[str, tuple[str, ...]], blob: str) -> list[str]:
    hits: list[str] = []
    for key, tokens in table.items():
        if any(t and t in blob for t in tokens):
            hits.append(key)
    return hits


def classify_facets(
    *,
    work_title: str = "",
    composer: str = "",
    raw_message: str = "",
    facets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return instruments/forms/era + archetype_id + confidence (no Catalog required)."""
    seeded = dict(facets or {})
    blob = _blob(work_title, composer, raw_message)

    instruments = list(seeded.get("instruments") or [])
    if not instruments:
        instruments = _match_keys(_INSTRUMENT_TOKENS, blob)
    else:
        instruments = [str(x) for x in instruments if x]

    forms = list(seeded.get("forms") or [])
    if not forms:
        forms = _match_keys(_FORM_TOKENS, blob)
    else:
        forms = [str(x) for x in forms if x]

    era = ""
    seeded_era = seeded.get("era")
    if isinstance(seeded_era, list) and seeded_era:
        era = str(seeded_era[0])
    elif isinstance(seeded_era, str) and seeded_era.strip():
        era = seeded_era.strip()
    if not era:
        eras = _match_keys(_ERA_TOKENS, blob)
        era = eras[0] if eras else ""

    inst_set = frozenset(instruments)
    form_set = frozenset(forms)

    best_id = _FALLBACK
    best_score = 0.0
    for arch_id, need_inst, need_form, boost in _ARCHETYPE_RULES:
        if need_inst and not (need_inst & inst_set):
            # Soft: piano forms often omit explicit "piano" in title — allow form-only
            # when the archetype is piano-family and title lacks other instruments.
            piano_family = arch_id in {
                "lyric-piano-miniatures",
                "character-dance-piano",
                "keyboard-variations",
                "piano-concerto",
                "solo-piano-sonata",
            }
            # Duo packs must never soft-unlock without cello evidence (SPEC-032).
            if arch_id == "duo-cello-piano":
                continue
            # SPEC-033: never soft-unlock piano-concerto when another soloist is present.
            other_solo = inst_set & {
                "violin",
                "viola",
                "cello",
                "oboe",
                "voice",
            }
            if arch_id == "piano-concerto" and other_solo:
                continue
            if not (piano_family and need_form & form_set and not (inst_set - {"piano", "orchestra", "strings"})):
                continue
            if "piano" not in instruments:
                instruments = ["piano", *instruments]
                inst_set = frozenset(instruments)
        if need_form and not (need_form & form_set):
            continue
        # Duo still requires cello even when piano+sonata are present.
        if arch_id == "duo-cello-piano" and "cello" not in inst_set:
            continue
        score = boost
        score += 0.15 * len(need_form & form_set)
        score += 0.1 * len(need_inst & inst_set)
        if score > best_score:
            best_score = score
            best_id = arch_id

    title = (work_title or "").strip()
    if best_id == _FALLBACK:
        # Unknown titled work still gets a chamber floor (≥0.4 so synthesize can use it).
        confidence = 0.45 if title else 0.2
    else:
        confidence = min(0.95, 0.4 + best_score)
        if not instruments and forms:
            confidence = max(confidence, 0.55)
        if instruments and forms:
            confidence = max(confidence, 0.7)

    return {
        "instruments": instruments,
        "forms": forms,
        "era": era,
        "archetype_id": best_id,
        "confidence": round(confidence, 3),
    }
