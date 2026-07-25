---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "memory-index"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/memory-index/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:20:05Z"
effective_status: "active"
effective_since: "2026-07-25T11:20:05Z"
content_fingerprint: "sha256:f977690fddd8b2ee07a1671f30336551ae8c9c39f8d55d29d9018499d01f4598"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Memory Index

This is the cold recall map for `.aries_harness`.

- `MEMORY.md` is the hot snapshot loaded first
- this file stays compact and points to detailed cards under `memory/cards/`
- checkpoints and run notes are episodic evidence, not durable truth until promoted

## Active memory cards

| id | kind | load when | last verified | status | summary |
| --- | --- | --- | --- | --- | --- |

## Promotion rules

- promote facts only after they prove durable across at least one meaningful rerun, checkpoint, or repeated finding
- every durable card should point back to evidence
- prefer one stable card per fact over many overlapping notes

## Review rules

- active cards should have `last_verified_at`
- use `stale` when the fact may no longer be true
- use `superseded` instead of deletion when history still matters

## Card directory

- `memory/cards/README.md` documents the card shape
- `memory-inspect` checks hot/cold memory hygiene and stale cards

## Cards

| Card | Topic |
| --- | --- |
| `cards/CARD-001-operating-defaults.md` | Fleet operating defaults (mandatory harness / TDD / ui-ux-pro-max) |
| `cards/CARD-002-facility-and-library.md` | Facility paths under `.aries_harness/` + `aries-harness-skills` source pin |
