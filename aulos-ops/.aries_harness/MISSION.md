---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:0b485b22753f1f86e2233fb6e55e3fc18de37737325a38d316251ce148c48628"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

## Outcome

- Deliver `aulos-ops` as the Aulos admin and ops portal dashboard for fleet health and operator visibility.

## Scope boundary

- In scope: Vite/React ops dashboard, gateway health polling, service fleet catalog, offline build, harness artifact ladder
- Out of scope: auth/SSO, mutating admin actions, full observability backend, production hosting

## Success test

- npm build succeeds; dashboard polls `/health`; ARCH/SPEC/STORY linked

## Approval boundaries

- Live external side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
