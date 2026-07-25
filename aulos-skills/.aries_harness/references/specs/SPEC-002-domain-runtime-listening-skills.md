---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:4ad42dc388ac20702840f41bcc5286e7e6b8953b3a1cbe70b0f9bf07a8126901"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-002 — Domain-runtime skill contract for listening agent

## Manifest

Domain skills MUST set:

- `layer: domain-runtime`
- `runtime: agent`
- `triggers: [...]`
- `observability_title` (optional but recommended)

## Runtime behavior

`SkillRuntime.run(trigger, context)`:

1. Discover packs via `aulos_skills.registry.discover_skills`
2. Select skill where trigger ∈ skill.triggers
3. Load SKILL.md + referenced assets into a context pack
4. Execute procedure (deterministic corpus tools and/or LLM)
5. Validate outputs against declared `outputs`
6. Return `{ outputs, thinking, detail, skill_id, version }`

## Observability

Each run appends a workflow step:

- `id` = trigger suffix (intake/width/…)
- `title` = observability_title or skill name
- `thinking` = procedure rationale
- `detail` = short structured summary of outputs

## Verification

- `aulos-skills list` includes all `aulos-listening-*` packs
- Offline pytest: corpus hit for Goldberg; eval rubric loads
- Agent/API integration tests: workflow steps cite skill ids (implementation slice)
