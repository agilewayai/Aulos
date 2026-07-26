---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "evaluation"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:06Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:06Z"
content_fingerprint: "sha256:59555ef52e3f292b29e472778444dd6daa476f122bff416508f8d78f9c08154c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- lint:
- typecheck: `npm run build`
- test: upstream `aulos-api` `pytest tests/test_dev_blog.py` (SPEC-002 / SPEC-009)

## Acceptance notes

- Dev Blog tab lists/reads posts; generate yields three Chinese section headings
- Fake LLM path works without live keys

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
