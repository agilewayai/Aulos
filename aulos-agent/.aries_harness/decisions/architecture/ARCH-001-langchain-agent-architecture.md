---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "system-design"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T10:58:13+00:00"
effective_status: "active"
effective_since: "2026-07-25T10:58:13+00:00"
content_fingerprint: "sha256:980e08728ef52ce47b3af54b23aaa5169a0fed47ae907ad13f5ffb25696adcc0"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Architecture Design Pack

## Document Control

- Architecture ID: ARCH-001
- Artifact type: architecture
- Title: aulos-agent LangChain ecosystem architecture
- Status: active
- Owner: ubuntu
- Related request: REQ-001
- Related spec: SPEC-001
- Child refs: ADR-001, STORY-001
- Last reviewed: 2026-07-25
- Source of truth: `.aries_harness/decisions/architecture/ARCH-001-langchain-agent-architecture.md`

## Design Drivers

- Primary business outcome: a reusable, extendable agent runtime for the aulos initiative
- Quality attributes: modularity, testability offline, observability readiness, config-driven providers
- Constraints: LangChain ecosystem; single-agent first; Python; aries-harness recovery surface

## Current And Target Shape

- Current state summary: empty aulos workspace prior to bootstrap
- Target state summary: `aulos-agent` Python package with LangGraph ReAct tool-calling loop and harness artifacts
- Why the change is needed: need a standard agent architecture before feature coding

## Boundaries

- Domain links: AgentRun / Thread / Tool / Message (informal until DOM pack exists)
- Component or module boundaries:

```text
cli → graph.builder → nodes (agent | tools) → llm.factory
                   ↘ tools.registry
                   ↘ prompts
                   ↘ memory.checkpointer
                   ↘ observability.tracing
config.settings feeds llm / tracing / runtime defaults
```

- Integration boundaries: LLM providers via langchain-* adapters; optional LangSmith
- Data boundaries: ephemeral in-memory thread state (MemorySaver); no durable DB in Sprint-0

## Package layout

```text
aulos-agent/
├── .aries_harness/          # governed recovery + design artifacts
├── src/aulos_agent/
│   ├── config/              # pydantic settings / env
│   ├── llm/                 # chat model factory
│   ├── prompts/             # system + prompt templates
│   ├── tools/               # tool definitions + registry
│   ├── memory/              # checkpointer / thread memory
│   ├── graph/               # state, nodes, StateGraph builder
│   ├── observability/       # tracing bootstrap
│   └── cli.py               # operator entrypoint
├── tests/
├── .aries_harness/scripts/   # repo-local harness commands
└── pyproject.toml
```

## Runtime flow

1. CLI loads settings and builds the compiled graph once.
2. User message enters `AgentState.messages`.
3. `agent` node binds tools to the chat model and emits an AIMessage (possibly with tool_calls).
4. Conditional edge routes to `tools` node when tool_calls exist, else END.
5. Tool results append as ToolMessages; loop continues.
6. Optional LangSmith tracing wraps the run when env flags are set.

## Decisions

| Decision | Why | Tradeoff | Linked ADR |
| --- | --- | --- | --- |
| LangGraph StateGraph over raw AgentExecutor | durable graph control, checkpoints, explicit nodes | slightly more boilerplate | ADR-001 |
| langchain-core tools + bind_tools | ecosystem standard tool schema | provider parity quirks | ADR-001 |
| In-memory MemorySaver | zero-deps bootstrap | not durable across process restarts | ADR-001 |
| pydantic-settings | typed env config | extra dependency | ADR-001 |

## Delivery Impact

- Affected stories: STORY-001
- Verification impact: offline FakeListChatModel / tool unit tests
- Rollout or migration impact: none
- Observability impact: LANGCHAIN_TRACING_V2 / LANGSMITH_API_KEY optional

## Risks And Open Questions

- Risk: langchain package version skew across providers
- Open question: whether to adopt `create_react_agent` prebuilt vs hand-rolled graph (chosen: hand-rolled for teaching seams)
- Refresh trigger: introduce multi-agent supervisor or persistent store
- Audit log entry: AUDIT-001
