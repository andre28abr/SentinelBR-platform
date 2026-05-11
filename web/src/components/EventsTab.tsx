import { useEffect, useState } from 'react'

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

export default function EventsTab({ hostId }: { hostId: string }) {
  const [events, setEvents] = useState<EventItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    function load() {
      const url = `/api/v1/hosts/${hostId}/events?hours=${HOURS}&limit=${LIMIT}`
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
  }, [hostId])

  if (loading) return <p className="text-sm text-zinc-500">Carregando eventos…</p>

  if (error) {
    return (
      <div className="text-sm text-red-600 dark:text-red-400">
        {error}
        <p className="text-xs text-zinc-500 mt-1">
          Verifique se Loki está rodando (<code>make dev</code>).
        </p>
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="text-sm text-zinc-500 space-y-2">
        <p>Nenhum evento nas últimas {HOURS}h.</p>
        <p className="text-xs">
          Pra testar: rode o agente com{' '}
          <code className="bg-zinc-100 dark:bg-zinc-900 px-1 rounded">
            sentinel-agent run --ssh-source-file=samples/sshd-fixtures.log --ssh-source-once
          </code>
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
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
              <th className="px-3 py-2 font-medium text-zinc-500">Detalhe</th>
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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function EventDetail({ ev }: { ev: EventItem }) {
  const action = ev.fields['event.action']
  const outcome = ev.fields['event.outcome']
  const user = ev.fields['user.name']
  const ip = ev.fields['source.ip']
  const reason = ev.fields['event.reason']

  if (action || user || ip) {
    return (
      <div>
        <p className="font-medium">
          {action ?? 'evento'} {outcome && <span className="text-zinc-500">· {outcome}</span>}
          {reason && <span className="text-zinc-500"> ({reason})</span>}
        </p>
        <p className="text-zinc-500 mt-0.5">
          {user && <span>user=<code>{user}</code> </span>}
          {ip && <span>from=<code>{ip}</code> </span>}
        </p>
      </div>
    )
  }
  return <p className="text-zinc-500 truncate max-w-md font-mono">{ev.raw}</p>
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
