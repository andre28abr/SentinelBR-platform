import { useState } from 'react'

import { ApiError, api } from '@/lib/api'

interface ScanAction {
  id: string
  status: string
  target: string
  reason: string
  created_at: string
}

const SUGGESTED_PATHS = ['/var/www', '/tmp', '/home', '/opt']

export default function YaraPanel({ hostId }: { hostId: string }) {
  const [open, setOpen] = useState(false)
  const [path, setPath] = useState(SUGGESTED_PATHS[0])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastAction, setLastAction] = useState<ScanAction | null>(null)

  async function submit() {
    setError(null)
    setSubmitting(true)
    try {
      const action = await api.post<ScanAction>(`/api/v1/hosts/${hostId}/yara-scan`, {
        path,
        reason: 'manual_ui',
      })
      setLastAction(action)
      setOpen(false)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(typeof err.detail === 'string' ? err.detail : `HTTP ${err.status}`)
      } else {
        setError('erro ao agendar scan')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-zinc-500">
        Procura padrões de webshell, miner, ransomware e dropper em arquivos do host.
        O scan roda no agente e gera alertas se encontrar algo crítico.
      </p>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium"
        >
          Escanear pasta…
        </button>
        {lastAction && (
          <span className="text-xs text-zinc-500">
            Último scan agendado:{' '}
            <span className="font-mono">{lastAction.target}</span> ({lastAction.status})
          </span>
        )}
      </div>

      {open && (
        <Modal onClose={() => setOpen(false)}>
          <h3 className="text-base font-semibold mb-3">Escanear pasta com YARA</h3>
          <p className="text-xs text-zinc-500 mb-3">
            Escolha uma sugestão ou digite o caminho a escanear no host.
          </p>

          <div className="space-y-2 mb-4">
            <label className="block text-xs font-medium text-zinc-500">
              Caminho a escanear
            </label>
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/var/www"
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 font-mono"
            />
            <div className="flex flex-wrap gap-1 pt-1">
              {SUGGESTED_PATHS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPath(p)}
                  className="text-[10px] px-2 py-0.5 rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-mono"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-xs text-red-600 mb-3">{error}</p>}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={submitting || !path.trim()}
              className="px-3 py-2 text-sm rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 disabled:opacity-50"
            >
              {submitting ? 'Agendando…' : 'Iniciar scan'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  )
}

function Modal({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-zinc-950 rounded-lg shadow-xl max-w-md w-full p-5 border border-zinc-200 dark:border-zinc-800"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>
  )
}
