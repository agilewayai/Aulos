"""Research knowledge base — chunk, embed, retrieve for Salon Codex RAG."""

from __future__ import annotations

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from aulos_api.db.models import KnowledgeChunk, KnowledgeDocument
from aulos_api.services.embeddings import (
    cosine,
    embed_texts_sync,
    lexical_overlap_score,
    load_embed_config,
)

logger = logging.getLogger("aulos_api.knowledge")

_WORK_KEY_RE = re.compile(r"[^a-z0-9\u4e00-\u9fff]+", re.I)
_TOKEN_RE = re.compile(r"[a-z0-9\u4e00-\u9fff]{2,}", re.I)
_SEED_FLAG = False
_STOP_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "listening",
    "guide",
    "help",
    "want",
    "learn",
    "study",
    "about",
    "work",
    "classical",
    "masterwork",
    "please",
    "begin",
    "beginning",
    "欣赏",
    "导赏",
    "帮我",
    "一份",
    "详细",
    "开始",
    "准备",
    "我想",
    "写",
}
# Composer-only tokens are too weak to claim "same work" (Bach ≠ every Bach piece).
_WEAK_IDENTITY_TOKENS = {
    "bach",
    "johann",
    "sebastian",
    "beethoven",
    "ludwig",
    "van",
    "mozart",
    "wolfgang",
    "amadeus",
    "chopin",
    "frederic",
    "debussy",
    "claude",
    "巴赫",
    "贝多芬",
    "莫扎特",
    "肖邦",
    "德彪西",
}


def normalize_work_key(title: str, composer: str = "") -> str:
    blob = f"{composer} {title}".strip().lower()
    key = _WORK_KEY_RE.sub("-", blob).strip("-")
    return (key or "unknown")[:160]


def _content_tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in _STOP_TOKENS}


def works_compatible(
    query: str,
    *,
    doc_title: str = "",
    doc_composer: str = "",
    doc_work_key: str = "",
    min_score: float = 0.0,
    score: float = 0.0,
) -> bool:
    """True when a KB document is about the same work the user asked for.

    Nearest-neighbor embeddings alone are not enough when the corpus is sparse —
    otherwise every cold query collapses onto the flagship Goldberg dossier.
    """
    q_tokens = _content_tokens(query)
    title_tokens = _content_tokens(f"{doc_title} {doc_composer}")
    if not q_tokens or not title_tokens:
        return False

    # Exact-ish work_key containment (seeded keys like bwv-988)
    hint_key = normalize_work_key(query)
    work_key = (doc_work_key or "").lower()
    if work_key and len(work_key) >= 5 and (work_key in hint_key or hint_key in work_key):
        return score >= min_score

    overlap = q_tokens & title_tokens
    distinctive = title_tokens - _WEAK_IDENTITY_TOKENS
    distinctive_hit = bool(distinctive & q_tokens)
    if distinctive_hit and score >= min_score:
        return True
    # Two+ overlapping tokens, with at least one non-composer token preferred
    if len(overlap) >= 2 and (overlap - _WEAK_IDENTITY_TOKENS) and score >= min_score:
        return True
    return False


def _ensure_skills() -> None:
    try:
        import aulos_skills  # noqa: F401
        return
    except ImportError:
        pass
    sibling = Path(__file__).resolve().parents[4] / "aulos-skills" / "src"
    if sibling.is_dir() and str(sibling) not in sys.path:
        sys.path.insert(0, str(sibling))


