---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:16d48614af1fa813887e4f1f649c5dd38dcf349091ab66372f05704c61e74bf9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

## Outcome

- Deliver `aulos-skills` as the Aulos main harness skills pack — registry, playbooks, and operator CLI under aries-harness governance.

## Scope boundary

- In scope: skill packs under skills/, registry discovery, aulos-skills CLI, offline pytest, harness artifact ladder
- Out of scope: publishing marketplace, remote skill sync productization, multi-tenant skill ACLs

## Success test

- pytest green; `aulos-skills list` shows bundled skills; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
