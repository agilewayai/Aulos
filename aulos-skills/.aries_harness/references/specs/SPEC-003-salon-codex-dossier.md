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
content_fingerprint: "sha256:07303e5ff3f1ef38fa838b7fa88424f0590db4a2a30caa0446e96b03cd980b8b"
trace_history_source: "filesystem-only"
trace_last_commit_sha: ""
trace_last_commit_at: ""
trace_revision_count: "0"
---
# SPEC-003 — Salon Codex dossier schema

## Corpus file

Preferred: `assets/corpus/<key>.yaml` referenced from `index.yaml`.

Markdown dossiers remain parseable as a degraded seed format.

## Required top-level fields (flagship)

```yaml
dossier_id: string
work_title: string
composer: string
catalog: string          # e.g. BWV 988
era: string
form: string
listening_thesis: string # one sentence the ear should hold
```

## Optional rich blocks

- `composer_portrait`: `{ image_url, credit, caption }`
- `composer_profile`: `{ lifespan, summary, temperament, place_in_oeuvre, place_in_history }`
- `genesis`: `{ year, place, publication, patronage, background, instrument_culture }`
- `historical_stature`: `{ reasons: [], reception_arc }`
- `work_introduction`: prose
- `width_points`, `depth_points`, `myths_and_caveats`, `practice_notes`: string[]
- `listening_map`: `{ label, cue }[]`
- `variation_deepdives` / `section_deepdives`: `{ title, note }[]`
- `sound_world`: `{ original_instrument, ensemble_notes, modern_modes: [] }`
- `ambient_audio` (optional): `{ url, title, title_zh?, credit, credit_zh?, loop?, volume?, autoplay? }` —
  soft theme/recording played when the guide opens. Prefer CC0 / public-domain sources only.
- `related_works`: `{ title, why }[]` or string[]
- `interpretations`: `{ artist, year, instrument, era_note, why_listen, youtube_url?, discogs_url? }[]`
- `appreciation_videos`: `{ title, url, bilibili_url?, why }[]` — `url` is YouTube search; `bilibili_url` is 哔哩哔哩 search (`search.bilibili.com`). Renderer auto-fills `bilibili_url` from the YouTube query or title when omitted.
- Interpretations may include `youtube_url` + `bilibili_url` + `discogs_url` (search links only).
- `vinyl_and_discography`: `{ label, url, note }[]`

## Compose HTML acceptance

Guide HTML MUST include identifiable section headings for portal thesis, composer, genesis, stature, anatomy/map, sound world, interpretations, media, practice, and caveats when those blocks exist in context.
When `ambient_audio.url` is set, the page MUST expose an ambient player (`#aulos-ambient`) above the language switch and attempt soft autoplay with a visible play/pause control.

## Eval additions

Chamber coverage counts toward Structure (2 pts). Presence of interpretation + media shelf for corpus hits is expected for pass on flagship works.
