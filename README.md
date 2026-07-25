# aulos

Hackathon workspace for the Aulos initiative.

## Sub-projects

| Path | Role |
| --- | --- |
| [`aulos-agent/`](aulos-agent/) | LangChain / LangGraph agent runtime |
| [`aulos-api/`](aulos-api/) | HTTP API gateway (FastAPI) |
| [`aulos-web/`](aulos-web/) | Operator web GUI (Vite / React) |
| [`aulos-mcp/`](aulos-mcp/) | MCP server for agents integration |

All sub-projects are governed by aries-harness (`.aries_harness/`).

## Suggested local topology

```text
aulos-web ──HTTP──► aulos-api ──► aulos-agent
                        │
                        └──► aulos-mcp (MCP hosts / tools)
```

## Quick start

### API gateway

```bash
cd aulos-api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
aulos-api
```

### Web GUI

```bash
cd aulos-web
cp .env.example .env
npm install
npm run dev
```

### MCP server

```bash
cd aulos-mcp
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
aulos-mcp
```

### Agent runtime

```bash
cd aulos-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
aulos-agent "hello"
```
