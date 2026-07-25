---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:31ee525b20e443a2327c24337ab43d5f374ccf3ff23350985b1353cf37c8c4b2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Request Brief

## Semantic Role

- This artifact owns why the work matters, for whom it matters, and the boundary around the ask.
- It should capture outcome, value, constraints, and non-goals.
- It should not become the detailed behavior contract or the sprint slicing surface.

## Document Control

- Request ID: REQ-001
- Artifact type: request
- Objective mode: functional_capability
- Title: Bootstrap aulos-agent as a LangChain-ecosystem agent sub-project
- Status: active
- Owner: ubuntu
- Review date: 2026-07-25
- Parent refs: n/a
- Child refs: SPEC-001, STORY-001, ARCH-001
- Source of truth: `.aries_harness/references/requests/REQ-001-langchain-agent-bootstrap.md`

## Belongs Here

- Request source: operator ask to apply aries-harness and init `aulos-agent`
- Problem statement: the aulos workspace needs a governed agent sub-project with a standard LangChain/LangGraph architecture instead of ad-hoc scripts
- Current pain or anti-pattern: empty workspace with no agent runtime, no harness recovery surface, no explicit seams for tools/LLM/memory/graph
- Why now: hackathon / new initiative start; harness and architecture must exist before feature work
- Intended user or operator outcome: a runnable, testable agent skeleton that another operator can extend via tools and graph nodes
- Business value: faster, safer iteration on agent capabilities with inspectable harness state
- Success signals: `.aries_harness/` initialized; LangChain package layout present; smoke tests pass without live API keys; mission/architecture/stories are linked
- Target quality attributes: modularity, observability hooks, config-driven LLM selection, verification-first delivery
- Scope boundary: single-agent LangGraph ReAct-style runtime inside `aulos-agent/`
- Constraints: Python package; LangChain ecosystem (langchain-core, langgraph, provider adapters); aries-harness governed artifacts
- Non-goals: multi-agent swarm product, production deployment, UI frontend, custom model training

## Keep Out

- Detailed actor or system behavior flows
- Slice-by-slice task sequencing or backlog control
- Test execution logs, GitHub delivery notes, or deployment evidence

## Delivery Links

- Spec package: SPEC-001
- Story-slice pack: STORY-PACK-001
- Domain package: deferred (thin bootstrap)
- Architecture design pack: ARCH-001
- Value traceability matrix: TRACE-001

## Refresh Triggers

- What should force this brief to be reviewed: change of agent product goal, move off LangGraph, or multi-agent scope expansion
- Audit log entry: AUDIT-001 bootstrap

## Notes For Non-Feature Objectives

- Bootstrap is functional_capability with operability scaffolding; keep product goal explicit even while the first slice is skeleton-only.
