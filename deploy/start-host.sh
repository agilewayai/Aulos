#!/usr/bin/env bash
# Back-compat wrapper — prefer: bash deploy/aulos-ctl.sh deploy
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
exec bash "$ROOT/deploy/aulos-ctl.sh" deploy "$@"
