"""Map knowledge-plane composer dossiers into Salon Codex chambers (SPEC-025)."""

from __future__ import annotations

from typing import Any

from aulos_skills.salon_codex import coerce_dict


def _portrait_from_knowledge(portrait: dict[str, Any] | None, *, composer: str) -> dict[str, Any]:
    p = coerce_dict(portrait)
    if not p:
        return {}
    url = str(p.get("source_url") or p.get("image_url") or p.get("url") or "").strip()
    # Prefer commons / absolute URL; skip relative admin media paths for product HTML
    if url.startswith("/"):
        url = ""
    if not url:
        return {}
    credit = str(p.get("license_class") or p.get("credit") or p.get("title") or "").strip()
    caption = str(p.get("caption") or "").strip() or (
        f"{composer} — portrait from the knowledge plane" if composer else "Composer portrait"
    )
    return {
        "image_url": url,
        "credit": credit or "knowledge-plane media",
        "caption": caption,
        "source": "knowledge-plane",
    }


def _genesis_from_timeline(timeline: list[Any] | None) -> dict[str, Any]:
    events = [e for e in (timeline or []) if isinstance(e, dict)]
    if not events:
        return {}
    # Prefer birth / major events
    ranked = sorted(
        events,
        key=lambda e: (
            0 if str(e.get("event_type") or "") == "birth" else 1,
            0 if str(e.get("significance") or "") == "major" else 1,
            str(e.get("sort_key") or e.get("date_start") or "9999"),
        ),
    )
    birth = next((e for e in ranked if str(e.get("event_type") or "") == "birth"), ranked[0])
    year = str(birth.get("date_start") or birth.get("sort_key") or "")[:10]
    place = str(birth.get("place_label") or "")
    bits = []
    for e in ranked[:4]:
        title = str(e.get("title_en") or e.get("title_zh") or "").strip()
        if title:
            bits.append(title)
    out: dict[str, Any] = {}
    if year:
        out["year"] = year
    if place:
        out["place"] = place
    if bits:
        out["background"] = "; ".join(bits)
    out["source"] = "knowledge-plane-timeline"
    return out


def knowledge_dossier_to_chambers(dossier: dict[str, Any] | None) -> dict[str, Any]:
    """Convert GET /v1/kb/composers/{id}/dossier payload → Salon chamber patch."""
    raw = coerce_dict(dossier)
    if not raw:
        return {}
    composer = coerce_dict(raw.get("composer"))
    name = str(composer.get("name_en") or "").strip()
    name_zh = str(composer.get("name_zh") or "").strip()
    patch: dict[str, Any] = {"_provenance": {"source": "knowledge-plane", "composer_id": composer.get("id")}}
    if name:
        patch["composer"] = name

    portrait = _portrait_from_knowledge(raw.get("portrait") if isinstance(raw.get("portrait"), dict) else {}, composer=name)
    if portrait:
        patch["composer_portrait"] = portrait

    profile: dict[str, Any] = {}
    if composer.get("lifespan"):
        profile["lifespan"] = str(composer["lifespan"])
    if composer.get("era"):
        profile["era"] = str(composer["era"])
    if composer.get("summary_en"):
        profile["summary"] = str(composer["summary_en"])
    if profile:
        profile["source"] = "knowledge-plane"
        patch["composer_profile"] = profile

    genesis = _genesis_from_timeline(raw.get("timeline") if isinstance(raw.get("timeline"), list) else [])
    if genesis:
        patch["genesis"] = genesis

    zh: dict[str, Any] = {}
    if name_zh:
        zh["composer"] = name_zh
    if composer.get("summary_zh"):
        zh["composer_profile"] = {
            "summary": str(composer["summary_zh"]),
            "lifespan": str(composer.get("lifespan") or ""),
            "era": str(composer.get("era") or ""),
        }
    if zh:
        patch["zh"] = zh
    return patch


def merge_knowledge_thicken(
    dossier: dict[str, Any],
    knowledge_patch: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fill empty craft chambers from knowledge patch; never clobber richer values."""
    out = dict(dossier or {})
    patch = dict(knowledge_patch or {})
    if not patch:
        return out

    if patch.get("composer") and not str(out.get("composer") or "").strip():
        out["composer"] = patch["composer"]

    for key in ("composer_portrait", "composer_profile", "genesis"):
        cur = out.get(key)
        empty = cur in (None, "", {}, [])
        if empty and patch.get(key):
            out[key] = patch[key]
        elif key == "composer_portrait":
            cur_d = coerce_dict(cur)
            if not cur_d.get("image_url") and coerce_dict(patch.get(key)).get("image_url"):
                out[key] = patch[key]
        elif key == "composer_profile":
            cur_d = coerce_dict(cur)
            pat_d = coerce_dict(patch.get(key))
            merged = {**pat_d, **{k: v for k, v in cur_d.items() if v not in (None, "", [], {})}}
            if merged:
                out[key] = merged
        elif key == "genesis":
            cur_d = coerce_dict(cur)
            pat_d = coerce_dict(patch.get(key))
            if not cur_d.get("background") and pat_d:
                out[key] = {**pat_d, **cur_d} if cur_d else pat_d

    if patch.get("zh"):
        zh_out = coerce_dict(out.get("zh") or out.get("zh_hans"))
        zh_pat = coerce_dict(patch.get("zh"))
        if zh_pat.get("composer") and not zh_out.get("composer"):
            zh_out["composer"] = zh_pat["composer"]
        if zh_pat.get("composer_profile") and not coerce_dict(zh_out.get("composer_profile")).get("summary"):
            zh_out["composer_profile"] = zh_pat["composer_profile"]
        if zh_out:
            out["zh"] = zh_out
            out["zh_hans"] = dict(zh_out)

    prov = coerce_dict(out.get("_provenance"))
    prov["knowledge_thicken"] = True
    out["_provenance"] = prov
    return out


def dossier_is_thin(dossier: dict[str, Any] | None) -> bool:
    """True when knowledge-plane composer dossier cannot thicken Salon craft (SPEC-026)."""
    raw = dossier if isinstance(dossier, dict) else {}
    if not raw:
        return True
    composer = raw.get("composer") if isinstance(raw.get("composer"), dict) else {}
    if not composer and not raw.get("timeline") and not raw.get("portrait"):
        return True
    portrait = raw.get("portrait") if isinstance(raw.get("portrait"), dict) else {}
    url = str(
        portrait.get("source_url") or portrait.get("image_url") or portrait.get("url") or ""
    ).strip()
    timeline = raw.get("timeline") if isinstance(raw.get("timeline"), list) else []
    events = int(raw.get("events_count") or 0) or len(timeline)
    summary = str(composer.get("summary_en") or composer.get("summary") or "").strip()
    if url.startswith("http") and (events > 0 or len(summary) >= 40):
        return False
    if events >= 3 and len(summary) >= 20:
        return False
    if url.startswith("http") and len(summary) >= 40:
        return False
    return True
