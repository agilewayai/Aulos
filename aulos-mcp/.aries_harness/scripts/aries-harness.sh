#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

usage() {
  cat <<'EOF'
Usage:
  bash .aries_harness/scripts/aries-harness.sh init [options]
  bash .aries_harness/scripts/aries-harness.sh well-organized [options]
  bash .aries_harness/scripts/aries-harness.sh pipeline-inspect [options]
  bash .aries_harness/scripts/aries-harness.sh memory-inspect [options]
  bash .aries_harness/scripts/aries-harness.sh history-refresh [options]
  bash .aries_harness/scripts/aries-harness.sh history-status [options]
  bash .aries_harness/scripts/ah.sh <same-subcommand> [options]

Subcommands:
  init            Create a stable `.aries_harness/` skeleton for a project.
  well-organized  Reorganize extra `.aries_harness/` Markdown files and refresh INDEX.md.
  pipeline-inspect Inspect the engineering pipeline artifacts, phase ledger, and directory shape.
  memory-inspect  Inspect the harness memory system, card health, and hot/cold memory split.
  history-refresh Generate readable history, roadmap, status, retrospective, daily summaries, and doc-trace docs.
  history-status  Print a concise dev-history snapshot without rewriting files.
EOF
}

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

subcommand=$1
shift

case "$subcommand" in
  init)
    exec "$script_dir/init-project.sh" "$@"
    ;;
  well-organized)
    exec python3 "$script_dir/well-organized.py" "$@"
    ;;
  pipeline-inspect)
    exec python3 "$script_dir/pipeline-inspect.py" "$@"
    ;;
  memory-inspect)
    exec python3 "$script_dir/memory-inspect.py" "$@"
    ;;
  history-refresh)
    exec python3 "$script_dir/dev-history.py" refresh "$@"
    ;;
  history-status)
    exec python3 "$script_dir/dev-history.py" status "$@"
    ;;
  *)
    usage
    exit 1
    ;;
esac
