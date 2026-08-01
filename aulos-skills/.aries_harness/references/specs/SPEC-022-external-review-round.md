---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T12:05:00Z"
effective_status: "active"
effective_since: "2026-08-01T17:55:00Z"
content_fingerprint: "sha256:2e2e86b8754d85071219e7643297b6b46dda27962144797011a74505eec082cb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-022 — External review + targeted revise (expert / human)

Upstream: REQ-012. Complements SPEC-018, SPEC-019, SPEC-009.

## Playbook

```
route → intake → corpus → synthesize → width → depth → compose
  → external_review → revise → eval
```

| Trigger | Role |
| --- | --- |
| `listening.compose` | First draft; snapshot **frozen** `draft_v1` |
| `listening.external_review` | Expert hard-flaw report → intents → latest `review_report` + history entry |
| `listening.revise` | **Targeted** chamber patch + render → `draft_v2`; full compose only if `scope=full` |
| `listening.eval` | Score comparison v1 vs latest v2 |

Diary human revise shares the same locate → patch → history pipeline (`source=human`).

## ReviewIntent

```json
{
  "id": "…",
  "source": "expert|human",
  "severity": "high|medium|low",
  "summary": "…",
  "targets": ["listening_map", "composer_portrait"],
  "instruction": "…",
  "evidence": "…"
}
```

Chamber whitelist aligns with Salon Codex keys (+ chrome `work_title` for H1).

## Locate (`review_targets`)

1. Finding `code` → chamber map (deterministic).
2. Human notes → keyword / chamber-name rules (+ optional LLM classifier).
3. Empty targets + high severity → `targets=["*"]` → `scope=full`.

## Patch (`targeted_revise`)

1. Optional deterministic `apply_review_repairs` for expert codes.
2. Rewrite only named dossier chambers (LLM optional; deterministic scaffolds OK).
3. `render_bilingual_guide_html` — **skip** corpus/synthesize/width/depth.
4. Append `revision_history`; update `draft_v2` + `comparison`.

## generation_rounds (`aulos.generation_rounds/v2`)

- `draft_v1` frozen after first compose
- `review_report` = latest normalized report (expert or human view)
- `draft_v2` = latest patched HTML + scorecard + `patched_targets`
- `comparison` = v1 vs latest v2
- `revision_history[]` = iteration log (no full intermediate HTML)

## API

- Diary `/guides/{id}/revise` enqueues `kind=targeted_revise` with notes + existing
  research snapshot (not full listening chain).
- Studio manual recompose remains full-chain.

## Acceptance

- `tests/test_review_targets.py`, `tests/test_targeted_revise.py`
- `tests/test_external_review_round.py` (schema v2 + history)
- Diary revise test stubs targeted enqueue
