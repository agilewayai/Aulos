---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:30:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:30:00Z"
content_fingerprint: "sha256:1f556c15bb63c9803f24c32a2ada6861b8b932fdf959eb772a571585a2330004"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-030 — Promote staging + ops surface

Upstream: REQ-020. Extends SPEC-029 promote dry-run.

## Staging craft (`promote_staging.py`)

- Root: `craft_packs_root() / "staging"`.
- `materialize_craft_yaml(candidate, *, dossier=None, composer, work_title) -> dict`
- `write_staging_craft(work_id, pack, *, overwrite=False) -> Path`
- Refuse path traversal; `work_id` must match `^[a-z0-9]+([.-][a-z0-9]+)+$`.
- Written pack sets `work_id`, `family_id`, `_provenance.promote_staged=true`.

## API (aulos-api)

- `GET /v1/ops/listening-guides/promote-candidates?limit=`
- `POST /v1/ops/listening-guides/{guide_id}/promote-stage`
  - body: `{ overwrite?: bool }`
  - writes staging YAML; updates `research_json.promote_candidate.status=staged`
    + `staged_path` / `staged_at`.
- `guide_trace_dict` includes `promote_candidate`, `product_scorecard`,
  `synthesize_source`, `facet_classification` when present.
- Scorecard summaries include `has_promote_candidate`, `synthesize_source`.

## Ops UI

Guide quality detail: show promote draft + Stage craft button calling promote-stage.

## Classifier expand

Add form tokens: prelude, etude/étude, ballade, impromptu, fantaisie/fantasy,
string quartet, violin concerto; instruments: strings/quartet as needed.
Map prélude/etude/ballade/impromptu/fantasy → `lyric-piano-miniatures` or
`character-dance-piano` as appropriate; string quartet → `chamber-generic`
until a quartet family exists; violin concerto → `piano-concerto` only when
piano — else chamber-generic with violin+concerto facets (do not force piano-concerto).

## Acceptance

- `tests/test_promote_staging.py`
- `aulos-api/tests/test_promote_stage_api.py`
- EVAL.md SPEC-030 gate
