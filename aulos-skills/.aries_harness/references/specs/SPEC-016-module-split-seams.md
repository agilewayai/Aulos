---
schema_version: "0.1"
project_id: "aulos-workspace"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T09:20:00Z"
effective_status: "active"
effective_since: "2026-07-27T09:20:00Z"
content_fingerprint: "sha256:6adb7811ba61cca40c0b3761dd64ebd075c1448ac99e2299ae7287d12082acba"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-016 — Large-module split seams (AUDIT-009 F10)

## Objective mode

`structural_refactor`

## Pain

Dense files (`App.tsx`, `ops.py`, `listening.py`, guide harden blocks) cross ownership boundaries and slow review.

## Target

Split along existing seams without behavior change:

| Seam | Extract to |
| --- | --- |
| Public guide harden + sanitize | `aulos_api.services.guide_html_security` |
| Studio guide iframe prep | `aulos-web/src/guideHtml.ts` |
| Ops mail + provider config routes | `ops_mail.py` / `ops_integrations.py` included by `ops.py` |
| Ops skills tab UI | `aulos-ops/src/SkillsPanel.tsx` |

## Non-goals

- Full rewrite of `listening_guide.py` / `runtime.py` in this slice
- Behavior or API contract changes

## Acceptance

- Each extract has focused tests or existing suite still green
- `listening.py` and `ops.py` line counts drop vs pre-split baseline
- Web/ops builds pass
