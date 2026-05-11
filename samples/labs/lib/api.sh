#!/usr/bin/env bash
# Helpers que conversam com a REST API do server pra criar host + token de enrollment.
# Requer: curl, jq, e o stack do SentinelBR rodando (server :8000).

set -euo pipefail

# SENTINEL_API_URL: como o SCRIPT (no Mac) alcanca a API. Default: localhost.
# SENTINEL_AGENT_SERVER (em vm.sh): como o AGENTE (na VM) alcanca a API.
: "${SENTINEL_API_URL:=http://localhost:8000}"
: "${SENTINEL_ADMIN_EMAIL:=admin@sentinelbr.io}"
: "${SENTINEL_ADMIN_PASSWORD:=admin1234}"

api::login() {
  curl -sS -X POST "$SENTINEL_API_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$SENTINEL_ADMIN_EMAIL\",\"password\":\"$SENTINEL_ADMIN_PASSWORD\"}" \
    | jq -r .access_token
}

# api::ensure_host NAME HOSTNAME → echoes host_id (idempotente: reutiliza se ja existe)
api::ensure_host() {
  local name="$1" hostname="$2" token
  token="$(api::login)"
  if [[ -z "$token" || "$token" == "null" ]]; then
    echo "FALHA: login nao retornou token (server ta rodando? credenciais corretas?)" >&2
    return 1
  fi

  local existing
  existing="$(curl -sS "$SENTINEL_API_URL/api/v1/hosts" -H "Authorization: Bearer $token" \
    | jq -r --arg n "$name" '.[] | select(.name == $n) | .id' | head -n 1)"
  if [[ -n "$existing" ]]; then
    echo "$existing"
    return 0
  fi

  curl -sS -X POST "$SENTINEL_API_URL/api/v1/hosts" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$name\",\"hostname\":\"$hostname\"}" \
    | jq -r .id
}

# api::enrollment_token HOST_ID → echoes plain-text token (one-shot)
api::enrollment_token() {
  local host_id="$1" token
  token="$(api::login)"
  curl -sS -X POST "$SENTINEL_API_URL/api/v1/hosts/$host_id/enrollment-token" \
    -H "Authorization: Bearer $token" \
    | jq -r .token
}
