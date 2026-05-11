import { useEffect, useState } from 'react'

import ExplainPopover from '@/components/ExplainPopover'
import { ApiError, api } from '@/lib/api'

interface EventItem {
  event_id: string
  timestamp: string
  source: string
  severity: string
  raw: string
  fields: Record<string, string>
}

const REFRESH_MS = 5_000
const HOURS = 24
const LIMIT = 100

const SOURCES = ['todos', 'sshd', 'selinux', 'apparmor', 'yara'] as const
type SourceFilter = (typeof SOURCES)[number]

export default function EventsTab({ hostId }: { hostId: string }) {
  const [events, setEvents] = useState<EventItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [source, setSource] = useState<SourceFilter>('todos')

  useEffect(() => {
    let cancelled = false

    function load() {
      const params = new URLSearchParams({
        hours: String(HOURS),
        limit: String(LIMIT),
      })
      if (source !== 'todos') params.set('source', source)
      const url = `/api/v1/hosts/${hostId}/events?${params}`
      api
        .get<EventItem[]>(url)
        .then((data) => {
          if (cancelled) return
          setEvents(data)
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
  }, [hostId, source])

  const sourceFilter = (
    <div className="flex gap-1 mb-3">
      {SOURCES.map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => setSource(s)}
          className={`text-xs px-2 py-1 rounded ${
            source === s
              ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'
              : 'border border-zinc-200 dark:border-zinc-800'
          }`}
        >
          {s}
        </button>
      ))}
    </div>
  )

  if (loading) {
    return (
      <>
        {sourceFilter}
        <p className="text-sm text-zinc-500">Carregando eventos…</p>
      </>
    )
  }

  if (error) {
    return (
      <>
        {sourceFilter}
        <div className="text-sm text-red-600 dark:text-red-400">
          {error}
          <p className="text-xs text-zinc-500 mt-1">
            Verifique se Loki está rodando (<code>make dev</code>).
          </p>
        </div>
      </>
    )
  }

  if (events.length === 0) {
    return (
      <>
        {sourceFilter}
        <p className="text-sm text-zinc-500">
          Nenhum evento {source !== 'todos' ? `de ${source}` : ''} nas últimas {HOURS}h.
        </p>
      </>
    )
  }

  return (
    <div className="space-y-2">
      {sourceFilter}
      <p className="text-xs text-zinc-500">
        {events.length} eventos · últimas {HOURS}h · auto-refresh a cada {REFRESH_MS / 1000}s
      </p>
      <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-zinc-50 dark:bg-zinc-900 text-left">
            <tr>
              <th className="px-3 py-2 font-medium text-zinc-500">Quando</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Severidade</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Source</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Resumo</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Detalhes</th>
            </tr>
          </thead>
          <tbody>
            {events.map((e) => (
              <tr
                key={e.event_id || `${e.timestamp}-${e.raw}`}
                className="border-t border-zinc-100 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900"
              >
                <td className="px-3 py-2 font-mono whitespace-nowrap text-zinc-500">
                  {fmtTimeShort(e.timestamp)}
                </td>
                <td className="px-3 py-2 whitespace-nowrap">
                  <SeverityBadge severity={e.severity} />
                </td>
                <td className="px-3 py-2 font-mono text-zinc-500">{e.source}</td>
                <td className="px-3 py-2">
                  <EventDetail ev={e} />
                </td>
                <td className="px-3 py-2">
                  <ExplainPopover
                    kind="event"
                    event={{
                      source: e.source,
                      fields: e.fields,
                      raw: e.raw,
                      timestamp: e.timestamp,
                      severity: e.severity,
                    }}
                    variant="link"
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function EventDetail({ ev }: { ev: EventItem }) {
  const f = ev.fields
  const action = f['event.action']
  const outcome = f['event.outcome']
  const reason = f['event.reason']

  return (
    <div>
      <p className="font-medium">
        {action ?? 'evento'} {outcome && <span className="text-zinc-500">· {outcome}</span>}
        {reason && <span className="text-zinc-500"> ({reason})</span>}
      </p>
      <p className="text-zinc-500 mt-0.5 text-[11px]">
        {f['user.name'] && <span>user=<code>{f['user.name']}</code> </span>}
        {f['source.ip'] && <span>from=<code>{f['source.ip']}</code> </span>}
        {f['process.name'] && <span>proc=<code>{f['process.name']}</code> </span>}
        {f['selinux.source_type'] && (
          <span>
            {f['selinux.source_type']} → {f['selinux.target_type']}
            {f['selinux.permission'] && ` (${f['selinux.permission']})`}{' '}
          </span>
        )}
        {f['apparmor.profile'] && (
          <span>profile=<code>{f['apparmor.profile']}</code> </span>
        )}
        {f['yara.rule_name'] && (
          <span>rule=<code>{f['yara.rule_name']}</code> </span>
        )}
        {f['file.path'] && <span>file=<code>{f['file.path']}</code> </span>}
        {f['file.name'] && <span>file=<code>{f['file.name']}</code></span>}
      </p>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const color =
    severity === 'critical' || severity === 'error'
      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
      : severity === 'warn' || severity === 'warning'
        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
        : 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
  return (
    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${color}`}>{severity}</span>
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
