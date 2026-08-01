---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T11:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T11:30:00Z"
content_fingerprint: "sha256:530a7107a38a099bc9e258e3ecaff7676e2cb508ca278452636c0601c53a6617"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-008 — Adversarial process review (IntentLock + Critic)

## Why now

Guide #47 class failure: Discogs Horowitz/Mozart **piano concerto K.488** completed as
Mozart **Requiem / Dies irae / 末日经** because identity was weak and the LLM free-associated
a same-composer/performer meme. Deterministic identity_lock + decontam catch many swaps,
but process still needs a **strict reviewer of intent** after high-risk enrich/compose steps.

## Problem

- Producer nodes can drift mid-chain; late scrub is symptom medicine.
- Pure per-step LLM review is expensive and the critic can itself drift without a frozen intent.
- Catalog miss must not mean “no lock”.

## Outcome

1. Freeze an **IntentLock** at intake (read-only truth for the rest of the atelier).
2. After every listening node: **deterministic review** (identity_lock + SPEC-009 decontam).
3. After **synthesize** and **compose**: optional **LLM Critic Agent** (review-only JSON) that
   may only judge against IntentLock; FAIL injects `critique_corrections` and bounded rework.
4. Still-FAIL → `review_failed`; eval soft-fail; no silent dirty HTML.
5. OPS switch `listening.review_llm` (default on when live LLM ready).

## Non-goals

- LLM Critic on every atelier step (cost/latency).
- Replacing Catalog / identity_lock with the Critic.
- Knowledge-plane crawl review (phase 2).
