# aulos

Hackathon workspace for the Aulos initiative.

## Sub-projects

| Path | Role |
| --- | --- |
| [`aulos-agent/`](aulos-agent/) | LangChain / LangGraph agent runtime (aries-harness governed) |

Start here:

```bash
cd aulos-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
aulos-agent "hello"
```
