"""Work Identity Catalog — load + generic IdentityResolver (SPEC-008 / ADR-004).

Authority is catalog YAML under aulos-listening-corpus/assets/catalog/.
No per-work if/elif branches belong here or in intake.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_TOKEN_RE = re.compile(r"[a-z0-9\u4e00-\u9fff]{2,}", re.I)
_DEFAULT_WEAK = {
    "bach",
    "beethoven",
    "mozart",
    "chopin",
    "mahler",
    "bwv",
    "op",
    "opus",
    "suite",
    "sonata",
    "variation",
    "symphony",
    "nocturne",
    "巴赫",
    "贝多芬",
    "肖邦",
    "马勒",
}


def default_catalog_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "aulos-listening-corpus"
        / "assets"
        / "catalog"
    )


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "")}


@dataclass
class ComposerCard:
    composer_id: str
    name_en: str = ""
    name_zh: str = ""
    aliases: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkRecord:
    work_id: str
    composer_id: str
    canonical_title: str = ""
    canonical_title_zh: str = ""
    aliases: list[str] = field(default_factory=list)
    catalog_numbers: list[str] = field(default_factory=list)
    facets: dict[str, list[str]] = field(default_factory=dict)
    family_id: str | None = None
    corpus_key: str | None = None
    ambient_ref: str | None = None
    distinctive_tokens: list[str] = field(default_factory=list)
    conflict_work_ids: list[str] = field(default_factory=list)
    conflict_markers: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class IdentityResult:
    status: str  # work | composer_only | ambiguous | multi_work | unknown
    work_id: str | None = None
    composer_id: str | None = None
    work_title: str = ""
    work_title_zh: str = ""
    composer_name: str = ""
    family_id: str | None = None
    corpus_keys: list[str] = field(default_factory=list)
    ambient_ref: str | None = None
    facets: dict[str, list[str]] = field(default_factory=dict)
    conflict_markers: list[str] = field(default_factory=list)
    confidence: float = 0.0
    score: float = 0.0
    reason: str = ""

    def to_context(self) -> dict[str, Any]:
        """Fields for SkillRuntime intake / synthesize / ambient."""
        family_hints = [self.family_id] if self.family_id else []
        return {
            "identity_status": self.status,
            "work_id": self.work_id,
            "composer_id": self.composer_id,
            "work_title": self.work_title,
            "work_title_zh": self.work_title_zh,
            "composer_guess": self.composer_name,
            "family_hints": family_hints,
            "corpus_keys": list(self.corpus_keys),
            "ambient_ref": self.ambient_ref,
            "facets": dict(self.facets),
            "conflict_markers": list(self.conflict_markers),
            "identity_confidence": self.confidence,
            "identity_reason": self.reason,
        }


class WorkCatalog:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or default_catalog_root()
        self.composers: dict[str, ComposerCard] = {}
        self.works: dict[str, WorkRecord] = {}
        self.weak_tokens: set[str] = set(_DEFAULT_WEAK)
        self._load()

    def _load(self) -> None:
        if not self.root.is_dir():
            return
        policy = self.root / "policies" / "weak_tokens.yaml"
        if policy.is_file():
            data = yaml.safe_load(policy.read_text(encoding="utf-8")) or {}
            toks = data.get("tokens") or []
            self.weak_tokens = {str(t).lower() for t in toks if t}

        index_path = self.root / "index.yaml"
        index: dict[str, Any] = {}
        if index_path.is_file():
            index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}

        for entry in index.get("composers") or []:
            rel = str(entry.get("path") or "")
            path = self.root / rel
            if not path.is_file():
                continue
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            cid = str(raw.get("composer_id") or entry.get("id") or "")
            if not cid:
                continue
            self.composers[cid] = ComposerCard(
                composer_id=cid,
                name_en=str(raw.get("name_en") or ""),
                name_zh=str(raw.get("name_zh") or ""),
                aliases=[str(a) for a in (raw.get("aliases") or [])],
                raw=raw,
            )

        for entry in index.get("works") or []:
            rel = str(entry.get("path") or "")
            path = self.root / rel
            if not path.is_file():
                continue
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            wid = str(raw.get("work_id") or entry.get("id") or "")
            if not wid:
                continue
            ident = dict(raw.get("identity") or {})
            facets_raw = dict(raw.get("facets") or {})
            facets: dict[str, list[str]] = {}
            for k, v in facets_raw.items():
                if isinstance(v, list):
                    facets[k] = [str(x) for x in v]
                elif v is None or v == "":
                    facets[k] = []
                else:
                    facets[k] = [str(v)]
            corpus_key = raw.get("corpus_key")
            self.works[wid] = WorkRecord(
                work_id=wid,
                composer_id=str(raw.get("composer_id") or ""),
                canonical_title=str(raw.get("canonical_title") or ""),
                canonical_title_zh=str(raw.get("canonical_title_zh") or ""),
                aliases=[str(a) for a in (raw.get("aliases") or [])],
                catalog_numbers=[str(a) for a in (raw.get("catalog_numbers") or [])],
                facets=facets,
                family_id=(str(raw["family_id"]) if raw.get("family_id") else None),
                corpus_key=(str(corpus_key) if corpus_key else None),
                ambient_ref=(str(raw["ambient_ref"]) if raw.get("ambient_ref") else None),
                distinctive_tokens=[str(t).lower() for t in (ident.get("distinctive_tokens") or [])],
                conflict_work_ids=[str(t) for t in (ident.get("conflict_work_ids") or [])],
                conflict_markers=[str(t).lower() for t in (ident.get("conflict_markers") or [])],
                raw=raw,
            )

    def conflict_markers_for(self, work: WorkRecord) -> list[str]:
        """Markers to scrub when *this* work is primary.

        From each conflict work, take distinctive tokens / strong aliases / catalog
        numbers — NOT that work's own conflict_markers (those describe what to scrub
        when *that* work is primary, and would wrongly ban this work's own shelf).
        """
        markers: set[str] = set(m.lower() for m in work.conflict_markers if m)
        for cid in work.conflict_work_ids:
            other = self.works.get(cid)
            if not other:
                continue
            for t in other.distinctive_tokens:
                if t and t not in self.weak_tokens:
                    markers.add(t.lower())
            for a in other.aliases:
                al = a.lower().strip()
                if len(al) >= 4 and al not in self.weak_tokens:
                    markers.add(al)
            for n in other.catalog_numbers:
                nl = n.lower().strip()
                if nl and nl not in self.weak_tokens:
                    markers.add(nl)
                for tok in _tokens(n):
                    if tok in self.weak_tokens:
                        continue
                    if not tok.isalpha() or len(tok) >= 4:
                        markers.add(tok)
        own = {t.lower() for t in work.distinctive_tokens}
        own |= {a.lower() for a in work.aliases}
        # Also drop markers that are substrings of our own title (cello suite vs cello sonatas)
        title_blob = f"{work.canonical_title} {work.canonical_title_zh}".lower()
        cleaned = sorted(
            m
            for m in markers
            if m
            and m not in own
            and len(m) >= 3
            and m not in self.weak_tokens
            and m not in title_blob
        )
        return cleaned


@lru_cache(maxsize=4)
def load_catalog(root_str: str | None = None) -> WorkCatalog:
    root = Path(root_str) if root_str else default_catalog_root()
    return WorkCatalog(root)


class IdentityResolver:
    """Generic work identity scorer — data-driven, no work-name branches."""

    def __init__(self, catalog: WorkCatalog | None = None) -> None:
        self.catalog = catalog or load_catalog()

    def resolve(self, query: str, work_hint: str = "") -> IdentityResult:
        from aulos_skills.identity_lock import extract_catalog_numbers

        blob = _norm(f"{work_hint} {query}")
        if not blob:
            return IdentityResult(status="unknown", reason="empty query")

        q_tokens = _tokens(blob)
        q_nums = extract_catalog_numbers(blob)
        scored: list[tuple[float, WorkRecord, str]] = []
        for work in self.catalog.works.values():
            score, reason = self._score_work(
                work, blob=blob, q_tokens=q_tokens, query_catalog_numbers=q_nums
            )
            if score > 0:
                scored.append((score, work, reason))
        scored.sort(key=lambda x: x[0], reverse=True)

        composer_hit = self._match_composer(blob, q_tokens)

        # SPEC-032: multi unmatched catalog numbers → multi_work, never a false tie
        exact_catalog = [
            row for row in scored if any(p.startswith("catalog:") for p in row[2].split("+"))
        ]
        if len(q_nums) >= 2 and not exact_catalog:
            if composer_hit:
                card = self.catalog.composers[composer_hit]
                return IdentityResult(
                    status="multi_work",
                    composer_id=card.composer_id,
                    composer_name=card.name_en or card.name_zh,
                    confidence=0.4,
                    reason="multi_catalog_numbers",
                )
            return IdentityResult(status="multi_work", reason="multi_catalog_numbers")

        if not scored:
            if composer_hit:
                card = self.catalog.composers[composer_hit]
                return IdentityResult(
                    status="composer_only",
                    composer_id=card.composer_id,
                    composer_name=card.name_en or card.name_zh,
                    confidence=0.4,
                    reason="composer aliases only",
                )
            return IdentityResult(status="unknown", reason="no catalog match")

        best_score, best, best_reason = scored[0]
        # Require a real work-level signal (not composer surname alone)
        if best_score < 20:
            if composer_hit:
                card = self.catalog.composers[composer_hit]
                return IdentityResult(
                    status="composer_only",
                    composer_id=card.composer_id,
                    composer_name=card.name_en or card.name_zh,
                    confidence=0.35,
                    reason=f"weak work score={best_score:.0f}",
                )
            return IdentityResult(status="unknown", reason=f"weak score={best_score:.0f}")

        # Ambiguity: close scores on different works
        if len(scored) > 1 and scored[1][0] >= best_score - 5 and scored[1][0] >= 20:
            # Same composer close tie without decisive catalog/alias → ambiguous
            if scored[1][1].work_id != best.work_id:
                return IdentityResult(
                    status="ambiguous",
                    composer_id=best.composer_id,
                    composer_name=self._composer_name(best.composer_id),
                    confidence=0.45,
                    score=best_score,
                    reason=f"tie {best.work_id} vs {scored[1][1].work_id}",
                )

        return self._result_from_work(best, score=best_score, reason=best_reason)
    def _composer_name(self, composer_id: str) -> str:
        card = self.catalog.composers.get(composer_id)
        if not card:
            return ""
        return card.name_en or card.name_zh

    def _result_from_work(self, work: WorkRecord, *, score: float, reason: str) -> IdentityResult:
        markers = self.catalog.conflict_markers_for(work)
        keys = [work.corpus_key] if work.corpus_key else []
        conf = min(0.99, 0.55 + score / 200.0)
        return IdentityResult(
            status="work",
            work_id=work.work_id,
            composer_id=work.composer_id,
            work_title=work.canonical_title,
            work_title_zh=work.canonical_title_zh,
            composer_name=self._composer_name(work.composer_id),
            family_id=work.family_id,
            corpus_keys=keys,
            ambient_ref=work.ambient_ref,
            facets=dict(work.facets),
            conflict_markers=markers,
            confidence=conf,
            score=score,
            reason=reason,
        )

    def _match_composer(self, blob: str, q_tokens: set[str]) -> str | None:
        from aulos_skills.text_match import alias_in_text

        for card in self.catalog.composers.values():
            for alias in card.aliases:
                a = alias.lower().strip()
                if len(a) >= 2 and (alias_in_text(a, blob) or a in q_tokens):
                    return card.composer_id
        return None

    def _score_work(
        self,
        work: WorkRecord,
        *,
        blob: str,
        q_tokens: set[str],
        query_catalog_numbers: set[str] | None = None,
    ) -> tuple[float, str]:
        from aulos_skills.identity_lock import normalize_catalog_number
        from aulos_skills.text_match import alias_in_text, numeric_token_in_text

        score = 0.0
        reasons: list[str] = []
        q_nums = set(query_catalog_numbers or ())

        # Hard composer gate: if the query names a *different* catalog composer, reject.
        mentioned = self._mentioned_composer_ids(blob, q_tokens)
        if mentioned and work.composer_id not in mentioned:
            return 0.0, "wrong-composer"

        # Alias hits — token-boundary for short Latin aliases (SPEC-032)
        for alias in work.aliases:
            a = alias.lower().strip()
            if len(a) < 3:
                continue
            hit = alias_in_text(a, blob) if len(a) < 12 else (a in blob)
            if hit:
                bump = 55.0 if len(a) >= 8 else 40.0
                score += bump
                reasons.append(f"alias:{a}")
                break

        # Catalog numbers — exact / compact first; catalog-tok needs a digit token
        work_nums = {normalize_catalog_number(n) for n in work.catalog_numbers if n}
        exact_catalog = False
        for num in work.catalog_numbers:
            n = num.lower().strip()
            n_norm = normalize_catalog_number(num)
            n_compact = re.sub(r"[\s.\-]", "", n)
            blob_compact = re.sub(r"[\s.\-]", "", blob)
            if n and (n in blob or n_compact in blob_compact or (n_norm and n_norm in q_nums)):
                score += 45.0
                reasons.append(f"catalog:{n}")
                exact_catalog = True
                break
            num_tokens = _tokens(num)
            digit_overlap = {
                t for t in (num_tokens & q_tokens) if any(ch.isdigit() for ch in t)
            }
            # Bare prefix tokens (kv/op/bwv) alone must never score (SPEC-032).
            if digit_overlap and self._composer_mentioned(work.composer_id, blob, q_tokens):
                # When the query already locked catalog numbers, require overlap.
                if q_nums and work_nums.isdisjoint(q_nums):
                    continue
                score += 35.0
                reasons.append(f"catalog-tok:{','.join(sorted(digit_overlap))}")
                break

        # Distinctive tokens — digit runs must not match inside release ids
        composer_aliases = set()
        card = self.catalog.composers.get(work.composer_id)
        if card:
            composer_aliases = {a.lower() for a in card.aliases}
        dist_hits = []
        for t in work.distinctive_tokens:
            tl = (t or "").lower().strip()
            if not tl or tl in composer_aliases:
                continue
            if tl.isdigit() or (len(tl) <= 4 and any(ch.isdigit() for ch in tl)):
                if numeric_token_in_text(tl, blob) or tl in q_tokens:
                    dist_hits.append(tl)
            elif tl in blob or tl in q_tokens:
                dist_hits.append(tl)
        if dist_hits:
            score += min(50.0, 12.0 * len(dist_hits))
            reasons.append(f"dist:{','.join(dist_hits[:4])}")

        # Facets — when query has catalog numbers disjoint from this work, do not
        # invent a sibling win from generic facet overlap alone (SPEC-032).
        facet_hits: list[str] = []
        if not (q_nums and work_nums and work_nums.isdisjoint(q_nums) and not exact_catalog):
            for values in work.facets.values():
                for v in values:
                    vl = v.lower()
                    if vl and (vl in blob or vl in q_tokens):
                        facet_hits.append(vl)
            if facet_hits:
                score += min(24.0, 6.0 * len(set(facet_hits)))
                reasons.append(f"facet:{','.join(sorted(set(facet_hits))[:4])}")

        if score >= 12 and self._composer_mentioned(work.composer_id, blob, q_tokens):
            score += 8.0
            reasons.append("composer")

        # Require composer mention for work win when score is only generic form facets
        if score > 0 and not self._composer_mentioned(work.composer_id, blob, q_tokens):
            # Allow strong alias / catalog number without composer (e.g. "Goldberg Variations")
            if not any(r.startswith("alias:") or r.startswith("catalog:") for r in reasons):
                score *= 0.35
                reasons.append("no-composer-penalty")

        for other in self.catalog.works.values():
            if other.work_id == work.work_id:
                continue
            for alias in other.aliases:
                a = alias.lower().strip()
                if len(a) >= 5 and a in blob and a not in {x.lower() for x in work.aliases}:
                    score -= 30.0
                    reasons.append(f"foreign-alias:{a}")
                    break

        return max(0.0, score), "+".join(reasons) or "none"

    def _mentioned_composer_ids(self, blob: str, q_tokens: set[str]) -> set[str]:
        from aulos_skills.text_match import alias_in_text

        found: set[str] = set()
        for card in self.catalog.composers.values():
            for alias in card.aliases:
                a = alias.lower().strip()
                if len(a) >= 3 and (alias_in_text(a, blob) or a in q_tokens):
                    found.add(card.composer_id)
                    break
        return found

    def _composer_mentioned(self, composer_id: str, blob: str, q_tokens: set[str]) -> bool:
        from aulos_skills.text_match import alias_in_text

        card = self.catalog.composers.get(composer_id)
        if not card:
            return False
        for alias in card.aliases:
            a = alias.lower().strip()
            if len(a) >= 2 and (alias_in_text(a, blob) or a in q_tokens):
                return True
        return False


def resolve_identity(
    query: str,
    work_hint: str = "",
    *,
    catalog_root: Path | None = None,
) -> IdentityResult:
    catalog = load_catalog(str(catalog_root) if catalog_root else None)
    return IdentityResolver(catalog).resolve(query, work_hint=work_hint)
