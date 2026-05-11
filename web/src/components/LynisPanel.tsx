/**
 * <LynisPanel> — dispara lynis audit no host (Fase H3).
 *
 * Similar ao RkhunterPanel. Audit gera score (0-100) + findings que viram
 * 1 evento de resumo na aba Eventos.
 */

import { Icon } from '@iconify/react'
import { useState } from 'react'

import { ApiError, api } from '@/lib/api'

interface ScanAction {
  id: string
  status: string
}

interface Props {
  hostId: string
}

export default function LynisPanel({ hostId }: Props) {
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setError(null)
    setFeedback(null)
    setSubmitting(true)
    try {
      const action = await api.post<ScanAction>(
        `/api/v1/hosts/${hostId}/lynis-audit`,
        { reason: 'manual_ui' },
      )
      setFeedback(`Audit agendado (${action.status}). Score + findings na aba "Eventos".`)
    } catch (err) {
      setError(formatError(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon icon="lucide:clipboard-check" className="text-emerald-700 dark:text-emerald-400 text-xl" />
        <h3 className="text-base font-semibold">lynis</h3>
        <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200">
          instalado
        </span>
      </div>

      <p className="text-sm text-zinc-500">
        Auditoria de hardening — testa ~200 controles de segurança e gera
        índice 0-100 + lista de recomendações. Útil pra entender o quanto o
        servidor está endurecido.
      </p>

      <div className="bg-zinc-100 dark:bg-zinc-900 px-3 py-2 rounded">
        <p className="text-[10px] uppercase text-zinc-500 mb-1">Comando executado</p>
        <code className="text-xs font-mono">lynis audit system --quick --no-colors</code>
      </div>

      <button
        type="button"
        onClick={run}
        disabled={submitting}
        className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
      >
        {submitting ? 'Agendando…' : 'Rodar audit agora'}
      </button>

      {feedback && (
        <p className="text-xs text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-3 py-2 rounded">
          {feedback}
        </p>
      )}
      {error && (
        <p className="text-xs text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950 px-3 py-2 rounded">
          {error}
        </p>
      )}
    </div>
  )
}

function formatError(err: unknown): string {
  if (err instanceof ApiError) {
    return typeof err.detail === 'string' ? err.detail : `HTTP ${err.status}`
  }
  return 'erro desconhecido'
}
