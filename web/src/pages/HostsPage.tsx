import { type FormEvent, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import AlertBadge from '@/components/AlertBadge'
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
}

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
    return () => {
      cancelled = true
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

  return (
    <main className="min-h-screen p-6 max-w-4xl mx-auto">
      <header className="flex items-center justify-between mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold">Hosts</h1>
          <p className="text-sm text-zinc-500">{hosts.length} cadastrado(s)</p>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <AlertBadge />
          <Link to="/kb" className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
            ATT&CK
          </Link>
          <Link to="/hunting" className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
            Hunting
          </Link>
          <Link to="/purple-team" className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
            Purple Team
          </Link>
          <Link to="/compliance" className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100">
            LGPD
          </Link>
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
            <Link
              key={h.id}
              to={`/hosts/${h.id}`}
              className="block p-4 rounded-lg border border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition"
            >
              <div className="flex items-baseline justify-between">
                <h2 className="font-semibold">{h.name}</h2>
                <StatusBadge status={h.status} />
              </div>
              <p className="text-sm text-zinc-500 font-mono">{h.hostname}</p>
              {h.os_distro && (
                <p className="text-xs text-zinc-500 mt-1">
                  {h.os_distro} {h.os_version} ({h.os_family})
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </main>
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
    <span className={`text-xs px-2 py-1 rounded-full font-medium ${color}`}>{status}</span>
  )
}
