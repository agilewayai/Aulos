---
schema_version: "0.1"
project_id: "aulos-ops"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T11:22:04Z"
effective_status: "active"
effective_since: "2026-07-25T11:22:04Z"
content_fingerprint: "sha256:dd170fe3230e19fa5cd422bd7de55484ec35265ddb033e97d7daa50811a6a025"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-001 — Vite + React ops portal on a separate port

## Status

- accepted

## Context

- Need a Sprint-0 runtime for `aulos-ops` that is easy to verify offline and extend later.

## Decision

- Use Vite + React + TypeScript on :5174 with a thin health client to aulos-api, separate from aulos-web chat UX.

## Consequences

- Positive: fast local iteration; clear seam to siblings
- Negative: will need auth/observability hardening before production
