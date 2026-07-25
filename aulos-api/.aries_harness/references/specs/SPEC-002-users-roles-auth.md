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
content_fingerprint: "sha256:285e37c8f9b9b5e39008ec33032b602d30f3fc3c1557ea07dd42f69b5935b432"
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

## Acceptance
- Fake mail mode captures messages offline
- Wrong role → 403; bad/missing token → 401
- Password stored hashed (never plaintext)
