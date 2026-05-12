/**
 * <ScanProgressBadge> — mostra status da ultima action do tipo X num host.
 *
 * Polling a cada 3s por padrao. Renderiza badge com contexto:
 *   - Sem actions: "Nunca rodado"
 *   - pending:     "Aguardando agente pegar..."  (yellow)
 *   - sent:        "Em execucao desde HH:MM"     (blue)
 *   - executed:    "Concluido HH:MM"             (green)
 *   - failed:      "Falhou: <erro>"              (red)
 *
 * Usado em Clamav/Rkhunter/Chkrootkit/Lynis/AidePanel pra dar feedback
 * de progresso depois do "Rodar scan agora".
 */

import { useEffect, useState } from 'react'

import { ApiError, api } from '@/lib/api'

interface Action {
  id: string
  action_type: string
  target: string | null
  status: string
  created_at: string
  sent_at: string | null
  executed_at: string | null
  error_message: string | null
}

interface Props {
  hostId: string
  actionType: string
  /** se setado, filtra por target (pra clamav scan que tem path como target). */
  target?: string
  /** texto antes do badge, ex: "Último scan:" */
  label?: string
}

const POLL_MS = 3_000

export default function ScanProgressBadge({ hostId, actionType, target, label }: Props) {
  const [last, setLast] = useState<Action | null | undefined>(undefined)

  useEffect(() => {
    let cancelled = false
    function load() {
      api
        .get<Action[]>(`/api/v1/hosts/${hostId}/actions`)
        .then((data) => {
          if (cancelled) return
          const filtered = data.filter(
            (a) => a.action_type === actionType && (!target || a.target === target),
          )
          setLast(filtered[0] ?? null)
        })
        .catch((err) => {
          if (cancelled) return
          if (err instanceof ApiError) console.error('ScanProgressBadge:', err.detail)
        })
    }
    load()
    const t = setInterval(load, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [hostId, actionType, target])

  if (last === undefined) {
    return <span className="text-xs text-zinc-400">…</span>
  }
  if (last === null) {
    return (
      <span className="text-xs text-zinc-500">
        {label && <span>{label} </span>}nunca rodado
      </span>
    )
  }

  const cfg = statusConfig(last.status)
  const time = fmtTime(last.executed_at ?? last.sent_at ?? last.created_at)
  return (
    <span className="text-xs inline-flex items-center gap-2">
      {label && <span className="text-zinc-500">{label}</span>}
      <span className={`px-2 py-0.5 rounded font-medium ${cfg.classes}`}>
        {cfg.dot && <span className="inline-block w-1.5 h-1.5 rounded-full bg-current mr-1 animate-pulse" />}
        {cfg.label}
      </span>
      <span className="text-zinc-500 font-mono">{time}</span>
      {last.status === 'failed' && last.error_message && (
        <span className="text-red-600 dark:text-red-400 truncate max-w-xs" title={last.error_message}>
          ({last.error_message})
        </span>
      )}
    </span>
  )
}

function statusConfig(status: string) {
  switch (status) {
    case 'pending':
      return {
        label: 'aguardando agente',
        classes: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
        dot: true,
      }
    case 'sent':
      return {
        label: 'em execução',
        classes: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200',
        dot: true,
      }
    case 'executed':
      return {
        label: 'concluído',
        classes: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200',
        dot: false,
      }
    case 'failed':
      return {
        label: 'falhou',
        classes: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200',
        dot: false,
      }
    default:
      return {
        label: status,
        classes: 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300',
        dot: false,
      }
  }
}

function fmtTime(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: '2-digit',
  })
}
