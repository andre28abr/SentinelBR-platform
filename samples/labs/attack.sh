#!/usr/bin/env bash
# Re-roda os scripts de plant nas VMs ja existentes (nao recria as VMs).
# Util pra "atacar de novo": webshells voltam, tentativas brute-force novas
# entram no auth.log, etc. Disparara novos alertas no UI.

set -euo pipefail

LABS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/vm.sh
source "$LABS_DIR/lib/vm.sh"
# shellcheck source=lib/plant.sh
source "$LABS_DIR/lib/plant.sh"

DISTROS=("$@")
if [[ ${#DISTROS[@]} -eq 0 ]]; then
  DISTROS=(debian-11 ubuntu-22 fedora vuln-lab)
fi

for d in "${DISTROS[@]}"; do
  envfile="$LABS_DIR/distros/$d.env"
  [[ -f "$envfile" ]] || continue
  # shellcheck source=/dev/null
  source "$envfile"

  if ! vm::exists "$VM_NAME"; then
    echo "  - $VM_NAME nao existe, pulando"
    continue
  fi

  echo "▶ re-atacando $DISPLAY_NAME"
  plant::yara_targets "$VM_NAME"
  plant::bruteforce   "$VM_NAME" 8 "198.51.100.$((RANDOM % 254 + 1))"
  if [[ "${AGGRESSIVE:-false}" == "true" ]]; then
    plant::aggressive "$VM_NAME"
  fi
done

echo "✓ ataque renovado. Novos alertas vao aparecer no UI em <30s."
