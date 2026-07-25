# Aulos Ops

Admin and operations portal for the Aulos fleet. Governed by [aries-harness](.aries_harness/).

## Architecture

```text
browser  ──►  aulos-ops (Vite/React)  ──HTTP──►  aulos-api /health
                 │
                 └── service fleet overview (static catalog + live gateway health)
```

| Area | Role |
| --- | --- |
| `src/App.tsx` | ops dashboard UI |
| `src/api.ts` | gateway health client + service catalog |
| `vite.config.ts` | dev server on `:5174` + API proxy |

Design source of truth: `.aries_harness/decisions/architecture/ARCH-001-ops-portal-architecture.md`

## Quick start

```bash
# Terminal 1 — API gateway
cd ../aulos-api && source .venv/bin/activate && aulos-api

# Terminal 2 — ops portal
cd aulos-ops
cp .env.example .env
npm install
npm run dev
# → http://127.0.0.1:5174
```

## Verify

```bash
npm run build
bash scripts/aries-harness/aries-harness.sh history-status --project-root .
```

## Harness

Canonical recovery docs live under `.aries_harness/` (`MISSION.md`, `TASK_STACK.md`, `STATE.md`, `INDEX.md`).

Artifact ladder: `REQ-001` → `SPEC-001` → `STORY-001` → `ARCH-001` / `ADR-001`
