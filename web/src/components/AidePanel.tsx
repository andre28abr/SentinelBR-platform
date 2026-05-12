/**
 * <AidePanel> — dispara AIDE integrity check (Fase H7).
 *
 * Requer DB inicializado no host (admin precisou rodar `aide --init` antes).
 * Cada check gera 1 evento de resumo com added/changed/removed counts.
 */

import { Icon } from '@iconify/react'
import { useState } from 'react'

import ScanProgressBadge from '@/components/ScanProgressBadge'
import { ApiError, api } from '@/lib/api'

interface ScanAction {
  id: string
  status: string
}

interface Props {
  hostId: string
}

export default function AidePanel({ hostId }: Props) {
  const [submitting, setSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setError(null)
    setFeedback(null)
    setSubmitting(true)
    try {
      const action = await api.post<ScanAction>(
        `/api/v1/hosts/${hostId}/aide-check`,
        { reason: 'manual_ui' },
      )
      setFeedback(`Check agendado (${action.status}). Resumo na aba "Eventos" em até 30min.`)
    } catch (err) {
      setError(formatError(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Icon icon="lucide:database" className="text-emerald-700 dark:text-emerald-400 text-xl" />
        <h3 className="text-base font-semibold">AIDE</h3>
        <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200">
          instalado
        </span>
      </div>

      <p className="text-sm text-zinc-500">
        Advanced Intrusion Detection Environment — compara o estado atual do
        sistema contra um snapshot (database) feito anteriormente. Detecta
        modificações em <code className="font-mono">/etc</code>,{' '}
        <code className="font-mono">/usr/bin</code>, etc — útil pra pegar
        backdoors instalados.
      </p>

      <div className="bg-yellow-50 dark:bg-yellow-950 border border-yellow-300 dark:border-yellow-800 px-3 py-2 rounded text-xs text-yellow-800 dark:text-yellow-200">
        <strong>Pré-requisito:</strong> rode{' '}
        <code className="font-mono">sudo aide --init</code> no host primeiro
        pra criar o database. Sem isso, o check falha.
      </div>

      <div className="bg-zinc-100 dark:bg-zinc-900 px-3 py-2 rounded">
        <p className="text-[10px] uppercase text-zinc-500 mb-1">Comando executado</p>
        <code className="text-xs font-mono">aide --check</code>
      </div>

      <div className="bg-yellow-50 dark:bg-yellow-950 border border-yellow-300 dark:border-yellow-800 px-3 py-2 rounded text-xs text-yellow-800 dark:text-yellow-200">
        ⏱ Esse check pode levar <strong>5-30 minutos</strong> dependendo do
        tamanho do database. Pode fechar essa aba — o badge atualiza sozinho.
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <button
          type="button"
          onClick={run}
          disabled={submitting}
          className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {submitting ? 'Agendando…' : 'Rodar check agora'}
        </button>
        <ScanProgressBadge hostId={hostId} actionType="run_aide_check" label="Último:" />
      </div>

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
