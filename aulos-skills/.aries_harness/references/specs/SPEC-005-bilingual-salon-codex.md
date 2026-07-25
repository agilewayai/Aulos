---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:3eb4d1bf5c421c566b36f4144dafca31819987cb50cffe3edb19130686b4e0ce"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-005 — Bilingual Salon Codex (EN / 中文)

## Requirement

Every generated listening guide MUST offer both English and professional Chinese panes
with an in-page language switch. Default visible language is Chinese when a `zh` pack exists.

## Dossier

Top-level fields remain English. Nested `zh:` mirrors the same Salon Codex schema in Chinese.

Chinese prose standards:

- Museum / 导赏 wall-text quality
- Correct classical terminology (奏鸣曲、变奏、对位、羽管键琴、古钢琴…)
- No raw skill/ops jargon leaks (`SkillRuntime`, `corpus_hit`, `width_points`, …)
- Proper nouns (Gould, Discogs, YouTube) may remain; gloss in UI chrome when needed

## Render

`render_bilingual_guide_html` emits `data-lang="zh"` and `data-lang="en"` articles plus toggle.
