---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "request-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T21:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T21:30:00Z"
content_fingerprint: "sha256:c07ced8014472079c6c28be7221becf03ba6333bfa5e4146e9085ea560bf26e7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-023 — Instrument-faithful thicken + multi-work Discogs identity

## Outcome

Listening thicken must not substitute a different solo instrument (or a single
track from a multi-work pressing) when the locked title already names instruments
and multiple catalog numbers.

## Probe class (anti-case)

Failure class observed on a Bach violin / double-concerto Discogs pressing:
family pack `piano-concerto` unlocked from `concerto` + `orchestra` alone while
the title locked oboe+violin; Discogs intake collapsed a multi-BWV album to one
track. Acceptance tests use ≥2 unrelated identities (e.g. violin/oboe concerto
shelf vs piano concerto shelf; multi-BWV vs multi-Köchel).

## Non-goals

- Hand-authored craft for any single pressing
- Per-composer hardcoding

## Acceptance

1. Family packs that declare soloist instruments require soloist evidence in the
   blob; ensemble/form tokens alone must not unlock them.
2. Chained catalog numbers (`BWV 1041 • 1042`, `K. 330 / 331`) all extract.
3. Discogs releases with ≥2 distinct catalog numbers keep a program-level title
   (multi_work), not a single longest track title as IntentLock.
4. Product/process identity treats solo-instrument betrayal vs IntentLock as a
   high finding (class gate).
