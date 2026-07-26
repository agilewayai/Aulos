---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:45:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:45:00Z"
content_fingerprint: "sha256:6071c84c69608f2dd5464ad092653c539ed3e40896c0e5c4e84fc2fc64bb174e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-002 — Forgot / reset password (web)

## Document Control

- Spec ID: SPEC-002
- Title: Forgot and reset password UI
- Status: active
- Upstream API: aulos-api SPEC-002 behaviors 7–8

## Behaviors

1. Sign-in panel offers **Forgot password?** → request-reset form (email only).
2. Request reset calls `POST /v1/auth/forgot-password` and shows a neutral success notice (does not reveal whether the email exists).
3. Opening `/?reset_token=…` lands on the set-new-password form with token prefilled.
4. Submit calls `POST /v1/auth/reset-password` with token + new password (min 8); on success, switch to Sign in.

## Acceptance

- `npm run build` green
- Modes: `forgot` and `reset` alongside login/register/verify
