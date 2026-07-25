---
schema_version: "0.1"
project_id: "aulos-agent"
owner: "ubuntu"
doc_role: "memory"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T10:55:22Z"
effective_status: "active"
effective_since: "2026-07-25T10:55:22Z"
content_fingerprint: "sha256:3813f45e93d67f82b34c1da7b8a081fd1615c611ac6ead8fb2bf8514cb3dd70a"
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
