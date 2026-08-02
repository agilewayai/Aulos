"""Dimensional Salon templates — instruments × forms × era (SPEC-031).

Higher-dimensional thicken: no per-work branches. Named family YAML remains an
optional accelerator loaded elsewhere.
"""

from __future__ import annotations

from typing import Any

from aulos_skills.prose_hygiene import infer_form_label
from aulos_skills.salon_codex import coerce_dict


def _short_title(canonical: str, composer: str) -> str:
    t = (canonical or "").strip()
    if not t:
        return ""
    if composer and t.lower().startswith(composer.lower()):
        rest = t[len(composer) :].lstrip(" —–-")
        return rest or t
    if "—" in t:
        return t.split("—", 1)[-1].strip()
    return t


# Voice tables — dimensional, not work-named.
INSTRUMENT_VOICES: dict[str, dict[str, str]] = {
    "piano": {
        "label_en": "keyboard",
        "label_zh": "键盘",
        "thesis_en": "singing line and left-hand gait on the keyboard",
        "thesis_zh": "键盘上的如歌声部与左手步态",
        "map_open_en": "Lock cantabile and gait before ornament.",
        "map_open_zh": "装饰之前先锁住如歌与步态。",
    },
    "cello": {
        "label_en": "solo cello",
        "label_zh": "大提琴",
        "thesis_en": "bow speech and open-string gravity on cello",
        "thesis_zh": "大提琴的弓语与空弦重力",
        "map_open_en": "Lock the first bow character and drone.",
        "map_open_zh": "先锁住第一弓性格与低音。",
    },
    "violin": {
        "label_en": "violin",
        "label_zh": "小提琴",
        "thesis_en": "bow rhetoric and register lift on violin",
        "thesis_zh": "小提琴的弓法修辞与音区抬升",
        "map_open_en": "Lock the opening bow motive.",
        "map_open_zh": "先锁住开场弓动机。",
    },
    "oboe": {
        "label_en": "oboe",
        "label_zh": "双簧管",
        "thesis_en": "reed speech and breath line on oboe",
        "thesis_zh": "双簧管的簧片言语与气息线条",
        "map_open_en": "Lock the first reed entry character.",
        "map_open_zh": "先锁住第一声簧片进入性格。",
    },
    "viola": {
        "label_en": "viola",
        "label_zh": "中提琴",
        "thesis_en": "alto-register bow speech on viola",
        "thesis_zh": "中提琴中音声区的弓语",
        "map_open_en": "Lock the viola's opening speaking register.",
        "map_open_zh": "先锁住中提琴开场的言说音区。",
    },
    "strings": {
        "label_en": "string ensemble",
        "label_zh": "弦乐",
        "thesis_en": "inner-voice conversation across the string body",
        "thesis_zh": "弦乐声部之间的内声部对话",
        "map_open_en": "Lock which voice owns the first argument.",
        "map_open_zh": "先认出谁拥有第一论点。",
    },
    "orchestra": {
        "label_en": "orchestra",
        "label_zh": "管弦乐",
        "thesis_en": "orchestral color and sectional dialogue",
        "thesis_zh": "管弦音色与声部对话",
        "map_open_en": "Lock the opening color and pulse.",
        "map_open_zh": "先锁住开场音色与脉搏。",
    },
    "voice": {
        "label_en": "voices",
        "label_zh": "人声",
        "thesis_en": "choral/solo speech and liturgical architecture",
        "thesis_zh": "合唱／独唱言语与礼拜结构",
        "map_open_en": "Lock the first vocal character.",
        "map_open_zh": "先锁住第一人声性格。",
    },
}

