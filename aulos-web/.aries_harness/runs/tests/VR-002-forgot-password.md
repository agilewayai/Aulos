---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "verification-report"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T16:50:00Z"
effective_status: "active"
effective_since: "2026-07-26T16:50:00Z"
content_fingerprint: "sha256:301a6bea27ff742827bb80d3f239a999ed3e4a3956b428dc2718e4fd0bf82d0a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# VR-002 — Forgot / reset password

## Slice

- Web forgot/reset UI + API auth endpoints (SPEC-002)

## Verified

- `aulos-api/.venv/bin/pytest tests/test_auth.py` → 7 passed
- `aulos-web/npm run build` → success

## Residual risk

- Live email needs Mailgun configured in Ops
- Redeploy web + api for production
