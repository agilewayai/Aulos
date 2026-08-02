# Listening Salon Synthesize

## When to use

After corpus. Always run. If corpus already has full Salon Codex chambers, pass through.
If corpus missed or is thin, **compound** knowledge packs into a dossier width/depth can use.

## Procedure

1. Detect composer card from aliases in the message / `composer_guess`.
2. Detect genre-family scaffold from instruments + forms (cello+piano sonata/variation, keyboard variations…).
3. Merge layers carefully: kb (identity-gated) → family → composer → existing corpus → optional `llm_dossier`.
4. **KB refusal:** inject a knowledge dossier only on **positive** title match; empty `work_title` → refuse.
5. When family matches and corpus missed: **family structural lists win** (do not append-merge LLM/RAG flagship chambers).
6. Scrub foreign flagship markers (`goldberg`, `bwv 988`, `哥德堡`, `aria bass`, …) unless the work is that flagship.
7. Preserve family `ambient_audio` / `zh` packs; fill missing thesis, genesis, stature, sound, map, practice, media.
8. For SPEC-034 multi-work programs, fold `program_iterations[]` into
   `guide_sheets[]`: one sheet per program work plus one synthesis sheet.
9. Emit `program_parallel_plan` as deterministic fan-out/fan-in metadata; gateway
   or agent workers own actual concurrency and must not share unsafe DB/session objects.
10. In fast program-deepen mode, never surface raw JSON notes or web-caveat placeholders;
    parse JSON note payloads first and use composer/title/catalog/instrument identity floors
    when external evidence is weak.
11. Set `synthesize_hit=true` when this skill contributed chambers; record `synthesize_source`.

## Quality bar

Cold-path guides must still expose Composer (portrait when available), Anatomy, Sound world,
interpretations or honest caveats, bilingual `zh` when the family/card provides it, and ambient —
never a blank shell and never another work’s chambers.

## Anti-patterns

- Hardcoding one work’s HTML in the web app
- Inventing Discogs/YouTube URLs
- Overwriting a rich curated corpus with weaker LLM prose
- Keeping multi-work output only as scalar thesis/deepdive lists instead of sheet-ready structure
- Letting rejected LLM JSON or raw-web caveats become reader-facing sheet summaries
- Letting Goldberg (or any flagship) leak into unrelated cold-path dossiers via RAG/LLM
- Keeping KB dossiers with empty titles “just in case”
