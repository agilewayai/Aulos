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
content_fingerprint: "sha256:9f634d0f3def10b13955825dfa909c73e35e140ad65bdceb67ed49326acc1ead"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- lint:
- typecheck:
- test: `pytest tests/test_dev_blog.py` (SPEC-009); `pytest tests/test_auth.py` (SPEC-002 incl. forgot/reset)

## Acceptance notes

- `/v1/ops/dev-blog*` list/get/generate offline green with fake provider
- Generated body contains the three product section headings
- Forgot/reset password: anti-enumeration + token reset green offline

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