FORM_VOICES: dict[str, dict[str, str]] = {
    "nocturne": {
        "label_en": "nocturne",
        "label_zh": "夜曲",
        "contract_en": "one lyric night-room, not a dance set",
        "contract_zh": "一间抒情夜室，而非舞曲集",
    },
    "prelude": {
        "label_en": "prelude",
        "label_zh": "前奏曲",
        "contract_en": "a compact character cell that teaches a single idea",
        "contract_zh": "教授单一观念的紧凑性格细胞",
    },
    "etude": {
        "label_en": "étude",
        "label_zh": "练习曲",
        "contract_en": "a craft problem heard as music, not gym alone",
        "contract_zh": "把工艺问题听成音乐，而非纯体操",
    },
    "ballade": {
        "label_en": "ballade",
        "label_zh": "叙事曲",
        "contract_en": "narrative rooms under one rhetorical arc",
        "contract_zh": "同一修辞弧下的叙事房间",
    },
    "quartet": {
        "label_en": "string quartet",
        "label_zh": "弦乐四重奏",
        "contract_en": "four-voice argument, not orchestral mass",
        "contract_zh": "四声部论辩，而非管弦团块",
    },
    "concerto": {
        "label_en": "concerto",
        "label_zh": "协奏曲",
        "contract_en": "solo–tutti rhetoric across movements",
        "contract_zh": "跨乐章的独奏－全奏修辞",
    },
    "symphony": {
        "label_en": "symphony",
        "label_zh": "交响曲",
        "contract_en": "orchestral argument across a multi-movement arc",
        "contract_zh": "多乐章弧线上的管弦论辩",
    },
    "suite": {
        "label_en": "suite",
        "label_zh": "组曲",
        "contract_en": "linked rooms that share a body, not one sonata war",
        "contract_zh": "共享身体的连结房间，而非单一奏鸣曲战争",
    },
    "sonata": {
        "label_en": "sonata",
        "label_zh": "奏鸣曲",
        "contract_en": "argument across movements under one tonal identity",
        "contract_zh": "同一调性身份下跨乐章的论辩",
    },
    "rondo": {
        "label_en": "rondo",
        "label_zh": "回旋曲",
        "contract_en": "refrain returns that remember the opening character",
        "contract_zh": "记住开场性格的叠句回归",
    },
    "trio": {
        "label_en": "trio",
        "label_zh": "三重奏",
        "contract_en": "three-voice chamber speech",
        "contract_zh": "三声部室内言语",
    },
    "requiem": {
        "label_en": "requiem",
        "label_zh": "安魂曲",
        "contract_en": "liturgical architecture and mourning speech",
        "contract_zh": "礼拜结构与哀悼言语",
    },
    "songs-without-words": {
        "label_en": "songs without words",
        "label_zh": "无词歌",
        "contract_en": "sung speech without text on the keyboard",
        "contract_zh": "键盘上无歌词的歌唱言语",
    },
    "variation": {
        "label_en": "variations",
        "label_zh": "变奏",
        "contract_en": "one theme revised under changing masks",
        "contract_zh": "同一主题在变化面具下被改写",
    },
}

ERA_VOICES: dict[str, dict[str, str]] = {
    "baroque": {"en": "Baroque rhetorical grammar", "zh": "巴洛克修辞语法"},
    "classical": {"en": "Classical clarity and proportion", "zh": "古典清晰与比例"},
    "romantic": {"en": "Romantic salon/recital culture", "zh": "浪漫主义沙龙／独奏文化"},
    "modern": {"en": "modern / 20th-c. listening contracts", "zh": "现代／二十世纪聆听契约"},
}

_DEFAULT_INST = {
    "label_en": "ensemble",
    "label_zh": "编制",
    "thesis_en": "opening character and primary motive",
    "thesis_zh": "开场性格与主要动机",
    "map_open_en": "Lock the opening character first.",
    "map_open_zh": "先锁住开场性格。",
}

_DEFAULT_FORM = {
    "label_en": "chamber form",
    "label_zh": "室内曲式",
    "contract_en": "a focused listening room under one identity",
    "contract_zh": "同一身份下的专注聆听房间",
}


def _primary(items: list[str], preferred: tuple[str, ...]) -> str:
    for p in preferred:
        if p in items:
            return p
    return items[0] if items else ""


