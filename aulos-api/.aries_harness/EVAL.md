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
content_fingerprint: "sha256:75a0f1425e473d41dd514b69f3d298f10a14d910d82cc8a8c30183bb9bf30260"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- lint:
- typecheck:
- test: `pytest tests/test_dev_blog.py` (SPEC-009); `pytest tests/test_auth.py` (SPEC-002 incl. forgot/reset); `pytest tests/test_email_templates.py tests/test_mailgun.py` (SPEC-010); `pytest tests/test_mail_queue.py` (SPEC-011); `pytest tests/test_discogs.py` (SPEC-008 + search autocomplete + SPEC-034 structure); `pytest tests/test_chain_trace.py` (SPEC-012); `pytest tests/test_diary_guides.py` (SPEC-021 / REQ-011 lifecycle); `PYTHONPATH=. .venv/bin/pytest -q tests/test_listening_jobs.py tests/test_diary_guides.py` (failed eval/publish gate)

## Acceptance notes

- `/v1/ops/dev-blog*` list/get/generate offline green with fake provider
- Generated body contains the three product section headings
- Forgot/reset password: anti-enumeration + token reset green offline
- Transactional mail HTML uses Salon Codex stage/parchment craft
- Live mail enqueues to Redis `aulos:mail:queue`; fake stays sync
- Discogs AJAX: `GET /v1/discogs/search` auth + Classical-first suggestions
- Chain trace: `research_json.chain_trace` + owner/ops `/trace` routes for 复盘
- Diary guide lifecycle: revise with notes → queued; unpublish → ready; delete hard-removes exclusive unpublished guide (`test_diary_guides.py`)
- Failed listening reports (`eval_pass=false`, process hard-fail, ambient/review/decontam/structure gates) persist as `failed`, remain inspectable, are not KB-indexed, and cannot be published directly or via diary guide links.

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
