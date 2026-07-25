---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:674a748ac2e6fade1df5744d68b10885c408d8426b67ab0c0f8b9d37ad27043b"
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
- Title: Bootstrap aulos-ops as the Aulos admin/ops portal
- Status: active
- Owner: ubuntu
- Review date: 2026-07-25
- Child refs: SPEC-001, STORY-001, ARCH-001

## Belongs Here

- Request source: operator ask to apply aries-harness and init `aulos-ops`
- Problem statement: operators need a dedicated ops surface distinct from the chat GUI
- Why now: expand Aulos from runtime/GUI into harness skills + ops visibility
- Intended outcome: runnable, testable `aulos-ops` skeleton another operator can extend
- Scope boundary: `aulos-ops/` only for this request
- Constraints: aries-harness governed; Sprint-0 offline-verifiable
- Non-goals: auth/SSO, mutating admin actions, full observability backend, production hosting

## Delivery Links

- Spec package: SPEC-001
- Story-slice pack: STORY-PACK-001
- Architecture design pack: ARCH-001
- Value traceability matrix: TRACE-001