def build_dimension_template(
    work_title: str,
    composer: str,
    *,
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compose a family-shaped dossier from facet dimensions only."""
    clf = dict(classification or {})
    instruments = [str(x) for x in (clf.get("instruments") or []) if x]
    forms = [str(x) for x in (clf.get("forms") or []) if x]
    era = str(clf.get("era") or "").strip().lower()
    title = (work_title or "").strip()
    name = (composer or "").strip()
    short = _short_title(title, name) or title or "this work"

    inst_key = _primary(
        instruments,
        ("piano", "cello", "violin", "strings", "orchestra", "voice"),
    )
    form_key = _primary(
        forms,
        (
            "nocturne",
            "songs-without-words",
            "prelude",
            "etude",
            "ballade",
            "impromptu",
            "fantasy",
            "quartet",
            "concerto",
            "symphony",
            "suite",
            "trio",
            "requiem",
            "variation",
            "mazurka",
            "sonata",
            "duo",
        ),
    )
    # Map near-forms onto closest voice
    form_alias = {
        "impromptu": "prelude",
        "fantasy": "ballade",
        "character-piece": "nocturne",
        "mazurka": "nocturne",
        "polonaise": "nocturne",
        "waltz": "nocturne",
        "sonata": "suite",
        "duo": "trio",
    }
    form_voice_key = form_alias.get(form_key, form_key)

    inst = INSTRUMENT_VOICES.get(inst_key, _DEFAULT_INST)
    form = FORM_VOICES.get(form_voice_key, _DEFAULT_FORM)
    era_v = ERA_VOICES.get(era, {"en": "", "zh": ""})

    form_label = infer_form_label(
        work_title=title,
        form=str(form.get("label_en") or ""),
        facets={"instruments": instruments, "forms": forms, "era": era},
    )
    dim_id = f"{inst_key or 'ensemble'}+{form_key or 'form'}"

    thesis = (
        f"In {short}: hear {inst['thesis_en']} — {form['contract_en']}; "
        "lock the opening character before chasing ornament or legend."
    )
    thesis_zh = (
        f"就{short}而言：听见{inst['thesis_zh']}——{form['contract_zh']}；"
        "追装饰或传说之前先锁住开场性格。"
    )
    if era_v.get("en"):
        thesis += f" Frame it inside {era_v['en']}."
    if era_v.get("zh"):
        thesis_zh += f" 放回{era_v['zh']}。"

    intro = (
        f"{title or short} — dimensional thicken from facets "
        f"({inst['label_en']} × {form['label_en']}). "
        "Treat ear cues as identity; packaging titles stay reception caveats."
    )
    intro_zh = (
        f"{title or short}。由维度（{inst['label_zh']}×{form['label_zh']}）合成的聆听地板。"
        "以耳部线索为身份；包装标题保留为接受史存疑。"
    )

    out: dict[str, Any] = {
        "family_id": str(clf.get("archetype_id") or "chamber-generic"),
        "work_title": title,
        "composer": name,
        "era": era or "",
        "form": form_label,
        "listening_thesis": thesis,
        "work_introduction": intro,
        "listening_map": [
            {"label": "Opening", "cue": inst["map_open_en"]},
            {
                "label": "Middle",
                "cue": f"Contrast or episodic turn inside the same {form['label_en']}.",
            },
            {"label": "Close", "cue": "How the return remembers the opening character."},
        ],
        "width_points": [
            f"Frame {short} in biography, publication, and reception.",
            f"State the {inst['label_en']} and era of the recording.",
            f"Keep peer {form['label_en']} works as comparison, not identity swaps.",
        ],
        "depth_points": [
            f"Identify the unit the ear locks onto first ({inst['label_en']}).",
            f"Map landmarks that prove the {form['contract_en']}.",
            "Notice how the close remembers or revises the opening.",
        ],
        "practice_notes": [
            "One hearing with a single facet question.",
            "Second hearing with a three-cue landmark list.",
        ],
        "myths_and_caveats": [
            "Dimension template — verify anecdotes before stating as fact.",
            "Discogs packaging titles are not IntentLock work titles.",
        ],
        "zh": {
            "work_title": title,
            "composer": name,
            "listening_thesis": thesis_zh,
            "work_introduction": intro_zh,
            "listening_map": [
                {"label": "开场", "cue": inst["map_open_zh"]},
                {"label": "中段", "cue": f"同一{form['label_zh']}内的对比或插部转折。"},
                {"label": "收束", "cue": "再现如何记得开场性格。"},
            ],
            "width_points": [
                f"把{short}放回传记、出版与接受史。",
                f"说明录音的{inst['label_zh']}与时代。",
                f"把同族{form['label_zh']}作品保留为比较，而非身份替换。",
            ],
            "depth_points": [
                f"先认出耳朵锁定的最小单位（{inst['label_zh']}）。",
                f"画出证明「{form['contract_zh']}」的地标。",
                "注意收束如何记得或改写开场。",
            ],
        },
        "dossier_id": f"dimension:{dim_id}",
        "raw_format": "dimension-template",
        "_provenance": {
            "dimension_template": True,
            "instruments": instruments,
            "forms": forms,
            "era": era,
            "dimension_id": dim_id,
        },
    }
    return out
