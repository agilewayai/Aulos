# shellcheck shell=bash
# Operator secret validation for host deploy.

aulos_required_secret_keys() {
  printf '%s\n' \
    AULOS_JWT_SECRET \
    AULOS_BOOTSTRAP_SUPERADMIN_EMAIL \
    AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD \
    AULOS_KNOWLEDGE_ADMIN_TOKEN
}

aulos_load_host_env() {
  if [ ! -s "$AULOS_HOST_ENV" ]; then
    echo "ERROR: $AULOS_HOST_ENV is missing or empty." >&2
    echo "Run: bash deploy/aulos-ctl.sh secrets init" >&2
    return 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "$AULOS_HOST_ENV"
  set +a
}

aulos_secret_is_default() {
  local value="$1"
  case "$value" in
    aulos-dev-jwt-secret*|dev-only*|ChangeMe*|change-me*|REPLACE_WITH_*)
      return 0
      ;;
  esac
  return 1
}

aulos_check_secret() {
  local name="$1"
  local value="$2"
  if [ -z "${value// }" ]; then
    echo "ERROR: $name must be set in $AULOS_HOST_ENV" >&2
    return 1
  fi
  if aulos_secret_is_default "$value"; then
    echo "ERROR: $name uses a placeholder/default; set a unique value in $AULOS_HOST_ENV" >&2
    return 1
  fi
  return 0
}

aulos_validate_secrets() {
  aulos_load_host_env || return 1
  local key
  local failed=0
  while IFS= read -r key; do
    # shellcheck disable=SC2154
    if ! aulos_check_secret "$key" "${!key:-}"; then
      failed=1
    fi
  done < <(aulos_required_secret_keys)
  return "$failed"
}

aulos_secrets_init() {
  aulos_ensure_run_dir
  if [ -s "$AULOS_HOST_ENV" ]; then
    echo "host.env already exists at $AULOS_HOST_ENV — not overwriting."
    echo "Edit in place or remove the file to re-init."
    return 0
  fi
  cp "$AULOS_HOST_ENV_EXAMPLE" "$AULOS_HOST_ENV"
  chmod 600 "$AULOS_HOST_ENV"

  local jwt knowledge password
  jwt="$(openssl rand -base64 48 | tr -d '\n')"
  knowledge="$(openssl rand -hex 32)"
  password="$(openssl rand -base64 18 | tr -d '/+=' | head -c 24)"

  # Replace placeholders in place (portable sed).
  sed -i "s|^AULOS_JWT_SECRET=.*|AULOS_JWT_SECRET=${jwt}|" "$AULOS_HOST_ENV"
  sed -i "s|^AULOS_KNOWLEDGE_ADMIN_TOKEN=.*|AULOS_KNOWLEDGE_ADMIN_TOKEN=${knowledge}|" "$AULOS_HOST_ENV"
  sed -i "s|^AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD=.*|AULOS_BOOTSTRAP_SUPERADMIN_PASSWORD=${password}|" "$AULOS_HOST_ENV"

  echo "Created $AULOS_HOST_ENV (mode 600)."
  echo "Edit AULOS_BOOTSTRAP_SUPERADMIN_EMAIL, then run: bash deploy/aulos-ctl.sh deploy"
}
