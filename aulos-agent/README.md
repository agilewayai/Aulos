# Aulos Agent

LangChain / LangGraph agent sub-project for the aulos initiative, governed by [aries-harness](.aries_harness/).

## Architecture

```text
cli → graph (agent ↔ tools) → llm factory
                ↘ tools registry
                ↘ prompts
                ↘ memory checkpointer
                ↘ observability (LangSmith optional)
```

| Package | Role |
| --- | --- |
| `aulos_agent.config` | pydantic-settings / env |
| `aulos_agent.llm` | provider factory (`openai`, `anthropic`, `fake`) |
| `aulos_agent.prompts` | system prompt |
| `aulos_agent.tools` | built-in tools + registry |
| `aulos_agent.memory` | `MemorySaver` checkpointer |
| `aulos_agent.graph` | `AgentState`, nodes, `build_graph` |
| `aulos_agent.observability` | LangSmith tracing bootstrap |
| `aulos_agent.cli` | operator entrypoint |

Design source of truth: `.aries_harness/decisions/architecture/ARCH-001-langchain-agent-architecture.md`

## Quick start

```bash
cd aulos-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env

# Offline demo (default provider=fake)
aulos-agent "hello"
# or
python -m aulos_agent "hello"

# Live OpenAI
# set AULOS_LLM_PROVIDER=openai and OPENAI_API_KEY in .env
aulos-agent "what time is it in UTC?"
```

## Verify

```bash
pytest -q
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder for this bootstrap:

- `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`
