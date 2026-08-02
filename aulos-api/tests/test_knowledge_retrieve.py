"""Knowledge retrieve must not hijack unrelated queries onto Goldberg."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aulos_api.services.knowledge_base import works_compatible


def test_works_compatible_requires_distinctive_overlap() -> None:
    assert works_compatible(
        "Bach Goldberg Variations",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.5,
    )
    assert not works_compatible(
        "Mozart Symphony No. 40",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.55,
    )
    assert not works_compatible(
        "Bach Mass in B minor",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.66,
    )
    # Catalog prefix "BWV" alone must never equate Cello Suites with Goldberg
    assert not works_compatible(
        "Bach Cello Suites BWV 1007–1012",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.9,
    )
    assert not works_compatible(
        "巴赫 大提琴无伴奏组曲",
        doc_title="J.S. Bach — Goldberg Variations, BWV 988",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bwv-988",
        score=0.85,
    )


def test_works_compatible_rejects_discogs_template_and_foreign_composer() -> None:
    """Packaging tokens + mangled prior guide must not unlock a foreign dossier.

    Failure class: Discogs-templated Bach query shared 'Discogs'/'Performers'/'Release'
    with an indexed Brahms/Hindemith pressing whose composer/title were swapped.
    """
    bach_discogs_query = (
        "/discogs #3796623 Write a professional classical listening guide "
        "for Violin Concerto BWV 1060. Composers: Johann Sebastian Bach "
        "Performers: Arthur Grumiaux Discogs release Philips"
    )
    assert not works_compatible(
        bach_discogs_query,
        doc_title="Johannes Brahms, Paul Hindemith, Hirofumi Fukai. Discogs release 32",
        doc_composer="Sonate Für Viola. Performers",
        doc_work_key="sonate-f-r-viola-performers-hindemith",
        locked_composer="Johann Sebastian Bach",
        score=0.72,
    )
    # Honest same-work Discogs packaging still matches on catalog/work tokens.
    assert works_compatible(
        bach_discogs_query,
        doc_title="Bach — Concerto in D minor BWV 1060 for Oboe and Violin",
        doc_composer="Johann Sebastian Bach",
        doc_work_key="bach-bwv-1060-oboe-violin",
        locked_composer="Johann Sebastian Bach",
        score=0.72,
    )


def test_retrieve_refuses_self_poisoned_foreign_catalog_dossier(
    client: TestClient,
) -> None:
    """Bach-labeled KB row whose chambers carry another work's catalog must not inject."""
    from aulos_api.db.models import KnowledgeChunk, KnowledgeDocument
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.services.knowledge_base import retrieve

    get_engine()
    db = SessionLocal()
    try:
        poisoned = {
            "composer": "Johann Sebastian Bach",
            "work_title": "Bach — Concerto BWV 1060",
            "listening_thesis": "Focus on Op. 11 No. 5 viola sonata architecture.",
            "form": "Viola sonata",
            "work_introduction": "Hindemith Op. 11 for solo viola.",
            "width_points": ["欣德米特中提琴奏鸣曲"],
        }
        doc = KnowledgeDocument(
            work_key="test-poisoned-bach-bwv1060",
            composer="Johann Sebastian Bach",
            title="Johann Sebastian Bach — Concerto BWV 1060",
            dossier_json=json.dumps(poisoned, ensure_ascii=False),
            content_text="Bach BWV 1060 poisoned with Op. 11",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        db.add(
            KnowledgeChunk(
                document_id=doc.id,
                section="listening_thesis",
                text="Bach BWV 1060 concerto for oboe and violin",
                embedding_json="[]",
            )
        )
        db.commit()
        result = retrieve(
            db,
            query="Bach Concerto BWV 1060 for Oboe and Violin listening guide",
            work_hint="Johann Sebastian Bach — Concerto BWV 1060 for Oboe and Violin",
            composer="Johann Sebastian Bach",
            user_id=1,
            k=6,
        )
        dossier = result.get("kb_dossier") or {}
        blob = json.dumps(dossier, ensure_ascii=False).lower()
        assert "hindemith" not in blob and "欣德" not in blob
        assert "op11" not in blob.replace(" ", "").replace(".", "")
        for h in result.get("hits") or []:
            assert h.get("document_id") != doc.id
    finally:
        db.close()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "kb.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

    from aulos_api.config import get_settings
    from aulos_api.db import session as db_session

    get_settings.cache_clear()
    db_session.reset_engine()

    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
    db_session.reset_engine()


def test_retrieve_does_not_attach_goldberg_to_mozart(client: TestClient) -> None:
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.services.knowledge_base import retrieve, seed_corpus_knowledge

    get_engine()
    db = SessionLocal()
    try:
        seed_corpus_knowledge(db)
        result = retrieve(
            db,
            query="Mozart Symphony No. 40",
            work_hint="Mozart Symphony No. 40",
            composer="",
            user_id=1,
            k=6,
        )
        assert not (result.get("kb_dossier") or {}).get("work_title")
        assert result.get("rag_mode") in {"no_match", "empty", "lexical", "vector", "fastembed", "openai"}
        for hit in result.get("hits") or []:
            assert "Goldberg" not in (hit.get("title") or "")
    finally:
        db.close()


def test_retrieve_does_not_attach_goldberg_to_cello_suites(client: TestClient) -> None:
    """Regression: shared 'Bach'+'BWV' must not inject Goldberg kb_dossier onto cello suites."""
    from aulos_api.db.session import SessionLocal, get_engine
    from aulos_api.services.knowledge_base import retrieve, seed_corpus_knowledge

    get_engine()
    db = SessionLocal()
    try:
        seed_corpus_knowledge(db)
        for query, hint in (
            ("Bach Cello Suites BWV 1007-1012", "Bach Cello Suites BWV 1007-1012"),
            ("巴赫大提琴无伴奏组曲", "巴赫大提琴无伴奏组曲"),
            ("I'm listening to Bach unaccompanied cello suites", "Bach unaccompanied cello suites"),
        ):
            result = retrieve(db, query=query, work_hint=hint, composer="Johann Sebastian Bach", user_id=1, k=6)
            dossier = result.get("kb_dossier") or {}
            title = str(dossier.get("work_title") or "")
            assert "Goldberg" not in title, f"polluted dossier for {query!r}: {title}"
            assert "哥德堡" not in title
            for hit in result.get("hits") or []:
                assert "Goldberg" not in (hit.get("title") or "")
                assert "988" not in (hit.get("title") or "")
    finally:
        db.close()
