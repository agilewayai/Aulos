---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "managed-doc"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:23:43+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:40:00Z"
content_fingerprint: "sha256:198d0939f71973bcbc446d3784c65a484b49a8d4165d1987fa55c1e24f117d73"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Facility layout: scripts & templates under `.aries_harness/`

## Problem

Bootstrap copies left harness tooling at the project root (`scripts/aries-harness/`, `templates/aries_harness/`), polluting the package surface and looking like product code.

## Rule

For every Aulos sub-project:

| Asset | Canonical path |
| --- | --- |
| CLI / helpers | `.aries_harness/scripts/` |
| Init skeletons | `.aries_harness/templates/` |
| Recovery docs / runs / history | `.aries_harness/` (existing) |

Do **not** keep parallel copies under project-root `scripts/` or `templates/`.

## Invoke

```bash
bash .aries_harness/scripts/aries-harness.sh history-refresh --project-root .
bash .aries_harness/scripts/ah.sh well-organized --project-root .
```
