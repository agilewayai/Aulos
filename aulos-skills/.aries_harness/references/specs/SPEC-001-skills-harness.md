---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:96630c49b0b2fabe47440e4caedc736315293587db72586eced36ebad864ae12"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Spec Package

## Document Control

- Spec ID: SPEC-001
- Title: aulos-skills harness runtime
- Status: active
- Related request: REQ-001
- Child refs: STORY-PACK-001, ARCH-001

## Behaviors

1. The service boots with documented quick-start commands.
2. Offline verification path exists without live upstream credentials.
3. Primary integration seam is explicit in ARCH-001.
4. Harness recovery docs stay current.

## Acceptance heuristics

- Starter app installs/builds or pytest passes
- Artifact register links REQ → SPEC → STORY → ARCH

## Non-goals

- publishing marketplace, remote skill sync productization, multi-tenant skill ACLs
