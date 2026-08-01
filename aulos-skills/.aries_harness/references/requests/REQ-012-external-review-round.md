---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T12:05:00Z"
effective_status: "active"
effective_since: "2026-08-01T17:55:00Z"
content_fingerprint: "sha256:ffb171994f6633a4452952a5dbac8a6a6c3394493cfe8d1d8c5879032cfe258a"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-012 — Post-compose expert external review + targeted refresh

## Problem

First-pass 导赏 can still ship hard flaws (硬伤). Operators also leave human
`review_notes` on diary links. Both paths previously triggered **full-chain
recompose**, wasting time and thrashing unrelated chambers.

## Outcomes

1. After first `listening.compose`, `listening.external_review` runs with expert
   perspective (`music_guide_and_analysis_expert`) and emits hard-flaw report.
2. **Semantic locate** maps expert findings and human notes to Salon Codex chambers.
3. `listening.revise` (and diary revise) **patches only targeted chambers**, then
   re-renders HTML — no default width/depth/synthesize replay.
4. Unlocatable high-severity intents may fall back to `scope=full` (logged).
5. `generation_rounds` v2: frozen `draft_v1`, latest `review_report`, latest
   `draft_v2`, `comparison`, plus **`revision_history`** iteration log (targets,
   score before/after, diff summary) — not every intermediate HTML.
6. Studio / diary UI: three panes + side iteration history + dual scorecards.

## Non-goals

- Human-in-the-loop CMS / WYSIWYG HTML editing
- Unlimited automatic review↔revise loops (playbook still one auto round; humans
  may append further targeted refreshes)
- Archiving every intermediate full HTML
- Replacing SPEC-018 in-node deterministic review

## Acceptance

- Playbook: `… → compose → external_review → revise → eval` with targeted revise
- Expert + human notes share `ReviewIntent` / locate / patch pipeline
- `research_json.generation_rounds.schema` = `aulos.generation_rounds/v2`
- Gate: `tests/test_review_targets.py`, `tests/test_targeted_revise.py`,
  `tests/test_external_review_round.py`
