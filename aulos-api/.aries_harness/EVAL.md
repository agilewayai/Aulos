---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "evaluation"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:43Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:43Z"
content_fingerprint: "sha256:53d0e8713d1c9d7f86b9198aa3ad2c193dc471b5fabd298526399741dadd442d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- lint:
- typecheck:
- test: `pytest tests/test_dev_blog.py` (SPEC-009); `pytest tests/test_auth.py` (SPEC-002 incl. forgot/reset); `pytest tests/test_email_templates.py tests/test_mailgun.py` (SPEC-010); `pytest tests/test_mail_queue.py` (SPEC-011); `pytest tests/test_discogs.py` (SPEC-008 + search autocomplete); `pytest tests/test_chain_trace.py` (SPEC-012)

## Acceptance notes

- `/v1/ops/dev-blog*` list/get/generate offline green with fake provider
- Generated body contains the three product section headings
- Forgot/reset password: anti-enumeration + token reset green offline
- Transactional mail HTML uses Salon Codex stage/parchment craft
- Live mail enqueues to Redis `aulos:mail:queue`; fake stays sync
- Discogs AJAX: `GET /v1/discogs/search` auth + Classical-first suggestions
- Chain trace: `research_json.chain_trace` + owner/ops `/trace` routes for 复盘

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
