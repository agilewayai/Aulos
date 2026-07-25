---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "business-requirement"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:23:49+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:23:49+00:00"
content_fingerprint: "sha256:ff0407dc17cb5f7739cb389e38fbad23782a71c6eee07ceda2c79520d06d04f2"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-003 — Classical Listening Guide MVP

## Why now

Aulos’s primary product moment is listening: a learner begins a masterwork (e.g. Bach Goldberg Variations) and needs an art-agent companion that researches widely and deeply, then produces a professional listening guide — with visible thinking.

## Outcome

A signed-in user can name a work they plan to learn/listen to; Aulos runs an observable research workflow (width + depth) and returns a beautiful listening-guide web page plus a chain-of-thought / workflow trail.

## In scope

- Intent capture (“I’m listening to / learning …”)
- Multi-step workflow with statuses and thinking notes
- Wide research (context, era, composer, reception, related works)
- Deep research (form, movements/sections, listening cues, practice notes)
- Generated self-contained HTML listening guide
- Web studio UI: workflow observability + guide preview

## Non-goals

- Full score OCR / audio sync players
- Multi-user collaborative annotation
- Live web scraping of copyrighted scores

## Acceptance

- Offline (fake LLM) path produces a high-quality Goldberg (or generic classical) guide with ≥4 workflow steps
- Live LLM path (ops DeepSeek/Grok) can enrich research when configured
- User sees step trail (thinking + status) and rendered guide in aulos-web
