---
schema_version: "0.1"
project_id: "aulos-api"
owner: "ubuntu"
doc_role: "story-pack"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T07:00:00Z"
effective_status: "active"
effective_since: "2026-08-01T07:00:00Z"
content_fingerprint: "sha256:e587d03685701aab525f76abf4337f402a4720dde6c71b0080174a428c05f898"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# STORY-PACK-010 — Listening diary + plaza

Upstream: REQ-010 / SPEC-019 / SPEC-020

| Slice | Goal | Verify |
| --- | --- | --- |
| S1 | Models + Discogs diary snapshot + draft CRUD | `pytest tests/test_listening_diary.py` |
| S2 | Publish/unpublish + public plaza feed/slug | same + plaza cases |
| S3 | Follow + home feed + user blog profile | social cases |
| S4 | Like + comment | interaction cases |
| S5 | Web Plaza / My Diary UI | `aulos-web` build + manual smoke |
| S6 | diary → guide queue → review → publish on blog | `tests/test_diary_guides.py` |

## Done when

S1–S6 green offline; CKPT-010 updated; journal + honeycomb.
