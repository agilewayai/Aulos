"""Document publish policy for ingest (REQ-008 / ADR-006)."""

from __future__ import annotations

from aulos_knowledge.db import SourceAuthority

AUTO_PUBLISH_ORIGINS = frozenset({"identity_seed", "encyclopedia"})


def document_status_for_source(source: SourceAuthority | None) -> str:
    """Default ingest status. Auto-publish only for verified tier-S encyclopedia/identity."""
    if source is None:
        return "quarantine"
    if (source.verification_status or "") != "verified":
        return "quarantine"
    if (source.tier or "").upper() != "S":
        return "quarantine"
    origin = (source.origin_class or "").strip() or "encyclopedia"
    if origin not in AUTO_PUBLISH_ORIGINS:
        return "quarantine"
    return "published"
