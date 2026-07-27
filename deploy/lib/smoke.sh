# shellcheck shell=bash
# Post-deploy smoke and health verification.

aulos_curl_retry() {
  local url="$1"
  local attempts="${2:-12}"
  local sleep_s="${3:-1}"
  local i
  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_s"
  done
  return 1
}

aulos_smoke_local() {
  local failed=0
  echo "== local smoke =="
  if aulos_curl_retry "http://127.0.0.1:5090/health"; then
    curl -fsS "http://127.0.0.1:5090/health" && echo
  else
    echo "FAIL: API http://127.0.0.1:5090/health" >&2
    failed=1
  fi
  if curl -fsS "http://127.0.0.1:5091/" >/dev/null; then
    echo "OK: web :5091"
  else
    echo "FAIL: web :5091" >&2
    failed=1
  fi
  if curl -fsS "http://127.0.0.1:5092/" >/dev/null; then
    echo "OK: ops :5092"
  else
    echo "FAIL: ops :5092" >&2
    failed=1
  fi
  if aulos_curl_retry "http://127.0.0.1:5095/health"; then
    curl -fsS "http://127.0.0.1:5095/health" && echo
  else
    echo "FAIL: knowledge http://127.0.0.1:5095/health" >&2
    failed=1
  fi
  return "$failed"
}

aulos_smoke_public() {
  local failed=0
  echo "== public smoke =="
  if aulos_curl_retry "https://aulos.purezen.ai/health" 6 2; then
    curl -fsS "https://aulos.purezen.ai/health" && echo
  else
    echo "FAIL: https://aulos.purezen.ai/health" >&2
    failed=1
  fi
  if aulos_curl_retry "https://aulos-ops.purezen.ai/health" 6 2; then
    curl -fsS "https://aulos-ops.purezen.ai/health" && echo
  else
    echo "FAIL: https://aulos-ops.purezen.ai/health" >&2
    failed=1
  fi
  return "$failed"
}

aulos_smoke_all() {
  local failed=0
  aulos_smoke_local || failed=1
  aulos_smoke_public || failed=1
  if [ "$failed" -ne 0 ]; then
    echo "Smoke checks failed." >&2
    return 1
  fi
  echo "All smoke checks passed."
}
