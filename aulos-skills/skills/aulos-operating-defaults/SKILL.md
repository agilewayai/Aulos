# Aulos Operating Defaults

Canonical operator/agent preferences for all `aulos-*` work. Load this skill at session start.

## Default: work under aries-harness

For these work types, follow the aries-harness guides and keep `.aries_harness/` current:

| Work type | Harness focus | Expected artifacts / commands |
| --- | --- | --- |
| Product design | request → architecture | REQ / STORY packs; outcome, non-goals, acceptance |
| System architecture | ARCH / ADR | ARCH-*, ADR-*; boundaries and seams explicit |
| Spec development | SPEC | SPEC-* behavior contracts before broad coding |
| Dev-history refresh | history | `aries-harness.sh history-refresh` / `history-status` |
| Doc well-organized | well-organized | `aries-harness.sh well-organized`; keep INDEX/MISSION/STATE clean |
| DevOps / deploy | devops + rollout | runbooks under `runs/deployments/`; smoke + rollback |

Repo-local command shape:

```bash
bash scripts/aries-harness/aries-harness.sh well-organized --project-root .
bash scripts/aries-harness/aries-harness.sh history-refresh --project-root .
bash scripts/aries-harness/aries-harness.sh history-status --project-root .
```

Do not treat design, architecture, spec, history, organization, or devops as ad-hoc side notes outside the harness.

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
