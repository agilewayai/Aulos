---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "state"
harness_layer: "RunCookingLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T16:20:00Z"
content_fingerprint: "sha256:5e328f11f65861592c537f56dcd9cc046b9242b2351e160844d839c5ab225f7c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- Listening product gates active (CKPT-005 ambient + identity hygiene)
- Process remediation: harness mandatory + facility under `.aries_harness/` + self-evolution closeout

## Active run

- Day closeout: well-organized + history-refresh + evolution memo (process/facility/source)
- Next formal product work must open a RUN-* before edits

## Hot facts

- Project root: `aulos-skills/`
- Role: main harness skills
- Live gates: bilingual + ambient required; media `inline`; foreign-chamber scrub
- Facility: `.aries_harness/scripts/` + `.aries_harness/templates/` (not package-root)
- Canonical harness library: `git@github.com:agilewayai/aries-harness-skills.git` (`0.10.0-preview.10`)
- Skills: compose/eval 0.3.0, synthesize 0.2.0, corpus 0.3.0, operating-defaults 0.3.3
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-ops
- Timezone: store UTC / display OS local (operating-defaults 0.3.3; SPEC-007 on api)
- Self-evolution closeout 2026-07-25: EVO-002 + insights + CARD-002; fleet well-organized + history-refresh done

## Open risks

- Cross-service contract drift (web sandbox / API media vs skills SPEC-006)
- Upstream skills library still packages tooling at repo-root `scripts/` (library layout ≠ consumer policy)
- Formal RUN-* template not yet mandatory on every slice
