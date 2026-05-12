/**
 * <Fail2banPanel> — UI funcional pra fail2ban (Fase H2).
 *
 * - Lista de jails com IPs banidos atualmente
 * - Botao "desbanir" em cada IP (POST /fail2ban-unban -> cria Action)
 * - Modal "banir IP manualmente" (POST /fail2ban-ban -> cria Action)
 *
 * Dados vem do snapshot fail2ban_status_json reportado a cada heartbeat.
 */

import { Icon } from '@iconify/react'
import { useMemo, useState } from 'react'

import Tooltip from '@/components/Tooltip'
import { ApiError, api } from '@/lib/api'

interface JailDetail {
  name: string
  banned_count: number
  banned_ips: string[]
}

interface Props {
  hostId: string
  statusJson: string | null
  jailsActive: number
  bannedIps: number
}

interface ScanAction {
  id: string
  status: string
  target: string
}

export default function Fail2banPanel({ hostId, statusJson, jailsActive, bannedIps }: Props) {
  const jails = useMemo(() => parseJails(statusJson), [statusJson])
  const [banModalOpen, setBanModalOpen] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function unban(jail: string, ip: string) {
    setError(null)
    setFeedback(null)
    try {
      const action = await api.post<ScanAction>(
        `/api/v1/hosts/${hostId}/fail2ban-unban`,
        { jail, ip, reason: 'manual_ui' },
      )
      setFeedback(`Desban agendado: ${ip} no jail ${jail} (${action.status})`)
    } catch (err) {
      setError(formatError(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Icon icon="lucide:shield-ban" className="text-emerald-700 dark:text-emerald-400 text-xl" />
          <h3 className="text-base font-semibold">fail2ban</h3>
          <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200">
            ativo
          </span>
        </div>
        <button
          type="button"
          onClick={() => setBanModalOpen(true)}
          className="text-xs px-3 py-1.5 rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900"
        >
          Banir IP manualmente
        </button>
      </div>

      <p className="text-sm text-zinc-500">
        <span className="font-mono font-medium">{jailsActive}</span> jail
        {jailsActive === 1 ? '' : 's'} configurado{jailsActive === 1 ? '' : 's'} ·{' '}
        <span className="font-mono font-medium">{bannedIps}</span> IP
        {bannedIps === 1 ? '' : 's'} banido{bannedIps === 1 ? '' : 's'} no total.
      </p>

      {feedback && (
        <p className="text-xs text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950 px-3 py-2 rounded">
          {feedback}
        </p>
      )}
      {error && (
        <p className="text-xs text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950 px-3 py-2 rounded">
          {error}
        </p>
      )}

      {jails.length === 0 ? (
        <p className="text-sm text-zinc-500 italic">
          {statusJson === null
            ? 'Aguardando próximo heartbeat com snapshot do fail2ban (~30s)…'
            : 'Nenhum jail detectado. Configure /etc/fail2ban/jail.local no host.'}
        </p>
      ) : (
        <div className="space-y-3">
          {jails.map((j) => (
            <JailCard key={j.name} jail={j} onUnban={unban} />
          ))}
        </div>
      )}

      {banModalOpen && (
        <BanModal
          hostId={hostId}
          jailOptions={jails.map((j) => j.name)}
          onClose={() => setBanModalOpen(false)}
          onSuccess={(msg) => {
            setFeedback(msg)
            setBanModalOpen(false)
          }}
        />
      )}
    </div>
  )
}

function JailCard({
  jail,
  onUnban,
}: {
  jail: JailDetail
  onUnban: (jail: string, ip: string) => Promise<void>
}) {
  return (
    <div className="p-3 rounded-lg border border-zinc-200 dark:border-zinc-800">
      <div className="flex items-baseline justify-between mb-2">
        <h4 className="text-sm font-semibold font-mono">{jail.name}</h4>
        <span className="text-xs text-zinc-500">
          {jail.banned_count} banido{jail.banned_count === 1 ? '' : 's'}
        </span>
      </div>
      {jail.banned_ips.length === 0 ? (
        <p className="text-xs text-zinc-500 italic">Sem IPs banidos neste jail.</p>
      ) : (
        <ul className="space-y-1">
          {jail.banned_ips.map((ip) => (
            <li
              key={ip}
              className="flex items-center justify-between text-xs px-2 py-1 rounded bg-zinc-50 dark:bg-zinc-900"
            >
              <span className="font-mono">{ip}</span>
              <Tooltip content={`Desbanir ${ip} do jail ${jail.name}`}>
                <button
                  type="button"
                  onClick={() => onUnban(jail.name, ip)}
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  desbanir
                </button>
              </Tooltip>
            </li>
          ))}
          {jail.banned_count > jail.banned_ips.length && (
            <li className="text-[10px] text-zinc-500 italic px-2">
              … e mais {jail.banned_count - jail.banned_ips.length} (lista truncada
              pelo agente)
            </li>
          )}
        </ul>
      )}
    </div>
  )
}

function BanModal({
  hostId,
  jailOptions,
  onClose,
  onSuccess,
}: {
  hostId: string
  jailOptions: string[]
  onClose: () => void
  onSuccess: (msg: string) => void
}) {
  const [jail, setJail] = useState(jailOptions[0] ?? 'sshd')
  const [ip, setIp] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setError(null)
    setSubmitting(true)
    try {
      await api.post<ScanAction>(
        `/api/v1/hosts/${hostId}/fail2ban-ban`,
        { jail, ip, reason: 'manual_ui' },
      )
      onSuccess(`Ban agendado: ${ip} no jail ${jail}`)
    } catch (err) {
      setError(formatError(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-zinc-950 rounded-lg shadow-xl max-w-md w-full p-5 border border-zinc-200 dark:border-zinc-800"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold mb-3">Banir IP manualmente</h3>
        <p className="text-xs text-zinc-500 mb-3">
          O fail2ban vai aplicar o ban via firewall configurado nele.
        </p>

        <div className="space-y-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">Jail</label>
            <input
              type="text"
              value={jail}
              onChange={(e) => setJail(e.target.value)}
              list="jail-options"
              placeholder="sshd"
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 font-mono"
            />
            <datalist id="jail-options">
              {jailOptions.map((j) => (
                <option key={j} value={j} />
              ))}
            </datalist>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">IP a banir</label>
            <input
              type="text"
              value={ip}
              onChange={(e) => setIp(e.target.value)}
              placeholder="203.0.113.42"
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 font-mono"
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-600 mb-3">{error}</p>}

        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={submitting || !jail.trim() || !ip.trim()}
            className="px-3 py-2 text-sm rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 disabled:opacity-50"
          >
            {submitting ? 'Banindo…' : 'Banir IP'}
          </button>
        </div>
      </div>
    </div>
  )
}

function parseJails(json: string | null): JailDetail[] {
  if (!json) return []
  try {
    const parsed = JSON.parse(json) as { jails?: JailDetail[] }
    if (!Array.isArray(parsed.jails)) return []
    // Normaliza cada jail: garante name string + banned_ips array + count number.
    // Sem essa defesa, jail com `banned_ips: null` (agente velho ou bug) causa
    // crash em jail.banned_ips.length no JailCard.
    return parsed.jails
      .filter((j) => typeof j?.name === 'string')
      .map((j) => ({
        name: j.name,
        banned_count: typeof j.banned_count === 'number' ? j.banned_count : 0,
        banned_ips: Array.isArray(j.banned_ips) ? j.banned_ips : [],
      }))
  } catch {
    return []
  }
}

function formatError(err: unknown): string {
  if (err instanceof ApiError) {
    return typeof err.detail === 'string' ? err.detail : `HTTP ${err.status}`
  }
  return 'erro desconhecido'
}
