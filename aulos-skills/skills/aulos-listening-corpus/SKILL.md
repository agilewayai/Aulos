# Listening Corpus

## When to use

After intake, before or during width/depth. Prefer curated Salon Codex truth over cold LLM invention for featured works.

## Procedure

1. Match `corpus_keys` or fuzzy work_title against `assets/corpus/index.yaml`.
2. If hit: load dossier **YAML** (preferred) or markdown seed; set `corpus_hit=true`.
3. If miss: return empty dossier with `corpus_hit=false` and suggested research seeds.
4. Never silently overwrite user-stated edition/recording preferences.
5. Never invent YouTube/Discogs URLs — only curated links in the dossier.

## Corpus authorship rules

- Follow SPEC-003 Salon Codex schema (+ SPEC-005 bilingual `zh`, SPEC-006 ambient)
- Label legends explicitly
- Prefer structural listening utility over biographical romance
- Portrait images must be public-domain / clearly credited
- `ambient_audio` — soft theme or full playlist when openly licensed audio exists:
  - single: `url` / `file` + titles/credits/why (+ `_zh`)
  - playlist: `playlist_id` → `assets/corpus/playlists/<id>.yaml`
  - Use **CC0 / public domain** only; never rip commercial LPs
- Related / default ambient for cold works: `assets/corpus/ambient-library.yaml`
- Version dossiers; cite internal `dossier_id`

## Featured packs

- `bwv-988` — J.S. Bach, Goldberg Variations (`bwv-988-goldberg.yaml`)
  — ambient playlist: Open Goldberg / Ishizaka CC0 (32 tracks)
- Ambient library related packs: Bach keyboard, Beethoven lyric piano, Bach cello Suite I,
  Chopin nocturnes, romantic peers
