# Aulos Listening — 导赏 Router

Use this skill when a listener names a classical work they are learning or listening to, and Aulos must produce a professional listening guide with visible research.

## When to use

- User says they are listening to / learning / studying a masterwork
- Studio “Compose listening guide” intent
- Need a full width + depth + compose chain (not a one-shot chat answer)

## Default skill chain

1. `aulos-listening-intake` — normalize work + listener goal (EN/ZH)
2. `aulos-listening-corpus` — load curated dossier if available
3. `aulos-listening-synthesize` — compound composer cards + family scaffolds (+ optional LLM JSON)
4. `aulos-listening-width` — historical & cultural frame
5. `aulos-listening-depth` — form, ear cues, listening map
6. `aulos-listening-compose` — narrative + HTML page (draft v1)
7. `aulos-listening-external-review` — networked deep review Agent → report
8. `aulos-listening-revise` — second compose under review corrections (draft v2)
9. `aulos-listening-eval` — quality gate + dual-draft score comparison

## Quality bar

A good Aulos 导赏 guide must be:

- **Specific** — named sections, intervals, textures, not vague “beautiful”
- **Ear-actionable** — each claim tells the listener what to notice
- **Source-hygienic** — legends labeled as legends; foreign works do not leak in
- **Structured** — Salon Codex chambers (composer portrait when available → genesis → stature → anatomy → sound → media)
- **Bilingual** — EN + professional 中文 when a `zh` pack exists
- **Playable** — floating ambient player with cache-first media (SPEC-006)
- **Beautiful** — composed page, not a markdown dump
- **Parity** — cold-path works should approach flagship chamber coverage via synthesize, not a thin shell

## Observability

Emit one planning step: which skills will run and why (corpus hit or synthesize compound).

## Anti-patterns

- Skipping depth and writing poetic fluff
- Hardcoding one work’s HTML outside skills
- Treating reception myths as settled biography
- Shipping silent guides (no ambient) that only look complete in headings
- Allowing Goldberg / flagship chambers to appear in unrelated cold-path guides
- Dumping full corpus + all skills into one unstructured LLM call
