---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:01:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:01:00+00:00"
content_fingerprint: "sha256:176262ed64f2fe62a0a5645499504551479060d74a6e9461d1512b2013e104bd"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-006 — Work Identity Catalog (productized identity gate)

## Why now

Listening guides polluted across works (e.g. Bach cello suites inheriting Goldberg /
Beethoven duo shelves). Symptom patches (runtime `elif` trees, hardcoded scrub markers)
do not scale to Chopin, Mahler, or any future shelf.

## Problem

- Work identity is resolved by procedural string heuristics in Python.
- The research KB is sparse and nearest-neighbor RAG is misused as identity confirmation.
- Specs do not forbid case hardcoding or require a catalog authority.

## Outcome

- **Work Catalog** is the authority for composer/work identity (aliases, catalog numbers,
  facets, conflict links, ambient refs).
- **Identity Resolver** is a generic, data-driven scorer — no per-work `elif`.
- RAG enhances content only after identity is confirmed; scrub/ambient read conflict
  markers and facets from the catalog.

## Value

- Add Chopin / Mahler / any work by adding catalog YAML — not by editing runtime branches.
- Professional, confirmable identity records (EN/ZH titles, catalog numbers, provenance).

## Constraints

- Agent + Skill Harness remain the product core; API injects RAG but does not own identity.
- Do not invent biography anecdotes to fill uncertain fields — mark `uncertain: true`.

## Non-goals

- Full Salon Codex dossiers for every catalogued work in the first slice.
- LLM-as-identity-oracle replacing the catalog.

## Links

- SPEC-008, DOM-002, ADR-004
- Updates SPEC-006 (ambient + API RAG identity)
