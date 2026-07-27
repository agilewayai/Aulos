---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "history-roadmap"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T11:20:05Z"
generated_at: "2026-07-27T09:46:13+00:00"
effective_status: "generated"
effective_since: "2026-07-27T09:46:13+00:00"
content_fingerprint: "sha256:0573a6e2259e5acc4d60191754ca4b6dfb54446a2fc27a4e1fa3b5ce3730192c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Roadmap Snapshot

Generated at: `2026-07-27T09:46:13+00:00`

## Outcome target

- Deliver `aulos-skills` as the Aulos main harness skills pack — registry, playbooks, and operator CLI under aries-harness governance.

## Current milestone

- no current milestone recorded

## Now

- Optional operator: rotate live secrets in `.run/host.env` when ready to redeploy (F1 deferred).
- Later: deeper F10 splits (`listening_guide.py` / `runtime.py`) when product work touches those files.

## Next

- Optional operator: rotate live secrets in `.run/host.env` when ready to redeploy (F1 deferred).
- Later: deeper F10 splits (`listening_guide.py` / `runtime.py`) when product work touches those files.

## Later / guardrails

- In scope: skill packs under skills/, registry discovery, aulos-skills CLI, offline pytest, harness artifact ladder
- Out of scope: publishing marketplace, remote skill sync productization, multi-tenant skill ACLs
- pytest green; `aulos-skills list` shows bundled skills; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
