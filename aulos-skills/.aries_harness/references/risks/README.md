---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "pipeline-risks-readme"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:05Z"
content_fingerprint: "sha256:9db206d02b23700dc014f485dab1a81645ca0074556fbdf8ce47546db4bc07af"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Risk Register

Use this directory for detailed risk registers, mitigation plans, and escalation notes that complement `RISKS.md`.

## Recommended naming

- `RISK-*`
- `risk-register-*`
- `mitigation-*`

## Each artifact should make clear

- risk statement
- mitigation or escalation
- owner and status

## Layer rule

- this directory belongs to `MetaDefineLayer`
- keep incident-by-incident execution evidence in `runs/`, not in the risk register
