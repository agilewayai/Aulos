---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "adr-record"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:7b2c448dbc031f3b3573e3460673bfa8c0fb781f2bf5515a00429ff0c74d5eae"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-001: Use LangGraph as the agent orchestration runtime

## Status

Accepted — 2026-07-25

## Context

`aulos-agent` needs a typical LangChain-ecosystem agent architecture. Options include classic `AgentExecutor`, LangGraph prebuilts, or a hand-rolled LangGraph StateGraph.

## Decision

Use a hand-rolled LangGraph `StateGraph` with explicit `agent` and `tools` nodes, `MessagesState`-compatible state, and `MemorySaver` checkpointer. Prefer `langchain-core` messages/tools and provider packages (`langchain-openai` by default) behind an LLM factory.

## Consequences

- Clear seams for tools, prompts, memory, and observability
- Easy path to persistence and multi-node workflows later
- Slightly more code than `create_react_agent` prebuilt
- Provider selection stays in config, not scattered across nodes
