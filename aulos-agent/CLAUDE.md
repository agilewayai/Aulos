# CLAUDE.md

This file stays aligned with `AGENTS.md` so Claude and Codex share the same project assumptions.

## Project

`aulos-agent` is a LangChain / LangGraph single-agent runtime under aries-harness governance.

## Project root

Work inside `aulos-agent/` (this directory). Do not treat the parent `aulos/` folder as the package root unless explicitly asked.

## Coding rules

- Prefer extending `tools/` and `graph/nodes.py` over inventing parallel agent frameworks.
- Keep provider selection in `llm/factory.py` + `config/settings.py`.
- Offline tests must pass without live API keys (`AULOS_LLM_PROVIDER=fake`).
- Update `.aries_harness/` artifacts when scope, architecture, or acceptance changes.
- Follow Inspect → Plan → Edit → Verify → Summarize; journal durable notes in `.aries_harness/JOURNAL.md`.

## Key paths

- Architecture: `.aries_harness/decisions/architecture/ARCH-001-langchain-agent-architecture.md`
- Spec: `.aries_harness/references/specs/SPEC-001-langchain-agent-runtime.md`
- Execution card: `.aries_harness/references/tasks/EC-001-bootstrap-execution-card.md`
- Package: `src/aulos_agent/`

## Approval boundaries

- Live external tools / network side effects: ask the operator first.
- Committing secrets or `.env`: never.
- Force-push / destructive git: never unless explicitly requested.
