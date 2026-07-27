"""Multilingual Salon Codex HTML renderer (EN / 简体 / 繁體)."""

from __future__ import annotations

import json
from html import escape
from typing import Any

from aulos_skills.i18n import (
    LANG_EN,
    LANG_ZH_HANS,
    LANG_ZH_HANT,
    UI_COPY,
    dossier_has_zh,
    ensure_chinese_variants,
    is_chinese_lang,
    localize_view,
    normalize_lang,
    strip_tech_leaks_zh,
)
from aulos_skills.media_search import enrich_appreciation_video, enrich_interpretation_links


def _li(items: list[Any]) -> str:
    out = []
    for p in items:
        if isinstance(p, dict):
            text = "; ".join(f"{k}: {v}" for k, v in p.items())
        else:
            text = str(p)
        text = strip_tech_leaks_zh(text) if text else ""
        if text:
            out.append(f"<li>{escape(text)}</li>")
    return "".join(out)


def _p(text: str, *, zh: bool = False) -> str:
    text = (text or "").strip()
    if zh:
        text = strip_tech_leaks_zh(text)
    return f"<p>{escape(text)}</p>" if text else ""


def _pick(item: dict[str, Any], key: str, lang: str) -> str:
    if is_chinese_lang(lang):
        alt = item.get(f"{key}_zh")
        if alt:
            return str(alt)
        # Optional explicit Traditional field
        if normalize_lang(lang) == LANG_ZH_HANT:
            alt_hant = item.get(f"{key}_zh_hant") or item.get(f"{key}_hant")
            if alt_hant:
                return str(alt_hant)
    return str(item.get(key) or "")


