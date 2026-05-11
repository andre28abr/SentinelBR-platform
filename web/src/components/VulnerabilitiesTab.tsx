import { useEffect, useState } from 'react'

import ExplainPopover from '@/components/ExplainPopover'
import { TableLimitFooter, useTableLimit } from '@/components/TableLimit'
import Tooltip from '@/components/Tooltip'
import { ApiError, api } from '@/lib/api'

interface Vulnerability {
  id: string
  cve_id: string
  package_name: string
  installed_version: string
  fixed_version: string | null
  severity: string
  cvss_score: number | null
  summary: string | null
  references: string | null
  discovered_at: string
}

interface Summary {
  score: number
  by_severity: Record<string, number>
  total: number
  last_scan_at: string | null
  items: Vulnerability[]
}

const REFRESH_MS = 10_000

export default function VulnerabilitiesTab({ hostId }: { hostId: string }) {
  const [data, setData] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scanning, setScanning] = useState(false)

  useEffect(() => {
    let cancelled = false

    function load() {
      api
        .get<Summary>(`/api/v1/hosts/${hostId}/vulnerabilities`)
        .then((r) => {
          if (!cancelled) setData(r)
        })
        .catch((e) => {
          if (!cancelled) setError(e instanceof ApiError ? String(e.detail) : 'erro')
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

  async function triggerScan() {
    setScanning(true)
    try {
      await api.post(`/api/v1/hosts/${hostId}/scan`, {})
    } catch (e) {
      setError(e instanceof ApiError ? String(e.detail) : 'erro no scan')
    } finally {
      setScanning(false)
    }
  }

  if (loading) return <p className="text-sm text-zinc-500">Carregando vulnerabilidades…</p>
  if (error) return <p className="text-sm text-red-600">{error}</p>
  if (!data) return null

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <ScoreCard score={data.score} />
        <SeverityCard label="critical" count={data.by_severity.critical || 0} color="red" />
        <SeverityCard label="high" count={data.by_severity.high || 0} color="orange" />
        <SeverityCard label="medium" count={data.by_severity.medium || 0} color="yellow" />
        <SeverityCard label="low+unknown"
          count={(data.by_severity.low || 0) + (data.by_severity.unknown || 0)}
          color="zinc" />
      </div>

      <div className="flex items-center gap-3 text-xs text-zinc-500">
        <span>
          {data.total} CVEs · ultimo scan:{' '}
          {data.last_scan_at ? new Date(data.last_scan_at).toLocaleString('pt-BR') : 'nunca'}
        </span>
        <button
          type="button"
          onClick={triggerScan}
          disabled={scanning}
          className="px-3 py-1 rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-xs disabled:opacity-50"
        >
          {scanning ? 'Scaneando…' : 'Re-scan agora'}
        </button>
      </div>

      {data.items.length === 0 ? (
        <p className="text-sm text-zinc-500">
          Nenhuma vulnerabilidade detectada. Rode{' '}
          <code className="bg-zinc-100 dark:bg-zinc-900 px-1 rounded">
            sentinel-agent inventory
          </code>{' '}
          no host pra enviar a lista de pacotes — scan automatico via OSV.
        </p>
      ) : (
        <VulnsTable items={data.items} />
      )}
    </div>
  )
}

function VulnsTable({ items }: { items: Vulnerability[] }) {
  const { visible, hasMore, expanded, toggle, containerClass, collapsedCount } =
    useTableLimit(items, { defaultVisible: 10 })
  return (
    <>
      <div className={`rounded-lg border border-zinc-200 dark:border-zinc-800 ${containerClass}`}>
        <table className="w-full text-xs">
          <thead className="bg-zinc-50 dark:bg-zinc-900 text-left sticky top-0">
            <tr>
              <th className="px-4 py-3 font-medium text-zinc-500">CVE</th>
              <th className="px-4 py-3 font-medium text-zinc-500">Sev</th>
              <th className="px-4 py-3 font-medium text-zinc-500">
                <Tooltip content="CVSS v3.x — pontuação de severidade técnica da vulnerabilidade (0-10). >=9 critical, 7-8.9 high, 4-6.9 medium.">
                  <span className="cursor-help">CVSS</span>
                </Tooltip>
              </th>
              <th className="px-4 py-3 font-medium text-zinc-500">Pacote</th>
              <th className="px-4 py-3 font-medium text-zinc-500">
                <Tooltip content="Versão que corrige a vulnerabilidade. Faça upgrade pra essa versão ou superior.">
                  <span className="cursor-help">Fix</span>
                </Tooltip>
              </th>
              <th className="px-4 py-3 font-medium text-zinc-500">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((v) => (
              <tr key={v.id} className="border-t border-zinc-100 dark:border-zinc-800">
                <td className="px-4 py-3 font-mono">
                  <a
                    href={`https://nvd.nist.gov/vuln/detail/${v.cve_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    {v.cve_id}
                  </a>
                </td>
                <td className="px-4 py-3">
                  <SeverityBadge severity={v.severity} />
                </td>
                <td className="px-4 py-3 font-mono text-zinc-500">
                  {v.cvss_score?.toFixed(1) ?? '—'}
                </td>
                <td className="px-4 py-3">
                  <span className="font-mono">{v.package_name}</span>
                  <span className="text-zinc-500"> {v.installed_version}</span>
                </td>
                <td className="px-4 py-3 font-mono text-zinc-500">
                  {v.fixed_version ?? '—'}
                </td>
                <td className="px-4 py-3">
                  <ExplainPopover kind="cve" cve={v} variant="link" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasMore && (
        <TableLimitFooter
          total={items.length}
          expanded={expanded}
          onToggle={toggle}
          collapsedCount={collapsedCount}
        />
      )}
    </>
  )
}

function ScoreCard({ score }: { score: number }) {
  const color =
    score >= 70
      ? 'border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950'
      : score >= 40
        ? 'border-orange-300 dark:border-orange-800 bg-orange-50 dark:bg-orange-950'
        : score >= 15
          ? 'border-yellow-300 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-950'
          : 'border-green-300 dark:border-green-800 bg-green-50 dark:bg-green-950'
  return (
    <Tooltip content="Risk Score 0-100: agregado das CVEs deste host. Pesos: critical=15, high=6, medium=2, low/unknown=0.5. Saturado em 100.">
      <div className={`p-3 rounded-lg border cursor-help ${color}`}>
        <p className="text-[10px] uppercase text-zinc-500 tracking-wide">Risk score</p>
        <p className="text-2xl font-bold mt-1">{score}<span className="text-xs text-zinc-500">/100</span></p>
      </div>
    </Tooltip>
  )
}

function SeverityCard({ label, count, color }: { label: string; count: number; color: string }) {
  const cls = {
    red: 'border-red-200 dark:border-red-900 text-red-700 dark:text-red-300',
    orange: 'border-orange-200 dark:border-orange-900 text-orange-700 dark:text-orange-300',
    yellow: 'border-yellow-200 dark:border-yellow-900 text-yellow-700 dark:text-yellow-300',
    zinc: 'border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300',
  }[color]
  return (
    <div className={`p-3 rounded-lg border ${cls ?? ''}`}>
      <p className="text-[10px] uppercase tracking-wide opacity-70">{label}</p>
      <p className="text-2xl font-bold mt-1">{count}</p>
    </div>
  )
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
  return <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${color}`}>{severity}</span>
}
