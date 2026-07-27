# shellcheck shell=bash
# Shared paths and environment for Aulos host DevOps scripts.

aulos_root() {
  local here
  here="$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
  printf '%s\n' "$here"
}

aulos_init_paths() {
  AULOS_ROOT="$(aulos_root)"
  AULOS_RUN_DIR="$AULOS_ROOT/.run"
  AULOS_UNIT_DIR="${HOME}/.config/systemd/user"
  AULOS_DEPLOY_DIR="$AULOS_ROOT/deploy"
  AULOS_HOST_ENV="$AULOS_RUN_DIR/host.env"
  AULOS_HOST_ENV_EXAMPLE="$AULOS_DEPLOY_DIR/host.env.example"

  export PATH="${PATH}:/home/ubuntu/.nvm/versions/node/v26.4.0/bin"
}

aulos_ensure_runtime_dir() {
  if [ -z "${XDG_RUNTIME_DIR:-}" ]; then
    export XDG_RUNTIME_DIR="/run/user/$(id -u)"
  fi
}

aulos_ensure_run_dir() {
  mkdir -p "$AULOS_RUN_DIR" "$AULOS_UNIT_DIR"
  touch "$AULOS_HOST_ENV"
}

aulos_service_units() {
  printf '%s\n' aulos-api aulos-web aulos-ops aulos-knowledge
}

aulos_unit_name() {
  local short="${1:-}"
  case "$short" in
    api | aulos-api) printf '%s\n' aulos-api.service ;;
    web | aulos-web) printf '%s\n' aulos-web.service ;;
    ops | aulos-ops) printf '%s\n' aulos-ops.service ;;
    knowledge | aulos-knowledge) printf '%s\n' aulos-knowledge.service ;;
    host | aulos-host) printf '%s\n' aulos-host.target ;;
    "") printf '%s\n' aulos-api.service aulos-web.service aulos-ops.service aulos-knowledge.service ;;
    *) printf '%s\n' "$short" ;;
  esac
}

aulos_log_file() {
  local short="${1:-}"
  case "$short" in
    api | aulos-api) printf '%s\n' "$AULOS_RUN_DIR/api.log" ;;
    web | aulos-web) printf '%s\n' "$AULOS_RUN_DIR/web.log" ;;
    ops | aulos-ops) printf '%s\n' "$AULOS_RUN_DIR/ops.log" ;;
    knowledge | aulos-knowledge) printf '%s\n' "$AULOS_RUN_DIR/knowledge.log" ;;
    *) return 1 ;;
  esac
}
