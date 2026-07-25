---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:c403a4f65571d7e2e932babeef970dd9ca4e754f0f94871a446c3842e59977b4"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Request Brief

## Document Control

- Request ID: REQ-001
- Artifact type: request
- Objective mode: functional_capability
- Title: Bootstrap aulos-skills as the Aulos main harness work package
- Status: active
- Owner: ubuntu
- Review date: 2026-07-25
- Child refs: SPEC-001, STORY-001, ARCH-001

## Belongs Here

- Request source: operator ask to apply aries-harness and init `aulos-skills`
- Problem statement: Aulos needs a central harness skills surface instead of ad-hoc playbooks scattered across services
- Why now: expand Aulos from runtime/GUI into harness skills + ops visibility
- Intended outcome: runnable, testable `aulos-skills` skeleton another operator can extend
- Scope boundary: `aulos-skills/` only for this request
- Constraints: aries-harness governed; Sprint-0 offline-verifiable
- Non-goals: publishing marketplace, remote skill sync productization, multi-tenant skill ACLs

## Delivery Links

- Spec package: SPEC-001
- Story-slice pack: STORY-PACK-001
- Architecture design pack: ARCH-001
- Value traceability matrix: TRACE-001
