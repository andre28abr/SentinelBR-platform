import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import ActionsTab from '@/components/ActionsTab'
import EventsTab from '@/components/EventsTab'
import { ApiError, api } from '@/lib/api'

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

interface EnrollmentToken {
  token: string
  expires_at: string
  install_command: string
}

const REFRESH_MS = 5_000

export default function HostDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [host, setHost] = useState<Host | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [token, setToken] = useState<EnrollmentToken | null>(null)
  const [generating, setGenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!id) return
    let cancelled = false

    function load() {
      api
        .get<Host>(`/api/v1/hosts/${id}`)
        .then((data) => {
          if (!cancelled) setHost(data)
        })
        .catch((err) => {
          if (!cancelled) setError(err instanceof ApiError ? String(err.detail) : 'erro')
        })
    }

    load()
    const t = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [id])

  async function generateToken() {
    if (!id) return
    setGenerating(true)
    try {
      const t = await api.post<EnrollmentToken>(`/api/v1/hosts/${id}/enrollment-token`)
      setToken(t)
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'erro ao gerar token')
    } finally {
      setGenerating(false)
    }
  }

  async function copyCommand() {
    if (!token) return
    await navigator.clipboard.writeText(token.install_command)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  if (error && !host) {
    return (
      <main className="min-h-screen p-6 max-w-3xl mx-auto">
        <Link to="/" className="text-sm text-zinc-500 hover:underline">
          ← voltar
        </Link>
        <p className="mt-4 text-red-600">{error}</p>
      </main>
    )
  }

  if (!host) return <p className="p-6 text-sm text-zinc-500">Carregando…</p>

  return (
    <main className="min-h-screen p-6 max-w-3xl mx-auto">
      <Link to="/" className="text-sm text-zinc-500 hover:underline">
        ← voltar
      </Link>

      <header className="mt-4 mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-baseline justify-between">
          <h1 className="text-2xl font-bold">{host.name}</h1>
          <StatusBadge status={host.status} />
        </div>
        <p className="text-sm text-zinc-500 font-mono">{host.hostname}</p>
      </header>

      <section className="mb-6">
        <h2 className="text-sm font-semibold mb-2 text-zinc-500 uppercase tracking-wide">
          Sistema operacional
        </h2>
        {host.os_distro ? (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <Row label="Distro" value={`${host.os_distro} ${host.os_version ?? ''}`} />
            <Row label="Familia" value={host.os_family ?? '-'} />
            <Row label="Last heartbeat" value={fmtTime(host.last_heartbeat)} />
            <Row label="Criado em" value={fmtTime(host.created_at)} />
          </dl>
        ) : (
          <p className="text-sm text-zinc-500">Aguardando primeiro heartbeat do agente.</p>
        )}
      </section>

      {host.status !== 'active' && (
        <section className="mb-6 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
          <h2 className="font-semibold mb-2">Instalar agente</h2>
          <p className="text-sm text-zinc-500 mb-3">
            Gere um token de uso unico (validade 60min) e cole o comando no host.
          </p>

          {!token ? (
            <button
              type="button"
              onClick={generateToken}
              disabled={generating}
              className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {generating ? 'Gerando…' : 'Gerar token de enrollment'}
            </button>
          ) : (
            <div className="space-y-3">
              <pre className="bg-zinc-100 dark:bg-zinc-900 p-3 rounded text-xs overflow-x-auto whitespace-pre-wrap break-all">
                {token.install_command}
              </pre>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={copyCommand}
                  className="text-xs px-3 py-1 rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900"
                >
                  {copied ? 'Copiado!' : 'Copiar comando'}
                </button>
                <span className="text-xs text-zinc-500">
                  expira em {fmtTime(token.expires_at)}
                </span>
              </div>
              <p className="text-xs text-zinc-500">
                Esse token aparece <strong>uma unica vez</strong>. Se perder, gere outro.
              </p>
            </div>
          )}
        </section>
      )}

      {host.status === 'active' && (
        <section className="mb-6 p-4 rounded-lg border border-green-300 dark:border-green-800 bg-green-50 dark:bg-green-950">
          <p className="text-sm text-green-900 dark:text-green-200">
            Agente conectado e enviando heartbeats.
          </p>
        </section>
      )}

      <section className="mb-6">
        <h2 className="text-sm font-semibold mb-3 text-zinc-500 uppercase tracking-wide">
          Ações de resposta
        </h2>
        {id && <ActionsTab hostId={id} />}
      </section>

      <section className="mb-6">
        <h2 className="text-sm font-semibold mb-3 text-zinc-500 uppercase tracking-wide">
          Eventos recentes
        </h2>
        {id && <EventsTab hostId={id} />}
      </section>
    </main>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-zinc-500">{label}</dt>
      <dd className="font-medium font-mono text-xs">{value}</dd>
    </>
  )
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === 'active'
      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
      : status === 'inactive'
        ? 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
        : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
  return <span className={`text-xs px-2 py-1 rounded-full font-medium ${color}`}>{status}</span>
}

function fmtTime(s: string | null): string {
  if (!s) return '-'
  return new Date(s).toLocaleString('pt-BR')
}
