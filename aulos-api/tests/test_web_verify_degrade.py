"""META-001 §4.1 — LLM verify failure must degrade to web_search_raw floor."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_verify_llm_error_returns_raw_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    from aulos_api.services import web_research as wr

    monkeypatch.setattr(
        wr,
        "load_llm_config",
        lambda _db: SimpleNamespace(ready_for_live=True),
    )
    monkeypatch.setattr(
        wr,
        "chat_with_ops_llm",
        AsyncMock(side_effect=RuntimeError("401 unauthorized")),
    )
    out = await wr.verify_sources_to_dossier(
        db=None,  # type: ignore[arg-type]
        work_title="Johann Sebastian Bach BWV 1041 Violin Concerto",
        composer="Johann Sebastian Bach",
        work_id="",
        facets={},
        sources=[
            {
                "provider": "brave",
                "title": "BWV 1041",
                "snippet": "A-minor ritornello concerto",
                "url": "https://example.test/1041",
            }
        ],
    )
    assert out
    assert out["_provenance"]["method"] == "web_search_raw"
    assert out["_provenance"]["verified"] is False
    assert out["width_points"]
    assert "ritornello" in out["width_points"][0].lower()
