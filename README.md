# aulos

Hackathon workspace for the Aulos initiative.

## Sub-projects

| Path | Role |
| --- | --- |
| [`aulos-agent/`](aulos-agent/) | LangChain / LangGraph agent runtime |
| [`aulos-api/`](aulos-api/) | HTTP API gateway (FastAPI) |
| [`aulos-web/`](aulos-web/) | Operator web GUI (Vite / React) |
| [`aulos-mcp/`](aulos-mcp/) | MCP server for agents integration |
| [`aulos-skills/`](aulos-skills/) | Main harness skills pack + CLI |
| [`aulos-knowledge/`](aulos-knowledge/) | Professional music knowledge plane (Postgres/Redis/artifacts) |
| [`aulos-ops/`](aulos-ops/) | Admin and ops portal dashboard |

All sub-projects are governed by aries-harness (`.aries_harness/`).

## Live URLs

| Service | URL |
| --- | --- |
| Web GUI | https://aulos.purezen.ai |
| Ops portal | https://aulos-ops.purezen.ai |

Host daemons + k3s Ingress: see [`deploy/OPS.md`](deploy/OPS.md) (runbook) and [`deploy/README.md`](deploy/README.md) (quick ref).

```bash
bash deploy/aulos-ctl.sh deploy    # full production deploy
bash deploy/aulos-ctl.sh smoke     # health checks
bash deploy/aulos-ctl.sh doctor    # preflight
```

## Suggested local topology

```text
aulos-web ──HTTP──► aulos-api ──► aulos-agent
     │                  │
aulos-ops ──────────────┤
                        └──► aulos-mcp (MCP hosts / tools)

aulos-skills  (harness skill packs / operator CLI across the fleet)
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

### Ops portal

```bash
cd aulos-ops
cp .env.example .env
npm install
npm run dev
# → http://127.0.0.1:5174
```

### Skills harness

```bash
cd aulos-skills
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
aulos-skills list
aulos-skills show aulos-core
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
