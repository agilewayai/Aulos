---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "history-roadmap"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/history-doc/v1"
generated_by: "/aries-harness history-refresh"
initialized_at: "2026-07-25T10:55:22Z"
generated_at: "2026-07-25T16:23:54+00:00"
effective_status: "generated"
effective_since: "2026-07-25T16:23:54+00:00"
content_fingerprint: "sha256:bc7a113b66046d049c223b94b8c4616b507dc36355bc75f4601a2132826dd658"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Roadmap Snapshot

Generated at: `2026-07-25T16:23:54+00:00`

## Outcome target

- Deliver a reusable LangChain / LangGraph agent runtime (`aulos-agent`) with aries-harness governance so operators can extend tools, prompts, and graph nodes safely.

## Current milestone

- no current milestone recorded

## Now

- no next action recorded

## Next

- no next action recorded

## Later / guardrails

- In scope: single-agent LangGraph ReAct-style package, config/LLM/tools/memory/observability seams, offline verification, harness artifact ladder
- Out of scope: multi-agent swarm product, production deployment, custom UI, model training
- Package installs; offline `pytest` passes; ARCH-001 / SPEC-001 / STORY-001 are linked in the artifact register; CLI runs with `AULOS_LLM_PROVIDER=fake`

## Approval boundaries

- Live external tool side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
