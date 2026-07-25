---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "behavior-spec"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:10:22Z"
effective_status: "active"
effective_since: "2026-07-25T11:10:22Z"
content_fingerprint: "sha256:37f36c49e27dec76bb899f44f69828e66245796e92a6a676edec21d30c10399d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Spec Package

## Document Control

- Spec ID: SPEC-001
- Title: aulos-api gateway runtime
- Status: active
- Owner: ubuntu
- Related request: REQ-001
- Child refs: STORY-PACK-001, ARCH-001
- Last reviewed: 2026-07-25

## Actors

- Operator (human)
- Sibling Aulos services (api / web / mcp / agent as applicable)

## Behaviors

1. The service boots with documented quick-start commands.
2. Offline verification path exists without live upstream credentials.
3. Primary integration seam is explicit and documented in ARCH-001.
4. Harness recovery docs (`MISSION`, `STATE`, `TASK_STACK`, `INDEX`) stay current.

## Acceptance heuristics

- Starter app installs/builds
- Automated checks pass where defined
- Artifact register links REQ → SPEC → STORY → ARCH

## Non-goals

- auth/SSO, rate limiting productization, multi-tenant tenancy, production deploy
