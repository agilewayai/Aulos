"""Catalog-derived craft floor — systemic thickness without per-work YAML (SPEC-026)."""

from __future__ import annotations

from typing import Any

from aulos_skills.identity import load_catalog
from aulos_skills.prose_hygiene import infer_form_label
from aulos_skills.salon_codex import coerce_dict, empty_dossier, family_to_dossier


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


def _facet_era(facets: dict[str, Any]) -> str:
    era = facets.get("era")
    if isinstance(era, list) and era:
        return str(era[0])
    if isinstance(era, str):
        return era
    return ""


def build_catalog_craft_floor(
    work_id: str,
    *,
    family: dict[str, Any] | None = None,
    composer_name: str = "",
    work_title: str = "",
) -> dict[str, Any]:
    """Bind Catalog work + family into a work-specific Salon floor."""
    wid = (work_id or "").strip()
    if not wid:
        return {}
    cat = load_catalog()
    work = cat.works.get(wid)
    if work is None:
        return {}

    composer = cat.composers.get(work.composer_id) if work.composer_id else None
    name_en = (composer_name or (composer.name_en if composer else "") or "").strip()
    title = (work_title or str(work.canonical_title or "") or "").strip()
    short = _short_title(title, name_en) or title or wid
    facets = dict(work.facets or {})
    composer_raw = dict(composer.raw or {}) if composer else {}

    fam = dict(family or {})
    if not fam:
        # SPEC-027: auto-load Catalog family_id when caller omits family
        fid = str(work.family_id or "")
        if fid:
            from aulos_skills.family_packs import load_family_pack

            fam = load_family_pack(fid)
    if fam:
        base = family_to_dossier(fam, composer=name_en, work_title=title)
    else:
        base = empty_dossier()
        base["work_title"] = title
        base["composer"] = name_en
        base["form"] = infer_form_label(work_title=title, form="", facets=facets)
        base["listening_thesis"] = (
            f"Hear {short} as a focused listening room — lock the opening character "
            "and primary motive before chasing ornament or legend."
        )
        base["work_introduction"] = (
            f"{title} is Catalog-resolved. Treat documented craft and ear cues as "
            "identity; keep packaging titles and nicknames as reception caveats."
        )
        base["listening_map"] = [
            {"label": "Opening", "cue": f"Lock the first character of {short}."},
            {"label": "Middle", "cue": "Tint, contrast, or episodic turn — same work."},
            {"label": "Close", "cue": "How the return remembers the opening."},
        ]
        base["width_points"] = [
            f"Frame {short} in biography, publication, and reception.",
            "Separate legends from documented fact.",
            "State the recording’s instrument and era.",
        ]
        base["depth_points"] = [
            "Identify the unit the ear locks onto first.",
            "Map landmarks with ear cues.",
            "Notice how the close remembers the opening.",
        ]
        base["practice_notes"] = [
            "One hearing with a single question.",
            "Second hearing with a landmark list.",
        ]
        base["myths_and_caveats"] = [
            "Catalog floor without curated craft pack — verify anecdotes before stating as fact.",
            "Discogs multi-language packaging titles are not IntentLock work titles.",
        ]

    base["work_title"] = title or str(base.get("work_title") or short)
    base["composer"] = name_en or str(base.get("composer") or "")
    nums = [str(n) for n in (work.catalog_numbers or []) if n]
    if nums:
        base["catalog"] = ", ".join(nums)
    era = str(composer_raw.get("era") or "") or _facet_era(facets)
    if era and not str(base.get("era") or "").strip():
        base["era"] = era
    if not str(base.get("form") or "").strip():
        base["form"] = infer_form_label(
            work_title=title,
            form=str(base.get("form") or ""),
            facets=facets,
        )

    thesis = str(base.get("listening_thesis") or "")
    if short and short.lower() not in thesis.lower() and thesis:
        lead = thesis[0].lower() + thesis[1:] if thesis[0].isupper() else thesis
        base["listening_thesis"] = f"In {short}: {lead}"
    elif short and not thesis:
        base["listening_thesis"] = (
            f"Hear {short} as a focused listening room — lock opening character first."
        )

    intro = str(base.get("work_introduction") or "")
    if title and title not in intro:
        base["work_introduction"] = (
            f"{title}. {intro}" if intro else f"{title} — Catalog craft floor."
        )

    profile = coerce_dict(base.get("composer_profile"))
    if composer:
        lifespan = str(composer_raw.get("lifespan") or "")
        if lifespan and not profile.get("lifespan"):
            profile["lifespan"] = lifespan
        if era and not profile.get("era"):
            profile["era"] = era
        if not profile.get("summary"):
            profile["summary"] = (
                f"{composer.name_en} — Catalog composer card; "
                "thicken via knowledge-plane dossier."
            )
        profile["source"] = profile.get("source") or "catalog"
        base["composer_profile"] = profile

    zh = coerce_dict(base.get("zh") or base.get("zh_hans"))
    title_zh = str(work.canonical_title_zh or "").strip()
    name_zh = str((composer.name_zh if composer else "") or "").strip()
    if title_zh:
        zh.setdefault("work_title", title_zh)
    if name_zh:
        zh.setdefault("composer", name_zh)
    zh_thesis = str(zh.get("listening_thesis") or "").strip()
    short_zh = title_zh.split("—")[-1].strip() if title_zh and "—" in title_zh else title_zh
    if short_zh and zh_thesis and short_zh[:4] not in zh_thesis:
        zh["listening_thesis"] = f"就{short_zh}而言：{zh_thesis}"
    elif short_zh and not zh_thesis:
        zh["listening_thesis"] = (
            f"把{short_zh}当作一个专注的聆听房间——先锁住开场性格与主要动机，再追装饰或传说。"
        )
    if title_zh and not str(zh.get("work_introduction") or "").strip():
        zh["work_introduction"] = (
            f"{title_zh}。以可验证的工艺与耳部线索为身份；包装标题与别名保留为接受史存疑。"
        )
    if zh:
        base["zh"] = zh
        base["zh_hans"] = dict(zh)

    base["dossier_id"] = f"catalog-floor:{wid}"
    base["raw_format"] = "catalog-craft-floor"
    base["work_id"] = wid
    if work.family_id:
        base["family_id"] = work.family_id
    elif fam.get("family_id"):
        base["family_id"] = fam.get("family_id")
    prov = coerce_dict(base.get("_provenance"))
    prov["catalog_craft_floor"] = True
    prov["work_id"] = wid
    base["_provenance"] = prov
    return base
