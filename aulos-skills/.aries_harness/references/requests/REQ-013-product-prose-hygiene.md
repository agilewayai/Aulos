---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T18:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T18:30:00Z"
content_fingerprint: "sha256:5acdcd25f59fab69465179a0246ba3cdbb8a0866ff6fc4e2935f970588508c2c"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-013 — Product-prose hygiene for cold Discogs / bilingual guides

## Problem

Cold-path Discogs guides (and post–Agent Review drafts) can ship **product-unreadable**
quality even when process scorecards look strong:

1. Packaging / multi-language release titles become IntentLock `work_title` (truncated dumps).
2. Process tags (`CRITIQUE LOCK`, `REVIEW REPAIR`, critique codes) are pinned into thesis / H1.
3. CJK dossier fields land on the EN layer; ZH/EN panes diverge or confuse.
4. Symphony-scale form placeholders ("Large-scale work…") for lyric piano miniatures.
5. External-review LLM hallucinates "only ambient / empty body" when chrome hides craft text,
   then revise "repairs" into worse prose.
6. Scorecards can climb while product prose stays broken (hard-flaw blindness).

## Outcomes

1. Packaging titles normalize to listening-work titles before IntentLock.
2. Critique / review corrections park in caveats only — never product thesis / H1.
3. Language layers partition: EN fields English; CJK moves to `zh`.
4. Form labels infer miniature / cycle shelves instead of large-scale placeholders.
5. External review strips ambient chrome, passes chamber inventory, drops empty-body
   hallucinations when dossier is rich; deterministic hard flaws for process locks and
   packaging titles.
6. Catalog + family floor for lyric piano miniatures (Mendelssohn Songs Without Words first).

## Non-goals

- Case-only rewrite of one Mendelssohn guide without pipeline changes.
- Full bilingual machine translation of every chamber (partition + scaffold first).
- Replacing expert LLM review entirely with rules.

## Acceptance

- Unit tests: packaging clean, lock strip, bilingual partition, form infer, empty-body drop.
- Regenerated cold Discogs guide: no process locks in HTML; clean work title; EN/ZH thesis
  partitioned; eval_pass improves; process scorecard no longer claims 0 flaws while locks remain.
