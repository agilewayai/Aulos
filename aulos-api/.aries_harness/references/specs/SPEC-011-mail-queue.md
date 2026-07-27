---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/feature-doc/v1"
initialized_at: "2026-07-26T17:00:00Z"
effective_status: "active"
effective_since: "2026-07-26T17:00:00Z"
content_fingerprint: "sha256:5f786f1eaba257f254b02d3f46ae4b6ea6eb6c909bd36a713c1a35fa8eef2de6"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-011 — Transactional mail message queue

## Document Control

- Spec ID: SPEC-011
- Title: Async mail queue (Redis)
- Status: active
- Related: SPEC-002 auth mail, SPEC-010 Salon email craft, ADR-007 Redis pattern

## Behaviors

1. Live transactional mail (`verify_email`, `reset_password`, ops resend) is **enqueued** on Redis list `aulos:mail:queue` and delivered by a background worker — HTTP handlers must not block on Mailgun RTT.
2. Fake mail provider remains **synchronous** (offline tests + instant mailbox).
3. Ops Mailgun **configuration probe** stays synchronous so operators get an immediate ok/fail.
4. If Redis enqueue fails, fall back to a daemon thread delivery (still non-blocking for the request).
5. `AULOS_MAIL_QUEUE_ENABLED=false` forces sync delivery for all kinds (escape hatch).
6. API lifespan starts the mail worker alongside DB HA.

## Acceptance

- `pytest tests/test_mail_queue.py` green
- Existing `test_auth.py` / `test_mailgun.py` remain green (fake sync path)
