"""Unknown-case archetype floor — mechanism thicken without Catalog (SPEC-029)."""

from __future__ import annotations

from typing import Any

from aulos_skills.prose_hygiene import infer_form_label
from aulos_skills.salon_codex import coerce_dict, family_to_dossier


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



def build_archetype_floor(
    work_title: str,
    composer: str,
    *,
    classification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parameterized bilingual Salon floor from FacetClassifier archetype."""
    clf = dict(classification or {})
    arch_id = str(clf.get("archetype_id") or "chamber-generic").strip() or "chamber-generic"
    title = (work_title or "").strip()
    name = (composer or "").strip()
    short = _short_title(title, name) or title or arch_id

    fam: dict[str, Any] = {}
    if arch_id != "chamber-generic":
        try:
            from aulos_skills.family_packs import load_family_pack

            fam = load_family_pack(arch_id)
        except Exception:  # noqa: BLE001
            fam = {}

    if fam:
        base = family_to_dossier(fam, composer=name, work_title=title)
        used_dimension = False
    else:
        # Dimensional voices — never a hand case scaffold
        from aulos_skills.dimension_templates import build_dimension_template

        base = dict(build_dimension_template(title, name, classification=clf))
        used_dimension = True

    base["work_title"] = title or str(base.get("work_title") or short)
    base["composer"] = name or str(base.get("composer") or "")

    facets = {
        "instruments": list(clf.get("instruments") or []),
        "forms": list(clf.get("forms") or []),
        "era": clf.get("era") or "",
    }
    if clf.get("era") and not str(base.get("era") or "").strip():
        base["era"] = str(clf["era"])
    if not str(base.get("form") or "").strip():
        base["form"] = infer_form_label(
            work_title=title,
            form=str(base.get("form") or ""),
            facets=facets,
        )

    thesis = str(base.get("listening_thesis") or "")
    if short and short.lower() not in thesis.lower() and thesis:
        lead = thesis[0].lower() + thesis[1:] if thesis and thesis[0].isupper() else thesis
        base["listening_thesis"] = f"In {short}: {lead}"
    elif short and not thesis:
        base["listening_thesis"] = (
            f"Hear {short} as a focused listening room — lock opening character first."
        )

    intro = str(base.get("work_introduction") or "")
    if title and title not in intro:
        base["work_introduction"] = (
            f"{title}. {intro}" if intro else f"{title} — archetype craft floor."
        )

    zh = coerce_dict(base.get("zh") or base.get("zh_hans"))
    zh_thesis = str(zh.get("listening_thesis") or "").strip()
    if short and zh_thesis and short[:4] not in zh_thesis and short not in zh_thesis:
        zh["listening_thesis"] = f"就{short}而言：{zh_thesis}"
    elif short and not zh_thesis:
        zh["listening_thesis"] = (
            f"把{short}当作一个专注的聆听房间——先锁住开场性格与主要动机，再追装饰或传说。"
        )
    if name and not str(zh.get("composer") or "").strip():
        zh["composer"] = name
    if title and not str(zh.get("work_title") or "").strip():
        zh["work_title"] = title
    if zh:
        base["zh"] = zh
        base["zh_hans"] = dict(zh)

    if used_dimension and str(base.get("dossier_id") or "").startswith("dimension:"):
        pass
    else:
        base["dossier_id"] = f"archetype:{arch_id}"
        base["raw_format"] = "unknown-case-archetype"
    base["family_id"] = arch_id
    prov = coerce_dict(base.get("_provenance"))
    prov["unknown_case_thicken"] = True
    prov["archetype_id"] = arch_id
    prov["facet_confidence"] = float(clf.get("confidence") or 0.0)
    if used_dimension:
        prov["dimension_template"] = True
    base["_provenance"] = prov
    return base
