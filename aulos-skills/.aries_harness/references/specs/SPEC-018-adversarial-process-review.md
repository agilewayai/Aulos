---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T11:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T11:30:00Z"
content_fingerprint: "sha256:527b9b207786e66f58719587eaacba3b9067f53e3cab1535074a2604afcc9a84"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-018 — Adversarial Review Agent (IntentLock + hybrid Critic)

Upstream: REQ-008. Complements SPEC-008 (identity) and SPEC-009 (decontam).

## IntentLock (frozen after intake)

Stored on chain context as `intent_lock` (dict). **Must not be overwritten** by LLM/KB layers.

| Field | Type | Notes |
| --- | --- | --- |
| `work_title` | str | Authoritative title |
| `composer` | str | Authoritative composer |
| `catalog_numbers` | list[str] | Normalized (k488, bwv988, op77, …) |
| `form_families` | list[str] | From `policies/form_lock_groups.yaml` |
| `alien_markers` | list[str] | Opposing-family aliens |
| `work_id` | str\|null | Catalog hit if any |
| `conflict_markers` | list[str] | Catalog + lock aliens merged |
| `source` | str | `discogs` \| `catalog` \| `diary` \| `intake` |

## ReviewReport

```json
{
  "ok": true,
  "layer": "deterministic|llm_critic",
  "trigger": "listening.synthesize",
  "verdict": "PASS|FAIL",
  "deviations": [{"code": "...", "summary": "..."}],
  "required_corrections": ["..."],
  "markers_used": [],
  "repaired": false
}
```

Context accumulates `review_events[]` (and keeps `decontam_events` for back-compat).

## Trigger table

| After node | Deterministic | LLM Critic |
| --- | --- | --- |
| intake | freeze IntentLock only | no |
| corpus | yes (if dossier out) | no |
| synthesize | yes | **yes** (when `listening.review_llm`) |
| width | yes | no |
| depth | yes | no |
| compose | yes | **yes** (when `listening.review_llm`) |
| eval | soft-fail if `review_failed` | optional final check |

Rework cap: **1** per layer per node (deterministic + critic each ≤1), same spirit as SPEC-009.

## LLM Critic contract

- **Review only** — never invent a new work title or write a full guide.
- Input: IntentLock + node output slice (thesis/form/intro/HTML excerpt).
- Output: ReviewReport JSON only.
- FAIL if narrative swaps form family, drops all lock catalog numbers while inserting foreign numbers, or elevates performer meme over locked work.
- On FAIL: set `critique_corrections`, `refuse_topics` (= alien_markers); re-run producer once with corrections prepended.

## OPS

- Setting key / env: `listening.review_llm` (bool). When LLM not live → deterministic-only (Critic skipped, not a pass-by-default hole for markers).

## Acceptance

- Concerto lock + Requiem narrative fails review before final HTML (with or without Catalog work card).
- Clean Goldberg / K.488 paths do not false-FAIL.
- `review_events` visible on chain context / research payload.
- SkillRuntime path (diary queue) enforces the same gates without requiring LangGraph.
