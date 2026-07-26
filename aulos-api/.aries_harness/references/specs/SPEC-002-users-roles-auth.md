---
schema_version: "0.1"
project_id: "aulos-api"
owner: "arthur"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:47:11Z"
effective_status: "active"
effective_since: "2026-07-25T11:47:11Z"
content_fingerprint: "sha256:7dc34ff2ff9b577ed61b3ee775e22ac1bd4789c0d16ab32532df125307030676"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-002 — Users / roles / auth / Mailgun

## Roles
- `user` — default for registered accounts
- `superadmin` — ops portal + Mailgun configuration

## Behaviors
1. `POST /v1/auth/register` creates unverified user + sends verification email (Mailgun or fake).
2. `POST /v1/auth/verify-email` marks email verified using one-time token.
3. `POST /v1/auth/login` returns JWT only when email is verified and password matches.
4. `GET /v1/auth/me` returns identity + roles for bearer token.
5. `GET/PUT /v1/ops/mailgun` requires `superadmin`; stores API key/domain/from for Mailgun.
6. Bootstrap: env `AULOS_BOOTSTRAP_SUPERADMIN_EMAIL` + `PASSWORD` creates verified superadmin on startup if missing.
7. `POST /v1/auth/forgot-password` accepts `{ email }`; always returns a generic success (no account enumeration). If an active user exists, creates `purpose=reset_password` one-time token and emails a reset link (`{web_base_url}/?reset_token=…`).
8. `POST /v1/auth/reset-password` accepts `{ token, password }` (min 8 chars); validates unused unexpired reset token, updates `password_hash`, marks token used. Does not auto-login.

## Acceptance
- Fake mail mode captures messages offline
- Wrong role → 403; bad/missing token → 401
- Password stored hashed (never plaintext)
- Forgot/reset: unknown email still 200; bad/used/expired reset token → 400; after reset, old password fails login and new password works
