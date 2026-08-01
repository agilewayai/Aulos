---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "architecture-decision"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T11:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T11:30:00Z"
content_fingerprint: "sha256:179534f5ffe3bbec970f2f9e698b9e7837b22d453de4b0d15be89255dcc4428c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# ADR-005 — Hybrid adversarial review (deterministic every step + LLM Critic on enrich/compose)

## Status

Accepted (2026-08-01).

## Context

Sibling-work drift (guide #47) showed that producer LLMs can substitute a more famous work
by the same composer/performer. Operators asked for multi-agent adversarial review after
each step. Full per-step LLM critics multiply latency/cost and can themselves drift without
a frozen intent.

## Decision

1. **IntentLock** frozen at intake is the only truth the Critic may use.
2. **Deterministic review** (identity_lock + decontam) runs after every enrich/compose node.
3. **LLM Critic** runs only after `listening.synthesize` and `listening.compose`, review-only JSON.
4. Critic lives in **SkillRuntime** (not only LangGraph) so diary/queue paths are covered.
5. OPS flag `listening.review_llm` can disable the LLM layer; deterministic gates remain on.

## Consequences

- +0–2 LLM calls per guide when live; false positives gated by IntentLock tests.
- Decontam and Critic share alien markers / corrections vocabulary.
- Fleet-wide review protocol deferred (listening atelier first).
