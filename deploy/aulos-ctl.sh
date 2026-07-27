#!/usr/bin/env bash
# Aulos host DevOps control plane — single entry for deploy, smoke, status, secrets.
set -euo pipefail

_CTL_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
# shellcheck source=lib/common.sh
source "$_CTL_DIR/lib/common.sh"
# shellcheck source=lib/secrets.sh
source "$_CTL_DIR/lib/secrets.sh"
# shellcheck source=lib/build.sh
source "$_CTL_DIR/lib/build.sh"
# shellcheck source=lib/smoke.sh
source "$_CTL_DIR/lib/smoke.sh"

aulos_init_paths
aulos_ensure_runtime_dir

usage() {
  cat <<'EOF'
Aulos host DevOps control (production stack on this machine).

Usage:
  bash deploy/aulos-ctl.sh <command> [args]

Commands:
  deploy              Full production deploy (build + secrets + systemd + ingress + smoke)
  build               Build venvs and portal dist/ only
  restart [service]   Restart all or one service (api|web|ops|knowledge|host)
  status              systemd units + ingress summary
  smoke               Health checks (local + public, with retry)
  logs <service>      Tail last 80 lines (api|web|ops|knowledge); -f to follow
  doctor              Preflight: linger, secrets, ports, kubectl, postgres
  secrets init        Create .run/host.env from template with random secrets
  secrets check       Validate operator secrets without deploying
  units install       Copy systemd units and daemon-reload
  ingress apply       Apply k3s Service/Ingress manifests
  test                Run deploy pytest suite (rate gate, headers, cache)

Environment:
  XDG_RUNTIME_DIR     Set automatically when missing (systemd user bus)
  AULOS_BUILD_ID      Optional portal build id override (see deploy/README.md)

Docs: deploy/OPS.md · deploy/README.md
EOF
}

cmd_doctor() {
  local ok=1
  echo "== aulos doctor =="
  echo "root: $AULOS_ROOT"

  if loginctl show-user "$(whoami)" -p Linger 2>/dev/null | grep -q 'yes'; then
    echo "OK: loginctl linger enabled"
  else
    echo "WARN: loginctl linger not enabled — services may stop on logout" >&2
    ok=0
  fi

  if command -v kubectl >/dev/null 2>&1; then
    echo "OK: kubectl present"
  else
    echo "WARN: kubectl not found (ingress apply will fail)" >&2
    ok=0
  fi

  if aulos_validate_secrets 2>/dev/null; then
    echo "OK: host.env secrets"
  else
    echo "WARN: host.env secrets incomplete or placeholder" >&2
    ok=0
  fi

  local port
  for port in 5090 5091 5092 5095 5433 6379; do
    if ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":${port}$"; then
      echo "OK: port :$port listening"
    else
      echo "WARN: port :$port not listening" >&2
    fi
  done

  if [ "$ok" -eq 1 ]; then
    echo "Doctor: ready for deploy."
  else
    echo "Doctor: issues found — fix warnings before deploy." >&2
    return 1
  fi
}

cmd_units_install() {
  aulos_ensure_run_dir
  echo "[units] Install systemd user units"
  cp -f "$AULOS_DEPLOY_DIR/systemd/user/"*.service "$AULOS_UNIT_DIR/"
  cp -f "$AULOS_DEPLOY_DIR/systemd/user/"*.target "$AULOS_UNIT_DIR/"
  systemctl --user daemon-reload
  systemctl --user enable aulos-host.target
}

cmd_ingress_apply() {
  echo "[ingress] Apply k3s manifests"
  sudo kubectl apply -f "$AULOS_DEPLOY_DIR/k3s/aulos.yaml"
  sudo kubectl get ingress aulos-web aulos-ops
}

cmd_restart() {
  local target="${1:-}"
  aulos_ensure_runtime_dir
  if [ -z "$target" ]; then
    systemctl --user restart aulos-api.service aulos-web.service aulos-ops.service aulos-knowledge.service
  else
    systemctl --user restart "$(aulos_unit_name "$target")"
  fi
}

cmd_status() {
  aulos_ensure_runtime_dir
  systemctl --user --no-pager --plain status aulos-host.target \
    aulos-api.service aulos-web.service aulos-ops.service aulos-knowledge.service | sed -n '1,120p' || true
  echo
  if command -v kubectl >/dev/null 2>&1; then
    sudo kubectl get ingress aulos-web aulos-ops 2>/dev/null || true
  fi
}

cmd_logs() {
  local follow=0
  local service=""
  while [ $# -gt 0 ]; do
    case "$1" in
      -f | --follow) follow=1; shift ;;
      *) service="$1"; shift ;;
    esac
  done
  if [ -z "$service" ]; then
    echo "Usage: aulos-ctl logs [-f] <api|web|ops|knowledge>" >&2
    return 1
  fi
  local log
  log="$(aulos_log_file "$service")" || {
    echo "Unknown service: $service" >&2
    return 1
  }
  if [ "$follow" -eq 1 ]; then
    tail -f "$log"
  else
    tail -n 80 "$log"
  fi
}

cmd_test() {
  echo "[test] deploy pytest suite"
  if [ ! -x "$AULOS_ROOT/aulos-api/.venv/bin/python" ]; then
  python3 -m venv "$AULOS_ROOT/aulos-api/.venv"
  "$AULOS_ROOT/aulos-api/.venv/bin/pip" install -e "$AULOS_ROOT/aulos-api/[dev]" -q
  fi
  "$AULOS_ROOT/aulos-api/.venv/bin/python" -m pytest -q \
    "$AULOS_DEPLOY_DIR/test_rate_gate.py" \
    "$AULOS_DEPLOY_DIR/test_serve_cache.py" \
    "$AULOS_DEPLOY_DIR/test_security_headers.py"
}

cmd_deploy() {
  aulos_ensure_run_dir
  aulos_build_all
  echo "[deploy] Validate operator secrets"
  aulos_validate_secrets
  cmd_units_install
  systemctl --user enable --now aulos-host.target
  cmd_restart
  cmd_ingress_apply
  echo
  cmd_status
  echo
  sleep 2
  aulos_smoke_all
}

main() {
  local cmd="${1:-help}"
  shift || true
  case "$cmd" in
    help | -h | --help) usage ;;
    deploy) cmd_deploy "$@" ;;
    build) aulos_build_all ;;
    restart) cmd_restart "$@" ;;
    status) cmd_status "$@" ;;
    smoke) aulos_smoke_all ;;
    logs) cmd_logs "$@" ;;
    doctor) cmd_doctor "$@" ;;
    test) cmd_test "$@" ;;
    secrets)
      local sub="${1:-}"
      shift || true
      case "$sub" in
        init) aulos_secrets_init ;;
        check) aulos_validate_secrets && echo "host.env secrets OK" ;;
        *) echo "Usage: aulos-ctl secrets {init|check}" >&2; return 1 ;;
      esac
      ;;
    units)
      local sub="${1:-}"
      shift || true
      case "$sub" in
        install) cmd_units_install ;;
        *) echo "Usage: aulos-ctl units install" >&2; return 1 ;;
      esac
      ;;
    ingress)
      local sub="${1:-}"
      shift || true
      case "$sub" in
        apply) cmd_ingress_apply ;;
        *) echo "Usage: aulos-ctl ingress apply" >&2; return 1 ;;
      esac
      ;;
    *)
      echo "Unknown command: $cmd" >&2
      usage >&2
      return 1
      ;;
  esac
}

main "$@"
