import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import ActionsTab from '@/components/ActionsTab'
import AppHeader from '@/components/AppHeader'
import Breadcrumbs from '@/components/Breadcrumbs'
import ClamavPanel from '@/components/ClamavPanel'
import EventsTab from '@/components/EventsTab'
import Tabs from '@/components/Tabs'
import Tooltip from '@/components/Tooltip'
import VulnerabilitiesTab from '@/components/VulnerabilitiesTab'
import YaraPanel from '@/components/YaraPanel'
import { ApiError, api } from '@/lib/api'

interface Host {
  id: string
  name: string
  hostname: string
  os_family: string | null
  os_distro: string | null
  os_version: string | null
  kernel: string | null
  arch: string | null
  location: string | null
  status: string
  last_heartbeat: string | null
  created_at: string
  clamav_installed: boolean | null
  clamav_version: string | null
  clamav_db_age_days: number | null
  services_running: number | null
  services_failed: number | null
  packages_upgradable: number | null
  listening_ports: number | null
  cron_jobs: number | null
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
      <main className="min-h-screen p-6 max-w-7xl mx-auto">
        <AppHeader />
        <Breadcrumbs items={[{ label: 'Hosts', to: '/' }, { label: 'erro' }]} />
        <p className="mt-4 text-red-600">{error}</p>
      </main>
    )
  }

  if (!host) return <p className="p-6 text-sm text-zinc-500">Carregando…</p>

  const overview = (
    <div className="space-y-6">
      <section>
        <h2 className="text-sm font-semibold mb-2 text-zinc-500 uppercase tracking-wide">
          Sistema operacional
        </h2>
        {host.os_distro ? (
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <Row label="Distro" value={`${host.os_distro} ${host.os_version ?? ''}`} />
            <Row label="Familia" value={host.os_family ?? '-'} />
            <Row label="Kernel" value={host.kernel ?? '-'} />
            <Row label="Arquitetura" value={host.arch ?? '-'} />
            <Row label="Last heartbeat" value={fmtTime(host.last_heartbeat)} />
            <Row label="Criado em" value={fmtTime(host.created_at)} />
          </dl>
        ) : (
          <p className="text-sm text-zinc-500">Aguardando primeiro heartbeat do agente.</p>
        )}
      </section>

      <section>
        <LocationEditor
          hostId={host.id}
          initial={host.location}
          onSaved={(loc) => setHost({ ...host, location: loc })}
        />
      </section>

      {host.status !== 'active' && (
        <section className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
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
        <section className="p-4 rounded-lg border border-green-300 dark:border-green-800 bg-green-50 dark:bg-green-950">
          <p className="text-sm text-green-900 dark:text-green-200">
            Agente conectado e enviando heartbeats.
          </p>
        </section>
      )}

      {(host.services_running !== null || host.packages_upgradable !== null) && (
        <section>
          <h2 className="text-sm font-semibold mb-3 text-zinc-500 uppercase tracking-wide">
            Painel do sistema
          </h2>
          <SystemPanel host={host} />
        </section>
      )}
    </div>
  )

  const antimalware = (
    <div className="space-y-6">
      <section>
        <h2 className="text-sm font-semibold mb-3 text-zinc-500 uppercase tracking-wide">
          YARA — Detecção por regras
        </h2>
        {id && <YaraPanel hostId={id} />}
      </section>
      <section>
        <h2 className="text-sm font-semibold mb-3 text-zinc-500 uppercase tracking-wide">
          ClamAV — Antivírus por assinaturas
        </h2>
        <ClamavPanel
          hostId={host.id}
          installed={host.clamav_installed}
          version={host.clamav_version}
          dbAgeDays={host.clamav_db_age_days}
        />
      </section>
    </div>
  )

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto">
      <AppHeader />
      <Breadcrumbs items={[{ label: 'Hosts', to: '/' }, { label: host.name }]} />

      <section className="mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-baseline justify-between">
          <h1 className="text-2xl font-bold">{host.name}</h1>
          <StatusBadge status={host.status} />
        </div>
        <p className="text-sm text-zinc-500 font-mono">{host.hostname}</p>
      </section>

      <Tabs
        items={[
          { value: 'overview', label: '🖥 Visão geral', content: overview },
          {
            value: 'vulns',
            label: '🛡 Vulnerabilidades',
            content: id ? <VulnerabilitiesTab hostId={id} /> : null,
          },
          { value: 'antimalware', label: '🦠 Anti-malware', content: antimalware },
          {
            value: 'actions',
            label: '⚡ Ações',
            content: id ? <ActionsTab hostId={id} /> : null,
          },
          {
            value: 'events',
            label: '📋 Eventos',
            content: id ? <EventsTab hostId={id} /> : null,
          },
        ]}
      />
    </main>
  )
}

