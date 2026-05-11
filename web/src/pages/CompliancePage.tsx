import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

interface ComplianceReport {
  period_start: string
  period_end: string
  period_days: number
  total_logins: number
  failed_logins: number
  distinct_users_logged_in: number
  hosts_total: number
  hosts_active: number
  hosts_created_in_period: number
  hosts_deleted_in_period: number
  alerts_created_in_period: number
  alerts_open: number
  alerts_acknowledged_in_period: number
  alerts_resolved_in_period: number
  actions_executed_in_period: number
  mttr_seconds: number | null
  audit_log_entries_in_period: number
  audit_retention_days: number
  note: string
}

interface AuditLog {
  id: string
  actor_user_id: string | null
  actor_email: string | null
  action: string
  target_type: string | null
  target_id: string | null
  details: Record<string, unknown>
  ip_address: string | null
  success: boolean
  created_at: string
}

export default function CompliancePage() {
  const { user, logout } = useAuthStore()
  const [report, setReport] = useState<ComplianceReport | null>(null)
  const [logs, setLogs] = useState<AuditLog[]>([])
  const [days, setDays] = useState(30)
  const [actionFilter, setActionFilter] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    api
      .get<ComplianceReport>(`/api/v1/compliance/report?days=${days}`)
      .then((r) => {
        if (!cancelled) setReport(r)
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof ApiError ? String(e.detail) : 'erro')
      })
    return () => {
      cancelled = true
    }
  }, [days])

  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams({ days: String(days), limit: '100' })
    if (actionFilter) params.set('action', actionFilter)
    api
      .get<AuditLog[]>(`/api/v1/audit-logs?${params}`)
      .then((r) => {
        if (!cancelled) setLogs(r)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [days, actionFilter])

  return (
    <main className="min-h-screen p-6 max-w-5xl mx-auto">
      <header className="flex items-center justify-between mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-sm text-zinc-500 hover:underline">
            Hosts
          </Link>
          <span className="text-zinc-300 dark:text-zinc-700">/</span>
          <h1 className="text-2xl font-bold">Compliance LGPD</h1>
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

      <div className="mb-4 flex items-center gap-3 text-sm">
        <span className="text-zinc-500">Periodo:</span>
        {[7, 30, 90, 180].map((d) => (
          <button
            key={d}
            type="button"
            onClick={() => setDays(d)}
            className={`px-3 py-1 rounded ${
              days === d
                ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
                : 'border border-zinc-200 dark:border-zinc-800'
            }`}
          >
            {d}d
          </button>
        ))}
      </div>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      {report && (
        <section className="mb-8">
          <h2 className="text-sm font-semibold mb-3 text-zinc-500 uppercase tracking-wide">
            Relatório (LGPD Art. 37)
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Stat label="Logins (sucesso+falha)" value={report.total_logins} />
            <Stat label="Logins falhos" value={report.failed_logins}
              danger={report.failed_logins > 5} />
            <Stat label="Usuarios distintos" value={report.distinct_users_logged_in} />
            <Stat label="Hosts ativos / total"
              value={`${report.hosts_active}/${report.hosts_total}`} />
            <Stat label="Alertas no periodo" value={report.alerts_created_in_period} />
            <Stat label="Alertas abertos agora" value={report.alerts_open}
              danger={report.alerts_open > 0} />
            <Stat label="Alertas reconhecidos" value={report.alerts_acknowledged_in_period} />
            <Stat label="Alertas resolvidos" value={report.alerts_resolved_in_period} />
            <Stat label="Ações IR executadas" value={report.actions_executed_in_period} />
            <Stat
              label="MTTR (médio)"
              value={
                report.mttr_seconds === null
                  ? '—'
                  : `${report.mttr_seconds.toFixed(1)}s`
              }
            />
            <Stat label="Audit entries" value={report.audit_log_entries_in_period} />
            <Stat label="Retencao" value={`${report.audit_retention_days}d`} />
          </div>
          <p className="text-xs text-zinc-500 mt-4 italic">{report.note}</p>
        </section>
      )}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-zinc-500 uppercase tracking-wide">
            Audit log ({logs.length})
          </h2>
          <input
            type="text"
            placeholder="filtrar por action (ex: login_failed)"
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs px-2 py-1 rounded border border-zinc-200 dark:border-zinc-800 bg-transparent w-64"
          />
        </div>

        <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-zinc-50 dark:bg-zinc-900 text-left">
              <tr>
                <th className="px-3 py-2 font-medium text-zinc-500">Quando</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Action</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Quem</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Em</th>
                <th className="px-3 py-2 font-medium text-zinc-500">IP</th>
                <th className="px-3 py-2 font-medium text-zinc-500">OK?</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr
                  key={l.id}
                  className="border-t border-zinc-100 dark:border-zinc-800"
                >
                  <td className="px-3 py-2 font-mono text-zinc-500 whitespace-nowrap">
                    {new Date(l.created_at).toLocaleString('pt-BR')}
                  </td>
                  <td className="px-3 py-2 font-medium">{l.action}</td>
                  <td className="px-3 py-2 text-zinc-500">{l.actor_email ?? '—'}</td>
                  <td className="px-3 py-2 font-mono text-zinc-500">
                    {l.target_type && `${l.target_type}:${l.target_id?.slice(0, 8) ?? ''}…`}
                  </td>
                  <td className="px-3 py-2 font-mono text-zinc-500">{l.ip_address ?? '—'}</td>
                  <td className="px-3 py-2">
                    {l.success ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-red-600">✗</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  )
}

function Stat({
  label,
  value,
  danger,
}: {
  label: string
  value: string | number
  danger?: boolean
}) {
  return (
    <div
      className={`p-3 rounded-lg border ${
        danger
          ? 'border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950'
          : 'border-zinc-200 dark:border-zinc-800'
      }`}
    >
      <p className="text-[10px] uppercase text-zinc-500 tracking-wide">{label}</p>
      <p
        className={`text-xl font-bold mt-1 ${
          danger ? 'text-red-700 dark:text-red-300' : ''
        }`}
      >
        {value}
      </p>
    </div>
  )
}
