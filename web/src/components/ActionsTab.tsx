import { useEffect, useState } from 'react'

import { ApiError, api } from '@/lib/api'

interface Action {
  id: string
  host_id: string
  alert_id: string | null
  action_type: string
  target: string
  reason: string
  status: string
  error_message: string | null
  created_at: string
  sent_at: string | null
  executed_at: string | null
  reverted_at: string | null
}

const REFRESH_MS = 5_000

export default function ActionsTab({ hostId }: { hostId: string }) {
  const [actions, setActions] = useState<Action[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    function load() {
      api
        .get<Action[]>(`/api/v1/hosts/${hostId}/actions`)
        .then((data) => {
          if (cancelled) return
          setActions(data)
          setError(null)
        })
        .catch((err) => {
          if (cancelled) return
          setError(err instanceof ApiError ? String(err.detail) : 'erro')
        })
        .finally(() => {
          if (!cancelled) setLoading(false)
        })
    }

    load()
    const t = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [hostId])

  async function revert(actionId: string) {
    try {
      await api.put<Action>(`/api/v1/actions/${actionId}`, { status: 'reverted' })
    } catch {
      // ignore — proximo refresh corrige
    }
  }

  if (loading) return <p className="text-sm text-zinc-500">Carregando ações…</p>
  if (error) return <p className="text-sm text-red-600">{error}</p>

  if (actions.length === 0) {
    return (
      <p className="text-sm text-zinc-500">
        Nenhuma ação de resposta nesse host. Quando um alerta de brute-force disparar,
        o IP será bloqueado automaticamente e aparecerá aqui. Scans YARA agendados
        também aparecem aqui.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <p className="text-xs text-zinc-500">
        {actions.length} ações · auto-refresh {REFRESH_MS / 1000}s
      </p>
      <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-zinc-50 dark:bg-zinc-900 text-left">
            <tr>
              <th className="px-3 py-2 font-medium text-zinc-500">Quando</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Tipo</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Target</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Status</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Motivo</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {actions.map((a) => (
              <tr
                key={a.id}
                className="border-t border-zinc-100 dark:border-zinc-800"
              >
                <td className="px-3 py-2 text-zinc-500 whitespace-nowrap">
                  {fmtTimeShort(a.created_at)}
                </td>
                <td className="px-3 py-2 font-medium">{a.action_type}</td>
                <td className="px-3 py-2 font-mono">{a.target}</td>
                <td className="px-3 py-2">
                  <StatusBadge status={a.status} />
                  {a.error_message && (
                    <p className="text-[10px] text-red-600 mt-1 max-w-xs">{a.error_message}</p>
                  )}
                </td>
                <td className="px-3 py-2 text-zinc-500 max-w-xs truncate">{a.reason}</td>
                <td className="px-3 py-2">
                  {a.action_type === 'block_ip' && a.status === 'executed' && (
                    <button
                      type="button"
                      onClick={() => revert(a.id)}
                      className="text-[10px] px-2 py-1 rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900"
                    >
                      desbloquear
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'executed'
      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
      : status === 'failed'
        ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
        : status === 'reverted'
          ? 'bg-zinc-200 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
          : status === 'sent'
            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200'
            : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${color}`}>
      {status}
    </span>
  )
}

function fmtTimeShort(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: '2-digit',
  })
}
