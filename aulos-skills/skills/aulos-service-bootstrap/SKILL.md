# Aulos Service Bootstrap

Use when initializing a new Aulos sub-project under aries-harness.

## Steps

1. Create project root and seed `.aries_harness/scripts/` + `.aries_harness/templates/` (facility assets; not project-root `scripts/`/`templates/`)
2. Run `bash .aries_harness/scripts/aries-harness.sh init --project-root <path> --project-id <id>`
3. Add starter app (Python package or Vite app) with offline verify path
4. Write REQ-001 / SPEC-001 / STORY-PACK-001 / ARCH-001 / ADR-001 / EC-001
5. Update root `README.md` topology table
6. Run verify + `history-refresh`

## Done condition

- Harness recovery docs present
- Offline verify green
- Artifact register links REQ → SPEC → STORY → ARCH
