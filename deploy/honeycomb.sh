#!/usr/bin/env bash
# Honeycomb — fleet harness hygiene: well-organized + history-refresh on every aulos-* project.
# Canonical term: see aulos-skills/skills/aulos-operating-defaults/SKILL.md
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PROJECTS=(aulos-skills aulos-api aulos-web aulos-ops aulos-knowledge aulos-agent aulos-mcp)

for proj in "${PROJECTS[@]}"; do
  dir="$ROOT/$proj"
  harness="$dir/.aries_harness/scripts/aries-harness.sh"
  if [ ! -x "$harness" ]; then
    echo "SKIP: $proj (no aries-harness.sh)" >&2
    continue
  fi
  echo "=== Honeycomb: $proj ==="
  bash "$harness" well-organized --project-root "$dir"
  bash "$harness" history-refresh --project-root "$dir"
done

echo "Honeycomb complete (${#PROJECTS[@]} projects)."
