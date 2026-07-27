# Aulos Operating Defaults

Canonical operator/agent preferences for all `aulos-*` work. **Load this skill at session start.**

## Meta principles (纲领) — META-001

Fleet-wide thinking rules live in **`aulos-skills/.aries_harness/references/META-001-meta-principles.md`** (v2). Apply on every non-trivial slice:

1. **Root cause** — fix the class of failure; data/Catalog over heuristics; multi-stage validate.
2. **Asset sync** — harness forced; REQ/SPEC/JOURNAL/schema/deploy stay aligned; Honeycomb closeout.
3. **Engineering craft** — TDD, coerce LLM input, hard-fail product gates, no chat-only or symptom patches.
4. **Architecture boundaries** — agent-centric product; identity before RAG; knowledge plane separate;
   classical knowledge sources must be **registry-verified** (aulos-knowledge REQ-008) before crawl/RAG.

META-001 is registered in REG-001 (MetaDefineLayer). This skill covers **how we run**; META-001 covers **how we think**. Incident detail: `docs/insights.md` with `↑ META-001 §…` back-links.

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
| **Honeycomb** | well-organized + history | fleet `deploy/honeycomb.sh` or per-project commands below |
| Doc well-organized | well-organized | `aries-harness.sh well-organized`; keep INDEX/MISSION/STATE clean |
| DevOps / deploy | devops + rollout | `deploy/OPS.md` + `deploy/aulos-ctl.sh`; smoke + rollback |
| Self-evolution | promotion | insights + skill/SPEC/gate updates with measurable before/after |

Repo-local command shape (facility scripts live under `.aries_harness/scripts/`):

```bash
bash .aries_harness/scripts/aries-harness.sh well-organized --project-root .
bash .aries_harness/scripts/aries-harness.sh history-refresh --project-root .
bash .aries_harness/scripts/aries-harness.sh history-status --project-root .
```

Do not treat design, architecture, spec, history, organization, devops, or product fixes as ad-hoc side notes outside the harness.

## Honeycomb (fleet harness hygiene)

**Honeycomb** is the Aulos fleet name for closing a slice with harness files tidy and history evidence regenerated. It is **not** a separate tool — it means:

1. **`well-organized`** — move stray `.aries_harness/` Markdown into managed collections; refresh `INDEX.md` layer topology.
2. **`history-refresh`** — regenerate `history/` projections (STATUS, ROADMAP, TIMELINE, RETROSPECTIVE, `daily/*.md`, doc-trace).

Run **per project** (from that sub-project root):

```bash
bash .aries_harness/scripts/aries-harness.sh well-organized --project-root .
bash .aries_harness/scripts/aries-harness.sh history-refresh --project-root .
```

Run **fleet-wide** (all `aulos-*` harness projects):

```bash
bash deploy/honeycomb.sh
```

Typical closeout: finish `JOURNAL.md` → **Honeycomb** → optional Dev Blog generate (**SPEC-017** factual voice) → git commit. Operators may say “做一次 Honeycomb” to mean this pair, workspace-wide or for named projects.

## Facility layout + canonical library

- **Facility assets** live only under `.aries_harness/scripts/` and `.aries_harness/templates/` — not project-root `scripts/` or `templates/`.
- **Canonical harness library:** `git@github.com:agilewayai/aries-harness-skills.git`. Do **not** treat obsolete `AriesHarnessStudio` / `aries-studio` as source of truth.
- Day/slice closeout: run **Honeycomb** (`well-organized` then `history-refresh`); promote strategic lessons via self-evolution (`docs/insights.md` + evolution memo).

## Timezone: store UTC, display OS local

- **Storage / API wire:** UTC only (`timezone.utc`, ISO-8601 ending in `Z` via `aulos_api.timefmt.to_utc_iso`).
- **Product UI (web/ops):** format with `formatDateTime` / `formatTime` in `src/time.ts` — uses `toLocaleString(undefined, …)` so the **OS / browser timezone** is used. Never force `timeZone: 'UTC'` for user-visible stamps.
- **Out of scope:** `.aries_harness/` generated docs may keep UTC timestamps (shared operator surface).

## Chinese locales (script tags only)

- Guide UI: **简体** (`zh-Hans`) + **繁体** (`zh-Hant`) + English.
- Open-source source must not introduce regional locale abbreviations in code, UI, or prompts.
- Identity stays Catalog-driven (SPEC-008); intake recovers composer from `《》` / catalog aliases.

## Product capabilities via Agent + Skill Harness (forced)

- **Core power** is `aulos-agent` + `aulos-skills` packs + tools — not API Python workflow scripts.
- Listening / 导赏 jobs: API authenticates, injects RAG/context, persists results; **Agent** calls `run_listening_skill` (and related tools) per skill playbook.
- Do **not** reintroduce `SkillRuntime.iter_listening_chain` (or equivalent) as the product orchestrator inside `aulos-api`.
- Domain improvements ship as skill pack PRs; agent tools stay thin adapters over `run_trigger`.

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

## Database migration closeout (forced)

Production hot store is **PostgreSQL** (`AULOS_DB_URL`); SQLite is **failover cold mirror** only (`AULOS_DB_FAILOVER_URL`, ADR-007).

Every slice that changes ORM models / table shape must close with:

1. **Schema patch** in `aulos-api` `db/schema_patches.py` (idempotent `ALTER` + indexes) — `create_all` does **not** add columns to existing PG tables.
2. **Apply on both dialects** at boot / HA `configure_engines` (primary Postgres + SQLite failover).
3. **Verify production PG** after deploy: columns/constraints present; smoke one write path that uses the new fields.
4. **Optional HA sync** so the cold SQLite mirror catches up (OPS Fleet → Business DB HA).
5. Offline pytest may keep temp SQLite — that is **not** production migration.

Incomplete if code ships with model fields that exist only on a local SQLite pilot DB.

## DevOps / host production (forced)

Production runs on the `ubuntu` host via **systemd user units** + **k3s Ingress**. Single entry:

```bash
bash deploy/aulos-ctl.sh deploy    # build + secrets + units + ingress + smoke
bash deploy/aulos-ctl.sh doctor    # preflight before first deploy
bash deploy/aulos-ctl.sh smoke     # verify local + public health
```

Canonical runbook: [`deploy/OPS.md`](../../../deploy/OPS.md). Secrets live in **gitignored** `.run/host.env` only (`aulos-ctl secrets init`).

Deploy closeout (mandatory):

1. Sub-project tests green for changed code (`aulos-api` pytest, portal build/lint as applicable)
2. `bash deploy/aulos-ctl.sh test` when deploy layer changes
3. `bash deploy/aulos-ctl.sh smoke` after production deploy
4. Harness `JOURNAL` + `history-refresh` for operator-visible releases

Rollback: checkout known-good git SHA → `aulos-ctl deploy`. No blue/green — document incident in JOURNAL.

Agents **must ask** before `aulos-ctl deploy` unless the operator explicitly requested deploy in the current turn.

## Guardrails

- Never commit secrets or `.env` / `.run/host.env`
- Ask before live external side effects or production deploy mutations
- Prefer sibling contracts through `aulos-api` and documented MCP tools
