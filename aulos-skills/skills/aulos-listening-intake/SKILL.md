# Listening Intent Intake

## When to use

First step of any listening-guide run.

## Procedure

1. Extract the work name (prefer quoted titles; detect famous aliases like “Goldberg Variations” / 哥德堡).
2. Support **Chinese and English** boilerplate stripping (“我准备开始欣赏…帮我写导赏”).
3. Infer composer + medium + form families (e.g. Beethoven + cello + sonata/variation → duo-cello-piano).
4. Infer listener goal: first hearing / structural learning / performance prep / comparative listening.
5. Propose `corpus_keys` and `family_hints` for corpus + synthesize skills.
6. Hand off a normalized `work_title` — never leave the raw request sentence as the title.

## Output schema

- `work_title` (string)
- `composer_guess` (string, may be empty)
- `listener_goal` (enum-like string)
- `experience_level` (string)
- `corpus_keys` (string[])
- `family_hints` (string[])

## Anti-patterns

- Over-normalizing into generic “Baroque keyboard work”
- Ignoring explicit movement or recording hints the user gave
- Using the entire Chinese request sentence as `work_title`
