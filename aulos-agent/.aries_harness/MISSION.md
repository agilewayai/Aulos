---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "mission"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T10:55:22Z"
effective_status: "active"
effective_since: "2026-07-25T10:55:22Z"
content_fingerprint: "sha256:deffc92c9c83448ac318f355b54ac5158f1481ce7f0909c0acd754e52374a1f9"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Mission

## Outcome

- Deliver a reusable LangChain / LangGraph agent runtime (`aulos-agent`) with aries-harness governance so operators can extend tools, prompts, and graph nodes safely.

## Scope boundary

- In scope: single-agent LangGraph ReAct-style package, config/LLM/tools/memory/observability seams, offline verification, harness artifact ladder
- Out of scope: multi-agent swarm product, production deployment, custom UI, model training

## Success test

- Package installs; offline `pytest` passes; ARCH-001 / SPEC-001 / STORY-001 are linked in the artifact register; CLI runs with `AULOS_LLM_PROVIDER=fake`

## Approval boundaries

- Live external tool side effects or irreversible network actions require human confirmation
- Production deploy / secret handling changes require human confirmation
