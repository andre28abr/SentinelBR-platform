/**
 * <AuditdPanel> — lista regras ativas do auditd (Fase H5).
 *
 * Read-only: o agente roda `auditctl -l` e empacota em JSON. UI lista as
 * regras. Edicao de regras (auditctl -w/-a) fica pra fase futura — admins
 * geralmente editam /etc/audit/rules.d/*.rules direto no host.
 */

import { Icon } from '@iconify/react'
import { useMemo } from 'react'

interface Props {
  statusJson: string | null
}

export default function AuditdPanel({ statusJson }: Props) {
  const rules = useMemo(() => parseRules(statusJson), [statusJson])

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon icon="lucide:file-search" className="text-emerald-700 dark:text-emerald-400 text-xl" />
        <h3 className="text-base font-semibold">auditd</h3>
        <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200">
          ativo
        </span>
      </div>

      <p className="text-sm text-zinc-500">
        Regras ativas no auditd (saída de <code className="font-mono">auditctl -l</code>).
        Pra editar, modifique <code className="font-mono">/etc/audit/rules.d/*.rules</code> no
        host e recarregue com <code className="font-mono">augenrules --load</code>.
      </p>

      {rules.length === 0 ? (
        <p className="text-sm text-zinc-500 italic">
          {statusJson === null
            ? 'Aguardando próximo heartbeat com snapshot do auditd (~30s)…'
            : 'Nenhuma regra carregada — auditd está ativo mas sem rules.'}
        </p>
      ) : (
        <div className="bg-zinc-100 dark:bg-zinc-900 rounded">
          <p className="text-[10px] uppercase text-zinc-500 px-3 pt-2">
            {rules.length} regra{rules.length === 1 ? '' : 's'}
          </p>
          <ul className="text-xs font-mono divide-y divide-zinc-200 dark:divide-zinc-800">
            {rules.map((r, i) => (
              <li key={`${i}-${r.slice(0, 32)}`} className="px-3 py-1.5 break-all">
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function parseRules(json: string | null): string[] {
  if (!json) return []
  try {
    const parsed = JSON.parse(json) as { rules?: string[] }
    return Array.isArray(parsed.rules) ? parsed.rules : []
  } catch {
    return []
  }
}