def flatten_dossier_chunks(dossier: dict[str, Any], *, max_chars: int = 700) -> list[tuple[str, str]]:
    """Return (section, text) chunks from a Salon Codex dossier."""
    chunks: list[tuple[str, str]] = []

    def add(section: str, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        if len(text) <= max_chars:
            chunks.append((section, text))
            return
        # split on sentences / newlines
        parts: list[str] = []
        buf = ""
        for piece in re.split(r"(?<=[。.!?\n])\s*", text):
            if not piece:
                continue
            if len(buf) + len(piece) + 1 <= max_chars:
                buf = f"{buf} {piece}".strip()
            else:
                if buf:
                    parts.append(buf)
                buf = piece
        if buf:
            parts.append(buf)
        for i, p in enumerate(parts):
            chunks.append((f"{section}:{i + 1}" if len(parts) > 1 else section, p))

    add("title", f"{dossier.get('composer', '')} — {dossier.get('work_title', '')}".strip(" —"))
    add("listening_thesis", str(dossier.get("listening_thesis") or ""))
    add("work_introduction", str(dossier.get("work_introduction") or ""))
    add("era_form", f"Era: {dossier.get('era', '')}. Form: {dossier.get('form', '')}".strip())
    profile = dict(dossier.get("composer_profile") or {})
    for k in ("summary", "temperament", "place_in_oeuvre", "place_in_history"):
        add(f"composer_profile.{k}", str(profile.get(k) or ""))
    genesis = dict(dossier.get("genesis") or {})
    for k, v in genesis.items():
        add(f"genesis.{k}", str(v or ""))
    stature = dict(dossier.get("historical_stature") or {})
    add("reception_arc", str(stature.get("reception_arc") or ""))
    for reason in stature.get("reasons") or []:
        add("stature", str(reason))
    for p in dossier.get("width_points") or []:
        add("width", str(p))
    for p in dossier.get("depth_points") or []:
        add("depth", str(p))
    for row in dossier.get("listening_map") or []:
        if isinstance(row, dict):
            add("listening_map", f"{row.get('label', '')}: {row.get('cue', '')}")
        else:
            add("listening_map", str(row))
    for row in dossier.get("variation_deepdives") or []:
        if isinstance(row, dict):
            add("deepdive", f"{row.get('title', '')}: {row.get('note', '')}")
    sound = dict(dossier.get("sound_world") or {})
    for k, v in sound.items():
        if isinstance(v, list):
            add(f"sound.{k}", "; ".join(str(x) for x in v))
        else:
            add(f"sound.{k}", str(v or ""))
    for row in dossier.get("interpretations") or []:
        if isinstance(row, dict):
            add(
                "interpretation",
                f"{row.get('artist', '')} ({row.get('year', '')}): {row.get('why_listen', '')}",
            )
    for p in dossier.get("practice_notes") or []:
        add("practice", str(p))
    for p in dossier.get("myths_and_caveats") or []:
        add("caveat", str(p))
    zh = dict(dossier.get("zh") or {})
    if zh:
        add("zh.listening_thesis", str(zh.get("listening_thesis") or ""))
        add("zh.work_introduction", str(zh.get("work_introduction") or ""))
        for p in zh.get("width_points") or []:
            add("zh.width", str(p))
        for p in zh.get("depth_points") or []:
            add("zh.depth", str(p))
    return chunks


def upsert_document(
    db: Session,
    *,
    work_key: str,
    title: str,
    composer: str,
    dossier: dict[str, Any],
    source_guide_id: int | None,
    user_id: int | None,
) -> KnowledgeDocument:
    chunk_pairs = flatten_dossier_chunks(dossier)
    content_text = "\n\n".join(t for _, t in chunk_pairs)
    # Prefer user-scoped doc; else seed (user_id None)
    q = db.query(KnowledgeDocument).filter(KnowledgeDocument.work_key == work_key)
    if user_id is None:
        q = q.filter(KnowledgeDocument.user_id.is_(None))
    else:
        q = q.filter(KnowledgeDocument.user_id == user_id)
    doc = q.one_or_none()
    if doc is None:
        doc = KnowledgeDocument(
            work_key=work_key,
            title=title,
            composer=composer,
            user_id=user_id,
        )
        db.add(doc)
        db.flush()
    doc.title = title or doc.title
    doc.composer = composer or doc.composer
    doc.source_guide_id = source_guide_id
    doc.dossier_json = json.dumps(dossier, ensure_ascii=False)
    doc.content_text = content_text
    # replace chunks
    db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).delete()
    texts = [t for _, t in chunk_pairs]
    vectors, mode = embed_texts_sync(db, texts) if texts else ([], "lexical")
    if len(vectors) < len(texts):
        from aulos_api.services.embeddings import lexical_vector

        while len(vectors) < len(texts):
            vectors.append(lexical_vector(texts[len(vectors)]))
        mode = "lexical" if mode != "vector" else mode
    cfg = load_embed_config(db)
    model_tag = cfg.model if mode in ("fastembed", "openai", "vector") else "lexical-hash"
    for (section, text), vec in zip(chunk_pairs, vectors):
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                section=section,
                text=text,
                embedding_json=json.dumps(vec),
                dims=len(vec),
                model=model_tag,
            )
        )
    db.commit()
    db.refresh(doc)
    logger.info(
        "kb_upsert work_key=%s guide=%s user=%s chunks=%s mode=%s",
        work_key,
        source_guide_id,
        user_id,
        len(chunk_pairs),
        mode,
    )
    return doc


