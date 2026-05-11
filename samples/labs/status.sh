#!/usr/bin/env bash
# Mostra status das VMs do lab + status no DB.

set -euo pipefail

LABS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/vm.sh
source "$LABS_DIR/lib/vm.sh"

echo "═ OrbStack VMs ═════════════════════════════════════════════════"
orbctl list 2>&1 | (grep -E 'lab-|NAME' || echo "  nenhuma VM lab- ainda")

echo
echo "═ Agente em cada VM ════════════════════════════════════════════"
for d in debian-11 ubuntu-22 fedora vuln-lab; do
  envfile="$LABS_DIR/distros/$d.env"
  [[ -f "$envfile" ]] || continue
  # shellcheck source=/dev/null
  source "$envfile"
  vm::status "$VM_NAME"
done

echo
echo "═ Hosts no banco ═══════════════════════════════════════════════"
docker exec sentinelbr-dev-postgres-1 psql -U sentinelbr -d sentinelbr -t \
  -c "SELECT name || ' — status=' || status || ' — hb=' || COALESCE(last_heartbeat::text, 'nunca') FROM hosts WHERE name LIKE 'Lab %' ORDER BY name;" \
  2>/dev/null || echo "  Postgres nao acessivel (stack rodando?)"
