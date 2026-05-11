import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import AlertBadge from '@/components/AlertBadge'
import OsIcon, { osLabel } from '@/components/OsIcon'
import { ApiError, api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

interface Host {
  id: string
  name: string
  hostname: string
  os_family: string | null
  os_distro: string | null
  os_version: string | null
  status: string
  last_heartbeat: string | null
  created_at: string
  ip_address: string | null
  cpu_count: number | null
  load_avg_1m: number | null
  mem_used_bytes: number | null
  mem_total_bytes: number | null
  disk_used_bytes: number | null
  disk_total_bytes: number | null
  uptime_seconds: number | null
}

const REFRESH_MS = 5_000

export default function HostsPage() {
  const { user, logout } = useAuthStore()
  const [hosts, setHosts] = useState<Host[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [hostname, setHostname] = useState('')
  const [creating, setCreating] = useState(false)

  async function refresh() {
    setError(null)
    try {
      const data = await api.get<Host[]>('/api/v1/hosts')
      setHosts(data)
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'erro ao carregar')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false

    function load() {
      api
        .get<Host[]>('/api/v1/hosts')
        .then((data) => {
          if (!cancelled) setHosts(data)
        })
        .catch((err) => {
          if (!cancelled) setError(err instanceof ApiError ? String(err.detail) : 'erro ao carregar')
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
  }, [])

  async function onCreate(e: FormEvent) {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post('/api/v1/hosts', { name, hostname })
      setName('')
      setHostname('')
      setShowForm(false)
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'erro ao criar')
    } finally {
      setCreating(false)
    }
  }

  const activeCount = hosts.filter((h) => h.status === 'active').length

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto">
      {/* Header — 2 linhas: info / menu */}
      <header className="mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800 space-y-3">
        {/* Linha 1: titulo + contadores + org + user */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-baseline gap-3">
            <h1 className="text-2xl font-bold">Hosts</h1>
            <span className="text-sm text-zinc-500">
              <span className="font-semibold text-green-600 dark:text-green-400">{activeCount}</span>
              {' '}/{' '}{hosts.length}{' '}conectado{hosts.length === 1 ? '' : 's'}
            </span>
          </div>
          <div className="flex items-center gap-3 text-sm">
            {user?.org && (
              <span className="text-zinc-500">
                <span className="text-[10px] uppercase">org:</span>{' '}
                <span className="font-mono text-zinc-700 dark:text-zinc-300">{user.org.name}</span>
              </span>
            )}
            <span className="text-zinc-300 dark:text-zinc-700">·</span>
            <span className="text-zinc-500">{user?.email}</span>
            <button
              type="button"
              onClick={logout}
              className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              sair
            </button>
          </div>
        </div>
        {/* Linha 2: menu de navegacao */}
        <nav className="flex items-center gap-1 text-sm">
          <AlertBadge />
          <span className="text-zinc-300 dark:text-zinc-700 mx-2">|</span>
          <Link to="/kb" className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100">
            ATT&CK
          </Link>
          <Link to="/hunting" className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100">
            Hunting
          </Link>
          <Link to="/purple-team" className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100">
            Purple Team
          </Link>
          <Link to="/compliance" className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100">
            LGPD
          </Link>
        </nav>
      </header>

      <div className="mb-4">
        <button
          type="button"
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium"
        >
          {showForm ? 'Cancelar' : '+ Novo host'}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={onCreate}
          className="mb-6 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 space-y-3"
        >
          <div className="space-y-1">
            <label className="block text-xs font-medium text-zinc-500">Nome (label)</label>
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Servidor de produção"
              className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 px-3 py-2 bg-transparent text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-medium text-zinc-500">Hostname (FQDN)</label>
            <input
              required
              value={hostname}
              onChange={(e) => setHostname(e.target.value)}
              placeholder="srv01.empresa.com.br"
              className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 px-3 py-2 bg-transparent text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {creating ? 'Criando…' : 'Criar host'}
          </button>
        </form>
      )}

      {error && <p className="text-sm text-red-600 dark:text-red-400 mb-4">{error}</p>}

      {loading ? (
        <p className="text-sm text-zinc-500">Carregando…</p>
      ) : hosts.length === 0 ? (
        <p className="text-sm text-zinc-500">Nenhum host ainda. Cria o primeiro acima.</p>
      ) : (
        <div className="space-y-2">
          {hosts.map((h) => (
            <HostCard key={h.id} host={h} />
          ))}
        </div>
      )}
    </main>
  )
}