def upsert_from_report(db: Session, *, report: Any, guide_id: int, user_id: int) -> KnowledgeDocument | None:
    ctx = getattr(report, "context", None) or {}
    dossier = dict(ctx.get("corpus_dossier") or {})
    if not dossier:
        # synthesize may have left dossier on width salon
        width = dict(ctx.get("width_dossier") or {})
        dossier = dict(width.get("salon_dossier") or {})
    if not dossier and getattr(report, "summary", None):
        dossier = {
            "work_title": report.work_title,
            "composer": report.composer,
            "listening_thesis": report.summary,
        }
    if not dossier:
        return None
    title = str(dossier.get("work_title") or report.work_title or "")
    composer = str(dossier.get("composer") or report.composer or "")
    key = normalize_work_key(title, composer)
    return upsert_document(
        db,
        work_key=key,
        title=title,
        composer=composer,
        dossier=dossier,
        source_guide_id=guide_id,
        user_id=user_id,
    )


def seed_corpus_knowledge(db: Session) -> int:
    """Index curated corpus YAML as global (user_id=None) knowledge once."""
    global _SEED_FLAG
    existing = (
        db.query(KnowledgeDocument.id)
        .filter(KnowledgeDocument.user_id.is_(None))
        .limit(1)
        .one_or_none()
    )
    if existing is not None:
        _SEED_FLAG = True
        return 0
    _ensure_skills()
    try:
        import yaml
    except ImportError:
        return 0
    roots = [
        Path(__file__).resolve().parents[4] / "aulos-skills" / "skills" / "aulos-listening-corpus" / "assets" / "corpus",
    ]
    count = 0
    for corpus_dir in roots:
        index_path = corpus_dir / "index.yaml"
        if not index_path.is_file():
            continue
        try:
            index = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            continue
        for entry in index.get("works") or index.get("entries") or []:
            rel = str(entry.get("path") or "")
            if not rel.endswith((".yaml", ".yml")):
                continue
            path = corpus_dir / rel
            if not path.is_file():
                continue
            try:
                dossier = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception:  # noqa: BLE001
                continue
            if not isinstance(dossier, dict):
                continue
            title = str(dossier.get("work_title") or entry.get("work_title") or entry.get("title") or rel)
            composer = str(dossier.get("composer") or entry.get("composer") or "")
            key = str(entry.get("key") or "") or normalize_work_key(title, composer)
            upsert_document(
                db,
                work_key=key,
                title=title,
                composer=composer,
                dossier=dossier,
                source_guide_id=None,
                user_id=None,
            )
            count += 1
    _SEED_FLAG = True
    logger.info("kb_seed_corpus docs=%s", count)
    return count


