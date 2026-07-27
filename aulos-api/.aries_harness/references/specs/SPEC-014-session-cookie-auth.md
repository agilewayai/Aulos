---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T09:00:00Z"
effective_status: "active"
effective_since: "2026-07-27T09:00:00Z"
content_fingerprint: "sha256:c71cc1d47fc2a9a417db9ab4f2e917ce3ad89831fc2e9258e079f01d3c8829c9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-014 — HttpOnly session cookie auth (AUDIT-009 F3)

## Problem

Portal JWTs in `localStorage` are readable by any same-origin script (guide iframe XSS path). Bearer tokens in JS amplify guide HTML execution risk.

## Target

- Login sets `aulos_session` HttpOnly cookie (JWT payload unchanged).
- `GET /v1/auth/me` and protected routes accept **cookie OR** `Authorization: Bearer` (tests/CLI keep bearer).
- `POST /v1/auth/logout` clears cookie.
- `aulos-web` and `aulos-ops` use `credentials: 'include'`; no portal token in `localStorage`.

## Cookie contract

| Attribute | Value |
| --- | --- |
| Name | `aulos_session` |
| HttpOnly | true |
| SameSite | `Lax` |
| Secure | true when `AULOS_SESSION_COOKIE_SECURE=true` or `AULOS_WEB_BASE_URL` is `https://` |
| Path | `/` |
| Max-Age | matches JWT expiry |

## Non-goals

- CSRF double-submit token (deferred; SameSite=Lax + same-origin proxy is Sprint-1 baseline)
- Removing `access_token` from login JSON (kept for API clients)

## Acceptance

- `tests/test_auth.py::test_login_sets_session_cookie_and_me_works_without_bearer`
- `tests/test_auth.py::test_logout_clears_session_cookie`
- Bearer auth tests remain green
- Web/Ops `api.ts` has no `localStorage` token writes
