---
schema_version: "0.1"
project_id: "aulos-knowledge"
owner: "ubuntu"
doc_role: "request-brief"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T07:20:00Z"
effective_status: "active"
effective_since: "2026-08-01T07:20:00Z"
content_fingerprint: "sha256:fb0773259363c282e5e3b1c0465b2cae8e2c0d91ba162f5b084335e1e3762554"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# REQ-011 — Clickable person entity cards (KB → web → persist)

## Outcome

From 聆乐 diary (and later other surfaces), composer / performer / ensemble names are
clickable. Opening a name shows an **entity info card**.

Resolution order (forced):

1. Search local knowledge plane (composer entity + published docs/chunks).
2. If missing or thin → fetch **registry-verified** authority sources only
   (Wikidata + Wikipedia encyclopedia tier).
3. Persist into knowledge plane, then return the card.

## Non-goals

- Free-web scrape of random blogs
- Full dossier build on every click (heavy SPARQL stays optional follow-up)
- Social graph for people

## Links

- SPEC-011-person-entity-card (knowledge)
- aulos-api proxy `/v1/entities/person`
- aulos-web 聆乐 clickable names
