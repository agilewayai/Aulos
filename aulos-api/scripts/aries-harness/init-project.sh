#!/usr/bin/env bash
set -euo pipefail

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(CDPATH= cd -- "$script_dir/../.." && pwd)
template_dir="$repo_root/templates/aries_harness"
fingerprint_file="ARIES_HARNESS_FINGERPRINT.json"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/aries-harness/aries-harness.sh init [options]

Options:
  --project-root PATH   Target project root. Defaults to current directory.
  --project-id ID       Logical project id. Defaults to basename of project root.
  --owner NAME          Owner label written into templates. Defaults to $USER or operator.
  --force               Allow writing into an existing non-empty `.aries_harness/`.
  --dry-run             Print planned actions without writing files.
  -h, --help            Show this help.
EOF
}

project_root="."
project_id=""
owner="${USER:-operator}"
force=0
dry_run=0

while [ $# -gt 0 ]; do
  case "$1" in
    --project-root)
      project_root=${2:?missing value for --project-root}
      shift 2
      ;;
    --project-id)
      project_id=${2:?missing value for --project-id}
      shift 2
      ;;
    --owner)
      owner=${2:?missing value for --owner}
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

project_root=$(python3 -c 'import os,sys; print(os.path.abspath(sys.argv[1]))' "$project_root")
if [ ! -d "$project_root" ]; then
  echo "Project root does not exist: $project_root" >&2
  exit 1
fi

if [ -z "$project_id" ]; then
  project_id=$(basename "$project_root")
fi

harness_dir="$project_root/.aries_harness"
created_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [ ! -d "$template_dir" ]; then
  echo "Template directory not found: $template_dir" >&2
  exit 1
fi

if [ -d "$harness_dir" ] && [ "$(find "$harness_dir" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l | tr -d ' ')" -gt 0 ] && [ "$force" -ne 1 ]; then
  echo "Refusing to overwrite non-empty $harness_dir without --force" >&2
  echo "Use /aries-harness well-organized or rerun with --force if you really want to reinitialize." >&2
  exit 1
fi

managed_dirs=(
  "$harness_dir"
  "$harness_dir/layers"
  "$harness_dir/layers/MetaDefineLayer"
  "$harness_dir/layers/RunCookingLayer"
  "$harness_dir/layers/SharedSupportSurface"
  "$harness_dir/memory"
  "$harness_dir/memory/cards"
  "$harness_dir/history"
  "$harness_dir/history/daily"
  "$harness_dir/checkpoints"
  "$harness_dir/decisions"
  "$harness_dir/decisions/architecture"
  "$harness_dir/decisions/adrs"
  "$harness_dir/runs"
  "$harness_dir/runs/tests"
  "$harness_dir/runs/reports"
  "$harness_dir/runs/github"
  "$harness_dir/runs/deployments"
  "$harness_dir/references"
  "$harness_dir/references/requests"
  "$harness_dir/references/specs"
  "$harness_dir/references/stories"
  "$harness_dir/references/domain"
  "$harness_dir/references/iterations"
  "$harness_dir/references/tasks"
  "$harness_dir/references/risks"
  "$harness_dir/archive"
)

render_template() {
  local template_path=$1
  local dest_path=$2
  PROJECT_ID="$project_id" OWNER="$owner" DATE="$created_at" python3 - "$template_path" "$dest_path" <<'PY'
import os
import pathlib
import sys

template_path = pathlib.Path(sys.argv[1])
dest_path = pathlib.Path(sys.argv[2])
text = template_path.read_text(encoding="utf-8")
replacements = {
    "{{PROJECT_ID}}": os.environ["PROJECT_ID"],
    "{{OWNER}}": os.environ["OWNER"],
    "{{DATE}}": os.environ["DATE"],
}
for marker, value in replacements.items():
    text = text.replace(marker, value)
dest_path.write_text(text, encoding="utf-8")
PY
}

if [ "$dry_run" -eq 1 ]; then
  echo "Would create managed directories:"
  printf '  %s\n' "${managed_dirs[@]}"
  echo "Would render fingerprinted templates from $template_dir into $harness_dir"
  echo "Would create root marker: $harness_dir/$fingerprint_file"
  echo "Would normalize managed Markdown governance metadata and refresh INDEX.md"
  exit 0
fi

for dir in "${managed_dirs[@]}"; do
  mkdir -p "$dir"
done

while IFS= read -r template_path; do
  rel_path=${template_path#"$template_dir"/}
  dest_rel=${rel_path%.tmpl}
  dest_path="$harness_dir/$dest_rel"
  mkdir -p "$(dirname "$dest_path")"
  render_template "$template_path" "$dest_path"
done < <(find "$template_dir" -type f -name '*.tmpl' | sort)

for dir in \
  history \
  history/daily \
  checkpoints \
  decisions \
  decisions/architecture \
  decisions/adrs \
  runs \
  runs/tests \
  runs/reports \
  runs/github \
  runs/deployments \
  references \
  references/requests \
  references/specs \
  references/stories \
  references/domain \
  references/iterations \
  references/tasks \
  references/risks \
  archive \
  memory/cards; do
  keep_file="$harness_dir/$dir/.gitkeep"
  if [ ! -f "$keep_file" ]; then
    : > "$keep_file"
  fi
done

python3 "$script_dir/well-organized.py" --project-root "$project_root" >/dev/null

echo "Initialized $harness_dir"
echo "Project id: $project_id"
echo "Owner: $owner"
echo "Harness fingerprint:"
echo "  $harness_dir/$fingerprint_file"
echo "Governance normalization:"
echo "  normalized managed Markdown metadata and refreshed INDEX.md"
echo "Canonical commands:"
echo "  /aries-harness init"
echo "  /aries-harness well-organized"
echo "  /aries-harness pipeline-inspect"
echo "  /aries-harness memory-inspect"
echo "  /aries-harness history-refresh"
echo "  /aries-harness history-status"
echo "Layer manifests:"
echo "  $harness_dir/layers/MetaDefineLayer/README.md"
echo "  $harness_dir/layers/RunCookingLayer/README.md"
echo "  $harness_dir/layers/SharedSupportSurface/README.md"
echo "Repo-local shell equivalents:"
echo "  bash scripts/aries-harness/aries-harness.sh init --project-root $project_root"
echo "  bash scripts/aries-harness/aries-harness.sh well-organized --project-root $project_root"
echo "  bash scripts/aries-harness/aries-harness.sh pipeline-inspect --project-root $project_root"
echo "  bash scripts/aries-harness/aries-harness.sh memory-inspect --project-root $project_root"
echo "  bash scripts/aries-harness/aries-harness.sh history-refresh --project-root $project_root"
echo "  bash scripts/aries-harness/aries-harness.sh history-status --project-root $project_root"
