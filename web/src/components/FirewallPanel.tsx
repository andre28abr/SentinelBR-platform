/**
 * <FirewallPanel> — snapshot read-only do firewall ativo (Fase H4).
 *
 * O agente roda `ufw status numbered` / `firewall-cmd --list-all` / `nft list
 * ruleset` / `iptables -L -n -v` (dependendo do backend) e empacota em JSON
 * com `{backend, raw}`. UI renderiza como bloco monoespaçado.
 *
 * Ações write (allow/deny port/IP) ficam pra fase futura.
 */

import { Icon } from '@iconify/react'
import { useMemo } from 'react'

interface Props {
  backend: string // ufw | firewalld | nftables | iptables
  statusJson: string | null
}

export default function FirewallPanel({ backend, statusJson }: Props) {
  const raw = useMemo(() => parseRaw(statusJson), [statusJson])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <Icon icon="lucide:brick-wall" className="text-emerald-700 dark:text-emerald-400 text-xl" />
        <h3 className="text-base font-semibold">Firewall</h3>
        <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200 font-mono">
          {backend}
        </span>
      </div>

      <p className="text-sm text-zinc-500">
        Snapshot read-only do firewall ativo no host. Reportado a cada
        heartbeat. Modificar regras pela UI virá em fase futura — por enquanto,
        edite no host e aguarde o próximo heartbeat (~30s).
      </p>

      {raw ? (
        <pre className="text-xs font-mono bg-zinc-100 dark:bg-zinc-900 p-3 rounded overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap">
          {raw}
        </pre>
      ) : (
        <p className="text-sm text-zinc-500 italic">
          {statusJson === null
            ? 'Aguardando próximo heartbeat com snapshot do firewall (~30s)…'
            : 'Snapshot vazio. O agente pode não ter permissão pra ler as regras.'}
        </p>
      )}
    </div>
  )
}

function parseRaw(json: string | null): string {
  if (!json) return ''
  try {
    const parsed = JSON.parse(json) as { raw?: string }
    return typeof parsed.raw === 'string' ? parsed.raw : ''
  } catch {
    return ''
  }
}
