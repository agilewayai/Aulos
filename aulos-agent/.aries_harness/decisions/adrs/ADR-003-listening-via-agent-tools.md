---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "adr-record"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:10:00Z"
effective_status: "active"
effective_since: "2026-07-25T17:10:00Z"
content_fingerprint: "sha256:4f540710adb9426133410b7cfb75fb5ec41b273b68e37f5ba9a3fdca71f8ab85"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-003 — Listening via Agent tool chain (not API SkillRuntime)

## Status

Accepted

## Context

Listening guides were composed by `aulos-api` calling `SkillRuntime.iter_listening_chain` directly. That made the API the orchestrator and left the agent as a thin optional sidecar — opposite of the intended product core.

## Decision

1. Product listening jobs are executed by **aulos-agent** using skill tools (`run_listening_skill` per trigger).
2. `SkillRuntime.run_trigger` remains the **tool implementation**; `iter_listening_chain` is not the product entrypoint.
3. Offline uses `ListeningPlaybookFakeModel` to emit the canonical trigger tool-call sequence.
4. API becomes a gateway: auth, RAG/LLM context injection, SSE, persistence.

## Consequences

- Agent package grows a listening service + richer skill tools.
- API tests must go through AgentProxy (in-process or HTTP).
- One-shot `run_listening_skill_chain` tool is test-only / demoted.
