---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "verification-record"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-26T18:15:00Z"
effective_status: "active"
effective_since: "2026-07-26T18:15:00Z"
content_fingerprint: "sha256:eb2f19f5dfd95bdcdb4e5928b00c0679ccad32c46cb8382267c87a3a27d5db5c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# VR-013 — SPEC-013 durable jobs + library

## Gates

- `pytest tests/test_listening_jobs.py` — 3 passed
- `test_listening_guide_stream_sse` + recompose stream — passed
- Host: `aulos-api` / `aulos-web` active; health 200

## Result

Accepted.
