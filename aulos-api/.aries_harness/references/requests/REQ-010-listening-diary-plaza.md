---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T07:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T07:00:00Z"
content_fingerprint: "sha256:6350048832524049fc04c5ab85797f45e2164f0105791e4f4ab922c8c82b0a13"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-010 — Listening diary + 爱乐广场 (SNS)

## Objective mode

`functional_capability`

## Why now

Listeners start from a physical pressing (Discogs vinyl/CD), not from a Catalog work.
Aulos needs a first-class **聆乐日记** surface: publish what I listened to today, then later
attach 导赏 as shareable extensions on the same listening blog. A preliminary SNS
**爱乐者聆听广场** lets published diaries be discovered, followed, liked, and commented.

## Problem

Studio only produces ListeningGuides (work-centric research HTML). There is no diary
aggregate for “today’s disc”, no private→public publish path for listening logs, and no
plaza / follow graph. Discogs today is only an intake to the guide chain.

## Outcome

1. User searches Discogs (vinyl/CD), creates a **draft** ListeningDiaryPost with release
   snapshot (cover, title, composers, performers, ensembles, year, catno, tracklist) plus
   optional short listening note.
2. Private My Diary list; **Publish** → public plaza + user listening blog.
3. Plaza SNS: public feed, following feed, follow graph, like, comment.
4. Schema foreshadows **DiaryGuideLink** (diary → guide by aspect) and pluggable
   **ListeningSource** providers (Discogs now; NetEase/QQ/Apple/YouTube later).

## Constraints

- Diary ≠ Guide aggregate; Guide remains separate and may be attached later.
- Catalog is not diary identity; source provider + external_id is.
- Official Discogs API only; no HTML scrape.
- Locales: `en` / `zh-Hans` / `zh-Hant` only.
- UTC on the wire; OS-local display in web.
- TDD; schema_patches for PG + SQLite.

## Non-goals (this request)

- Generating 导赏 from a diary in the first ship (link table only).
- NetEase / QQ / Apple / YouTube adapters (extension points only).
- Rich-text longform blog, DMs, notification center.
- Knowledge-plane Discogs ingest.

## Links

- Downstream: DOM-004, SPEC-019, SPEC-020, STORY-PACK-010, CKPT-010
- Cross: SPEC-008 Discogs connector reuse; web Plaza / My Diary UI