def retrieve(
    db: Session,
    *,
    query: str,
    work_hint: str = "",
    composer: str = "",
    user_id: int | None = None,
    k: int = 6,
) -> dict[str, Any]:
    """Semantic (or lexical) retrieve. Returns hits + optional merged kb_dossier."""
    seed_corpus_knowledge(db)
    qtext = " ".join(x for x in [query, work_hint, composer] if x).strip()
    if not qtext:
        return {"rag_mode": "none", "hits": [], "kb_dossier": {}, "rag_hits": []}

    hint_key = normalize_work_key(work_hint or query, composer)
    # Prefer docs matching work_key prefix / tokens
    docs = db.query(KnowledgeDocument).all()
    if user_id is not None:
        # user docs first, then global seeds
        docs = sorted(
            docs,
            key=lambda d: (
                0 if d.user_id == user_id else (1 if d.user_id is None else 2),
                0 if hint_key and hint_key in (d.work_key or "") else 1,
            ),
        )

    # Build candidate chunks — soft-filter by identity; never fall back to "all docs"
    # (that previously made every query inherit the flagship Goldberg dossier).
    chunk_rows: list[tuple[KnowledgeChunk, KnowledgeDocument]] = []
    for doc in docs:
        if hint_key and hint_key[:20] not in (doc.work_key or "") and hint_key not in (doc.work_key or ""):
            blob = f"{doc.title} {doc.composer} {doc.work_key}"
            tokens = _content_tokens(hint_key.replace("-", " "))
            if tokens and not any(t in blob.lower() for t in tokens):
                continue
        for ch in db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).all():
            chunk_rows.append((ch, doc))

    if not chunk_rows:
        return {"rag_mode": "no_match", "hits": [], "kb_dossier": {}, "rag_hits": []}

    vectors, mode = embed_texts_sync(db, [qtext])
    qvec = vectors[0] if vectors else []

    scored: list[tuple[float, KnowledgeChunk, KnowledgeDocument]] = []
    for ch, doc in chunk_rows:
        try:
            vec = json.loads(ch.embedding_json or "[]")
        except json.JSONDecodeError:
            vec = []
        if mode == "vector" and qvec and vec and len(vec) == len(qvec):
            score = cosine(qvec, vec)
        elif mode in ("fastembed", "openai") and qvec and vec and len(vec) == len(qvec):
            score = cosine(qvec, vec)
        else:
            score = lexical_overlap_score(qtext, ch.text)
            # boost same work_key
            if hint_key and hint_key in (doc.work_key or ""):
                score += 0.15
        scored.append((score, ch, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    compatible: list[tuple[float, KnowledgeChunk, KnowledgeDocument]] = []
    for score, ch, doc in scored:
        if works_compatible(
            qtext,
            doc_title=doc.title or "",
            doc_composer=doc.composer or "",
            doc_work_key=doc.work_key or "",
            min_score=0.12,
            score=float(score),
        ):
            compatible.append((score, ch, doc))

    top = (compatible or [])[:k]
    hits = []
    best_doc: KnowledgeDocument | None = None
    best_score = -1.0
    for score, ch, doc in top:
        hits.append(
            {
                "score": round(float(score), 4),
                "section": ch.section,
                "text": ch.text,
                "work_key": doc.work_key,
                "title": doc.title,
                "composer": doc.composer,
                "document_id": doc.id,
            }
        )
        if score > best_score:
            best_score = score
            best_doc = doc

    kb_dossier: dict[str, Any] = {}
    # Full dossier injection requires identity match — never nearest-neighbor alone.
    if best_doc and best_score >= 0.18 and works_compatible(
        qtext,
        doc_title=best_doc.title or "",
        doc_composer=best_doc.composer or "",
        doc_work_key=best_doc.work_key or "",
        min_score=0.18,
        score=float(best_score),
    ):
        try:
            kb_dossier = json.loads(best_doc.dossier_json or "{}")
        except json.JSONDecodeError:
            kb_dossier = {}

    rag_hits = [h["text"] for h in hits]
    logger.info(
        "kb_retrieve mode=%s hits=%s best=%s score=%.3f dossier=%s",
        mode if top else "no_match",
        len(hits),
        (best_doc.work_key if best_doc else None),
        best_score,
        bool(kb_dossier),
    )
    return {
        "rag_mode": mode if top else "no_match",
        "hits": hits,
        "kb_dossier": kb_dossier,
        "rag_hits": rag_hits,
    }


def knowledge_stats(db: Session) -> dict[str, Any]:
    seed_corpus_knowledge(db)
    docs = db.query(KnowledgeDocument).count()
    chunks = db.query(KnowledgeChunk).count()
    return {
        "documents": docs,
        "chunks": chunks,
        "embed_ready": load_embed_config(db).ready,
    }
