import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import ExplainPopover from '@/components/ExplainPopover'
import RowActionsMenu, { type MenuItem } from '@/components/RowActionsMenu'
import { ApiError, api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

interface Alert {
  id: string
  host_id: string
  rule_id: string
  rule_name: string
  severity: string
  description: string
  count: number
  first_event_at: string
  last_event_at: string
  status: string
  context: Record<string, string>
  created_at: string
  updated_at: string
}

const REFRESH_MS = 5_000

export default function AlertsPage() {
  const { user, logout } = useAuthStore()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<'open' | 'acknowledged' | 'resolved' | 'all'>(
    'open',
  )

  useEffect(() => {
    let cancelled = false

    function load() {
      const url =
        statusFilter === 'all' ? '/api/v1/alerts' : `/api/v1/alerts?status=${statusFilter}`
      api
        .get<Alert[]>(url)
        .then((data) => {
          if (cancelled) return
          setAlerts(data)
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
  }, [statusFilter])

  async function changeStatus(alertId: string, status: 'acknowledged' | 'resolved') {
    try {
      await api.put<Alert>(`/api/v1/alerts/${alertId}`, { status })
    } catch {
      // ignore — proximo refresh corrige UI
    }
  }

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto">
      <header className="flex items-center justify-between mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-sm text-zinc-500 hover:underline">
            Hosts
          </Link>
          <span className="text-zinc-300 dark:text-zinc-700">/</span>
          <h1 className="text-2xl font-bold">Alertas</h1>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-zinc-500">{user?.email}</span>
          <button
            type="button"
            onClick={logout}
            className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            sair
          </button>
        </div>
      </header>

      <div className="mb-4 flex gap-2 text-sm">
        {(['open', 'acknowledged', 'resolved', 'all'] as const).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded ${
              statusFilter === s
                ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
                : 'border border-zinc-200 dark:border-zinc-800'
            }`}
          >
            {s === 'open' ? 'abertos' : s === 'acknowledged' ? 'acks' : s === 'resolved' ? 'resolvidos' : 'todos'}
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando alertas…</p>
      ) : alerts.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Nenhum alerta {statusFilter === 'all' ? '' : statusFilter}. Tudo tranquilo.
        </p>
      ) : (
        <div className="space-y-2">
          {alerts.map((a) => (
            <article
              key={a.id}
              className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <SeverityBadge severity={a.severity} />
                    <Link
                      to={`/hosts/${a.host_id}`}
                      className="text-xs text-zinc-500 hover:underline font-mono"
                    >
                      host: {a.host_id.slice(0, 8)}…
                    </Link>
                    <span className="text-xs text-zinc-500">
                      · {fmtRelative(a.last_event_at)}
                    </span>
                  </div>
                  <p className="font-semibold">{a.rule_name}</p>
                  <p className="text-sm text-zinc-500">{a.description}</p>
                  {Object.entries(a.context).length > 0 && (
                    <p className="text-xs text-zinc-500 mt-1 font-mono">
                      {Object.entries(a.context)
                        .map(([k, v]) => `${k}=${v}`)
                        .join(' · ')}
                    </p>
                  )}
                </div>
                <div className="flex items-start gap-3 text-xs">
                  <ExplainPopover
                    kind="rule"
                    ruleId={a.rule_id}
                    variant="link"
                    label="ver detalhes"
                  />
                  <RowActionsMenu items={buildAlertActions(a, changeStatus)} />
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  )
}

function buildAlertActions(
  a: Alert,
  changeStatus: (id: string, status: 'acknowledged' | 'resolved') => Promise<void>,
): MenuItem[] {
  const items: MenuItem[] = []
  if (a.status === 'open') {
    items.push({ label: 'Reconhecer', onClick: () => changeStatus(a.id, 'acknowledged') })
  }
  if (a.status !== 'resolved') {
    items.push({ label: 'Resolver', onClick: () => changeStatus(a.id, 'resolved') })
  }
  return items
}

function SeverityBadge({ severity }: { severity: string }) {
  const color =
    severity === 'critical'
      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
      : severity === 'high'
        ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200'
        : severity === 'medium'
          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
          : 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${color}`}>
      {severity}
    </span>
  )
}

function fmtRelative(iso: string): string {
  const d = new Date(iso)
  const sec = Math.floor((Date.now() - d.getTime()) / 1000)
  if (sec < 60) return `${sec}s atrás`
  if (sec < 3600) return `${Math.floor(sec / 60)}m atrás`
  if (sec < 86400) return `${Math.floor(sec / 3600)}h atrás`
  return d.toLocaleDateString('pt-BR')
}
