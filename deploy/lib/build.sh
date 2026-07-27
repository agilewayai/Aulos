# shellcheck shell=bash
# Build host-deploy artifacts (venvs + frontends).

aulos_ensure_api_venv() {
  echo "[build] Ensure aulos-api venv"
  if [ ! -x "$AULOS_ROOT/aulos-api/.venv/bin/aulos-api" ]; then
    python3 -m venv "$AULOS_ROOT/aulos-api/.venv"
    "$AULOS_ROOT/aulos-api/.venv/bin/pip" install -e "$AULOS_ROOT/aulos-api/[dev]"
  fi
  "$AULOS_ROOT/aulos-api/.venv/bin/pip" install -e "$AULOS_ROOT/aulos-skills" -q
  if [ -x "$AULOS_ROOT/aulos-mcp/.venv/bin/python" ]; then
    "$AULOS_ROOT/aulos-mcp/.venv/bin/pip" install -e "$AULOS_ROOT/aulos-skills" -q || true
  fi
}

aulos_ensure_knowledge_venv() {
  if [ ! -x "$AULOS_ROOT/aulos-knowledge/.venv/bin/aulos-knowledge" ]; then
    echo "[build] Ensure aulos-knowledge venv"
    python3 -m venv "$AULOS_ROOT/aulos-knowledge/.venv"
    "$AULOS_ROOT/aulos-knowledge/.venv/bin/pip" install -e "$AULOS_ROOT/aulos-knowledge/[dev]"
  fi
}

aulos_build_web() {
  echo "[build] aulos-web"
  (
    cd "$AULOS_ROOT/aulos-web"
    npm install --silent
    npm run build
  )
}

aulos_build_ops() {
  echo "[build] aulos-ops"
  (
    cd "$AULOS_ROOT/aulos-ops"
    npm install --silent
    npm run build
  )
}

aulos_build_all() {
  aulos_ensure_api_venv
  aulos_ensure_knowledge_venv
  aulos_build_web
  aulos_build_ops
}
