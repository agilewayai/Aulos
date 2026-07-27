"""SPEC-009 Ops daily product development blog — offline tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from aulos_api.services.dev_blog_contract import (
    SECTION_ARCHITECTURE,
    SECTION_FEATURES,
    SECTION_STORIES,
    validate_dev_blog_body,
)


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
    monkeypatch.setenv("AULOS_TASK_QUEUE_SYNC", "true")

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
    assert "Discogs" in body or "Git" in body


def test_fake_draft_avoids_hype_phrases(sample_repo: Path) -> None:
    from aulos_api.services.dev_blog import collect_day_evidence, render_fake_draft

    ev = collect_day_evidence("2026-07-20", repo_root=sample_repo)
    _, body = render_fake_draft(ev)
    warnings = validate_dev_blog_body(body)
    assert not any("hype" in w for w in warnings)


def test_validate_dev_blog_body_flags_marketing() -> None:
    hype = (
        "# 标题\n\n## 今天产品多了什么\n关键一步全面升级\n\n"
        "## 谁因此更好用了\n最大受益者\n\n## 系统怎么搭起来的\n无\n"
    )
    warnings = validate_dev_blog_body(hype)
    assert any("hype" in w for w in warnings)


def test_ops_dev_blog_generate_list_get_by_id(
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
    assert gen.status_code == 202, gen.text
    task = gen.json()
    assert task["status"] == "completed"
    assert task["task_type"] == "dev_blog.generate"
    post_id = task["post_id"]
    assert post_id is not None

    got = client.get(f"/v1/ops/dev-blog/posts/{post_id}", headers=headers)
    assert got.status_code == 200
    data = got.json()
    assert data["day"] == "2026-07-20"
    assert data["provider"] == "fake"
    assert SECTION_FEATURES in data["body_md"]
    first_body = data["body_md"]
    first_at = data["generated_at"]

    gen2 = client.post("/v1/ops/dev-blog/2026-07-20/generate", headers=headers, json={})
    assert gen2.status_code == 202
    assert gen2.json()["post_id"] != post_id

    listed = client.get("/v1/ops/dev-blog", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    regen = client.post(
        "/v1/ops/dev-blog/2026-07-20/generate",
        headers=headers,
        json={"force": True, "post_id": post_id},
    )
    assert regen.status_code == 202
    assert regen.json()["post_id"] == post_id

    got2 = client.get(f"/v1/ops/dev-blog/posts/{post_id}", headers=headers)
    assert got2.json()["body_md"] == first_body or got2.json()["generated_at"] >= first_at

    search = client.get("/v1/ops/dev-blog", headers=headers, params={"q": "Discogs"})
    assert search.status_code == 200
    assert len(search.json()) >= 1


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

    missing_post = client.get("/v1/ops/dev-blog/posts/99999", headers=headers)
    assert missing_post.status_code == 404
