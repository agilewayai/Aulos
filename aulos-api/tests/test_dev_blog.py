"""SPEC-009 Ops daily product development blog — offline tests."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


SECTION_FEATURES = "## 今天产品多了什么"
SECTION_STORIES = "## 谁因此更好用了"
SECTION_ARCHITECTURE = "## 系统怎么搭起来的"


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "devblog.db"
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


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True)


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    root = tmp_path / "monorepo"
    root.mkdir()
    _git(root, "init")
    _git(root, "config", "user.email", "dev@example.com")
    _git(root, "config", "user.name", "Dev")

    api = root / "aulos-api" / ".aries_harness"
    ops = root / "aulos-ops" / ".aries_harness" / "history" / "daily"
    api.mkdir(parents=True)
    ops.mkdir(parents=True)
    (root / "aulos-ops" / ".aries_harness").mkdir(parents=True, exist_ok=True)

    (api / "JOURNAL.md").write_text(
        "# Journal\n\n## 2026-07-20T12:00:00Z\n\n- Shipped Discogs listening seed for vinyl lovers.\n",
        encoding="utf-8",
    )
    (ops / "2026-07-20.md").write_text(
        "# Daily\n\n## Feature evolution track\n\n- Discogs tab in Ops.\n",
        encoding="utf-8",
    )
    (api / "STATE.md").write_text("# State\n\n- Active: listening product\n", encoding="utf-8")

    _git(root, "add", ".")
    env = {
        **dict(**{k: v for k, v in __import__("os").environ.items()}),
        "GIT_AUTHOR_DATE": "2026-07-20T15:30:00+00:00",
        "GIT_COMMITTER_DATE": "2026-07-20T15:30:00+00:00",
    }
    subprocess.run(
        ["git", "-C", str(root), "commit", "-m", "Add Discogs vinyl listening helper"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return root


def test_collect_day_evidence_from_git_and_harness(sample_repo: Path) -> None:
    from aulos_api.services.dev_blog import collect_day_evidence

    ev = collect_day_evidence("2026-07-20", repo_root=sample_repo)
    assert ev.day == "2026-07-20"
    assert any("Discogs" in c["subject"] for c in ev.commits)
    assert any(h["project"] == "aulos-api" for h in ev.harness_excerpts)
    assert any("2026-07-20.md" in h["path"] for h in ev.harness_excerpts)


def test_fake_draft_has_three_sections(sample_repo: Path) -> None:
    from aulos_api.services.dev_blog import collect_day_evidence, render_fake_draft

    ev = collect_day_evidence("2026-07-20", repo_root=sample_repo)
    title, body = render_fake_draft(ev)
    assert "2026-07-20" in title
    assert SECTION_FEATURES in body
    assert SECTION_STORIES in body
    assert SECTION_ARCHITECTURE in body
    assert "Discogs" in body or "提交" in body


def test_ops_dev_blog_generate_list_get_force(
    client: TestClient,
    sample_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AULOS_REPO_ROOT", str(sample_repo))
    from aulos_api.config import get_settings

    get_settings.cache_clear()

    headers = _admin_headers(client)
    empty = client.get("/v1/ops/dev-blog", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == []

    gen = client.post("/v1/ops/dev-blog/2026-07-20/generate", headers=headers, json={})
    assert gen.status_code == 200, gen.text
    data = gen.json()
    assert data["day"] == "2026-07-20"
    assert data["provider"] == "fake"
    assert SECTION_FEATURES in data["body_md"]
    assert SECTION_STORIES in data["body_md"]
    assert SECTION_ARCHITECTURE in data["body_md"]
    assert data["evidence"]["commit_count"] >= 1
    first_body = data["body_md"]
    first_at = data["generated_at"]
    assert first_at.endswith("Z") or "+" in first_at

    listed = client.get("/v1/ops/dev-blog", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["day"] == "2026-07-20"
    assert "body_md" not in listed.json()[0]

    got = client.get("/v1/ops/dev-blog/2026-07-20", headers=headers)
    assert got.status_code == 200
    assert got.json()["body_md"] == first_body

    # without force, cached
    again = client.post("/v1/ops/dev-blog/2026-07-20/generate", headers=headers, json={"force": False})
    assert again.status_code == 200
    assert again.json()["generated_at"] == first_at

    force = client.post("/v1/ops/dev-blog/2026-07-20/generate", headers=headers, json={"force": True})
    assert force.status_code == 200
    assert force.json()["provider"] == "fake"
    # regenerated timestamp should be present (may equal if same second — still ok if body ok)
    assert SECTION_FEATURES in force.json()["body_md"]


def test_invalid_day_rejected(client: TestClient, sample_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AULOS_REPO_ROOT", str(sample_repo))
    from aulos_api.config import get_settings

    get_settings.cache_clear()
    headers = _admin_headers(client)
    bad = client.post("/v1/ops/dev-blog/not-a-day/generate", headers=headers, json={})
    assert bad.status_code == 400


def test_missing_day_404(client: TestClient) -> None:
    headers = _admin_headers(client)
    missing = client.get("/v1/ops/dev-blog/2099-01-01", headers=headers)
    assert missing.status_code == 404
