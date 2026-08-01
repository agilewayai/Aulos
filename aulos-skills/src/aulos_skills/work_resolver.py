"""Work Resolver — packaging-cleaned Discogs/hint → Catalog work_id (SPEC-024)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aulos_skills.identity import IdentityResult, IdentityResolver, load_catalog, resolve_identity
from aulos_skills.prose_hygiene import clean_packaging_work_title


@dataclass
class ResolvedWork:
    work_title: str
    composer: str
    work_id: str | None = None
    composer_id: str | None = None
    family_id: str | None = None
    corpus_keys: list[str] | None = None
    ambient_ref: str | None = None
    conflict_markers: list[str] | None = None
    status: str = "unknown"
    reason: str = ""
    from_discogs: bool = False
    identity: IdentityResult | None = None

    def to_intake_fields(self) -> dict[str, Any]:
        return {
            "work_title": self.work_title,
            "composer": self.composer,
            "composer_guess": self.composer,
            "work_id": self.work_id,
            "composer_id": self.composer_id,
            "family_hints": [self.family_id] if self.family_id else [],
            "corpus_keys": list(self.corpus_keys or []),
            "ambient_ref": self.ambient_ref,
            "conflict_markers": list(self.conflict_markers or []),
            "identity_status": self.status,
            "work_resolver_reason": self.reason,
        }


def _discogs_seed(kb: dict[str, Any] | None) -> tuple[str, str, bool]:
    kb = dict(kb or {})
    prov = dict(kb.get("_provenance") or {})
    from_discogs = bool(
        prov.get("source") == "discogs"
        or prov.get("discogs")
        or kb.get("discogs_release_id")
        or kb.get("_discogs")
    )
    title = str(kb.get("work_title") or "").strip()
    composer = str(kb.get("composer") or "").strip()
    return title, composer, from_discogs


def _identity_from_work_id(work_id: str) -> IdentityResult | None:
    wid = (work_id or "").strip()
    if not wid:
        return None
    cat = load_catalog()
    work = cat.works.get(wid)
    if not work:
        return None
    return IdentityResolver(cat)._result_from_work(work, score=100.0, reason=f"kb_seed:{wid}")


def resolve_listening_work(
    *,
    raw_message: str = "",
    work_hint: str = "",
    kb_dossier: dict[str, Any] | None = None,
) -> ResolvedWork:
    """Resolve listening identity: clean packaging, then Catalog, keep Discogs facts."""
    kb = dict(kb_dossier or {})
    kb_title, kb_composer, from_discogs = _discogs_seed(kb)
    hint = (work_hint or "").strip()
    message = (raw_message or "").strip()

    # Prefer API-stamped Catalog lock on the Discogs/KB seed
    seeded = _identity_from_work_id(str(kb.get("work_id") or ""))
    if seeded and seeded.status == "work":
        family_id = seeded.family_id or (str(kb.get("family_id") or "") or None)
        return ResolvedWork(
            work_title=seeded.work_title or clean_packaging_work_title(kb_title, composer=kb_composer),
            composer=seeded.composer_name or kb_composer,
            work_id=seeded.work_id,
            composer_id=seeded.composer_id,
            family_id=family_id,
            corpus_keys=list(seeded.corpus_keys or []),
            ambient_ref=seeded.ambient_ref,
            conflict_markers=list(seeded.conflict_markers or []),
            status="work",
            reason=seeded.reason or "kb_seed_work_id",
            from_discogs=from_discogs,
            identity=seeded,
        )

    # Only trust KB title when Discogs provenance is present — polluted KB titles
    # (e.g. Goldberg seed on a cello-suite request) must not hijack resolve.
    candidate = ""
    if from_discogs and kb_title:
        candidate = kb_title
    elif hint:
        candidate = hint

    composer = kb_composer if from_discogs else ""
    cleaned = clean_packaging_work_title(candidate, composer=composer) if candidate else ""
    if not cleaned and hint:
        cleaned = clean_packaging_work_title(hint, composer=composer)

    resolve_query = " ".join(x for x in (composer, cleaned, message) if x).strip() or message
    resolve_hint = cleaned or hint
    identity = resolve_identity(resolve_query, work_hint=resolve_hint)

    work_title = cleaned
    if identity.status == "work" and identity.work_title:
        work_title = identity.work_title
        composer = identity.composer_name or composer
    elif not work_title:
        work_title = ""

    if from_discogs and kb_composer and not composer:
        composer = kb_composer
    if from_discogs and kb_title and identity.status != "work":
        work_title = clean_packaging_work_title(kb_title, composer=composer) or work_title

    family_id = identity.family_id if identity.status == "work" else None
    if not family_id and kb.get("family_id") and identity.status == "work":
        family_id = str(kb["family_id"])

    return ResolvedWork(
        work_title=work_title,
        composer=composer or (identity.composer_name or ""),
        work_id=identity.work_id if identity.status == "work" else None,
        composer_id=identity.composer_id,
        family_id=family_id,
        corpus_keys=list(identity.corpus_keys or []) if identity.status == "work" else [],
        ambient_ref=identity.ambient_ref if identity.status == "work" else None,
        conflict_markers=list(identity.conflict_markers or []) if identity.status == "work" else [],
        status=identity.status,
        reason=identity.reason or ("discogs+catalog" if from_discogs else "catalog"),
        from_discogs=from_discogs,
        identity=identity,
    )
