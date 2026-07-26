---
schema_version: "0.1"
project_id: "aulos-web"
owner: "ubuntu"
doc_role: "evaluation"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:42Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:42Z"
content_fingerprint: "sha256:a928d325ff422bc2a0cd25cd283bef4aa134cc180652b7e5c6c07fa9b3ac008f"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Evaluation

## Verification commands

- lint:
- typecheck: `npm run build`
- test: upstream `aulos-api` `pytest tests/test_auth.py` (forgot/reset)

## Acceptance notes

- Sign in offers Forgot password; reset link `/?reset_token=` opens set-password form
- Neutral success copy after forgot request (no account enumeration)

## Layer boundary

- this file defines the verification contract and acceptance gate
- do not turn this file into a run log or test transcript

## Execution evidence

- store detailed test execution and fix notes under `runs/tests/`
