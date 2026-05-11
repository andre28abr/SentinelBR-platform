#!/usr/bin/env bash
# Destroi TODAS as VMs do lab (orbctl delete -f). Sem prompt — assume que voce
# sabe o que esta fazendo. NAO mexe no banco do server (hosts ficam la com
# status 'inactive' apos o heartbeat parar).

set -euo pipefail

LABS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/vm.sh
source "$LABS_DIR/lib/vm.sh"

DISTROS=("$@")
if [[ ${#DISTROS[@]} -eq 0 ]]; then
  DISTROS=(debian-11 ubuntu-22 fedora vuln-lab)
fi

for d in "${DISTROS[@]}"; do
  envfile="$LABS_DIR/distros/$d.env"
  [[ -f "$envfile" ]] || continue
  # shellcheck source=/dev/null
  source "$envfile"
  vm::delete "$VM_NAME"
done

echo "✓ VMs do lab removidas. Os hosts permanecem no DB (sumario historico)."
echo "  Pra remover do DB tambem: na UI, deletar pelo botao do host."
