#!/usr/bin/env bash
# Helpers OrbStack: criar VM, push do agente, instalar deps, enroll, run.

set -euo pipefail

LABS_DIR="${LABS_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
ROOT_DIR="${ROOT_DIR:-$(cd "$LABS_DIR/../.." && pwd)}"
AGENT_BIN="$LABS_DIR/bin/sentinel-agent-linux-arm64"
YARA_RULES_DIR="$ROOT_DIR/agent/yara-rules"

# Como o agente (dentro da VM) alcanca o server no Mac.
: "${SENTINEL_AGENT_SERVER:=http://host.orb.internal:8000}"
: "${SENTINEL_AGENT_GRPC:=host.orb.internal:9443}"

vm::exists() {
  orbctl list -q 2>/dev/null | grep -qx "$1"
}

vm::create() {
  local name="$1" distro="$2" arch="${3:-arm64}"
  if vm::exists "$name"; then
    echo "  - VM $name ja existe, pulando create"
    return 0
  fi
  echo "  + criando VM $name ($distro $arch)"
  orbctl create -a "$arch" -u sentinel "$distro" "$name" >/dev/null
}

vm::install_deps() {
  local name="$1" pkg_mgr="$2"  # apt | dnf
  echo "  + instalando yara em $name"
  case "$pkg_mgr" in
    apt)
      orb -m "$name" -u root bash -c \
        'export DEBIAN_FRONTEND=noninteractive && apt-get update -qq && apt-get install -y -qq yara curl ca-certificates >/dev/null'
      ;;
    dnf)
      orb -m "$name" -u root dnf install -y -q yara curl ca-certificates >/dev/null
      ;;
    *) echo "pkg_mgr desconhecido: $pkg_mgr" >&2; return 1;;
  esac

  # ClamAV opcional (controlado por INSTALL_CLAMAV=true no .env da distro).
  # freshclam baixa ~200MB de assinaturas e pode demorar 1-2min — rodamos com
  # || true pra nao quebrar o provision se a rede falhar.
  if [[ "${INSTALL_CLAMAV:-false}" == "true" ]]; then
    echo "  + instalando clamav em $name (freshclam pode demorar ~1min)"
    case "$pkg_mgr" in
      apt)
        orb -m "$name" -u root bash -c \
          'export DEBIAN_FRONTEND=noninteractive && \
           apt-get install -y -qq clamav clamav-daemon >/dev/null && \
           (systemctl stop clamav-freshclam 2>/dev/null || true) && \
           (freshclam --quiet || true) && \
           (systemctl start clamav-freshclam 2>/dev/null || true)'
        ;;
      dnf)
        orb -m "$name" -u root bash -c \
          'dnf install -y -q clamav clamav-update >/dev/null && \
           (sed -i "s/^Example/#Example/" /etc/freshclam.conf 2>/dev/null || true) && \
           (freshclam --quiet || true)'
        ;;
    esac
  fi
}

vm::push_agent() {
  local name="$1"
  if [[ ! -x "$AGENT_BIN" ]]; then
    echo "FALHA: $AGENT_BIN nao existe — rode 'make lab-build-agent' antes" >&2
    return 1
  fi
  echo "  + push do binario sentinel-agent + regras YARA pra $name"
  orbctl push -m "$name" "$AGENT_BIN" /tmp/sentinel-agent
  orb -m "$name" -u root bash -c 'mv /tmp/sentinel-agent /usr/local/bin/sentinel-agent && chmod +x /usr/local/bin/sentinel-agent'
  orb -m "$name" -u root mkdir -p /etc/sentinelbr/yara-rules
  for rule in "$YARA_RULES_DIR"/*.yar; do
    orbctl push -m "$name" "$rule" "/tmp/$(basename "$rule")"
    orb -m "$name" -u root bash -c "mv /tmp/$(basename "$rule") /etc/sentinelbr/yara-rules/"
  done
}

vm::enroll() {
  local name="$1" token="$2"
  echo "  + enroll $name no server"
  orb -m "$name" -u root sentinel-agent enroll \
    --server="$SENTINEL_AGENT_SERVER" \
    --grpc="$SENTINEL_AGENT_GRPC" \
    --token="$token" >/dev/null

  # Quirk do lab: o server responde com grpc_endpoint=localhost:9443 (config
  # default — pra dev local no Mac). De dentro da VM, "localhost" eh a propria
  # VM, nao o Mac. Patcheamos state.json pra apontar pro host.orb.internal.
  # Em prod o server seria configurado com SENTINELBR_GRPC_PUBLIC_ENDPOINT.
  orb -m "$name" -u root sed -i \
    "s|\"grpc_endpoint\":\\s*\"localhost:9443\"|\"grpc_endpoint\": \"$SENTINEL_AGENT_GRPC\"|" \
    /root/.sentinelbr/state.json
}

vm::install_systemd() {
  local name="$1"
  cat > /tmp/sentinelbr-agent.service <<'EOF'
[Unit]
Description=SentinelBR agent (lab)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment=HOME=/root
ExecStart=/usr/local/bin/sentinel-agent run \
  --ssh-source-file=/var/log/auth.log \
  --yara-rules-path=/etc/sentinelbr/yara-rules \
  --yara-watch-dir=/var/www \
  --yara-watch-dir=/tmp \
  --quarantine-dry-run \
  --firewall-dry-run
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
  orbctl push -m "$name" /tmp/sentinelbr-agent.service /tmp/sentinelbr-agent.service
  orb -m "$name" -u root bash -c '
    mv /tmp/sentinelbr-agent.service /etc/systemd/system/sentinelbr-agent.service &&
    systemctl daemon-reload &&
    systemctl enable --now sentinelbr-agent.service
  '
  rm -f /tmp/sentinelbr-agent.service
}

vm::status() {
  local name="$1"
  if ! vm::exists "$name"; then
    echo "  - $name: nao existe"
    return
  fi
  local heartbeat
  heartbeat="$(orb -m "$name" -u root systemctl is-active sentinelbr-agent 2>/dev/null || echo 'desconhecido')"
  echo "  $name: agente=$heartbeat"
}

vm::delete() {
  local name="$1"
  if vm::exists "$name"; then
    echo "  - removendo $name"
    orbctl delete -f "$name" >/dev/null 2>&1 || true
  fi
}