def _render_lang_article(
    *,
    lang: str,
    work_title: str,
    composer: str,
    dossier: dict[str, Any],
    summary: str,
) -> str:
    lang = normalize_lang(lang)
    ui = UI_COPY.get(lang) or UI_COPY[LANG_ZH_HANS]
    zh = is_chinese_lang(lang)
    era = str(dossier.get("era") or "")
    form = str(dossier.get("form") or "")
    catalog = str(dossier.get("catalog") or "")
    work_introduction = str(dossier.get("work_introduction") or "")
    width_points = list(dossier.get("width_points") or [])
    depth_points = list(dossier.get("depth_points") or [])
    listening_map = [m for m in list(dossier.get("listening_map") or []) if isinstance(m, dict)]
    practice_notes = list(dossier.get("practice_notes") or [])
    myths = list(dossier.get("myths_and_caveats") or [])
    related = list(dossier.get("related_works") or [])
    deepdives = [d for d in list(dossier.get("variation_deepdives") or []) if isinstance(d, dict)]
    interpretations = [
        enrich_interpretation_links(i, work_title=work_title, composer=composer)
        for i in list(dossier.get("interpretations") or [])
        if isinstance(i, dict)
    ]
    videos = [
        enrich_appreciation_video(v, work_title=work_title, composer=composer)
        for v in list(dossier.get("appreciation_videos") or [])
        if isinstance(v, dict)
    ]
    vinyl = [v for v in list(dossier.get("vinyl_and_discography") or []) if isinstance(v, dict)]
    portrait = dict(dossier.get("composer_portrait") or {}) if isinstance(dossier.get("composer_portrait"), dict) else {}
    profile = dict(dossier.get("composer_profile") or {}) if isinstance(dossier.get("composer_profile"), dict) else {}
    genesis = dict(dossier.get("genesis") or {}) if isinstance(dossier.get("genesis"), dict) else {}
    stature = dict(dossier.get("historical_stature") or {}) if isinstance(dossier.get("historical_stature"), dict) else {}
    reasons = list(stature.get("reasons") or [])
    reception = str(stature.get("reception_arc") or "")
    sound = dict(dossier.get("sound_world") or {})

    title = str(dossier.get("work_title") or work_title)
    composer_name = str(dossier.get("composer") or composer)

    chips = "".join(
        f"<span class='chip'>{escape(c)}</span>"
        for c in [composer_name, catalog, era, form]
        if c
    )

    map_blocks = "".join(
        f"<article class='map-item'><h3>{escape(_pick(m, 'label', lang))}</h3>"
        f"<p>{escape(_pick(m, 'cue', lang))}</p></article>"
        for m in listening_map
        if _pick(m, "label", lang) or _pick(m, "cue", lang)
    )

    related_blocks = []
    for r in related:
        if not isinstance(r, dict):
            r = {"title": str(r), "why": ""}
        t = _pick(r, "title", lang)
        if not t:
            continue
        related_blocks.append(
            f"<article class='rel'><h3>{escape(t)}</h3>{_p(_pick(r, 'why', lang), zh=zh)}</article>"
        )
    related_html = "".join(related_blocks)

    deepdive_blocks = "".join(
        f"<article class='map-item'><h3>{escape(_pick(d, 'title', lang))}</h3>"
        f"<p>{escape(_pick(d, 'note', lang))}</p></article>"
        for d in deepdives
        if isinstance(d, dict) and _pick(d, "title", lang)
    )

    interp_blocks = []
    for i in interpretations:
        if not isinstance(i, dict):
            continue
        artist = escape(str(i.get("artist") or ""))
        year = escape(str(i.get("year") or ""))
        instrument = _pick(i, "instrument", lang)
        era_note = _pick(i, "era_note", lang)
        why = _pick(i, "why_listen", lang)
        block = (
            "<article class='interp'>"
            f"<h3>{artist} · {year}</h3>"
            f"<p class='meta-line'>{escape(instrument)} — {escape(era_note)}</p>"
            f"{_p(why, zh=zh)}"
        )
        if i.get("youtube_url"):
            block += (
                f"<p class='links'><a href=\"{escape(str(i['youtube_url']))}\" "
                f"target=\"_blank\" rel=\"noopener\">{escape(ui['youtube'])}</a>"
            )
            if i.get("bilibili_url"):
                block += (
                    f" · <a href=\"{escape(str(i['bilibili_url']))}\" "
                    f"target=\"_blank\" rel=\"noopener\">{escape(ui['bilibili'])}</a>"
                )
            block += "</p>"
        elif i.get("bilibili_url"):
            block += (
                f"<p class='links'><a href=\"{escape(str(i['bilibili_url']))}\" "
                f"target=\"_blank\" rel=\"noopener\">{escape(ui['bilibili'])}</a></p>"
            )
        if i.get("discogs_url"):
            block += (
                f"<p class='links'><a href=\"{escape(str(i['discogs_url']))}\" "
                f"target=\"_blank\" rel=\"noopener\">{escape(ui['discogs'])}</a></p>"
            )
        block += "</article>"
        interp_blocks.append(block)
    interp_html = "".join(interp_blocks)

    video_blocks = []
    for v in videos:
        if not isinstance(v, dict):
            continue
        title = _pick(v, "title", lang) or str(v.get("title") or "")
        if not title and not v.get("url") and not v.get("bilibili_url"):
            continue
        yt = str(v.get("url") or "").strip()
        bili = str(v.get("bilibili_url") or "").strip()
        if not yt and not bili:
            continue
        links: list[str] = []
        if yt:
            links.append(
                f"<a href=\"{escape(yt)}\" target=\"_blank\" rel=\"noopener\">{escape(ui['youtube'])}</a>"
            )
        if bili:
            links.append(
                f"<a href=\"{escape(bili)}\" target=\"_blank\" rel=\"noopener\">{escape(ui['bilibili'])}</a>"
            )
        video_blocks.append(
            "<article class='media'>"
            f"<h3>{escape(title)}</h3>"
            f"{_p(_pick(v, 'why', lang), zh=zh)}"
            f"<p class='links'>{' · '.join(links)}</p>"
            "</article>"
        )
    video_html = "".join(video_blocks)
    vinyl_blocks = "".join(
        f"<article class='media'><h3><a href=\"{escape(str(v.get('url', '')))}\" target=\"_blank\" rel=\"noopener\">"
        f"{escape(_pick(v, 'label', lang) or str(v.get('label') or ''))}</a></h3>"
        f"{_p(_pick(v, 'note', lang), zh=zh)}</article>"
        for v in vinyl
        if isinstance(v, dict) and v.get("url")
    )

    portrait_html = ""
    if portrait.get("image_url"):
        caption = _pick(portrait, "caption", lang) or str(portrait.get("caption") or "")
        credit = _pick(portrait, "credit", lang) or str(portrait.get("credit") or "")
        alt = f"{composer_name}肖像" if zh else f"Portrait of {composer_name}"
        portrait_html = (
            "<figure class='portrait'>"
            f"<img src=\"{escape(str(portrait['image_url']))}\" "
            f"alt=\"{escape(alt)}\" width=\"800\" height=\"1040\" "
            f"loading=\"eager\" decoding=\"async\" fetchpriority=\"high\" "
            f"referrerpolicy=\"no-referrer\"/>"
            f"<figcaption>{escape(caption)}"
            f"<span class='credit'>{escape(credit)}</span>"
            "</figcaption></figure>"
        )

    profile_bits = []
    if profile.get("lifespan"):
        profile_bits.append(f"<p class='meta-line'>{escape(str(profile['lifespan']))}</p>")
    for key, label_key in (
        ("summary", "life"),
        ("temperament", "temperament"),
        ("place_in_oeuvre", "oeuvre"),
        ("place_in_history", "history"),
    ):
        val = _pick(profile, key, lang) if False else str(profile.get(key) or "")
        # profile fields are fully replaced in zh layer
        if profile.get(key):
            profile_bits.append(f"<h3>{escape(ui[label_key])}</h3>{_p(str(profile[key]), zh=zh)}")
    profile_html = "".join(profile_bits)

    genesis_rows = []
    for key, label_key in (
        ("year", "year"),
        ("place", "place"),
        ("publication", "publication"),
        ("patronage", "patronage"),
        ("background", "background"),
        ("instrument_culture", "instrument_culture"),
    ):
        if genesis.get(key):
            genesis_rows.append(
                f"<div class='fact'><span>{escape(ui[label_key])}</span>"
                f"<p>{escape(strip_tech_leaks_zh(str(genesis[key])) if zh else str(genesis[key]))}</p></div>"
            )
    genesis_html = "".join(genesis_rows)

    sound_parts = []
    if sound.get("original_instrument"):
        sound_parts.append(f"<h3>{escape(ui['original_instrument'])}</h3>{_p(str(sound['original_instrument']), zh=zh)}")
    if sound.get("ensemble_notes"):
        sound_parts.append(f"<h3>{escape(ui['ensemble'])}</h3>{_p(str(sound['ensemble_notes']), zh=zh)}")
    modes = list(sound.get("modern_modes") or [])
    if modes:
        sound_parts.append(f"<h3>{escape(ui['modes'])}</h3><ul>{_li(modes)}</ul>")
    sound_html = "".join(sound_parts)

    sections: list[str] = []
    if portrait_html or profile_html:
        sections.append(
            f"<section id='composer-{lang}'><h2>{escape(ui['composer'])}</h2>"
            f"<div class='composer-grid'>{portrait_html}<div class='composer-copy'>{profile_html}</div></div>"
            f"</section>"
        )
    if work_introduction:
        sections.append(
            f"<section id='introduction-{lang}'><h2>{escape(ui['introduction'])}</h2>"
            f"{_p(work_introduction, zh=zh)}</section>"
        )
    if genesis_html:
        sections.append(
            f"<section id='genesis-{lang}'><h2>{escape(ui['genesis'])}</h2>"
            f"<div class='facts'>{genesis_html}</div></section>"
        )
    if reasons or reception:
        reasons_ul = f"<ul>{_li(reasons)}</ul>" if reasons else ""
        sections.append(
            f"<section id='stature-{lang}'><h2>{escape(ui['stature'])}</h2>"
            f"{reasons_ul}{_p(reception, zh=zh)}</section>"
        )
    if width_points:
        sections.append(
            f"<section id='wide-{lang}'><h2>{escape(ui['wide'])}</h2><ul>{_li(width_points)}</ul></section>"
        )
    anatomy = ""
    if depth_points:
        anatomy += f"<h3>{escape(ui['deep'])}</h3><ul>{_li(depth_points)}</ul>"
    if deepdive_blocks:
        anatomy += f"<h3>{escape(ui['deepdives'])}</h3><div class='map'>{deepdive_blocks}</div>"
    if map_blocks:
        anatomy += f"<h3>{escape(ui['map'])}</h3><div class='map'>{map_blocks}</div>"
    if anatomy:
        sections.append(f"<section id='anatomy-{lang}'><h2>{escape(ui['anatomy'])}</h2>{anatomy}</section>")
    if sound_html:
        sections.append(f"<section id='sound-{lang}'><h2>{escape(ui['sound'])}</h2>{sound_html}</section>")
    if related_html:
        sections.append(
            f"<section id='kindred-{lang}'><h2>{escape(ui['kindred'])}</h2>"
            f"<div class='rels'>{related_html}</div></section>"
        )
    if interp_html:
        sections.append(
            f"<section id='interpretations-{lang}'><h2>{escape(ui['interpretations'])}</h2>"
            f"<div class='interps'>{interp_html}</div></section>"
        )
    media_inner = ""
    if video_html:
        media_inner += f"<h3>{escape(ui['videos'])}</h3><div class='medias'>{video_html}</div>"
    if vinyl_blocks:
        media_inner += f"<h3>{escape(ui['vinyl'])}</h3><div class='medias'>{vinyl_blocks}</div>"
    if media_inner:
        sections.append(f"<section id='media-{lang}'><h2>{escape(ui['media'])}</h2>{media_inner}</section>")
    if practice_notes:
        sections.append(
            f"<section id='practice-{lang}'><h2>{escape(ui['practice'])}</h2>"
            f"<ul>{_li(practice_notes)}</ul></section>"
        )
    if myths:
        sections.append(
            f"<section id='caveats-{lang}'><h2>{escape(ui['caveats'])}</h2>"
            f"<ul>{_li(myths)}</ul></section>"
        )

    lede = summary or str(dossier.get("listening_thesis") or "")
    if zh:
        lede = strip_tech_leaks_zh(lede)

    # Caller removes `hidden` from the default language pane.
    return f"""
<article class="lang-pane" data-lang="{lang}" hidden lang="{lang if zh else 'en'}">
  <p class="eyebrow">{escape(ui['eyebrow'])}</p>
  <h1>{escape(title)}</h1>
  <p class="lede">{escape(lede)}</p>
  <div class="meta">{chips}</div>
  {"".join(sections)}
  <footer>{escape(ui['footer'])}</footer>
</article>
"""


