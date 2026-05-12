#!/usr/bin/env bash
# Sobe TODAS as VMs do lab (ou as listadas em $@), provisiona o agente,
# planta vulnerabilidades. Idempotente — pode rodar de novo pra "renovar".
#
# Pre-req:
#   - OrbStack instalado e rodando
#   - stack do SentinelBR rodando: server + grpc + worker + beat (`make dev` + `make server` + `make grpc` + `make worker` + `make beat`)
#   - binario cross-compilado: `make lab-build-agent`

set -euo pipefail

LABS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/api.sh
source "$LABS_DIR/lib/api.sh"
# shellcheck source=lib/vm.sh
source "$LABS_DIR/lib/vm.sh"
# shellcheck source=lib/plant.sh
source "$LABS_DIR/lib/plant.sh"

DISTROS=("$@")
if [[ ${#DISTROS[@]} -eq 0 ]]; then
  DISTROS=(debian-11 ubuntu-22 fedora rocky-9 alpine-3 vuln-lab)
fi

# Pre-flight checks
command -v orb >/dev/null 2>&1 || { echo "FALHA: 'orb' nao encontrado (instale OrbStack)" >&2; exit 1; }
command -v jq  >/dev/null 2>&1 || { echo "FALHA: 'jq' nao encontrado (brew install jq)" >&2; exit 1; }
[[ -x "$LABS_DIR/bin/sentinel-agent-linux-arm64" ]] || \
  { echo "FALHA: binario do agente nao existe — rode 'make lab-build-agent'" >&2; exit 1; }
api::login >/dev/null || \
  { echo "FALHA: server nao responde em $SENTINEL_SERVER (rode 'make server' + 'make grpc')" >&2; exit 1; }

for d in "${DISTROS[@]}"; do
  envfile="$LABS_DIR/distros/$d.env"
  [[ -f "$envfile" ]] || { echo "FALHA: distro '$d' nao tem env em $envfile" >&2; exit 1; }
  # Reset opt-ins entre iteracoes — sem isso, flags do .env anterior vazariam
  # pro proximo (ex: INSTALL_HARDENING_TOOLS do fedora.env afetando ubuntu-22).
  unset INSTALL_CLAMAV INSTALL_HARDENING_TOOLS AGGRESSIVE
  # shellcheck source=/dev/null
  source "$envfile"

  echo "▶ provisionando $DISPLAY_NAME ($VM_NAME)"
  vm::create   "$VM_NAME" "$DISTRO" "$ARCH"
  vm::install_deps "$VM_NAME" "$PKG_MGR"
  vm::push_agent "$VM_NAME"

  host_id="$(api::ensure_host "$DISPLAY_NAME" "$HOSTNAME")"
  echo "  host_id no DB: $host_id"

  # Re-enroll: o token eh one-shot, entao se a VM ja foi enrollada antes
  # (state.json existe), pulamos. Se nao, geramos um novo token.
  if orb -m "$VM_NAME" -u root test -f /root/.sentinelbr/state.json 2>/dev/null; then
    echo "  - $VM_NAME ja enrollado, pulando enroll"
  else
    token="$(api::enrollment_token "$host_id")"
    [[ -n "$token" && "$token" != "null" ]] || \
      { echo "FALHA: nao consegui gerar token de enrollment" >&2; exit 1; }
    vm::enroll "$VM_NAME" "$token"
  fi

  vm::install_systemd "$VM_NAME"

  # Plant vulnerabilities
  plant::yara_targets   "$VM_NAME"
  plant::bruteforce     "$VM_NAME" 12
  plant::vuln_packages  "$VM_NAME" "$PKG_MGR"
  # Iscas universais — exercitam YARA (Dropper/ReverseShell/Persistence) +
  # ClamAV (EICAR). Inertes: nada eh executado, so texto pra detectores.
  plant::eicar          "$VM_NAME"
  plant::dropper        "$VM_NAME"
  plant::reverse_shell  "$VM_NAME"
  plant::persistence    "$VM_NAME"
  if [[ "${AGGRESSIVE:-false}" == "true" ]]; then
    plant::aggressive "$VM_NAME"
  fi
  plant::trigger_inventory "$VM_NAME"

  echo "✓ $DISPLAY_NAME pronto (heartbeat em <30s, vulns aparecerao no UI)"
  echo
done

echo "═══════════════════════════════════════════════════════════════"
echo "Lab pronto. Veja em http://localhost:5173"
echo "Detalhes do que foi plantado em cada VM: samples/labs/EXPECTED.md"
echo "Para mostrar status:                      make lab-status"
echo "Para destruir tudo:                       make lab-down"
echo "═══════════════════════════════════════════════════════════════"
