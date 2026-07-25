"""S2 unit: _rag_context passes Catalog work_id into knowledge plane retrieve."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aulos_api.services.listening_guide import _rag_context


def test_rag_context_passes_work_id_when_plane_enabled(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_retrieve_sync(*, query: str, work_id: str = "", composer_id: str = "", k: int = 6):
        calls.append({"query": query, "work_id": work_id, "composer_id": composer_id, "k": k})
        return {
            "hits": [
                {
                    "title": "Cello Suites",
                    "text": "unaccompanied cello",
                    "aulos_work_id": "bach.cello-suites.bwv-1007-1012",
                    "score": 0.9,
                },
                {
                    "title": "Goldberg",
                    "text": "Aria bass",
                    "aulos_work_id": "bach.goldberg.bwv-988",
                    "score": 0.8,
                },
            ]
        }

    monkeypatch.setattr(
        "aulos_api.services.knowledge_proxy.knowledge_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "aulos_api.services.knowledge_proxy.retrieve_sync",
        fake_retrieve_sync,
    )

    with patch("aulos_api.services.listening_guide.kb_retrieve") as kb:
        kb.return_value = {"rag_mode": "lexical", "hits": [], "kb_dossier": {}, "rag_hits": []}
        out = _rag_context(
            MagicMock(),
            message="巴赫大提琴无伴奏组曲导赏",
            work_hint="",
            composer="",
            user_id=1,
        )

    assert calls and calls[0]["work_id"] == "bach.cello-suites.bwv-1007-1012"
    assert out.get("knowledge_work_id") == "bach.cello-suites.bwv-1007-1012"
    titles = " ".join(h.get("title") or "" for h in (out.get("hits") or []))
    assert "Goldberg" not in titles
    assert "Cello" in titles or out.get("rag_hits")
