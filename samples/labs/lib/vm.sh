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
  local name="$1" pkg_mgr="$2"  # apt | dnf | apk
  # Rocky/Alma (RHEL clones) nao tem clamav/rkhunter/chkrootkit/lynis no
  # repo base — esses pacotes ficam no EPEL. Fedora ja vem com tudo.
  # Habilitamos EPEL aqui pra todo install dnf subsequente encontrar.
  if [[ "$pkg_mgr" == "dnf" ]]; then
    # /etc/os-release pode ter ID com ou sem aspas (ID="rocky" no Rocky 9,
    # ID=fedora no Fedora). Usa ID_LIKE como fallback robusto pra RHEL clones.
    orb -m "$name" -u root bash -c '
      if grep -qE "^ID=\"?(rocky|almalinux|centos|ol)\"?" /etc/os-release || \
         grep -qE "^ID_LIKE=.*rhel" /etc/os-release; then
        # Fedora tem ID_LIKE com rhel as vezes, entao excluimos explicitamente.
        if ! grep -qE "^ID=fedora" /etc/os-release; then
          dnf install -y -q epel-release >/dev/null 2>&1 || true
        fi
      fi
    '
  fi
  echo "  + instalando yara em $name"
  case "$pkg_mgr" in
    apt)
      orb -m "$name" -u root bash -c \
        'export DEBIAN_FRONTEND=noninteractive && apt-get update -qq && apt-get install -y -qq yara curl ca-certificates >/dev/null'
      ;;
    dnf)
      orb -m "$name" -u root dnf install -y -q yara curl ca-certificates >/dev/null
      ;;
    apk)
      # Alpine: musl libc + busybox. apk eh super rapido.
      orb -m "$name" -u root sh -c \
        'apk add --quiet --no-cache yara curl ca-certificates bash'
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
      apk)
        orb -m "$name" -u root sh -c \
          'apk add --quiet --no-cache clamav clamav-libunrar && \
           (freshclam --quiet || true)'
        ;;
    esac
  fi

  # Hardening tools (Tier 1+2): fail2ban + auditd + rkhunter + chkrootkit +
  # lynis + AIDE + firewall. Opt-in via INSTALL_HARDENING_TOOLS=true.
  # Hoje so o lab-fedora liga isso pra showcase da aba "Ferramentas".
  if [[ "${INSTALL_HARDENING_TOOLS:-false}" == "true" ]]; then
    vm::install_hardening_tools "$name" "$pkg_mgr"
  fi
}

# Instala suite Tier 1+2 e configura tudo pra UI mostrar dados nao-vazios:
# - fail2ban: jail.local minimo + ban manual de 1 IP fake pra UI
# - firewall: regra de exemplo
# - auditd: regra de monitoring de /etc/passwd
# - AIDE: instala mas NAO roda --init (demora ~5min, fica pro user)
vm::install_hardening_tools() {
  local name="$1" pkg_mgr="$2"
  echo "  + instalando suite hardening (fail2ban+auditd+rkhunter+chkrootkit+lynis+aide+firewall) em $name"
  case "$pkg_mgr" in
    apt)
      orb -m "$name" -u root bash -c \
        'export DEBIAN_FRONTEND=noninteractive && \
         apt-get install -y -qq fail2ban auditd rkhunter chkrootkit lynis aide ufw apparmor-utils >/dev/null'
      orb -m "$name" -u root bash -c \
        '(systemctl enable --now fail2ban 2>/dev/null || true) && \
         (systemctl enable --now auditd 2>/dev/null || true) && \
         (ufw --force enable 2>/dev/null || true)'
      ;;
    dnf)
      # Instala pacote por pacote — pacotes que faltam (ex: chkrootkit em
      # Rocky 9 mesmo com EPEL) sao silenciosamente pulados. Agente detecta
      # via LookPath e UI mostra "nao detectado" pra cards faltantes.
      orb -m "$name" -u root bash -c \
        'for pkg in fail2ban audit rkhunter chkrootkit lynis aide firewalld; do
           dnf install -y -q "$pkg" >/dev/null 2>&1 || echo "  (sem $pkg neste distro)"
         done'
      # SELinux pacotes — em container OrbStack o kernel nao suporta ativar
      # (selinuxfs ausente), mas instalar getenforce/sestatus deixa o agente
      # detectar e a UI mostrar status "Disabled" + comandos. Em VM real ja
      # vem instalado.
      orb -m "$name" -u root bash -c \
        'dnf install -y -q policycoreutils selinux-policy selinux-policy-targeted >/dev/null 2>&1 || true'
      # Service activation — silencia falhas (orbstack containers as vezes nao tem
      # systemd completo, mas o agente detecta via LookPath de qualquer forma).
      orb -m "$name" -u root bash -c \
        '(systemctl enable --now fail2ban 2>/dev/null || true) && \
         (systemctl enable --now auditd 2>/dev/null || true) && \
         (systemctl enable --now firewalld 2>/dev/null || true)'
      ;;
    apk)
      # Alpine: pacotes disponiveis no community/main repos.
      # rkhunter/chkrootkit/lynis NAO existem no Alpine (silencia gracefully —
      # cards do UI mostram "nao detectado" + hint de install).
      orb -m "$name" -u root sh -c \
        'apk add --quiet --no-cache fail2ban audit aide nftables ip6tables 2>/dev/null || true'
      orb -m "$name" -u root sh -c \
        '(rc-update add fail2ban default 2>/dev/null || true) && \
         (rc-service fail2ban start 2>/dev/null || true)'
      ;;
  esac

  # fail2ban jail.local minimo: ativa sshd jail. Sem isso fail2ban-client status
  # retorna 0 jails configurados. Se /etc/fail2ban nao existe (pkg nao
  # instalado, ex: Alpine repo sem fail2ban), pula sem quebrar.
  orb -m "$name" -u root sh -c '
    if [ -d /etc/fail2ban ]; then
      cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime = 600
