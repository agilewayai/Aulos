---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "adr-record"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:02e52db97d56ddb28d2a35288969297fb0316fd9c65a35a78b01b6fd605097b2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-002 — Domain-runtime skill packs for the listening agent

## Status

Accepted (design baseline)

## Context

Aulos needs compounding 导赏 capability. Hardcoding research in the API does not scale to many masterworks or methodological improvements. `aulos-skills` already hosts filesystem skill packs with registry discovery — but only for operator harness work.

## Decision

1. Extend skill manifests with `layer: domain-runtime` and `runtime: agent`.
2. Build a **SkillRuntime** in the listening path that loads these packs by trigger.
3. Keep operator skills (`layer: core|ops`) separate; coding agents continue to use them to *develop* domain skills.
4. Every listening workflow step must cite the skill id + version that produced it.

## Consequences

- Guide quality improvements ship as skill PRs in `aulos-skills`
- Agent/API become thinner orchestrators — **API must not** run `iter_listening_chain`; **Agent** calls per-trigger skill tools (see aulos-agent ADR-003 / ARCH-002)
- Eval rubrics become first-class and testable offline
- `SkillRuntime.run_trigger` is the tool implementation seam; product orchestration lives in the agent playbook
