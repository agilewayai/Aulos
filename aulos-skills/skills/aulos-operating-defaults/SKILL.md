# Aulos Operating Defaults

Canonical operator/agent preferences for all `aulos-*` work. **Load this skill at session start.**

## Aries Harness — mandatory default (forced)

**Aries Harness is not optional guidance.** It is the default forced process for product work, architecture, specs, coding slices, verification, history, and devops across the Aulos fleet.

Skip or weaken harness steps **only** when the operator explicitly waives them in the current turn.

### Non-negotiable loop

1. **Inspect** — read this project’s `MISSION.md` / `STATE.md` / active SPEC (and workspace `AGENTS.md`).
2. **Contract** — for behavior changes: REQ/SPEC (or SPEC delta) before broad coding; update `TASK_STACK`.
3. **TDD** — Red → Green → Refactor (failing test or gate first).
4. **Verify** — nearest pytest/build + harness acceptance in `EVAL.md` when relevant.
5. **Summarize / promote** — `JOURNAL.md`, `history-refresh`, STATE/INDEX/REG as needed; insights when the lesson must change future runs.
6. **Incomplete if chat-only** — shipping code without harness artifacts is an incomplete loop (see AUDIT-001).

### Work-type → harness focus

| Work type | Harness focus | Expected artifacts / commands |
| --- | --- | --- |
| Product design | request → architecture | REQ / STORY packs; outcome, non-goals, acceptance |
| System architecture | ARCH / ADR | ARCH-*, ADR-*; boundaries and seams explicit |
| Spec development | SPEC | SPEC-* behavior contracts **before** broad coding |
| Coding slice | coding-loop | TDD + VR notes; update EVAL when gates change |
| Dev-history refresh | history | `aries-harness.sh history-refresh` / `history-status` |
| Doc well-organized | well-organized | `aries-harness.sh well-organized`; keep INDEX/MISSION/STATE clean |
| DevOps / deploy | devops + rollout | runbooks under `runs/deployments/`; smoke + rollback |
| Self-evolution | promotion | insights + skill/SPEC/gate updates with measurable before/after |

Repo-local command shape (facility scripts live under `.aries_harness/scripts/`):

```bash
bash .aries_harness/scripts/aries-harness.sh well-organized --project-root .
bash .aries_harness/scripts/aries-harness.sh history-refresh --project-root .
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

Do not treat design, architecture, spec, history, organization, devops, or product fixes as ad-hoc side notes outside the harness.

## Facility layout + canonical library

- **Facility assets** live only under `.aries_harness/scripts/` and `.aries_harness/templates/` — not project-root `scripts/` or `templates/`.
- **Canonical harness library:** `git@github.com:agilewayai/aries-harness-skills.git`. Do **not** treat obsolete `AriesHarnessStudio` / `aries-studio` as source of truth.
- Day/slice closeout: run `well-organized` then `history-refresh`; promote strategic lessons via self-evolution (`docs/insights.md` + evolution memo).

## Timezone: store UTC, display OS local

- **Storage / API wire:** UTC only (`timezone.utc`, ISO-8601 ending in `Z` via `aulos_api.timefmt.to_utc_iso`).
- **Product UI (web/ops):** format with `formatDateTime` / `formatTime` in `src/time.ts` — uses `toLocaleString(undefined, …)` so the **OS / browser timezone** is used. Never force `timeZone: 'UTC'` for user-visible stamps.
- **Out of scope:** `.aries_harness/` generated docs may keep UTC timestamps (shared operator surface).

## Iteration → harness promotion (mandatory)

Every product fix, playback fix, eval change, or cold-path parity improvement must land as:

1. REQ/SPEC (or SPEC delta) when behavior changes
2. Skill `SKILL.md` + `skill.yaml` version bump when `aulos-skills` behavior changes
3. Measurable gate: pytest and/or `EVAL.md` command
4. Journal memo + `history-refresh`
5. Insight line in `.aries_harness/docs/insights.md` (or project equivalent) when the lesson should change future runs

Chat-only repairs without harness promotion are incomplete loops.

## Coding loop: TDD

Default coding loop is **test-driven**:

1. Inspect — MISSION / STATE / SPEC / failing or missing tests
2. Plan — smallest slice + done condition
3. **Red** — write or extend the failing test first
4. **Green** — implement the minimum to pass
5. **Refactor** — clean up with tests green
6. Verify — full project test/build + harness status as needed
7. Summarize — update STATE / JOURNAL / VR notes

Rules:

- Prefer offline-verifiable tests (no live secrets required)
- Do not merge/ship a slice without the new tests covering the change
- Update harness acceptance when behavior contracts change

## UI / UX: apply ui-ux-pro-max

Whenever the work includes UI structure, visual design, interaction patterns, or UX quality:

1. **Read and follow** the `ui-ux-pro-max` skill before designing or changing UI
2. Still keep product/spec/architecture decisions in aries-harness artifacts
3. Respect Aulos brand and existing portal patterns (`aulos-web`, `aulos-ops`) unless a redesign is explicitly requested

Applies to: new pages, component redesigns, color/typography/layout choices, dashboards, admin portals, responsive/accessibility passes.

## Guardrails

- Never commit secrets or `.env`
- Ask before live external side effects or production deploy mutations
- Prefer sibling contracts through `aulos-api` and documented MCP tools
