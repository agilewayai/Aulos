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
content_fingerprint: "sha256:c84298f9236882ab106133dd3b3e3095b9dcde5969c0e8f4581d5fedbe54d222"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# State

## Current phase

- AUDIT-009 F2/F10/F11 closed: guide HTML security contract + sanitizer, module splits, plaintext-secrets ADR.
- F1 deferred (operator live secret rotation only).
- F3 session cookies already shipped (SPEC-014).
- SPEC-009 node decontam + family evidence gate (Brahms Op.77 / guide #44)
- Process remediation: harness mandatory + facility under `.aries_harness/` + self-evolution closeout

## Active run

- Closed: AUDIT-009 F2/F10/F11 continuation (2026-07-27)
- Closed: AUDIT-009 workspace architecture/code review (2026-07-27)
- Closed: REQ-007 / SPEC-009 decontam slice (2026-07-26)

## Next action

- Optional operator: rotate live secrets in `.run/host.env` when ready to redeploy (F1 deferred).
- Later: deeper F10 splits (`listening_guide.py` / `runtime.py`) when product work touches those files.

## Blockers

- None for local/hackathon iteration. Production signoff still optional on F1 credential rotation.

## Hot facts

- Project root: `aulos-skills/`
- Role: main harness skills
- Live gates: bilingual + ambient required; media `inline`; foreign-chamber scrub; **per-node decontam rework**
- Family match: composer-scoped packs need instrument/form evidence (not composer alone)
- Facility: `.aries_harness/{scripts,templates}` (not package-root)
- Canonical harness library: `git@github.com:agilewayai/aries-harness-skills.git` (`0.10.0-preview.10`)
- Skills: compose/eval 0.3.0, synthesize 0.2.0, corpus 0.3.0, operating-defaults 0.3.3
- Sibling services: aulos-web, aulos-api, aulos-mcp, aulos-agent, aulos-ops, aulos-knowledge
- Timezone: store UTC / display OS local (operating-defaults 0.3.3; SPEC-007 on api)

## Open risks

- AUDIT-009 residual deferred: F1 live credential rotation (operator); further F10 splits for largest skill/API modules.
- Cold Discogs works without Catalog `work_id` still lean on LLM/KB; decontam markers are catalog-derived aliens — sparse catalog ⇒ weaker alien set
- Cross-service contract drift (web sandbox / API media vs skills SPEC-006)
- Formal RUN-* template not yet mandatory on every slice