function LocationEditor({
  hostId,
  initial,
  onSaved,
}: {
  hostId: string
  initial: string | null
  onSaved: (loc: string | null) => void
}) {
  const [editing, setEditing] = useState(false)
  const [value, setValue] = useState(initial ?? '')
  const [saving, setSaving] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  async function save() {
    setSaving(true)
    setErr(null)
    try {
      const updated = await api.put<Host>(`/api/v1/hosts/${hostId}`, { location: value })
      onSaved(updated.location)
      setEditing(false)
    } catch (e) {
      setErr(e instanceof ApiError ? String(e.detail) : 'erro')
    } finally {
      setSaving(false)
    }
  }

  if (!editing) {
    return (
      <div className="flex items-center gap-3">
        <span className="text-sm font-semibold text-zinc-500 uppercase tracking-wide">
          Localização:
        </span>
        <span className="text-sm">
          {initial ? <>📍 {initial}</> : <span className="text-zinc-400 italic">não definida</span>}
        </span>
        <button
          type="button"
          onClick={() => {
            setValue(initial ?? '')
            setEditing(true)
          }}
          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
        >
          editar
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-semibold text-zinc-500 uppercase tracking-wide">
        Localização
      </label>
      <div className="flex gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="ex: DC-São Paulo / Rack A12 / U23"
          maxLength={255}
          autoFocus
          className="flex-1 rounded-md border border-zinc-300 dark:border-zinc-700 px-3 py-1.5 bg-transparent text-sm"
        />
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="px-3 py-1.5 rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-sm disabled:opacity-50"
        >
          {saving ? 'Salvando…' : 'Salvar'}
        </button>
        <button
          type="button"
          onClick={() => setEditing(false)}
          className="px-3 py-1.5 rounded-md border border-zinc-300 dark:border-zinc-700 text-sm"
        >
          Cancelar
        </button>
      </div>
      {err && <p className="text-xs text-red-600">{err}</p>}
    </div>
  )
}

function SystemPanel({ host }: { host: Host }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      <SystemCard
        label="Serviços rodando"
        value={host.services_running}
        tooltip="Serviços systemd ativos (systemctl list-units --type=service). Conta unidades em estado 'running'."
        color="green"
        cliHint="systemctl list-units --type=service"
      />
      <SystemCard
        label="Serviços falhos"
        value={host.services_failed}
        tooltip="Serviços systemd em estado 'failed'. Cada falha indica algo que travou ou crash-looped. Investigar com journalctl -u <service>."
        color={host.services_failed && host.services_failed > 0 ? 'red' : 'zinc'}
        cliHint="systemctl --failed"
      />
      <SystemCard
        label="Atualizações"
        value={host.packages_upgradable}
        tooltip="Pacotes com versão mais nova disponível (apt list --upgradable / dnf check-update). Inclui patches de segurança."
        color={
          host.packages_upgradable && host.packages_upgradable > 50
            ? 'red'
            : host.packages_upgradable && host.packages_upgradable > 10
              ? 'orange'
              : 'green'
        }
        cliHint="apt update && apt list --upgradable"
      />
      <SystemCard
        label="Portas em LISTEN"
        value={host.listening_ports}
        tooltip="Quantidade de portas TCP em estado LISTEN (ss -tlnH). Cada porta exposta é potencial superfície de ataque."
        color="zinc"
        cliHint="ss -tlnp"
      />
      <SystemCard
        label="Cron jobs"
        value={host.cron_jobs}
        tooltip="Tarefas agendadas em /etc/cron.d, /etc/cron.{hourly,daily,weekly,monthly} e /var/spool/cron. Backdoors costumam se esconder aqui."
        color="zinc"
        cliHint="crontab -l && ls /etc/cron.d/"
      />
    </div>
  )
}

function SystemCard({
  label,
  value,
  tooltip,
  color,
  cliHint,
}: {
  label: string
  value: number | null
  tooltip: string
  color: 'red' | 'orange' | 'green' | 'zinc'
  cliHint: string
}) {
  const cls = {
    red: 'border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300',
    orange:
      'border-orange-300 dark:border-orange-800 bg-orange-50 dark:bg-orange-950 text-orange-700 dark:text-orange-300',
    green:
      'border-green-300 dark:border-green-800 bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300',
    zinc: 'border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300',
  }[color]
  return (
    <Tooltip content={`${tooltip}\n\nNo host: ${cliHint}`}>
      <div className={`p-3 rounded-lg border cursor-help ${cls}`}>
        <p className="text-[10px] uppercase opacity-70 tracking-wide">{label}</p>
        <p className="text-2xl font-bold mt-1">{value ?? '—'}</p>
      </div>
    </Tooltip>
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
