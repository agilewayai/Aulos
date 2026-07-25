# Listening Wide Research

## When to use

After intake (and after corpus load if any). Build the cultural and historical frame for Salon Codex chambers.

## Research questions

1. When/where was the work written or published? For whom?
2. Who is the composer — life temper, oeuvre status, music-historical stake?
3. Why does this work endure (specific reasons, not generic “masterpiece”)?
4. How did reception change (neglect, revival, landmark recordings)?
5. Which popular stories are **legend** vs documented?
6. What kindred works and famous interpretations (multi-era) should the listener know?
7. Which YouTube appreciation paths and Discogs vinyl/masters are curated?

## Procedure

1. Start from corpus Salon Codex fields if present; do not invent citations or media URLs.
2. Separate **facts**, **scholarly consensus**, and **reception lore**.
3. Produce width points a curious listener can hold — dense, not encyclopedic.
4. Pass through portrait, genesis, stature, related works, interpretations, and media shelf.

## Output schema

- `era`, `composer_profile`, `composer_portrait`, `genesis`
- `width_points[]`, `historical_reasons[]`, `reception_arc`
- `myths_and_caveats[]`, `related_works[{title,why}]`
- `interpretations[]`, `appreciation_videos[]`, `vinyl_and_discography[]`

## Anti-patterns

- Presenting the Goldberg night-music story as proven biography
- Name-dropping without saying what the listener should do with the name
- Fabricating Discogs masters or YouTube IDs
