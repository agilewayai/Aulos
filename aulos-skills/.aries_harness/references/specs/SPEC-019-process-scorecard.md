---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-08-01T10:42:00Z"
effective_status: "active"
effective_since: "2026-08-01T10:42:00Z"
content_fingerprint: "sha256:1ca49079dfc8031a65c2b04416fe88e138c1f9470ba550ea96676cca1bcb05c7"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-019 — Listening Process Scorecard

Upstream: REQ-009. Complements SPEC-018 (review), SPEC-009 (decontam), SPEC-003 (Salon Codex).

## Principles

- Deterministic, class-level dimensions (no per-work branches).
- Reuse IntentLock / review_events / decontam / existing eval probes.
- N/A dims excluded from percentage (never counted as zero).
- Band: ≥85 `strong` / 70–84 `solid` / 55–69 `developing` / &lt;55 `weak`.

## NodeScorecard

Emitted after each scored skill trigger into `context.node_scorecards[]`.

```json
{
  "trigger": "listening.synthesize",
  "layer": "node",
  "scores": {"identity": 3, "fidelity": 2, "richness": 2},
  "na_dims": ["ambient"],
  "earned": 7,
  "max_possible": 9,
  "pct": 77.8,
  "band": "solid",
  "findings": [{"severity": "medium", "code": "...", "note": "..."}],
  "hard_fail": false
}
```

### Process dimensions (0–3)

| dim | Meaning | Typical triggers |
| --- | --- | --- |
| `identity` | IntentLock / composer / title frozen; portrait↔composer + foreign family dossier_id | intake+ |
| `fidelity` | review/decontam ok; no intent betrayal | synthesize+ |
| `richness` | dossier_richness / chamber coverage | synthesize, width, depth |
| `source_hygiene` | myths/caveats; refuse alien body | synthesize, compose |
| `bilingual` | zh + en layers present | width, compose |
| `ambient` | ambient player resolved | compose |
| `craft` | structure / ear cues / chambers; H1 matches work_title | compose, eval |

Hard-fail identity findings (`portrait_composer_mismatch`, `foreign_family_dossier`,
`html_title_drift`) append into `critique_corrections` for adversarial rework (self-improvement).

### Applicability matrix

| Trigger | identity | fidelity | richness | source_hygiene | bilingual | ambient | craft |
| --- | --- | --- | --- | --- | --- | --- | --- |
| route | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| intake | yes | N/A | N/A | N/A | N/A | N/A | N/A |
| corpus | yes | N/A | yes | N/A | N/A | N/A | N/A |
| synthesize | yes | yes | yes | yes | N/A | N/A | N/A |
| width | yes | yes | yes | N/A | yes | N/A | N/A |
| depth | yes | yes | yes | N/A | N/A | N/A | N/A |
| compose | yes | yes | N/A | yes | yes | yes | yes |
| eval | yes | yes | N/A | N/A | yes | yes | yes |

`route` may omit a card or emit all-N/A skipped (no array entry preferred).

## ProcessScorecard

Written at eval into `context.process_scorecard`:

```json
{
  "schema": "aulos.process_scorecard/v1",
  "nodes": ["...NodeScorecard"],
  "product": {
    "scores": {
      "specificity": 0, "ear_cues": 0, "structure": 0,
      "bilingual": 0, "ambient": 0, "craft": 0
    },
    "earned": 0, "max_possible": 18, "pct": 0, "band": "weak", "hard_fail": false
  },
  "rollup": {"earned": 0, "max_possible": 0, "pct": 0, "band": "weak", "hard_fail": false},
  "gates": {
    "eval_pass": false,
    "review_failed": false,
    "decontam_failed": false,
    "ambient_ok": false
  }
}
```

Rollup = sum of all node earned/max + product earned/max.

## Hard fails

- Missing ambient player on compose/eval product.
- `review_failed` or unrepaired intent betrayal → fidelity hard_fail.
- Existing eval atelier-floor failures remain `eval_pass=false`.

## Persistence / surfaces

- `research_json.process_scorecard` + `node_scorecards`
- `chain_trace` milestone `skill.scorecard`
- Web Atelier summary card
- Ops `GET /v1/ops/listening-guides/scorecards` + trace payload

## Acceptance

1. Clean Catalog path → rollup band ∈ {solid, strong}.
2. Requiem-vs-concerto pollution → fidelity low or hard_fail aligned with SPEC-018.
3. No ambient → product.ambient=0 + hard_fail; legacy `eval_pass=false`.
4. Legacy clients reading only `eval_score`/`eval_pass` unbroken.
5. Unit tests cover N/A exclusion and rollup math.
