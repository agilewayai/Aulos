---
schema_version: "0.1"
project_id: "aulos-mcp"
owner: "ubuntu"
doc_role: "memory-card-guide"
harness_layer: "SharedSupportSurface"
managed_by: "aries-harness"
fingerprint: "aries-harness/memory-card-guide/v1"
generated_by: "/aries-harness init"
initialized_at: "2026-07-25T11:07:44Z"
effective_status: "active"
effective_since: "2026-07-25T11:07:44Z"
content_fingerprint: "sha256:ec51df195a407f2a33edc56e3a94beca85d167ed8835eec113732fa0f337efeb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# Memory Cards Guide

Use one card per durable fact, pattern, pitfall, decision-memory, or workflow preference.

## Recommended frontmatter

```yaml
---
memory_id: "env.pytest-pythonpath"
memory_kind: "fact"
status: "active"
summary: "pytest must run with PYTHONPATH=src in this repo"
source_refs:
  - checkpoints/checkpoint-2026-04-17.md
last_verified_at: "2026-04-17"
review_after: "2026-05-17"
tags:
  - env
  - pytest
---
```

## Recommended body

### Claim

- what is true

### Why it matters

- why another session should care

### Evidence

- where this came from and what verified it

### Retrieval cues

- when to load this card into active context

### Invalidation

- what would make this card stale or superseded

## Hygiene rules

- if a card is no longer trustworthy, mark it `stale`
- if a newer card replaces it, mark it `superseded`
- keep raw logs in checkpoints or runs, not in durable cards
