---
schema_version: "0.1"
project_id: "aulos-skills"
owner: "ubuntu"
doc_role: "spec-package"
harness_layer: "MetaDefineLayer"
managed_by: "aries-harness"
fingerprint: "aries-harness/bootstrap-doc/v1"
initialized_at: "2026-07-25T16:19:58+00:00"
effective_status: "active"
effective_since: "2026-07-25T16:19:58+00:00"
content_fingerprint: "sha256:3d78d549093d2c5891d28ae78182a7777f9cad293e1db9e112c3eef8228dd36e"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-004 — Synthesize skill & knowledge packs

## Skill

`aulos-listening-synthesize` @ `listening.synthesize`

## Knowledge packs

### Composer card (`assets/composers/<id>.yaml`)

Required: `composer`, `composer_portrait`, `composer_profile`
Optional: `aliases[]` for intake matching

### Family scaffold (`assets/families/<id>.yaml`)

Required: `family_id`, `match` (composers/instruments/forms hints), `form`, `sound_world`,
`listening_map`, `depth_points`, `practice_notes`, `width_points`
Optional: `related_works`, `interpretations`, `appreciation_videos`, `vinyl_and_discography`,
`historical_stature`, `work_title_template`, `catalog`

**Match rule (SPEC-009):** when `match.composers` is non-empty, require ≥1 instrument or form
token hit in the title/message blob — composer surname alone must not unlock the pack.

### LLM dossier JSON

Same Salon Codex fields as SPEC-003. API asks for JSON only; runtime parses fenced or raw JSON.

## Acceptance

For message ≈ “欣赏贝多芬的大提琴、钢琴奏鸣曲和变奏曲”:

1. `work_title` normalized (not the raw Chinese sentence)
2. `composer` = Ludwig van Beethoven
3. Guide HTML includes Composer (portrait URL), Genesis or stature, Anatomy, Sound world,
   interpretations or media when scaffold/LLM provides them
4. `html_len` and chamber count approach flagship order-of-magnitude (not <10k empty shell)
