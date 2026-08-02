"""Discogs release structure — structure-first covenant (META-001 §4.1 / SPEC-034).

Pipeline order (forced):
  1. Fetch full Discogs release/master payload (credits, tracklist, formats, …)
  2. Build ReleaseStructure — identify program works / shelves before any deepen
  3. Only then expand layer-by-layer (identity → corpus → synthesize → …)

Forbidden: collapsing a multi-work pressing into one family scaffold before the
program is recognized.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any  # noqa: TC003 — runtime dict/Any contracts

from aulos_skills.identity_lock import extract_catalog_numbers, normalize_catalog_number

SCHEMA = "aulos.release_structure/v1"

# Discogs classical releases often pack EN/DE/FR titles with " = " separators.
_POLYGLOT_SPLIT_RE = re.compile(r"\s*=\s*")
_COMPOSER_ROLE_RE = re.compile(
    r"(?i)\b(compos(er|ed|ition)?|written[\s-]?by|music[\s-]?by)\b"
)
_PERFORMER_ROLE_RE = re.compile(
    r"(?i)\b(piano|violin|cello|violoncello|viola|flute|oboe|clarinet|"
    r"bassoon|horn|trumpet|trombone|organ|harpsichord|guitar|voice|"
    r"soprano|alto|tenor|bass|choir|orchestra|ensemble|quartet|trio|"
    r"conductor|directed|performed|soloist|harp|percussion|timpani)\b"
)
_ENSEMBLE_NAME_RE = re.compile(
    r"(?i)\b(orchestra|ensemble|choir|chorus|philharmonic|symphony|"
    r"quartet|trio|quintet|sextet|consort)\b"
)
_VARIOUS_RE = re.compile(r"(?i)^(various|various artists|unknown|anonymous)$")


def canonical_discogs_title(title: str) -> str:
    """Collapse Discogs polyglot track titles to one deepen/search-safe label.

    META-001 §4.1: never feed ``A = B = C`` multilingual strings into web/LLM.
    Prefer the segment that carries a catalog number; else the shortest clean segment.
    """
    raw = (title or "").strip()
    if not raw:
        return ""
    parts = [p.strip(" -–—|") for p in _POLYGLOT_SPLIT_RE.split(raw) if p.strip()]
    if not parts:
        return raw[:160]
    if len(parts) == 1:
        return parts[0][:160]

    def _score(p: str) -> tuple[int, int, int]:
        cats = extract_catalog_numbers(p)
        # Prefer catalog-bearing, English-ish (ASCII heavy), shorter labels
        ascii_ratio = sum(1 for ch in p if ord(ch) < 128) / max(len(p), 1)
        return (1 if cats else 0, 1 if ascii_ratio >= 0.85 else 0, -len(p))

    best = max(parts, key=_score)
    return best[:160]


def catalog_display(cat: str) -> str:
    """bwv1041 → BWV 1041; k488 → K. 488."""
    s = normalize_catalog_number(cat) or (cat or "").lower().strip()
    m = re.match(r"^(bwv|op|k|hob|d|wwv|rv)(\d{1,4}[a-z]?)$", s)
    if not m:
        return (cat or "").strip()
    prefix, num = m.group(1), m.group(2)
    if prefix == "bwv":
        return f"BWV {num}"
    if prefix == "k":
        return f"K. {num}"
    if prefix == "op":
        return f"Op. {num}"
    return f"{prefix.upper()} {num}"


def program_search_query(
    *,
    composer: str = "",
    title: str = "",
    catalog_numbers: list[str] | None = None,
) -> str:
    """Catalog-first work query for web gather (never polyglot Discogs title).

    Composer is passed separately to ``gather_web_sources`` — do not duplicate it here.
    """
    del composer  # API accepts composer for call-site clarity; gather adds it
    cats = [catalog_display(c) for c in (catalog_numbers or []) if c]
    short = canonical_discogs_title(title)
    bits = list(cats[:2])
    if short:
        cue = short
        for c in cats:
            cue = re.sub(re.escape(c), "", cue, flags=re.I)
        cue = re.sub(r"\s+", " ", cue).strip(" -–—,;/")
        if cue and len(cue) <= 72:
            bits.append(cue)
    q = " ".join(b for b in bits if b)
    return q[:160] or short[:160]


def _clean_credit_name(name: str) -> str:
    cleaned = re.sub(r"\s+\(\d+\)\s*$", "", str(name or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _dedupe_names(names: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for name in names:
        clean = _clean_credit_name(name)
        low = clean.lower()
        if not clean or low in seen:
            continue
        out.append(clean)
        seen.add(low)
    return out


def _item_names(items: list[Any] | None) -> list[str]:
    out: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        name = _clean_credit_name(str(item.get("name") or ""))
        if name:
            out.append(name)
    return _dedupe_names(out)


def _role_names(items: list[Any] | None, role_re: re.Pattern[str]) -> list[str]:
    out: list[str] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        if not role_re.search(role):
            continue
        name = _clean_credit_name(str(item.get("name") or ""))
        if name:
            out.append(name)
    return _dedupe_names(out)


def _release_artist_composer_candidates(
    raw: dict[str, Any],
    *,
    performers: list[str] | None = None,
    ensembles: list[str] | None = None,
) -> list[str]:
    """Conservative Discogs fallback: release artists are composers only after exclusions.

    Classical Discogs releases often list composers as top-level artists and put
    performers in ``extraartists``. Use this only as a structure-level fallback,
    then require positional agreement before assigning per-work composers.
    """
    extras = list(raw.get("extraartists") or [])
    excluded = {
        n.lower()
        for n in _dedupe_names(
            list(performers or [])
            + list(ensembles or [])
            + _role_names(extras, _PERFORMER_ROLE_RE)
        )
    }
    out: list[str] = []
    for name in _item_names(list(raw.get("artists") or [])):
        low = name.lower()
        if low in excluded:
            continue
        if _VARIOUS_RE.search(name) or _ENSEMBLE_NAME_RE.search(name):
            continue
        out.append(name)
    return _dedupe_names(out)


def _assign_program_composers(
    program: list["ProgramWork"],
    composer_pool: list[str],
) -> list["ProgramWork"]:
    composers = _dedupe_names(composer_pool)
    if not composers:
        return program
    if len(composers) == 1:
        for p in program:
            if not p.composers:
                p.composers = [composers[0]]
        return program
    if len(composers) == len(program):
        for p, composer in zip(program, composers):
            if not p.composers:
                p.composers = [composer]
    return program


@dataclass
class ProgramWork:
    """One identifiable work (or movement group) on the pressing."""

    index: int
    title: str
    catalog_numbers: list[str] = field(default_factory=list)
    positions: list[str] = field(default_factory=list)
    track_titles: list[str] = field(default_factory=list)
    composers: list[str] = field(default_factory=list)
    instruments_hint: list[str] = field(default_factory=list)
    heading: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReleaseStructure:
    """Canonical album/program map before listening deepen."""

    schema: str = SCHEMA
    release_id: int | None = None
    master_id: int | None = None
    release_title: str = ""
    shape: str = "unknown"  # single_work | multi_work_program | shelf | unknown
    composers: list[str] = field(default_factory=list)
    performers: list[str] = field(default_factory=list)
    ensembles: list[str] = field(default_factory=list)
    label: str = ""
    catno: str = ""
    year: str = ""
    country: str = ""
    genres: list[str] = field(default_factory=list)
    styles: list[str] = field(default_factory=list)
    formats: list[str] = field(default_factory=list)
    uri: str = ""
    track_count: int = 0
    program: list[ProgramWork] = field(default_factory=list)
    catalog_numbers_all: list[str] = field(default_factory=list)
    structure_ready: bool = False
    ready_reasons: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


_SOLO_HINTS = (
    (r"violin|小提琴", "violin"),
    (r"oboe|双簧管|雙簧管", "oboe"),
    (r"piano|钢琴|鋼琴|fortepiano", "piano"),
    (r"cello|violoncello|大提琴", "cello"),
    (r"viola|中提琴", "viola"),
    (r"flute|长笛|長笛", "flute"),
    (r"clarinet|单簧管|單簧管", "clarinet"),
    (r"two violins|双小提琴|雙小提琴|doppelkonzert", "two_violins"),
)


def _instrument_hints(text: str) -> list[str]:
    import re

    found: list[str] = []
    blob = text or ""
    for pat, name in _SOLO_HINTS:
        if re.search(pat, blob, flags=re.I) and name not in found:
            found.append(name)
    return found


def _track_rows(raw: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    heading = ""
    for t in raw.get("tracklist") or []:
        if not isinstance(t, dict):
            continue
        typ = str(t.get("type_") or "track").strip().lower() or "track"
        title = str(t.get("title") or "").strip()
        if typ == "heading":
            heading = title
            continue
        if not title:
            continue
        rows.append(
            {
                "position": str(t.get("position") or "").strip(),
                "title": title,
                "duration": str(t.get("duration") or "").strip(),
                "type": typ,
                "heading": heading,
                "extraartists": list(t.get("extraartists") or []),
            }
        )
    return rows


def _cluster_program(rows: list[dict[str, Any]], release_title: str) -> list[ProgramWork]:
    """Cluster tracks into program works by catalog id / heading / distinct work titles."""
    if not rows:
        return []

    clusters: list[dict[str, Any]] = []
    for row in rows:
        cats = sorted(extract_catalog_numbers(row["title"]))
        row_composers = _role_names(row.get("extraartists") or [], _COMPOSER_ROLE_RE)
        key = cats[0] if cats else ""
        heading = row.get("heading") or ""
        # Prefer catalog cluster; else heading; else unique title stem
        matched = None
        if key:
            for c in clusters:
                if key in c["catalog_numbers"] or (
                    c["catalog_numbers"] and set(cats) & set(c["catalog_numbers"])
                ):
                    matched = c
                    break
        if matched is None and heading:
            for c in clusters:
                if c.get("heading") == heading and not c["catalog_numbers"]:
                    matched = c
                    break
        if matched is None and cats:
            # new catalog work
            matched = {
                "title": row["title"],
                "catalog_numbers": list(cats),
                "positions": [],
                "track_titles": [],
                "heading": heading,
                "composers": [],
            }
            clusters.append(matched)
        elif matched is None:
            # movement without catalog — attach to last open cluster if same heading
            if clusters and clusters[-1].get("heading") == heading and heading:
                matched = clusters[-1]
            else:
                matched = {
                    "title": row["title"],
                    "catalog_numbers": list(cats),
                    "positions": [],
                    "track_titles": [],
                    "heading": heading,
                    "composers": [],
                }
                clusters.append(matched)

        for c in cats:
            if c not in matched["catalog_numbers"]:
                matched["catalog_numbers"].append(c)
        for comp in row_composers:
            if comp and comp not in matched["composers"]:
                matched["composers"].append(comp)
        if row["position"]:
            matched["positions"].append(row["position"])
        matched["track_titles"].append(row["title"])
        # Prefer canonical (catalog-bearing, non-polyglot) over longest Discogs string
        cand = canonical_discogs_title(row["title"])
        cur = canonical_discogs_title(matched["title"])
        cand_cats = extract_catalog_numbers(cand)
        cur_cats = extract_catalog_numbers(cur)
        if (bool(cand_cats), -len(cand)) > (bool(cur_cats), -len(cur)):
            matched["title"] = cand
        elif not matched["title"]:
            matched["title"] = cand

    program: list[ProgramWork] = []
    for i, c in enumerate(clusters):
        title = canonical_discogs_title(str(c["title"] or ""))
        cats = [normalize_catalog_number(x) or x for x in c["catalog_numbers"]]
        cats = sorted({x for x in cats if x})
        hints = _instrument_hints(" ".join([title, *c["track_titles"], release_title]))
        program.append(
            ProgramWork(
                index=i,
                title=title[:160],
                catalog_numbers=cats,
                positions=list(c["positions"]),
                track_titles=list(c["track_titles"])[:24],
                composers=_dedupe_names(list(c.get("composers") or [])),
                instruments_hint=hints,
                heading=str(c.get("heading") or ""),
            )
        )

    # No catalog ids anywhere → treat as one shelf/single work (movements, not program works).
    if program and not any(p.catalog_numbers for p in program):
        all_tracks = [t for p in program for t in p.track_titles]
        all_pos = [pos for p in program for pos in p.positions]
        hints = _instrument_hints(" ".join([release_title, *all_tracks]))
        return [
            ProgramWork(
                index=0,
                title=(release_title or program[0].title)[:200],
                catalog_numbers=[],
                positions=all_pos[:48],
                track_titles=all_tracks[:48],
                composers=_dedupe_names(
                    [comp for p in program for comp in (p.composers or [])]
                ),
                instruments_hint=hints,
                heading="",
            )
        ]
    return program


def build_release_structure(
    raw: dict[str, Any] | None,
    *,
    release_id: int | None = None,
    master_id: int | None = None,
    uri: str = "",
    composers: list[str] | None = None,
    performers: list[str] | None = None,
    ensembles: list[str] | None = None,
) -> ReleaseStructure:
    """Build structure map from a full Discogs release/master JSON object."""
    raw = dict(raw or {})
    rid = release_id if release_id is not None else int(raw.get("id") or 0) or None
    title = str(raw.get("title") or "").strip()
    rows = _track_rows(raw)
    program = _cluster_program(rows, title)
    explicit_composers = _dedupe_names(
        list(composers or []) + _role_names(list(raw.get("extraartists") or []), _COMPOSER_ROLE_RE)
    )
    artist_composers = _release_artist_composer_candidates(
        raw,
        performers=performers,
        ensembles=ensembles,
    )
    composer_pool = explicit_composers or artist_composers
    program = _assign_program_composers(program, composer_pool)
    program_composers = _dedupe_names(
        [comp for p in program for comp in (p.composers or [])]
    )
    release_composers = _dedupe_names(explicit_composers + program_composers)
    if not release_composers:
        release_composers = _dedupe_names(list(composers or []))

    labels = raw.get("labels") or []
    label_name = ""
    catno = ""
    if labels and isinstance(labels[0], dict):
        label_name = str(labels[0].get("name") or "")
        catno = str(labels[0].get("catno") or "")

    formats: list[str] = []
    for fmt in raw.get("formats") or []:
        if isinstance(fmt, dict) and fmt.get("name"):
            formats.append(str(fmt["name"]))

    blob_cats = sorted(
        extract_catalog_numbers(
            " ".join(
                [
                    title,
                    *[r["title"] for r in rows],
                    *[p.title for p in program],
                ]
            )
        )
    )

    # Prefer program-derived catalogs when present
    prog_cats = sorted({c for p in program for c in p.catalog_numbers})
    all_cats = prog_cats or blob_cats

    if len(prog_cats) >= 2 or len(program) >= 2:
        shape = "multi_work_program"
    elif len(program) == 1 and (program[0].catalog_numbers or program[0].title):
        shape = "single_work"
    elif rows:
        shape = "shelf"
    else:
        shape = "unknown"

    gaps: list[str] = []
    reasons: list[str] = []
    if not raw:
        gaps.append("empty_payload")
    if not title:
        gaps.append("missing_release_title")
    if not rows:
        gaps.append("missing_tracklist")
    if shape == "multi_work_program" and not prog_cats and len(program) < 2:
        gaps.append("multi_work_unresolved")
    if shape == "multi_work_program" and len(program) < 2:
        gaps.append("program_underclustered")

    if shape == "single_work" and rows:
        reasons.append("single_work_with_tracks")
    if shape == "multi_work_program" and len(program) >= 2:
        reasons.append(f"program_works={len(program)}")
    if all_cats:
        reasons.append(f"catalogs={len(all_cats)}")
    if release_composers or performers:
        reasons.append("credits_present")

    structure_ready = (
        bool(title)
        and bool(rows)
        and shape in {"single_work", "multi_work_program", "shelf"}
        and "program_underclustered" not in gaps
        and "multi_work_unresolved" not in gaps
    )
    if structure_ready:
        reasons.append("structure_ready")

    return ReleaseStructure(
        release_id=rid,
        master_id=master_id,
        release_title=title,
        shape=shape,
        composers=release_composers,
        performers=list(performers or []),
        ensembles=list(ensembles or []),
        label=label_name,
        catno=catno,
        year=str(raw.get("year") or ""),
        country=str(raw.get("country") or "").strip(),
        genres=[str(g) for g in (raw.get("genres") or []) if g][:8],
        styles=[str(s) for s in (raw.get("styles") or []) if s][:8],
        formats=formats[:8],
        uri=uri,
        track_count=len(rows),
        program=program,
        catalog_numbers_all=all_cats,
        structure_ready=structure_ready,
        ready_reasons=reasons,
        gaps=gaps,
    )


def assert_structure_ready(structure: ReleaseStructure | dict[str, Any]) -> list[str]:
    """Return hard-fail codes when deepen must not proceed yet."""
    if isinstance(structure, ReleaseStructure):
        d = structure.to_dict()
    else:
        d = dict(structure or {})
    fails: list[str] = []
    if not d.get("structure_ready"):
        fails.append("release_structure_not_ready")
    gaps = list(d.get("gaps") or [])
    for g in gaps:
        fails.append(f"structure_gap:{g}")
    shape = str(d.get("shape") or "")
    program = list(d.get("program") or [])
    if shape == "multi_work_program" and len(program) < 2:
        fails.append("multi_work_program_incomplete")
    return fails


def expansion_plan(structure: ReleaseStructure | dict[str, Any]) -> list[dict[str, Any]]:
    """Layered expand plan consumed by listening pipeline (SPEC-034)."""
    if isinstance(structure, ReleaseStructure):
        d = structure.to_dict()
    else:
        d = dict(structure or {})
    plan: list[dict[str, Any]] = [
        {
            "layer": 0,
            "name": "release_metadata",
            "goal": "Preserve full Discogs credits, formats, label, URI",
        },
        {
            "layer": 1,
            "name": "program_map",
            "goal": "Freeze program works + catalog numbers before deepen",
            "works": len(d.get("program") or []),
            "shape": d.get("shape"),
        },
    ]
    for p in d.get("program") or []:
        if isinstance(p, ProgramWork):
            p = p.to_dict()
        composers = [str(c) for c in (p.get("composers") or []) if c]
        plan.append(
            {
                "layer": 2,
                "name": "work_deepen",
                "work_index": p.get("index"),
                "title": p.get("title"),
                "composer": composers[0] if composers else "",
                "composers": composers,
                "catalog_numbers": p.get("catalog_numbers") or [],
                "goal": "Identity → corpus → synthesize for this program work only",
            }
        )
    plan.append(
        {
            "layer": 3,
            "name": "pressing_synthesis",
            "goal": "Recording-level interpretations / vinyl / comparative shelf across program",
        }
    )
    return plan


def coerce_structure(obj: Any) -> dict[str, Any]:
    if isinstance(obj, ReleaseStructure):
        return obj.to_dict()
    if isinstance(obj, dict):
        return dict(obj)
    return {}


def structure_from_context(context: dict[str, Any] | None) -> dict[str, Any]:
    """Lift ReleaseStructure from chain context / kb_seed / discogs bag."""
    ctx = dict(context or {})
    for key in ("release_structure",):
        st = coerce_structure(ctx.get(key))
        if st.get("shape") or st.get("program") is not None:
            return st
    kb = dict(ctx.get("kb_dossier") or {})
    st = coerce_structure(kb.get("release_structure"))
    if st.get("shape") or st.get("program") is not None:
        return st
    prov = dict(kb.get("_provenance") or {})
    st = coerce_structure(prov.get("release_structure"))
    if st.get("shape") or st.get("program"):
        # provenance often stores a summary — prefer full kb copy when thin
        if st.get("program"):
            return st
    discogs = dict(ctx.get("discogs") or {})
    st = coerce_structure(discogs.get("release_structure"))
    if st.get("shape") or st.get("program") is not None:
        return st
    return {}


def is_multi_work_program(structure: ReleaseStructure | dict[str, Any] | None) -> bool:
    d = coerce_structure(structure)
    if str(d.get("shape") or "") == "multi_work_program":
        return True
    return len(d.get("program") or []) >= 2


def enrich_lock_catalogs(
    lock: dict[str, Any], structure: ReleaseStructure | dict[str, Any] | None
) -> dict[str, Any]:
    """Merge program catalogs into IntentLock (multi-work covenant)."""
    out = dict(lock or {})
    d = coerce_structure(structure)
    cats = [str(c) for c in (d.get("catalog_numbers_all") or []) if c]
    if cats:
        merged = sorted({*list(out.get("catalog_numbers") or []), *cats})
        out["catalog_numbers"] = merged
    if d.get("shape"):
        out["release_shape"] = str(d["shape"])
    if d.get("structure_ready") is not None:
        out["structure_ready"] = bool(d.get("structure_ready"))
    return out


def build_program_expand_dossier(
    structure: ReleaseStructure | dict[str, Any],
    *,
    composer: str = "",
    work_title: str = "",
    performers: list[str] | None = None,
) -> dict[str, Any]:
    """Layer-2/3 shelf dossier: one deepen stub per program work (SPEC-034 Slice C)."""
    from aulos_skills.salon_codex import empty_dossier

    d = coerce_structure(structure)
    program = []
    for p in d.get("program") or []:
        if isinstance(p, ProgramWork):
            program.append(p.to_dict())
        elif isinstance(p, dict):
            program.append(dict(p))
    if len(program) < 2:
        return {}

    title = (work_title or str(d.get("release_title") or "")).strip()
    program_composers = _dedupe_names(
        [comp for p in program for comp in (p.get("composers") or [])]
    )
    release_composers = _dedupe_names(list(d.get("composers") or []) + program_composers)
    composer_name = (composer or " / ".join(release_composers[:8])).strip()
    cats_all = [str(c) for c in (d.get("catalog_numbers_all") or []) if c]
    if not cats_all:
        cats_all = sorted(
            {c for p in program for c in (p.get("catalog_numbers") or []) if c}
        )
    n = len(program)
    out = empty_dossier()
    rid = d.get("release_id")
    out["dossier_id"] = f"release-program:{rid or 'unknown'}"
    out["work_title"] = title
    out["composer"] = composer_name
    out["catalog"] = " · ".join(cats_all[:12])
    out["era"] = "Program pressing — resolve era per catalogued work"
    out["form"] = f"Multi-work program ({n} works) on one pressing"
    out["listening_thesis"] = (
        f"Hear this pressing as a program of {n} works — lock each catalog identity "
        f"({', '.join(cats_all[:6]) or 'see tracklist'}) and its soloist contract before "
        "comparing dialogue across the shelf."
    )
    out["work_introduction"] = (
        f"{title or 'This pressing'} gathers {n} distinct works"
        + (f" by {composer_name}" if composer_name else "")
        + ". Serious listening maps the program first, then deepens each work in turn; "
        "couplings are not a license to collapse identities."
    )
    out["listening_map"] = []
    out["variation_deepdives"] = []
    out["width_points"] = [
        f"Program map: {n} works on this pressing"
        + (f" — catalogs {', '.join(cats_all[:8])}" if cats_all else "")
        + ".",
        "Treat each catalog number as its own IntentLock before comparative listening.",
    ]
    out["depth_points"] = []
    out["related_works"] = []
    zh_map: list[dict[str, str]] = []
    zh_dives: list[dict[str, Any]] = []
    zh_width = [
        f"先认清本片节目单：共 {n} 部作品"
        + (f"（{ '、'.join(cats_all[:8]) }）" if cats_all else "")
        + "。",
        "每一部作品各自锁定身份后，再做跨曲目比较。",
    ]
    zh_depth: list[str] = []

    for p in program:
        ptitle = str(p.get("title") or "Program work").strip()
        pcomposers = [str(c) for c in (p.get("composers") or []) if c]
        pcomposer = pcomposers[0] if pcomposers else composer_name
        pcats = [str(c) for c in (p.get("catalog_numbers") or []) if c]
        hints = [str(h) for h in (p.get("instruments_hint") or []) if h]
        cat_label = ", ".join(pcats) if pcats else "unnumbered"
        hint_label = ", ".join(hints) if hints else "solo / tutti"
        cue = (
            f"Catalog {cat_label}: lock opening character and {hint_label} entry "
            "before chasing brilliance."
        )
        out["listening_map"].append({"label": ptitle[:96], "cue": cue})
        zh_map.append(
            {
                "label": ptitle[:96],
                "cue": f"目录号 {cat_label}：先锁开场性格与 {hint_label} 进入，再追光彩。",
            }
        )
        try:
            work_no = int(p.get("index")) + 1
        except (TypeError, ValueError):
            work_no = len(out["variation_deepdives"]) + 1
        dive = {
            "title": ptitle[:160],
            "focus": f"Program work {work_no} · {cat_label}",
            "ear_cues": [
                f"Opening thesis for {ptitle[:80]}",
                f"Solo/tutti turns ({hint_label})",
                "Close: what remembers the opening contract?",
            ],
            "catalog": cat_label,
        }
        out["variation_deepdives"].append(dive)
        zh_dives.append(
            {
                "title": ptitle[:160],
                "focus": f"节目作品 · {cat_label}",
                "ear_cues": [
                    f"《{ptitle[:40]}》的开场命题",
                    f"独奏/全奏转折（{hint_label}）",
                    "收束如何记得开场契约？",
                ],
                "catalog": cat_label,
            }
        )
        out["depth_points"].append(
            f"Inside {ptitle[:100]} ({cat_label}): map first-movement landmarks "
            f"with ear cues for {hint_label}."
        )
        zh_depth.append(
            f"在《{ptitle[:60]}》（{cat_label}）内：用听觉地标画出第一乐章转折。"
        )
        out["width_points"].append(f"Program work: {ptitle[:120]}" + (f" [{cat_label}]" if pcats else ""))
        zh_width.append(f"节目作品：{ptitle[:120]}" + (f" [{cat_label}]" if pcats else ""))
        out["related_works"].append(
            {
                "title": (f"{pcomposer} — {ptitle}" if pcomposer else ptitle)[:180],
                "relation": "Same Discogs pressing program",
                "catalog": cat_label,
            }
        )

    performers = [str(x) for x in (performers or d.get("performers") or []) if x]
    if performers:
        out["interpretations"] = [
            {
                "artist": ", ".join(performers[:6]),
                "album": title or str(d.get("release_title") or ""),
                "why": "Primary pressing named via Discogs — comparative shelf across the program.",
                "year": str(d.get("year") or ""),
            }
        ]
    if d.get("label") or d.get("catno") or d.get("uri"):
        out["vinyl_and_discography"] = [
            {
                "label": " · ".join(
                    x for x in (str(d.get("label") or ""), str(d.get("catno") or ""), str(d.get("year") or "")) if x
                ),
                "url": str(d.get("uri") or ""),
                "note": f"Source release #{d.get('release_id') or '?'}",
            }
        ]
    out["practice_notes"] = [
        "Hearing 1: program map only — name each work/catalog before detail.",
        "Hearing 2: deepen one program work with movement landmarks.",
        "Hearing 3: compare soloist contracts across two works on the pressing.",
    ]
    out["myths_and_caveats"] = [
        "Coupling titles on multi-work pressings are not a single IntentLock work title.",
        "Do not collapse this shelf into one genre-family scaffold before program deepen.",
        "Each catalog number keeps its own form and soloist contract.",
    ]
    out["sound_world"] = {
        "original_instrument": "Per program work — see instruments_hint on each entry",
        "ensemble_notes": "Pressing-level forces may serve multiple works; verify scoring per catalog.",
        "modern_modes": ["Compare period vs modern setups across program works"],
    }
    out["zh"] = {
        "composer": composer_name,
        "listening_thesis": (
            f"把这张唱片当作 {n} 部作品的节目单来听——先锁定每部作品的目录身份"
            f"（{ '、'.join(cats_all[:6]) or '见曲目'}），再比较独奏契约。"
        ),
        "work_introduction": (
            f"{title or '本片'}汇集 {n} 部独立作品"
            + (f"（{composer_name}）" if composer_name else "")
            + "。认真的聆听先画节目单，再逐部加深；合辑标题不能吞掉作品身份。"
        ),
        "catalog": out["catalog"],
        "form": f"多作品节目单（{n} 部）",
        "width_points": zh_width[:12],
        "depth_points": zh_depth[:12],
        "listening_map": zh_map,
        "variation_deepdives": zh_dives,
        "practice_notes": [
            "第一遍：只画节目单，报出每部作品/目录号。",
            "第二遍：选一部作品画乐章地标。",
            "第三遍：比较两部作品的独奏契约。",
        ],
        "myths_and_caveats": [
            "合辑标题不是单一作品 IntentLock。",
            "认清节目单之前，禁止用单一体裁家族脚手架代替深化。",
        ],
    }
    out["zh_hans"] = dict(out["zh"])
    out["raw_format"] = "release-program-expand"
    out["_provenance"] = {
        "release_structure_expand": True,
        "program_count": n,
        "release_id": rid,
        "expansion_plan": expansion_plan(d),
    }
    return out


def apply_structure_gate(context: dict[str, Any]) -> dict[str, Any]:
    """Slice B: annotate context; refuse family scaffold when multi-work not ready."""
    st = structure_from_context(context)
    if not st:
        return context
    context["release_structure"] = st
    if not st.get("expansion_plan"):
        context["release_structure"] = {**st, "expansion_plan": expansion_plan(st)}
        st = context["release_structure"]
    fails = assert_structure_ready(st) if is_multi_work_program(st) else []
    # multi-work incomplete → hard refuse family shortcut
    if is_multi_work_program(st) and fails:
        context["structure_hard_fails"] = fails
        context["refuse_families"] = True
        corrections = list(context.get("critique_corrections") or [])
        note = "release_structure_not_ready: build program map before family deepen"
        if note not in corrections:
            corrections.insert(0, note)
        context["critique_corrections"] = corrections
    elif is_multi_work_program(st):
        context["structure_hard_fails"] = []
        context["program_expand_required"] = True
    return context
