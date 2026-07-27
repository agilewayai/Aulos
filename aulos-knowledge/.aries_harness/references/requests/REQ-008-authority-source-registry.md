---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "request"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-27T11:20:00Z"
effective_status: "active"
effective_since: "2026-07-27T11:20:00Z"
content_fingerprint: "sha256:6a5649c23790bcb13e3203c724d98dfdf144fd9023cf6542b4ea719f5ebb0a56"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-008 — Classical Music Authority Source Registry

## Outcome

Aulos classical knowledge plane has a single **Authority Source Registry**: only registered, verified sources may be crawled; ingest and RAG respect verification and publish policy.

## Non-goals (S1)

- New crawlers for IMSLP / Grove / RISM (candidates only in manifest) — **superseded by S2/S3 for Wikipedia/IMSLP/RISM**
- Moving Work Identity Catalog into the knowledge DB
- A separate registry microservice

## S2 / S3 (shipped)

- Wikipedia connector (EN/ZH MediaWiki extracts) + chunk provenance API/UI
- IMSLP + RISM connectors; Grove remains candidate without connector (proprietary)

## Acceptance

1. Versioned YAML registry manifest syncs into `source_authorities` on boot.
2. Jobs enqueue only when source is `enabled` + `verification_status=verified` + connector exists.
3. HTTP fetches refuse URLs outside registered `base_urls` (+ optional path prefixes).
4. Ingest defaults to quarantine unless publish policy allows auto-publish (tier S + verified + allowed origin_class).
5. Ops can register candidates and verify / reject / suspend sources.
6. Pytest gates cover unknown/unverified enqueue and URL policy.

## Related

- Upstream: ADR-006, META-001 §4 knowledge plane
- Downstream: SPEC-009 / SPEC-010 deltas, REG-SRC-001 manifest
