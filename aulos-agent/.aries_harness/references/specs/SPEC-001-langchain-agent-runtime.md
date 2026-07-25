---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:b98c3e0fd9f12955338507bf16b91ec57e2630e81d3379b984b38d468d61f6ee"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Spec Package

## Semantic Role

- This artifact owns the behavior and scope contract between the request brief and downstream delivery/design work.
- It should capture what must be true, how acceptance is judged, and which operational edges matter.
- It should not become the live task queue or the execution evidence surface.

## Document Control

- Spec ID: SPEC-001
- Artifact type: spec
- Objective mode: functional_capability
- Title: LangChain / LangGraph agent runtime contract
- Status: active
- Owner: ubuntu
- Parent request: REQ-001
- Child refs: STORY-001, ARCH-001, ADR-001
- Last reviewed: 2026-07-25
- Source of truth: `.aries_harness/references/specs/SPEC-001-langchain-agent-runtime.md`

## Belongs Here

- Objective: ship a reusable agent package with config, LLM factory, tools, prompts, LangGraph state/nodes/builder, memory checkpointer, observability hooks, and CLI entrypoint
- In scope:
  - Python package `aulos_agent` under `src/`
  - LangGraph StateGraph with tool-calling ReAct loop
  - pluggable tools registry with at least one built-in tool
  - settings via env / `.env`
  - in-memory checkpointer for thread continuity
  - unit tests that do not require live LLM credentials
- Out of scope:
  - production auth, multi-tenant storage, deployment pipelines
  - custom UI / chat frontend
  - multi-agent supervisor topology (may be a later story)
- Primary actors: operator (CLI), coding agent (harness), end user of the agent runtime
- Key flows:
  1. operator configures LLM provider via env
  2. operator invokes CLI with a prompt and optional thread id
  3. graph runs agent node → tools node loop until completion
  4. response and message history returned for the thread
- Acceptance conditions:
  - `uv sync` or `pip install -e ".[dev]"` succeeds
  - `pytest` passes offline (mocked LLM)
  - package imports resolve: `aulos_agent.graph`, `aulos_agent.tools`, `aulos_agent.llm`
  - architecture seams documented in ARCH-001 and README
- NFRs: typed config; fail-fast on missing required settings when live invoke is requested; no secrets committed
- Quality heuristics or target qualities: clear module boundaries; one graph builder entry; tools are declarative and registerable
- Regression guardrails: tool schema and AgentState fields remain stable unless ADR updated
- Touched surfaces: `src/aulos_agent/**`, `tests/**`, `.aries_harness/**`, project root docs
- Operational concerns: LangSmith tracing optional via env; approval-gated for external network/tool side effects in later slices
- Rollout or migration concerns: n/a for bootstrap

## Slice Candidates

| Slice ID | User value | Acceptance anchor | Priority | Notes |
| --- | --- | --- | --- | --- |
| STORY-001 | Runnable LangGraph agent skeleton | offline tests + import smoke | P0 | this increment |
| STORY-002 | Real provider invoke path | live smoke with API key | P1 | deferred |
| STORY-003 | Durable memory / store | checkpoint persistence | P2 | deferred |

## Keep Out

- Full business-case restatement from the request brief
- Sprint backlog ownership or live execution state
- Test execution logs, commit history, or deployment closeout evidence

## Design Implications

- Domain implications: AgentRun, Thread, ToolCall, Message as core concepts
- Architecture implications: layered package (config → llm → tools/prompts → graph → cli)
- Expected ADRs: ADR-001 LangGraph as orchestration runtime

## Linked Artifacts

- Story-slice pack: STORY-PACK-001
- Domain package: deferred
- Architecture design pack: ARCH-001
- Traceability matrix: TRACE-001

## Open Questions And Risks

- Open question: default LLM provider for hackathon (OpenAI-compatible vs Anthropic)
- Risk: provider SDK churn in langchain packages
- Refresh trigger: graph topology change or tool protocol change
- Audit log entry: AUDIT-001

## Notes For Non-Feature Objectives

- Keep skeleton behavior stable so later feature stories plug into tools/nodes without reshaping the package.
