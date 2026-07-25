---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T17:15:00+00:00"
effective_status: "active"
effective_since: "2026-07-25T17:15:00+00:00"
content_fingerprint: "sha256:5c0f7798d7d2c5396b85db8e2ee245b6a7027b20758c883057a21aa7f77a5461"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-010 — OPS Knowledge audit UI

## Surface

`aulos-ops` tab **Knowledge** (superadmin).

## Panels

1. **Sources** — list/register/enable authority sources; show tier, license, connector, QPS.
2. **Jobs** — list jobs; enqueue catalog_import / connector run; show status/errors.
3. **Documents** — browse published vs quarantine; quarantine action.
4. **Provenance** — pick document → source URL, artifact hash, job id, extractor version.
5. **Retrieve lab** — query + optional work_id; show hit titles/scores (debug identity bleed).
6. **Stats** — entity/doc/chunk/job counts; knowledge service health.

## Transport

Browser → `aulos-api` `/v1/ops/knowledge/*` (JWT) → proxy → `aulos-knowledge`.

## Acceptance

- Operator can register a source and run catalog_import without SSH.
- Any published doc opens provenance in one click.
- Knowledge tab visible only to superadmin (same gate as other ops tabs).
