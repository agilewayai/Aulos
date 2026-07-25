---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "memory"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:44Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:44Z"
content_fingerprint: "sha256:2b7ac7c276f6de6c144ec95ded75992f4d4a217b7d20dee428be49d69b28ad6d"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Memory

## Hot snapshot contract

- keep this file short enough to load every session
- promote detail into `memory/INDEX.md` and `memory/cards/`
- treat `checkpoints/` and `runs/` as episodic memory, not durable truth

## Active durable truths

### Architecture / invariants

- record only stable constraints that should survive session boundaries

### Environment / tooling

- runtime quirks:
- local setup caveats:

### Workflow / operator preferences

### Aries Harness (mandatory)

### Canonical harness library

- Source of truth: `git@github.com:agilewayai/aries-harness-skills.git` (not `AriesHarnessStudio` / `aries-studio`).
- Local reference clone: `/home/ubuntu/studio/aries-harness-skills` (keep in sync with origin).

### Facility layout

- Harness scripts/templates: `.aries_harness/scripts/` + `.aries_harness/templates/` (not project-root `scripts/`/`templates/`).
- Invoke: `bash .aries_harness/scripts/aries-harness.sh <cmd> --project-root .`


- Aries Harness is the **forced default** process for this project (not optional preference).
- SPEC/REQ before broad coding; TDD; JOURNAL + history-refresh; chat-only incomplete.
- Canonical: `aulos-skills/skills/aulos-operating-defaults/SKILL.md` and this project's `AGENTS.md` / `CLAUDE.md`.


- aries-harness first for product design, architecture, spec, history-refresh, well-organized, devops
- TDD coding loop (Red → Green → Refactor)
- UI/UX work must apply `ui-ux-pro-max`
- see `aulos-skills` skill `aulos-operating-defaults` / CARD-001

- note stable operator or project preferences here

### Recurring pitfalls

- promote only repeatable pitfalls, not one-off incidents

## Retrieval map

- load `memory/INDEX.md` when hot memory is not enough
- load only the matching card from `memory/cards/` instead of dumping all cold memory into context

## Pending promotions

- candidate facts to verify before promoting into durable cards:

## GC / review rules

- supersede duplicates instead of silently overwriting history
- review stale cards before trusting them
- if this file starts reading like a journal, move detail out
