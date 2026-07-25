---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "memory-card"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:55:00Z"
effective_status: "active"
effective_since: "2026-07-25T16:55:00Z"
content_fingerprint: "sha256:c97ea2a2b2d0efa25f81a30fea4290906317cb9d87eae0d4ba2b2aa5f357d7a4"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
last_verified_at: "2026-07-25T16:55:00Z"
---
# Memory Card — Facility layout + canonical library

## Fact

1. Harness facility CLI/templates live under `.aries_harness/scripts/` and
   `.aries_harness/templates/` — never project-root `scripts/` or `templates/`.
2. Invoke: `bash .aries_harness/scripts/aries-harness.sh <cmd> --project-root .`
3. Canonical library: `git@github.com:agilewayai/aries-harness-skills.git`
   (not obsolete `AriesHarnessStudio` / `aries-studio`).
4. Strategic lessons promote via self-evolution → `docs/insights.md` + evolution memo.

Evidence: EVO-002, FACILITY-001, AUDIT-001, operating-defaults 0.3.2.

## Refresh trigger

- Upstream `aries-harness-skills` changes consumer packaging layout
- Operator changes library remote or install path