def _ambient_bar(ambient: dict[str, Any], *, default_lang: str) -> str:
    from aulos_skills.ambient_playlist import resolve_ambient_audio

    ambient = resolve_ambient_audio(dict(ambient or {}))
    url = str(ambient.get("url") or "").strip()
    tracks = [t for t in (ambient.get("tracks") or []) if isinstance(t, dict) and t.get("url")]
    if not url and not tracks:
        return ""
    if tracks and not url:
        url = str(tracks[0]["url"])

    title_en = str(ambient.get("title") or (tracks[0]["title"] if tracks else "Theme"))
    title_zh = str(ambient.get("title_zh") or (tracks[0].get("title_zh") if tracks else title_en) or title_en)
    credit_en = str(ambient.get("credit") or "")
    credit_zh = str(ambient.get("credit_zh") or credit_en)
    is_playlist = len(tracks) > 1
    # Playlist advances on ended; single-track may loop.
    loop = "" if is_playlist else (" loop" if ambient.get("loop", True) else "")
    try:
        volume = float(ambient.get("volume", 0.28))
    except (TypeError, ValueError):
        volume = 0.28
    volume = max(0.05, min(volume, 0.85))
    default_lang = normalize_lang(default_lang)
    ui = UI_COPY.get(default_lang) or UI_COPY[LANG_ZH_HANS]
    use_zh = is_chinese_lang(default_lang)
    title = title_zh if use_zh else title_en
    credit = credit_zh if use_zh else credit_en
    why_en = str(ambient.get("why") or "")
    why_zh = str(ambient.get("why_zh") or why_en)
    why = why_zh if use_zh else why_en
    why_html = ""
    if why:
        why_label = ui.get("ambient_why") or "Why this music"
        why_html = (
            f'<p class="ambient-why-label" data-i18n-ambient="why_label">{escape(why_label)}</p>'
            f'<p class="ambient-why" data-i18n-ambient="why" data-why-en="{escape(why_en)}" data-why-zh="{escape(why_zh)}">{escape(why)}</p>'
        )

    first = tracks[0] if tracks else None
    origin = str((first or {}).get("url") or url)
    cache_src = str((first or {}).get("cache_src") or ambient.get("cache_src") or "")
    proxy_src = str((first or {}).get("proxy_src") or ambient.get("proxy_src") or "")
    if not cache_src or not proxy_src:
        from urllib.parse import quote

        encoded = quote(origin, safe="")
        cache_src = cache_src or f"/v1/media/audio?src={encoded}&mode=cache"
        proxy_src = proxy_src or f"/v1/media/audio?src={encoded}&mode=proxy"

    mime = "audio/mpeg" if origin.lower().endswith(".mp3") else "audio/ogg"
    # Prefer same-origin cache first — origin CDN is often blocked / slow.
    sources = [f'<source src="{escape(cache_src)}" type="{mime}" data-tier="cache"/>']

    playlist_json = "[]"
    playlist_html = ""
    expand_label = ui["ambient_expand"]
    hint = ui["ambient_hint"]
    kicker = ui["ambient_label"]
    if is_playlist:
        expand_label = ui.get("ambient_playlist") or expand_label
        hint = ui.get("ambient_playlist_hint") or hint
        kicker = ui.get("ambient_playlist") or kicker
        items = []
        for i, tr in enumerate(tracks):
            t_en = str(tr.get("title") or f"Track {i + 1}")
            t_zh = str(tr.get("title_zh") or t_en)
            label = t_zh if use_zh else t_en
            n = tr.get("n") or (i + 1)
            active = " is-active" if i == 0 else ""
            items.append(
                f'<li><button type="button" class="ambient-track{active}" data-track-index="{i}" '
                f'data-title-en="{escape(t_en)}" data-title-zh="{escape(t_zh)}">'
                f'<span class="ambient-track-n">{escape(str(n))}</span>'
                f'<span class="ambient-track-title" data-i18n-track-title="1">{escape(label)}</span>'
                f"</button></li>"
            )
        playlist_html = (
            f'<p class="ambient-playlist-label" data-i18n-ambient="playlist">{escape(ui.get("ambient_playlist") or "Playlist")}</p>'
            f'<ol class="ambient-playlist" data-ambient-playlist="1">{"".join(items)}</ol>'
        )
        slim_tracks = [
            {
                "url": tr["url"],
                "cache_src": tr.get("cache_src"),
                "proxy_src": tr.get("proxy_src"),
                "title": tr.get("title"),
                "title_zh": tr.get("title_zh"),
                "n": tr.get("n"),
            }
            for tr in tracks
        ]
        playlist_json = json.dumps(slim_tracks, ensure_ascii=False).replace("<", "\\u003c")

    mode = "playlist" if is_playlist else "single"
    return f"""
<aside class="ambient is-collapsed" data-ambient="1" data-ambient-player="v2" data-ambient-mode="{mode}" data-loop-playlist="{'1' if ambient.get('loop_playlist', True) else '0'}" data-volume="{volume}" data-origin-src="{escape(origin)}" data-cache-src="{escape(cache_src)}" data-proxy-src="{escape(proxy_src)}" data-title-en="{escape(title_en)}" data-title-zh="{escape(title_zh)}" data-credit-en="{escape(credit_en)}" data-credit-zh="{escape(credit_zh)}">
  <div class="ambient-mini">
    <button type="button" class="ambient-toggle" aria-label="{escape(ui['ambient_play'])}" data-i18n-ambient="play" data-label-play="{escape(ui['ambient_play'])}" data-label-pause="{escape(ui['ambient_pause'])}">
      <span class="ambient-icon" aria-hidden="true"></span>
    </button>
    <div class="ambient-mini-text">
      <p class="ambient-kicker" data-i18n-ambient="label">{escape(kicker)}</p>
      <p class="ambient-title ambient-title-compact" data-i18n-ambient="title">{escape(title)}</p>
    </div>
    <button type="button" class="ambient-expand" data-i18n-ambient="expand" aria-expanded="false">{escape(expand_label)}</button>
  </div>
  <div class="ambient-details" hidden>
    <p class="ambient-credit" data-i18n-ambient="credit">{escape(credit)}</p>
    {why_html}
    <p class="ambient-hint" data-i18n-ambient="hint">{escape(hint)}</p>
    {playlist_html}
  </div>
  <script type="application/json" id="aulos-ambient-playlist">{playlist_json}</script>
  <audio id="aulos-ambient" preload="metadata"{loop} playsinline>
    {"".join(sources)}
  </audio>
</aside>
"""


