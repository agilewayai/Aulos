# Aulos Web

Operator GUI for the Aulos initiative — chat console that talks to `aulos-api`. Governed by [aries-harness](.aries_harness/).

## Architecture

```text
browser  ──►  aulos-web (Vite/React)  ──HTTP──►  aulos-api  ──►  aulos-agent / aulos-mcp
```

| Area | Role |
| --- | --- |
| `src/App.tsx` | chat console UI |
| `src/api.ts` | gateway client (`POST /v1/chat`) |
| `vite.config.ts` | dev server + API proxy |

Design source of truth: `.aries_harness/decisions/architecture/ARCH-001-web-gui-architecture.md`

## Quick start

```bash
# Terminal 1 — API gateway (fake agent mode)
cd ../aulos-api && source .venv/bin/activate && aulos-api

# Terminal 2 — web GUI
cd aulos-web
cp .env.example .env
npm install
npm run dev
# → http://127.0.0.1:5173
```

Dev proxy forwards `/v1` and `/health` to `http://127.0.0.1:8000`.

## Verify

```bash
npm run build
bash scripts/aries-harness/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder: `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`