function HostCard({ host: h }: { host: Host }) {
  const memPct = h.mem_total_bytes ? Math.round((h.mem_used_bytes! / h.mem_total_bytes) * 100) : null
  const diskPct = h.disk_total_bytes ? Math.round((h.disk_used_bytes! / h.disk_total_bytes) * 100) : null

  return (
    <Link
      to={`/hosts/${h.id}`}
      className="block p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition"
    >
      <div className="flex items-start gap-3">
        <OsIcon distro={h.os_distro} family={h.os_family} size="md" />
        <div className="flex-1 min-w-0">
          {/* Linha 1: nome + status */}
          <div className="flex items-center justify-between gap-2">
            <h2 className="font-semibold truncate">{h.name}</h2>
            <StatusBadge status={h.status} />
          </div>
          {/* Linha 2: OS + hostname + IP */}
          <p className="text-xs text-zinc-500 mt-0.5 truncate">
            {h.os_distro ? osLabel(h.os_distro, h.os_version, h.os_family) : 'OS desconhecido'}
            {' · '}
            <span className="font-mono">{h.hostname}</span>
            {h.ip_address && (
              <>
                {' · '}
                <span className="font-mono">{h.ip_address}</span>
              </>
            )}
          </p>
          {/* Linha 3: mini-stats (so se tiver heartbeat) */}
          {(memPct !== null || diskPct !== null || h.load_avg_1m !== null || h.uptime_seconds !== null) && (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-2 text-xs text-zinc-500">
              {memPct !== null && (
                <Stat label="MEM" pct={memPct} extra={`${fmtBytes(h.mem_used_bytes!)} / ${fmtBytes(h.mem_total_bytes!)}`} />
              )}
              {diskPct !== null && (
                <Stat label="DISK" pct={diskPct} extra={`${fmtBytes(h.disk_used_bytes!)} / ${fmtBytes(h.disk_total_bytes!)}`} />
              )}
              {h.load_avg_1m !== null && (
                <span>
                  <span className="text-[10px] uppercase">Load</span>{' '}
                  <span className="font-mono">{h.load_avg_1m.toFixed(2)}</span>
                  {h.cpu_count !== null && (
                    <span className="text-zinc-400"> /{h.cpu_count} cores</span>
                  )}
                </span>
              )}
              {h.uptime_seconds !== null && (
                <span>
                  <span className="text-[10px] uppercase">Uptime</span>{' '}
                  <span className="font-mono">{fmtUptime(h.uptime_seconds)}</span>
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

function Stat({ label, pct, extra }: { label: string; pct: number; extra: string }) {
  const barColor =
    pct >= 90 ? 'bg-red-500' : pct >= 70 ? 'bg-orange-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-green-500'
  return (
    <span className="flex items-center gap-1.5" title={extra}>
      <span className="text-[10px] uppercase text-zinc-500">{label}</span>
      <span className="w-16 h-1.5 rounded-full bg-zinc-200 dark:bg-zinc-800 overflow-hidden">
        <span className={`block h-full ${barColor}`} style={{ width: `${Math.min(100, pct)}%` }} />
      </span>
      <span className="font-mono text-[11px]">{pct}%</span>
    </span>
  )
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'active'
      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
      : status === 'inactive'
        ? 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
  return (
    <span className={`text-xs px-2 py-1 rounded-full font-medium flex-shrink-0 ${color}`}>{status}</span>
  )
}

function fmtBytes(n: number): string {
  if (n < 1024) return `${n}B`
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(0)}KB`
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(0)}MB`
  return `${(n / 1024 ** 3).toFixed(1)}GB`
}

function fmtUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  const d = Math.floor(seconds / 86400)
  const h = Math.floor((seconds % 86400) / 3600)
  return h > 0 ? `${d}d ${h}h` : `${d}d`
}
