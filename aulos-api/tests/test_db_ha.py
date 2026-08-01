"""Business DB HA: primary → failover clone + role switch."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def ha_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    primary = tmp_path / "primary.db"
    failover = tmp_path / "failover.db"
    monkeypatch.setenv("AULOS_DB_URL", f"sqlite:///{primary}")
    monkeypatch.setenv("AULOS_DB_FAILOVER_URL", f"sqlite:///{failover}")
    monkeypatch.setenv("AULOS_DB_ACTIVE_ROLE", "primary")
    monkeypatch.setenv("AULOS_DB_SYNC_ENABLED", "false")
    monkeypatch.setenv("AULOS_DB_AUTO_FAILOVER", "false")
    monkeypatch.setenv("AULOS_REDIS_URL", "")
    monkeypatch.setenv("AULOS_DB_SYNC_REDIS_URL", "")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_EMAIL", "ha-admin@example.com")
    monkeypatch.setenv("AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD", "HaAdminPass123!")
    monkeypatch.setenv("AULOS_JWT_SECRET", "test-secret-ha-32chars-minimum!!")
    monkeypatch.setenv("AULOS_MAIL_PROVIDER", "console")
    monkeypatch.setenv("AULOS_RATE_LIMIT_ENABLED", "false")

    from aulos_api.config import get_settings

    get_settings.cache_clear()
    from aulos_api.db.session import reset_engine
    from aulos_api.services import db_ha

    reset_engine()
    db_ha.reset_ha_engines()
    db_ha._worker_started = False  # noqa: SLF001
    db_ha._stop.clear()  # noqa: SLF001

    from aulos_api.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c

    reset_engine()
    get_settings.cache_clear()


def _admin_token(client: TestClient) -> str:
    r = client.post(
        "/v1/auth/login",
        json={"email": "ha-admin@example.com", "password": "HaAdminPass123!"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def test_ha_status_and_clone(ha_client: TestClient) -> None:
    token = _admin_token(ha_client)
    h = ha_client.get("/v1/ops/db/ha", headers={"Authorization": f"Bearer {token}"})
    assert h.status_code == 200
    body = h.json()
    assert body["active_role"] == "primary"
    assert body["failover"]["configured"] is True
    assert body["primary"]["ok"] is True
    assert body["pool"]["probe_isolated"] is True
    assert body["pool"]["failover_fail_threshold"] >= 1

    sync = ha_client.post(
        "/v1/ops/db/sync?queue=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert sync.status_code == 200, sync.text
    assert sync.json()["status"] == "ok"
    assert sync.json()["row_total"] >= 1  # at least roles / superadmin

    role = ha_client.post(
        "/v1/ops/db/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "failover", "reason": "test"},
    )
    assert role.status_code == 200
    assert role.json()["active_role"] == "failover"

    # Still can login against failover mirror
    r = ha_client.post(
        "/v1/auth/login",
        json={"email": "ha-admin@example.com", "password": "HaAdminPass123!"},
    )
    assert r.status_code == 200


def test_pool_kwargs_postgres_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AULOS_DB_POOL_SIZE", "20")
    monkeypatch.setenv("AULOS_DB_MAX_OVERFLOW", "40")
    monkeypatch.setenv("AULOS_DB_FAILOVER_FAIL_THRESHOLD", "3")
    from aulos_api.config import get_settings

    get_settings.cache_clear()
    from aulos_api.services.db_ha import _pool_kwargs_for_url

    kw = _pool_kwargs_for_url("postgresql+psycopg://aulos:aulos@127.0.0.1:5433/aulos")
    assert kw["pool_size"] == 20
    assert kw["max_overflow"] == 40
    assert _pool_kwargs_for_url("sqlite:///./tmp.db") == {}
    get_settings.cache_clear()


def test_probe_uses_isolated_engine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Probe must not borrow from the business QueuePool (false primary_down)."""
    db = tmp_path / "probe.db"
    url = f"sqlite:///{db}"
    monkeypatch.setenv("AULOS_DB_URL", url)
    from aulos_api.config import get_settings

    get_settings.cache_clear()
    from aulos_api.services import db_ha

    db_ha.reset_ha_engines()
    business = db_ha._make_engine(url)  # noqa: SLF001
    probe_eng = db_ha._probe_engine_for(url)  # noqa: SLF001
    assert probe_eng is not business
    assert probe_eng.pool.__class__.__name__ == "NullPool"
    assert db_ha.probe(business) is True
    get_settings.cache_clear()