def render_bilingual_guide_html(
    *,
    dossier: dict[str, Any],
    work_title: str = "",
    composer: str = "",
    summary_en: str = "",
    summary_zh: str = "",
    default_lang: str | None = None,
) -> str:
    dossier = ensure_chinese_variants(dossier)
    en_view = localize_view(dossier, LANG_EN)
    has_zh = dossier_has_zh(dossier)
    zh_hans_view = localize_view(dossier, LANG_ZH_HANS) if has_zh else None
    zh_hant_view = localize_view(dossier, LANG_ZH_HANT) if has_zh else None

    title = str(en_view.get("work_title") or work_title or "Listening guide")
    composer_name = str(en_view.get("composer") or composer or "")
    summary_en = summary_en or str(en_view.get("listening_thesis") or "")
    summary_zh_hans = summary_zh or (
        str(zh_hans_view.get("listening_thesis") or "") if zh_hans_view else ""
    )
    summary_zh_hant = str(zh_hant_view.get("listening_thesis") or "") if zh_hant_view else summary_zh_hans

    if default_lang:
        default_lang = normalize_lang(default_lang)
    else:
        default_lang = LANG_ZH_HANS if has_zh else LANG_EN
    if has_zh and default_lang == LANG_EN:
        pass
    elif has_zh and not is_chinese_lang(default_lang):
        default_lang = LANG_ZH_HANS

    ambient = dict(en_view.get("ambient_audio") or dossier.get("ambient_audio") or {})
    ambient_html = _ambient_bar(ambient, default_lang=default_lang)

    en_article = _render_lang_article(
        lang=LANG_EN,
        work_title=title,
        composer=composer_name,
        dossier=en_view,
        summary=summary_en,
    )
    zh_hans_article = ""
    zh_hant_article = ""
    if zh_hans_view:
        zh_hans_article = _render_lang_article(
            lang=LANG_ZH_HANS,
            work_title=str(zh_hans_view.get("work_title") or title),
            composer=str(zh_hans_view.get("composer") or composer_name),
            dossier=zh_hans_view,
            summary=summary_zh_hans,
        )
    if zh_hant_view:
        zh_hant_article = _render_lang_article(
            lang=LANG_ZH_HANT,
            work_title=str(zh_hant_view.get("work_title") or title),
            composer=str(zh_hant_view.get("composer") or composer_name),
            dossier=zh_hant_view,
            summary=summary_zh_hant,
        )

    # Reveal default pane
    def _unhide(article: str, lang: str) -> str:
        if not article:
            return article
        marker = f'data-lang="{lang}" hidden'
        if default_lang == lang and marker in article:
            return article.replace(marker, f'data-lang="{lang}"', 1)
        return article

    en_article = _unhide(en_article, LANG_EN)
    zh_hans_article = _unhide(zh_hans_article, LANG_ZH_HANS)
    zh_hant_article = _unhide(zh_hant_article, LANG_ZH_HANT)
    if not has_zh:
        en_article = en_article.replace(' data-lang="en" hidden', ' data-lang="en"', 1).replace(
            'data-lang="en" hidden', 'data-lang="en"', 1
        )

    switcher = ""
    if has_zh:
        def _btn(code: str, label: str) -> str:
            active = "active" if default_lang == code else ""
            return (
                f'<button type="button" data-set-lang="{code}" class="{active}">'
                f"{escape(label)}</button>"
            )

        switcher = f"""
<nav class="lang-switch" aria-label="Language">
  {_btn(LANG_ZH_HANS, "简体")}
  {_btn(LANG_ZH_HANT, "繁体")}
  {_btn(LANG_EN, "English")}
</nav>
"""

    def _ambient_pack(code: str) -> dict[str, str]:
        ui = UI_COPY[code]
        return {
            "label": ui["ambient_label"],
            "play": ui["ambient_play"],
            "pause": ui["ambient_pause"],
            "hint": ui["ambient_hint"],
            "expand": ui["ambient_expand"],
            "collapse": ui["ambient_collapse"],
            "playlist": ui["ambient_playlist"],
            "playlist_hint": ui["ambient_playlist_hint"],
            "now": ui["ambient_now"],
            "why_label": ui["ambient_why"],
        }

    ambient_labels_json = json.dumps(
        {
            LANG_ZH_HANS: _ambient_pack(LANG_ZH_HANS),
            LANG_ZH_HANT: _ambient_pack(LANG_ZH_HANT),
            "zh": _ambient_pack(LANG_ZH_HANS),  # legacy
            LANG_EN: _ambient_pack(LANG_EN),
        },
        ensure_ascii=False,
    ).replace("<", "\\u003c")

    html_lang = default_lang if is_chinese_lang(default_lang) else "en"

    return f"""<!DOCTYPE html>
<html lang="{html_lang}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{escape(title)} — Aulos</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;500;600;700&family=Noto+Serif+SC:wght@500;700&display=swap" rel="stylesheet"/>
<style>
:root {{
  --stage: #0c1216; --ink: #e8efe9; --mute: #9aafa3;
  --accent: #c9a66b; --line: rgba(232,239,233,0.11); --glow: rgba(201,166,107,0.14);
}}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; background: var(--stage); color: var(--ink); font-family: Manrope, "Noto Sans SC", system-ui, sans-serif; }}
body {{
  min-height: 100vh;
  background:
    radial-gradient(ellipse 55% 40% at 85% 0%, var(--glow), transparent 50%),
    radial-gradient(ellipse 45% 35% at 0% 20%, rgba(90,70,40,0.12), transparent 55%),
    linear-gradient(168deg, #10171c 0%, #0c1216 48%, #12191f 100%);
}}
.wrap {{ max-width: 44rem; margin: 0 auto; padding: 2.75rem 1.25rem 7.5rem; }}
.lang-pane[data-lang="zh-Hans"] h1,
.lang-pane[data-lang="zh-Hans"] .lede,
.lang-pane[data-lang="zh-Hans"] h2,
.lang-pane[data-lang="zh-Hans"] h3 {{ font-family: "Noto Serif SC", Fraunces, serif; }}
.lang-pane[data-lang="zh-Hant"] h1,
.lang-pane[data-lang="zh-Hant"] .lede,
.lang-pane[data-lang="zh-Hant"] h2,
.lang-pane[data-lang="zh-Hant"] h3 {{ font-family: Fraunces, "Noto Serif SC", "Songti SC", serif; }}
.ambient {{
  position: fixed;
  z-index: 60;
  right: 0.75rem;
  bottom: 0.75rem;
  left: auto;
  width: min(22.5rem, calc(100vw - 1.5rem));
  margin: 0;
  padding: 0.35rem 0.5rem;
  border: 1px solid var(--line);
  background: rgba(16, 22, 27, 0.92);
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 36px rgba(0,0,0,0.45);
  max-height: min(72vh, 30rem);
  display: flex;
  flex-direction: column;
}}
.ambient-mini {{
  display: grid; grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 0.4rem; align-items: center;
  flex: 0 0 auto;
}}
.ambient-mini-text {{ min-width: 0; }}
.ambient-kicker {{
  margin: 0; letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--accent); font-size: 0.55rem; font-weight: 700;
  display: none;
}}
.ambient:not(.is-collapsed) .ambient-kicker {{ display: block; margin-bottom: 0.15rem; }}
.ambient-title {{
  margin: 0; color: var(--mute); font-family: Manrope, "Noto Sans SC", system-ui, sans-serif;
  font-size: 0.72rem; line-height: 1.25; font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.ambient:not(.is-collapsed) .ambient-title {{
  white-space: normal; color: var(--ink);
  font-family: Fraunces, "Noto Serif SC", serif; font-size: 0.88rem;
}}
.ambient-credit, .ambient-hint {{ margin: 0.4rem 0 0; color: var(--mute); font-size: 0.72rem; line-height: 1.45; }}
.ambient-why-label {{
  margin: 0.55rem 0 0.2rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--accent); font-size: 0.58rem; font-weight: 700;
}}
.ambient-why {{
  margin: 0; color: var(--mute); font-size: 0.72rem; line-height: 1.5;
  padding: 0.35rem 0.55rem; border-left: 2px solid var(--accent);
  background: linear-gradient(90deg, rgba(201,166,107,0.08), transparent 80%);
}}
.ambient-details {{
  padding: 0.1rem 0 0.1rem; border-top: 1px solid var(--line); margin-top: 0.4rem;
  overflow: auto; flex: 1 1 auto; min-height: 0;
}}
.ambient-toggle {{
  appearance: none; width: 1.7rem; height: 1.7rem; border-radius: 999px;
  border: 1px solid var(--accent); background: var(--accent); color: #1a1410;
  display: inline-flex; align-items: center; justify-content: center;
  cursor: pointer; padding: 0; flex-shrink: 0;
}}
.ambient-toggle.is-playing {{ background: transparent; color: var(--accent); }}
.ambient-icon {{
  width: 0; height: 0;
  border-style: solid; border-width: 0.3rem 0 0.3rem 0.5rem;
  border-color: transparent transparent transparent currentColor;
  margin-left: 0.08rem;
}}
.ambient-toggle.is-playing .ambient-icon {{
  width: 0.42rem; height: 0.52rem; margin-left: 0;
  border: 0; background:
    linear-gradient(currentColor, currentColor) left/0.14rem 100% no-repeat,
    linear-gradient(currentColor, currentColor) right/0.14rem 100% no-repeat;
}}
.ambient-expand {{
  appearance: none; border: 0; background: transparent; color: var(--mute);
  font: inherit; font-size: 0.62rem; cursor: pointer; padding: 0.1rem 0;
  text-decoration: underline; text-underline-offset: 0.12em; white-space: nowrap;
  opacity: 0.85;
}}
.ambient-expand:hover {{ color: var(--accent); opacity: 1; }}
.ambient audio {{
  position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none;
  overflow: hidden; clip: rect(0 0 0 0);
}}
.ambient-playlist-label {{
  margin: 0.55rem 0 0.3rem; letter-spacing: 0.12em; text-transform: uppercase;
  color: var(--accent); font-size: 0.58rem; font-weight: 700;
}}
.ambient-playlist {{
  list-style: none; margin: 0; padding: 0; max-height: none;
  display: grid; gap: 0.12rem; border-top: 1px solid var(--line); padding-top: 0.35rem;
}}
.ambient-track {{
  appearance: none; width: 100%; display: grid; grid-template-columns: 1.6rem minmax(0, 1fr);
  gap: 0.4rem; align-items: baseline; text-align: left;
  border: 0; background: transparent; color: var(--mute); font: inherit;
  font-size: 0.72rem; line-height: 1.35; padding: 0.28rem 0.35rem; cursor: pointer;
  border-radius: 0.2rem;
}}
.ambient-track:hover {{ color: var(--ink); background: rgba(201,166,107,0.08); }}
.ambient-track.is-active {{
  color: var(--ink); background: rgba(201,166,107,0.14);
}}
.ambient-track-n {{
  font-variant-numeric: tabular-nums; opacity: 0.55; font-size: 0.66rem;
}}
.ambient-track.is-active .ambient-track-n {{ color: var(--accent); opacity: 1; }}
.ambient-track-title {{ min-width: 0; }}
.lang-switch {{
  display: inline-flex; gap: 0.15rem; margin: 0 0 0.85rem;
  border: 1px solid var(--line); padding: 0.12rem; background: rgba(21,28,34,0.7);
}}
.lang-switch button {{
  appearance: none; border: 0; background: transparent; color: var(--mute);
  font: inherit; font-weight: 600; font-size: 0.68rem; letter-spacing: 0.02em;
  padding: 0.22rem 0.5rem; cursor: pointer; min-height: 0; line-height: 1.2;
}}
.lang-switch button.active {{ background: var(--accent); color: #1a1410; }}
.lang-pane[hidden] {{ display: none !important; }}
.lang-pane[data-lang="zh-Hans"] h1,
.lang-pane[data-lang="zh-Hans"] h2,
.lang-pane[data-lang="zh-Hans"] h3,
.lang-pane[data-lang="zh-Hans"] .lede,
.lang-pane[data-lang="zh-Hant"] h1,
.lang-pane[data-lang="zh-Hant"] h2,
.lang-pane[data-lang="zh-Hant"] h3,
.lang-pane[data-lang="zh-Hant"] .lede {{
  font-family: "Noto Serif SC", Fraunces, "Songti SC", serif;
}}
@media (max-width: 719px) {{
  .wrap {{ padding: 1.35rem 1rem 6.5rem; }}
  .ambient {{
    right: 0.5rem; left: 0.5rem; bottom: 0.5rem; width: auto;
    max-height: min(60vh, 24rem);
  }}
}}
.eyebrow {{ letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent); font-size: 0.72rem; font-weight: 700; margin: 0 0 0.85rem; }}
.lang-pane[data-lang="zh-Hans"] .eyebrow,
.lang-pane[data-lang="zh-Hant"] .eyebrow {{ letter-spacing: 0.28em; }}
h1 {{ font-family: Fraunces, Georgia, serif; font-weight: 700; font-size: clamp(1.75rem, 7vw, 3.05rem); line-height: 1.07; letter-spacing: -0.03em; margin: 0 0 0.85rem; }}
.lede {{ color: var(--mute); font-size: clamp(1rem, 3.6vw, 1.1rem); line-height: 1.7; margin: 0 0 1.5rem; max-width: 38rem; font-family: Fraunces, Georgia, serif; font-weight: 500; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0 0 2.5rem; }}
.chip {{ border: 1px solid var(--line); background: rgba(21,28,34,0.85); padding: 0.4rem 0.7rem; font-size: 0.82rem; color: var(--mute); max-width: 100%; }}
section {{ margin: 0 0 1.75rem; padding: 1.35rem 0 0; border-top: 1px solid var(--line); }}
h2 {{ font-family: Fraunces, Georgia, serif; font-size: clamp(1.2rem, 4.5vw, 1.45rem); margin: 0 0 0.95rem; letter-spacing: -0.02em; }}
h3 {{ font-family: Fraunces, Georgia, serif; font-size: 1.02rem; margin: 1rem 0 0.45rem; color: var(--ink); font-weight: 600; }}
p {{ color: var(--mute); line-height: 1.65; margin: 0 0 0.75rem; }}
ul {{ margin: 0; padding-left: 1.15rem; display: grid; gap: 0.55rem; color: var(--mute); line-height: 1.55; }}
.composer-grid {{ display: grid; gap: 1.25rem; align-items: start; }}
@media (min-width: 720px) {{
  .composer-grid {{ grid-template-columns: minmax(0, 13.5rem) minmax(0, 1fr); gap: 1.75rem; }}
}}
.portrait {{ margin: 0; width: 100%; }}
.portrait img {{
  width: 100%; height: auto; max-width: 100%; display: block;
  border: 1px solid var(--line); box-shadow: 0 18px 40px rgba(0,0,0,0.35);
  filter: saturate(0.92) contrast(1.04); background: #1a1510;
}}
.portrait figcaption {{ margin-top: 0.65rem; font-size: 0.82rem; color: var(--mute); line-height: 1.45; }}
.portrait .credit {{ display: block; margin-top: 0.35rem; opacity: 0.75; font-size: 0.75rem; }}
@media (max-width: 719px) {{
  .portrait {{ max-width: 17rem; margin: 0 auto; }}
  .portrait img {{ max-height: min(68vh, 26rem); object-fit: contain; object-position: top center; }}
}}
.facts {{ display: grid; gap: 0.85rem; }}
.fact span {{ display: block; letter-spacing: 0.14em; text-transform: uppercase; font-size: 0.68rem; color: var(--accent); font-weight: 700; margin-bottom: 0.25rem; }}
.lang-pane[data-lang="zh-Hans"] .fact span,
.lang-pane[data-lang="zh-Hant"] .fact span {{ letter-spacing: 0.22em; }}
.fact p {{ margin: 0; }}
.map, .rels, .interps, .medias {{ display: grid; gap: 0.7rem; }}
.map-item, .rel, .interp, .media {{
  padding: 0.9rem 0 0.9rem 0.95rem;
  border-left: 2px solid var(--accent);
  background: linear-gradient(90deg, rgba(201,166,107,0.06), transparent 70%);
}}
.map-item h3, .rel h3, .interp h3, .media h3 {{ margin: 0 0 0.35rem; font-size: 0.98rem; }}
.meta-line {{ font-size: 0.88rem; color: var(--accent); margin-bottom: 0.35rem; }}
.links {{ margin: 0.35rem 0 0; font-size: 0.88rem; }}
a {{ color: var(--accent); text-underline-offset: 0.18em; }}
a:hover {{ color: var(--ink); }}
footer {{ margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--line); color: var(--mute); font-size: 0.82rem; }}
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<main class="wrap">
  {ambient_html}
  {switcher}
  {zh_hans_article}
  {zh_hant_article}
  {en_article}
</main>
<script type="application/json" id="aulos-ambient-i18n">{ambient_labels_json}</script>
<script>
(function () {{
  var root = document.documentElement;
  var buttons = document.querySelectorAll(".lang-switch [data-set-lang]");
  var panes = document.querySelectorAll(".lang-pane");
  var ambientI18n = {{}};
  try {{
    var node = document.getElementById("aulos-ambient-i18n");
    if (node) ambientI18n = JSON.parse(node.textContent || "{{}}");
  }} catch (e) {{}}

  function isZh(lang) {{
    return lang === "zh" || lang === "zh-Hans" || lang === "zh-Hant";
  }}

  function currentLang() {{
    var visible = document.querySelector('.lang-pane:not([hidden])');
    return (visible && visible.getAttribute("data-lang")) || "{default_lang}";
  }}

  function refreshAmbientCopy(lang) {{
    var box = document.querySelector(".ambient");
    if (!box) return;
    var pack = ambientI18n[lang] || ambientI18n["zh-Hans"] || ambientI18n.zh || ambientI18n.en || {{}};
    var isPlaylist = box.getAttribute("data-ambient-mode") === "playlist";
    var kicker = box.querySelector('[data-i18n-ambient="label"]');
    var hint = box.querySelector('[data-i18n-ambient="hint"]');
    var title = box.querySelector('[data-i18n-ambient="title"]');
    var credit = box.querySelector('[data-i18n-ambient="credit"]');
    var btn = box.querySelector(".ambient-toggle");
    var expand = box.querySelector(".ambient-expand");
    var plabel = box.querySelector('[data-i18n-ambient="playlist"]');
    if (kicker) {{
      kicker.textContent = isPlaylist && pack.playlist ? pack.playlist : (pack.label || kicker.textContent);
    }}
    if (hint) {{
      hint.textContent = isPlaylist && pack.playlist_hint ? pack.playlist_hint : (pack.hint || hint.textContent);
    }}
    if (title) {{
      var liveEn = box.getAttribute("data-now-title-en");
      var liveZh = box.getAttribute("data-now-title-zh");
      if (liveEn || liveZh) {{
        title.textContent = isZh(lang) ? (liveZh || liveEn) : (liveEn || liveZh);
      }} else {{
        title.textContent = box.getAttribute(isZh(lang) ? "data-title-zh" : "data-title-en") || title.textContent;
      }}
    }}
    if (credit) credit.textContent = box.getAttribute(isZh(lang) ? "data-credit-zh" : "data-credit-en") || credit.textContent;
    var whyLabel = box.querySelector('[data-i18n-ambient="why_label"]');
    var why = box.querySelector('[data-i18n-ambient="why"]');
    if (whyLabel && pack.why_label) whyLabel.textContent = pack.why_label;
    if (why) {{
      why.textContent = isZh(lang)
        ? (why.getAttribute("data-why-zh") || why.getAttribute("data-why-en") || why.textContent)
        : (why.getAttribute("data-why-en") || why.getAttribute("data-why-zh") || why.textContent);
    }}
    if (btn && pack.play && pack.pause) {{
      btn.setAttribute("data-label-play", pack.play);
      btn.setAttribute("data-label-pause", pack.pause);
      btn.setAttribute("aria-label", btn.classList.contains("is-playing") ? pack.pause : pack.play);
    }}
    if (expand) {{
      var open = !box.classList.contains("is-collapsed");
      var expandLabel = isPlaylist && pack.playlist ? pack.playlist : (pack.expand || expand.textContent);
      var collapseLabel = pack.collapse || expandLabel;
      expand.textContent = open ? collapseLabel : expandLabel;
    }}
    if (plabel && pack.playlist) plabel.textContent = pack.playlist;
    box.querySelectorAll(".ambient-track").forEach(function (tr) {{
      var t = tr.querySelector("[data-i18n-track-title]");
      if (!t) return;
      t.textContent = isZh(lang)
        ? (tr.getAttribute("data-title-zh") || tr.getAttribute("data-title-en") || t.textContent)
        : (tr.getAttribute("data-title-en") || tr.getAttribute("data-title-zh") || t.textContent);
    }});
  }}

  function setLang(lang) {{
    panes.forEach(function (p) {{
      var on = p.getAttribute("data-lang") === lang;
      if (on) p.removeAttribute("hidden"); else p.setAttribute("hidden", "");
    }});
    buttons.forEach(function (b) {{
      b.classList.toggle("active", b.getAttribute("data-set-lang") === lang);
    }});
    root.setAttribute("lang", isZh(lang) ? lang : "en");
    try {{ localStorage.setItem("aulos_guide_lang", lang); }} catch (e) {{}}
    refreshAmbientCopy(lang);
  }}
  buttons.forEach(function (b) {{
    b.addEventListener("click", function () {{ setLang(b.getAttribute("data-set-lang")); }});
  }});
  var saved = null;
  try {{ saved = localStorage.getItem("aulos_guide_lang"); }} catch (e) {{}}
  if (saved === "zh") saved = "zh-Hans";
  if (saved === "en" || saved === "zh-Hans" || saved === "zh-Hant") {{
    if (document.querySelector('.lang-pane[data-lang="' + saved + '"]')) setLang(saved);
  }} else {{
    refreshAmbientCopy(currentLang());
  }}

  var audio = document.getElementById("aulos-ambient");
  var toggle = document.querySelector(".ambient-toggle");
  var ambient = document.querySelector(".ambient");
  var expandBtn = document.querySelector(".ambient-expand");
  if (audio && toggle && ambient) {{
    var vol = parseFloat(ambient.getAttribute("data-volume") || "0.28");
    if (!isNaN(vol)) audio.volume = vol;
    var playlist = [];
    try {{
      var pn = document.getElementById("aulos-ambient-playlist");
      if (pn) playlist = JSON.parse(pn.textContent || "[]") || [];
    }} catch (e) {{ playlist = []; }}
    var trackIndex = 0;
    var loopPlaylist = ambient.getAttribute("data-loop-playlist") !== "0";
    var originSrc = ambient.getAttribute("data-origin-src") || "";
    var cacheSrc = ambient.getAttribute("data-cache-src") || "";
    var proxySrc = ambient.getAttribute("data-proxy-src") || "";
    var tierOrder = ["cache", "proxy", "origin"];
    var tierIdx = 0;
    var preferKey = "aulos_ambient_tier:" + (originSrc || "default");
    try {{
      var savedTier = localStorage.getItem(preferKey);
      if (savedTier === "proxy") tierIdx = 1;
      else if (savedTier === "origin") tierIdx = 2;
      else tierIdx = 0;
    }} catch (e) {{}}
    var stallTimer = null;
    var loadTimer = null;
    var failingOver = false;

    function resolveUrl(u) {{
      if (!u) return u;
      if (/^(https?:|blob:|data:)/i.test(u)) return u;
      try {{
        var base = document.baseURI || window.location.href;
        if (!base || base.indexOf("about:") === 0 || base.indexOf("blob:") === 0) {{
          if (window.parent && window.parent !== window) {{
            try {{ base = window.parent.location.href; }} catch (e) {{ base = ""; }}
          }}
        }}
        if (!base || base.indexOf("about:") === 0 || base.indexOf("blob:") === 0) {{
          base = window.location.origin && window.location.origin !== "null"
            ? window.location.origin + "/"
            : "https://aulos.purezen.ai/";
        }}
        return new URL(u, base).href;
      }} catch (e) {{
        return u;
      }}
    }}

    function currentTrack() {{
      return playlist[trackIndex] || null;
    }}

    function syncTrackSources() {{
      var tr = currentTrack();
      if (tr) {{
        originSrc = tr.url || originSrc;
        cacheSrc = tr.cache_src || cacheSrc;
        proxySrc = tr.proxy_src || proxySrc;
        ambient.setAttribute("data-origin-src", originSrc);
        ambient.setAttribute("data-cache-src", cacheSrc);
        ambient.setAttribute("data-proxy-src", proxySrc);
        ambient.setAttribute("data-now-title-en", tr.title || "");
        ambient.setAttribute("data-now-title-zh", tr.title_zh || tr.title || "");
        preferKey = "aulos_ambient_tier:" + originSrc;
        try {{
          var saved = localStorage.getItem(preferKey);
          tierIdx = saved === "origin" ? 2 : (saved === "proxy" ? 1 : 0);
        }} catch (e) {{ tierIdx = 0; }}
      }}
    }}

    function highlightTrack() {{
      ambient.querySelectorAll(".ambient-track").forEach(function (btn) {{
        var i = parseInt(btn.getAttribute("data-track-index") || "-1", 10);
        btn.classList.toggle("is-active", i === trackIndex);
      }});
      var active = ambient.querySelector(".ambient-track.is-active");
      if (active && active.scrollIntoView) {{
        try {{ active.scrollIntoView({{ block: "nearest", behavior: "smooth" }}); }} catch (e) {{}}
      }}
      refreshAmbientCopy(currentLang());
    }}

    function tierUrl(name) {{
      if (name === "cache") return cacheSrc;
      if (name === "proxy") return proxySrc;
      return originSrc;
    }}

    function clearLoadWatch() {{
      if (loadTimer) {{ clearTimeout(loadTimer); loadTimer = null; }}
    }}

    function applyTier(startIdx) {{
      tierIdx = Math.max(0, Math.min(startIdx, tierOrder.length - 1));
      var src = resolveUrl(tierUrl(tierOrder[tierIdx]));
      if (!src) return;
      while (audio.firstChild) audio.removeChild(audio.firstChild);
      audio.removeAttribute("src");
      audio.src = src;
      audio.setAttribute("data-active-tier", tierOrder[tierIdx]);
      try {{ audio.load(); }} catch (e) {{}}
      clearLoadWatch();
      loadTimer = setTimeout(function () {{
        if (audio.readyState < 2) failover("load-timeout");
      }}, 3500);
    }}

    function rememberTier() {{
      try {{ localStorage.setItem(preferKey, tierOrder[tierIdx]); }} catch (e) {{}}
    }}

    function clearStallWatch() {{
      if (stallTimer) {{ clearTimeout(stallTimer); stallTimer = null; }}
    }}

    function watchStall() {{
      clearStallWatch();
      var last = audio.currentTime || 0;
      stallTimer = setTimeout(function () {{
        if (audio.paused) return;
        if ((audio.currentTime || 0) <= last + 0.05 && !audio.ended) {{
          failover("stall");
        }}
      }}, 4500);
    }}

    function failover(reason) {{
      if (failingOver) return;
      if (tierIdx >= tierOrder.length - 1) return;
      failingOver = true;
      clearStallWatch();
      clearLoadWatch();
      var wasPlaying = !audio.paused;
      var t = audio.currentTime || 0;
      tierIdx += 1;
      applyTier(tierIdx);
      rememberTier();
      audio.addEventListener("loadedmetadata", function onMeta() {{
        audio.removeEventListener("loadedmetadata", onMeta);
        try {{ if (t > 0 && isFinite(t)) audio.currentTime = t; }} catch (e) {{}}
        failingOver = false;
        if (wasPlaying) tryPlay();
      }});
      setTimeout(function () {{ failingOver = false; }}, 1200);
      try {{ console.info("[aulos-ambient] failover", reason, tierOrder[tierIdx]); }} catch (e) {{}}
    }}

    function loadTrack(index, autoPlay) {{
      if (!playlist.length) {{
        applyTier(tierIdx);
        if (autoPlay) tryPlay();
        return;
      }}
      trackIndex = ((index % playlist.length) + playlist.length) % playlist.length;
      syncTrackSources();
      highlightTrack();
      applyTier(tierIdx);
      if (autoPlay) {{
        audio.addEventListener("loadedmetadata", function onReady() {{
          audio.removeEventListener("loadedmetadata", onReady);
          tryPlay();
        }});
        setTimeout(function () {{ tryPlay(); }}, 400);
      }}
    }}

    function nextTrack() {{
      if (!playlist.length) return;
      var next = trackIndex + 1;
      if (next >= playlist.length) {{
        if (!loopPlaylist) return;
        next = 0;
      }}
      loadTrack(next, true);
    }}

    syncTrackSources();
    applyTier(tierIdx);
    highlightTrack();

    function syncBtn() {{
      var playing = !audio.paused;
      toggle.classList.toggle("is-playing", playing);
      var play = toggle.getAttribute("data-label-play") || "Play";
      var pause = toggle.getAttribute("data-label-pause") || "Pause";
      toggle.setAttribute("aria-label", playing ? pause : play);
    }}
    function tryPlay() {{
      var p = audio.play();
      if (p && typeof p.then === "function") {{
        p.then(function () {{ syncBtn(); watchStall(); }}).catch(function () {{
          failover("play-reject");
          syncBtn();
        }});
      }} else {{ syncBtn(); }}
    }}
    toggle.addEventListener("click", function () {{
      if (audio.paused) tryPlay(); else {{ audio.pause(); clearStallWatch(); syncBtn(); }}
    }});
    audio.addEventListener("play", function () {{ syncBtn(); watchStall(); }});
    audio.addEventListener("playing", function () {{ rememberTier(); clearStallWatch(); clearLoadWatch(); watchStall(); }});
    audio.addEventListener("canplay", function () {{ clearLoadWatch(); }});
    audio.addEventListener("pause", function () {{ clearStallWatch(); syncBtn(); }});
    audio.addEventListener("timeupdate", function () {{
      if (!audio.paused) {{ clearStallWatch(); watchStall(); }}
    }});
    audio.addEventListener("error", function () {{ failover("error"); }});
    audio.addEventListener("stalled", function () {{ failover("stalled-event"); }});
    audio.addEventListener("waiting", function () {{ watchStall(); }});
    audio.addEventListener("ended", function () {{
      if (playlist.length > 1) nextTrack();
    }});
    ambient.querySelectorAll(".ambient-track").forEach(function (btn) {{
      btn.addEventListener("click", function () {{
        var i = parseInt(btn.getAttribute("data-track-index") || "0", 10);
        loadTrack(i, true);
      }});
    }});
    if (expandBtn) {{
      expandBtn.addEventListener("click", function () {{
        ambient.classList.toggle("is-collapsed");
        var open = !ambient.classList.contains("is-collapsed");
        var details = ambient.querySelector(".ambient-details");
        if (details) {{
          if (open) details.removeAttribute("hidden"); else details.setAttribute("hidden", "");
        }}
        expandBtn.setAttribute("aria-expanded", open ? "true" : "false");
        refreshAmbientCopy(currentLang());
      }});
    }}
    // Soft autoplay; browsers may require the first tap on the play button.
    tryPlay();
  }}
}})();
</script>
</body>
</html>
"""

