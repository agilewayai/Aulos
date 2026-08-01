---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T20:15:00Z"
effective_status: "active"
effective_since: "2026-08-01T20:15:00Z"
content_fingerprint: "sha256:47cc1a49490016f2ee9ce50511823564596df1e2809562d3c429341ce53522bb"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-029 — Unknown-Case Thicken Loop v1

Upstream: REQ-019. Sits above SPEC-026–028 asset caches.

## Mechanism layers

1. IdentityLock (existing)
2. FacetClassifier → archetype_id
3. Archetype floor (family pack or built-in template)
4. Contract-gated merge (existing chamber contracts)
5. PromoteCandidate dry-run (no production write)

## FacetClassifier (`facet_classifier.py`)

Input: `work_title`, `composer`, `raw_message`, optional facets dict.

Output:

```json
{
  "instruments": ["piano"],
  "forms": ["nocturne"],
  "era": "romantic",
  "archetype_id": "lyric-piano-miniatures",
  "confidence": 0.7
}
```

Token rules (data-driven lists, not work-name branches). Fallback archetype:
`chamber-generic`.

## Archetype floor (`unknown_case_thicken.py`)

`build_archetype_floor(title, composer, *, classification) -> dossier`

- Prefer `load_family_pack(archetype_id)` when registered.
- Else built-in `chamber-generic` template.
- Bind `{composer}`, `{short_title}` into thesis / map / ZH.
- Mark `dossier_id=archetype:{id}`, `_provenance.unknown_case_thicken=true`.

Synthesize: if no family matched and no catalog craft path filled layers, append
archetype floor and `sources += archetype:{id}` (replaces bare generic-scaffold
when classifier confidence ≥ 0.4).

## PromoteCandidate (`promote_candidate.py`)

Schema `aulos.promote_candidate/v1`. Fields: suggested_work_id, family_id,
facets, craft_draft (thesis/map/zh), gates, dry_run=true.

Emitted into context when: synthesize used archetype path, identity has
composer+title, and dossier meets chamber floors. API may persist under
`research_json.promote_candidate`.

## Acceptance

- `tests/test_unknown_case_thicken.py`
- EVAL.md SPEC-029
