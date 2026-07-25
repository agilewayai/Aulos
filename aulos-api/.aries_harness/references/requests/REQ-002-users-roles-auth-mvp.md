---
schema_version: "0.1"
project_id: "aulos-api"
owner: "arthur"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:47:11Z"
effective_status: "active"
effective_since: "2026-07-25T11:47:11Z"
content_fingerprint: "sha256:2b11ef5afb5bf34ee7937eef1fd4280354d7d5587480a9b203a2a0a067da0979"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-002 — Users, roles, registration/login, Mailgun email validation

## Outcome
- Users can register and log in on aulos-web after email validation via Mailgun.
- Ops dashboard (aulos-ops) is restricted to `superadmin` and can configure Mailgun.

## Scope
- In: users/roles foundation, register/login/verify, Mailgun send+config, JWT sessions, SQLite persistence, fake mail provider for offline tests
- Out: OAuth/SSO, password reset productization, multi-tenant orgs, fine-grained RBAC UI

## Success
- Offline pytest covers register → verify → login and superadmin Mailgun config
- Unverified users cannot obtain a usable session
- Non-superadmin cannot access ops Mailgun routes
- Web/ops UIs wire to the API

## Child refs
- SPEC-002, STORY-PACK-002, ARCH-002, ADR-002
