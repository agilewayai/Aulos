# Aulos API

HTTP API gateway for the Aulos initiative — facade for the web GUI, agent runtime, and MCP integrations. Governed by [aries-harness](.aries_harness/).

## Architecture

```text
aulos-web  ──HTTP──►  aulos-api  ──►  aulos-agent (optional)
                          │
                          └──►  aulos-mcp (optional)
```

| Package | Role |
| --- | --- |
| `aulos_api.config` | pydantic-settings / env |
| `aulos_api.routes` | `/health`, `/v1/chat` |
| `aulos_api.services` | agent/MCP proxy (fake mode default) |
| `aulos_api.app` | FastAPI factory + CORS |
| `aulos_api.cli` | `aulos-api` entrypoint |

Design source of truth: `.aries_harness/decisions/architecture/ARCH-001-api-gateway-architecture.md`

## Quick start

```bash
cd aulos-api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

aulos-api
# → http://127.0.0.1:8000/health
# → POST http://127.0.0.1:8000/v1/chat  {"message":"hello"}
```

## Verify

```bash
pytest -q
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder: `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`


## Auth MVP

| Endpoint | Notes |
| --- | --- |
| `POST /v1/auth/register` | Creates unverified `user`, sends verification email |
| `POST /v1/auth/verify-email` | One-time token |
| `POST /v1/auth/login` | JWT only after verification |
| `GET /v1/auth/me` | Bearer identity + roles |
| `GET/PUT /v1/ops/mailgun` | `superadmin` only |

Bootstrap superadmin via `AULOS_BOOTSTRAP_SUPERADMIN_EMAIL` / `AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD`.
Set `AULOS_MAIL_PROVIDER=mailgun` after configuring Mailgun in ops (default `fake` for offline).
