---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T10:42:00Z"
effective_status: "active"
effective_since: "2026-08-01T10:42:00Z"
content_fingerprint: "sha256:2199658eec356b217b8afd52d3907f3e652d1f89261743284cc12c6668e3873a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-009 — Listening process scorecard (observable atelier)

## Why now

Adversarial review (REQ-008) catches intent drift, but the atelier still lacks a
**graded, per-step quality surface**. Operators and listeners only see flat
`eval_score` / pass-fail — not which node was thin, polluted, or strong.

## Problem

- Production quality is not observable mid-chain.
- Flat eval cannot compare guides or regress process health.
- Ops has single-guide trace but no multi-guide quality board.

## Outcome

1. Every listening skill node emits a deterministic **NodeScorecard** (0–3 dims, N/A excluded).
2. `listening.eval` rolls up a **ProcessScorecard** (nodes + product dims + gates).
3. Persist on `research_json` / `chain_trace`; Atelier shows a summary card.
4. Ops lists recent guides by rollup pct/band for comparison.
5. Keep legacy `eval_score` / `eval_pass` for old clients.

## Non-goals (this slice)

- Gateway-stage (Discogs/RAG/LLM) scorecards.
- LLM-as-judge quality scores.
- Public share-page scorecard UI.
