"""Lexical retrieve for published chunks (pgvector path later)."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from aulos_knowledge.db import KnowledgeChunk, KnowledgeDocument

_TOKEN = re.compile(r"[a-z0-9\u4e00-\u9fff]{2,}", re.I)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text or "")}


def lexical_score(query: str, text: str) -> float:
    qt = _tokens(query)
    tt = _tokens(text)
    if not qt or not tt:
        return 0.0
    return len(qt & tt) / max(1, len(qt))


def retrieve(
    db: Session,
    *,
    query: str,
    work_id: str = "",
    composer_id: str = "",
    k: int = 6,
) -> dict[str, Any]:
    q = (
        db.query(KnowledgeChunk, KnowledgeDocument)
        .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
        .filter(KnowledgeDocument.status == "published")
    )
    if work_id:
        q = q.filter(
            (KnowledgeChunk.aulos_work_id == work_id)
            | (KnowledgeDocument.aulos_work_id == work_id)
            | (KnowledgeDocument.entity_id == work_id)
        )
    rows = q.limit(500).all()
    scored: list[tuple[float, KnowledgeChunk, KnowledgeDocument]] = []
    for ch, doc in rows:
        s = lexical_score(query, f"{doc.title} {ch.text}")
        if composer_id and composer_id not in f"{doc.entity_id} {doc.body}".lower() and not work_id:
            # soft: still allow if score strong
            if s < 0.35:
                continue
        if s > 0:
            scored.append((s, ch, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = []
    for s, ch, doc in scored[:k]:
        hits.append(
            {
                "score": round(s, 4),
                "section": ch.section,
                "text": ch.text,
                "title": doc.title,
                "document_id": doc.id,
                "aulos_work_id": doc.aulos_work_id or ch.aulos_work_id,
                "source_id": doc.source_id,
                "artifact_id": doc.artifact_id,
                "job_id": doc.job_id,
            }
        )
    return {"hits": hits, "rag_mode": "lexical-knowledge", "k": k}
