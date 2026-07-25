---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "pipeline-tests-readme"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:44Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:44Z"
content_fingerprint: "sha256:08d43302238b00ea866afb16bae153c1f10deed1c80bc5ba510438c3cf5b7954"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Test Execution And Fixes

Use this directory for test execution logs, fix attempts, regression notes, and validation closeouts.

## Recommended naming

- `TESTRUN-*`
- `test-execution-*`
- `fix-*`
- `verification-*`

## Each artifact should make clear

- commands or suites run
- pass/fail result
- fixes applied or still needed
- next verification step

## Layer rule

- this directory belongs to `RunCookingLayer`
- keep stable verification policy in `EVAL.md`, not here