findtime = 600
maxretry = 3

[sshd]
enabled = true
EOF
      (systemctl restart fail2ban 2>/dev/null || rc-service fail2ban restart 2>/dev/null || true)
    fi
  '

  # Aguarda fail2ban subir e bana 2 IPs fake (RFC 5737 documentation prefix
  # — IPs reservados pra docs, nao existem). Da dado nao-vazio pra UI mostrar.
  orb -m "$name" -u root sh -c '
    sleep 3
    (fail2ban-client set sshd banip 198.51.100.42 2>/dev/null || true)
    (fail2ban-client set sshd banip 203.0.113.42 2>/dev/null || true)
  '

  # Auditd: 1 regra de exemplo monitorando /etc/passwd writes.
  orb -m "$name" -u root sh -c '
    (auditctl -w /etc/passwd -p wa -k passwd_changes 2>/dev/null || true)
  '

  # firewalld: 1 regra de exemplo pra UI mostrar algo.
  if [[ "$pkg_mgr" == "dnf" ]]; then
    orb -m "$name" -u root bash -c '
      (firewall-cmd --permanent --add-rich-rule="rule family=\"ipv4\" source address=\"198.51.100.0/24\" port port=\"22\" protocol=\"tcp\" reject" 2>/dev/null || true) && \
      (firewall-cmd --reload 2>/dev/null || true)
    '
  fi

  echo "  + suite hardening pronta em $name (AIDE precisa 'aide --init' pra primeiro check)"
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
  # Se o serviço já está rodando (re-provision), reinicia pra usar o binário novo.
  # Em primeiro provision o systemctl unit ainda nao existe — silencia falha.
  orb -m "$name" -u root bash -c \
    '(systemctl restart sentinelbr-agent.service 2>/dev/null || true)'
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
  local name="$1" pkg_mgr="${2:-}"
  # Alpine usa OpenRC (nao systemd) — usa um init script diferente.
  if [[ "$pkg_mgr" == "apk" ]]; then
    vm::install_openrc "$name"
    return
  fi
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

# vm::install_openrc — supervisor pro agent em Alpine (OpenRC, NAO systemd).
# Cria init script em /etc/init.d/sentinelbr-agent + rc-update add.
vm::install_openrc() {
  local name="$1"
  cat > /tmp/sentinelbr-agent.openrc <<'EOF'
#!/sbin/openrc-run

name="sentinelbr-agent"
description="SentinelBR agent (lab)"
command="/usr/local/bin/sentinel-agent"
command_args="run --ssh-source-file=/var/log/auth.log --yara-rules-path=/etc/sentinelbr/yara-rules --yara-watch-dir=/var/www --yara-watch-dir=/tmp --quarantine-dry-run --firewall-dry-run"
command_background=true
pidfile="/run/${RC_SVCNAME}.pid"
output_log="/var/log/${RC_SVCNAME}.log"
error_log="/var/log/${RC_SVCNAME}.log"

depend() {
  need net
  after firewall
}
EOF
  orbctl push -m "$name" /tmp/sentinelbr-agent.openrc /tmp/sentinelbr-agent.openrc
  orb -m "$name" -u root sh -c '
    mv /tmp/sentinelbr-agent.openrc /etc/init.d/sentinelbr-agent &&
    chmod +x /etc/init.d/sentinelbr-agent &&
    rc-update add sentinelbr-agent default >/dev/null 2>&1 &&
    rc-service sentinelbr-agent start
  '
  rm -f /tmp/sentinelbr-agent.openrc
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
