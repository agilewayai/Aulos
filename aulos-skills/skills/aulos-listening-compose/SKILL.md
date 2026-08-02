# Listening Guide Compose

## When to use

After width + depth dossiers exist. Produce the user-facing Salon Codex guide page.

## Procedure

1. Prefer `listening_thesis` from corpus as the lede (one sentence the ear holds).
2. Assemble chambers in order: Work → Composer (portrait) → Genesis → Why it endures → Wide → Anatomy/map → Sound world → Kindred → Interpretations → Media (YouTube/Discogs) → Practice → Caveats.
3. Run ambient agent (`select_ambient`) before render — curated → related library → default.
4. Render with `render_bilingual_guide_html` (never the legacy English-only HTML path):
   - EN + ZH panes when `zh` pack exists; default ZH for Chinese listener messages.
   - Floating ambient player (`data-ambient-player=v2`), cache-first media tiers, why-text.
   - When `corpus_dossier.guide_sheets[]` exists, render navigable work sheets
     plus a synthesis sheet using accessible tabs inside each language pane.
5. Keep myths in caveats; keep ear cues in anatomy/map; keep Discogs/YouTube only when curated URLs exist.
6. Hand HTML + summary to eval skill.

## Voice

- Confident, precise, hospitable — a salon host / museum wall text, not a textbook
- Prefer verbs of listening (“track”, “notice”, “hold”) over vague praise

## Anti-patterns

- Walls of undifferentiated prose
- Collapsing a multi-work program into one undifferentiated essay when work sheets exist
- Emoji, purple gradients, generic “AI card” layouts
- Hiding uncertainty
- Inventing YouTube or Discogs links
- Shipping chamber-rich HTML **without** `#aulos-ambient` / bilingual panes
- Preferring origin CDN over `/v1/media` cache
- Using legacy `render_guide_html` for new guides
