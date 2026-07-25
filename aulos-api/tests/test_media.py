"""Media cache / proxy tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from aulos_api.services.media_cache import host_allowed, validate_source_url


def test_host_allowlist() -> None:
    assert host_allowed("https://upload.wikimedia.org/wikipedia/commons/x.ogg")
    assert host_allowed("https://archive.org/download/x/y.mp3")
    assert not host_allowed("https://evil.example/x.ogg")
    assert not host_allowed("http://127.0.0.1/secret.ogg")
    assert not host_allowed("https://169.254.169.254/latest/meta-data")


def test_validate_rejects_bad_hosts() -> None:
    with pytest.raises(ValueError):
        validate_source_url("https://attacker.test/a.ogg")


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "media.db"
    cache_dir = tmp_path / "media-cache"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-not-for-prod-32bytes-min!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "fake")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "AdminPass123!")
    monkeypatch.setenv("AULOS_WEB_BASE_URL", "http://127.0.0.1:5173")
    monkeypatch.setenv("AULOS_API_FAKE_AGENT", "true")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("AULOS_MEDIA_CACHE_DIR", str(cache_dir))

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


def test_media_rejects_non_allowlisted(client: TestClient) -> None:
    res = client.get("/v1/media/audio", params={"src": "https://evil.example/x.ogg", "mode": "cache"})
    assert res.status_code == 400


def test_media_serves_from_cache(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    url = "https://upload.wikimedia.org/wikipedia/commons/4/42/Goldberg_Variations_01_Aria.ogg"
    from aulos_api.services import media_cache as mc

    cache_dir = Path(mc.media_cache_dir())
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{mc.cache_key(url)}.ogg"
    path.write_bytes(b"OggS\x00fake-audio-bytes")

    res = client.get("/v1/media/audio", params={"src": url, "mode": "cache"})
    assert res.status_code == 200, res.text
    assert res.headers.get("x-aulos-media-mode") == "cache"
    assert res.content.startswith(b"OggS")
    disp = (res.headers.get("content-disposition") or "").lower()
    assert "inline" in disp
    assert "attachment" not in disp


def test_media_proxy_streams(client: TestClient) -> None:
    url = "https://upload.wikimedia.org/wikipedia/commons/demo.ogg"

    class FakeStream:
        status_code = 200
        headers = {"content-type": "audio/ogg", "content-length": "4"}

        async def aiter_bytes(self, _size: int = 65536):
            yield b"OggS"

        async def aclose(self):
            return None

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def build_request(self, *a, **k):
            return MagicMock()

        async def send(self, _req, stream: bool = False):
            return FakeStream()

        async def aclose(self):
            return None

    with patch("aulos_api.routes.media.httpx.AsyncClient", FakeClient):
        res = client.get("/v1/media/audio", params={"src": url, "mode": "proxy"})
    assert res.status_code == 200
    assert res.headers.get("x-aulos-media-mode") == "proxy"
    assert res.content == b"OggS"
