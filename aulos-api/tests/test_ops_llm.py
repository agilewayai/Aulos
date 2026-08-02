"""Ops LLM provider configuration tests (DeepSeek + Grok)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "llm.db"
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


def _admin_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.com", "password": "AdminPass123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_llm_config_defaults_and_save(client: TestClient) -> None:
    headers = _admin_headers(client)
    got = client.get("/v1/ops/llm", headers=headers)
    assert got.status_code == 200, got.text
    body = got.json()
    assert body["active_provider"] == "fake"
    assert body["ready_for_live"] is False
    assert body["draft_provider"] == "deepseek"
    assert body["review_provider"] == "grok"
    assert body["deepseek"]["model"] == "deepseek-chat"
    assert body["grok"]["model"] == "grok-3-mini"
    assert "deepseek" in body["supported_providers"]
    assert any(o["id"] == "deepseek-chat" for o in body["model_options"]["deepseek"])
    assert any(o["id"] == "grok-3-mini" for o in body["model_options"]["grok"])

    saved = client.put(
        "/v1/ops/llm",
        headers=headers,
        json={
            "active_provider": "deepseek",
            "deepseek_api_key": "sk-deepseek-test",
            "deepseek_model": "deepseek-chat",
            "deepseek_base_url": "https://api.deepseek.com",
            "grok_model": "grok-3-mini",
        },
    )
    assert saved.status_code == 200, saved.text
    out = saved.json()
    assert out["active_provider"] == "deepseek"
    assert out["ready_for_live"] is True
    assert out["deepseek"]["api_key_set"] is True
    assert out["deepseek"]["ready"] is True

    # blank key keeps existing
    keep = client.put(
        "/v1/ops/llm",
        headers=headers,
        json={"active_provider": "deepseek", "deepseek_api_key": ""},
    )
    assert keep.status_code == 200
    assert keep.json()["deepseek"]["api_key_set"] is True


def test_llm_test_fake_and_mocked_live(client: TestClient) -> None:
    headers = _admin_headers(client)
    fake = client.post("/v1/ops/llm/test", headers=headers, json={"provider": "fake"})
    assert fake.status_code == 200
    assert fake.json()["ok"] is True

    client.put(
        "/v1/ops/llm",
        headers=headers,
        json={
            "active_provider": "grok",
            "grok_api_key": "xai-test",
            "grok_model": "grok-3-mini",
            "grok_base_url": "https://api.x.ai/v1",
        },
    )

    with patch(
        "aulos_api.services.llm_providers.invoke_openai_compatible",
        new=AsyncMock(return_value="ok"),
    ):
        probed = client.post("/v1/ops/llm/test", headers=headers, json={"provider": "grok"})
    assert probed.status_code == 200, probed.text
    assert probed.json()["provider"] == "grok"
    assert probed.json()["ok"] is True


def test_grok_env_key_drop_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """XAI_API_KEY in env fills the Grok slot so Ops only needs a key later."""
    from aulos_api.services.llm_providers import LlmProvidersConfig, apply_env_llm_overrides

    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("AULOS_GROK_API_KEY", raising=False)
    monkeypatch.delenv("AULOS_LLM_PROVIDER", raising=False)

    empty = apply_env_llm_overrides(LlmProvidersConfig())
    assert empty.grok.model == "grok-3-mini"
    assert empty.grok.base_url == "https://api.x.ai/v1"
    assert not empty.grok.api_key
    assert empty.ready_for_live is False

    monkeypatch.setenv("XAI_API_KEY", "xai-from-host-env")
    monkeypatch.setenv("AULOS_LLM_PROVIDER", "grok")
    merged = apply_env_llm_overrides(LlmProvidersConfig())
    assert merged.grok.api_key == "xai-from-host-env"
    assert merged.grok.model == "grok-3-mini"
    assert merged.active_provider == "grok"
    assert merged.ready_for_live is True


def test_draft_and_review_providers_split() -> None:
    """Multi-agent: draft=DeepSeek, review=Grok; review does not fall back to draft."""
    from aulos_api.services.llm_providers import LlmProvidersConfig, ProviderCredentials

    cfg = LlmProvidersConfig(
        active_provider="deepseek",
        draft_provider="deepseek",
        review_provider="grok",
        deepseek=ProviderCredentials(
            api_key="sk-ds", model="deepseek-chat", base_url="https://api.deepseek.com"
        ),
        grok=ProviderCredentials(
            api_key="xai-g", model="grok-3-mini", base_url="https://api.x.ai/v1"
        ),
    )
    assert cfg.resolve_role_provider("draft") == "deepseek"
    assert cfg.resolve_role_provider("review") == "grok"
    assert cfg.ready_for_draft is True
    assert cfg.ready_for_review is True

    # Grok key missing → review returns None (no DeepSeek rubber-stamp)
    cfg.grok.api_key = ""
    assert cfg.resolve_role_provider("draft") == "deepseek"
    assert cfg.resolve_role_provider("review") is None


def test_chat_uses_ops_llm_when_ready(client: TestClient) -> None:
    headers = _admin_headers(client)
    client.put(
        "/v1/ops/llm",
        headers=headers,
        json={
            "active_provider": "deepseek",
            "deepseek_api_key": "sk-test",
            "deepseek_model": "deepseek-chat",
        },
    )
    with patch(
        "aulos_api.services.llm_providers.invoke_openai_compatible",
        new=AsyncMock(return_value="hello from deepseek"),
    ):
        chat = client.post(
            "/v1/chat",
            headers=headers,
            json={"message": "hi", "thread_id": "t1"},
        )
    assert chat.status_code == 200, chat.text
    body = chat.json()
    assert body["reply"] == "hello from deepseek"
    assert body["source"] == "deepseek"
