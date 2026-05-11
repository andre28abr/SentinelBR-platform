/**
 * <FirewallPanel> — snapshot read-only do firewall ativo (Fase H4) +
 * adicionar/remover regras (Fase H6, ufw e firewalld apenas).
 *
 * O agente roda `ufw status numbered` / `firewall-cmd --list-all` / `nft list
 * ruleset` / `iptables -L -n -v` (dependendo do backend) e empacota em JSON
 * com `{backend, raw}`. Pra ufw conseguimos parsear a numeracao pra botao
 * "remover"; pra firewalld extraimos rich-rules; outros backends so leitura.
 */

import { Icon } from '@iconify/react'
import { useMemo, useState } from 'react'

import { ApiError, api } from '@/lib/api'

interface Props {
  hostId: string
  backend: string // ufw | firewalld | nftables | iptables
  statusJson: string | null
}

interface ScanAction {
  id: string
  status: string
}

const SUPPORTED = new Set(['ufw', 'firewalld'])

export default function FirewallPanel({ hostId, backend, statusJson }: Props) {
  const raw = useMemo(() => parseRaw(statusJson), [statusJson])
  const ufwRules = useMemo(() => (backend === 'ufw' ? parseUFWRules(raw) : []), [backend, raw])
  const firewalldRules = useMemo(
    () => (backend === 'firewalld' ? parseFirewalldRichRules(raw) : []),
    [backend, raw],
  )
  const [addOpen, setAddOpen] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const supported = SUPPORTED.has(backend)

  async function removeRule(ruleId: string) {
    setError(null)
    setFeedback(null)
    try {
      const action = await api.delete<ScanAction>(
        `/api/v1/hosts/${hostId}/firewall-rule`,
        { rule_id: ruleId, reason: 'manual_ui' },
      )
      setFeedback(`Remoção agendada (${action.status}). Aplicada no próximo heartbeat.`)
    } catch (err) {
      setError(formatError(err))
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Icon icon="lucide:brick-wall" className="text-emerald-700 dark:text-emerald-400 text-xl" />
          <h3 className="text-base font-semibold">Firewall</h3>
          <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-200 font-mono">
            {backend}
          </span>
        </div>
        {supported && (
          <button
            type="button"
            onClick={() => setAddOpen(true)}
            className="text-xs px-3 py-1.5 rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900"
          >
            + Adicionar regra
          </button>
        )}
      </div>

      {!supported && (
        <p className="text-xs text-zinc-500 italic">
          Edição pela UI suporta apenas <code className="font-mono">ufw</code> e{' '}
          <code className="font-mono">firewalld</code>. Pra editar regras{' '}
          <code className="font-mono">{backend}</code>, use o terminal no host.
        </p>
      )}

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

      {backend === 'ufw' && ufwRules.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase text-zinc-500 mb-2">
            Regras numeradas
          </h4>
          <ul className="divide-y divide-zinc-200 dark:divide-zinc-800 border border-zinc-200 dark:border-zinc-800 rounded">
            {ufwRules.map((r) => (
              <li
                key={r.num}
                className="flex items-center justify-between gap-3 px-3 py-2 text-xs"
              >
                <div className="flex-1 font-mono break-all">
                  <span className="text-zinc-500 mr-2">[{r.num}]</span>
                  {r.text}
                </div>
                <button
                  type="button"
                  onClick={() => {
                    if (confirm(`Remover regra [${r.num}] ${r.text}?`)) removeRule(r.num)
                  }}
                  className="text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap"
                >
                  remover
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {backend === 'firewalld' && firewalldRules.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase text-zinc-500 mb-2">
            Rich rules
          </h4>
          <ul className="divide-y divide-zinc-200 dark:divide-zinc-800 border border-zinc-200 dark:border-zinc-800 rounded">
            {firewalldRules.map((r, i) => (
              <li
                key={`${i}-${r.slice(0, 32)}`}
                className="flex items-center justify-between gap-3 px-3 py-2 text-xs"
              >
                <code className="flex-1 font-mono break-all">{r}</code>
                <button
                  type="button"
                  onClick={() => {
                    if (confirm(`Remover regra: ${r}?`)) removeRule(r)
                  }}
                  className="text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap"
                >
                  remover
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div>
        <h4 className="text-xs font-semibold uppercase text-zinc-500 mb-2">Snapshot</h4>
        {raw ? (
          <pre className="text-xs font-mono bg-zinc-100 dark:bg-zinc-900 p-3 rounded overflow-x-auto max-h-[400px] overflow-y-auto whitespace-pre-wrap">
            {raw}
          </pre>
        ) : (
          <p className="text-sm text-zinc-500 italic">
            {statusJson === null
              ? 'Aguardando próximo heartbeat (~30s)…'
              : 'Snapshot vazio — agente pode não ter permissão pra ler regras.'}
          </p>
        )}
      </div>

      {addOpen && (
        <AddRuleModal
          hostId={hostId}
          onClose={() => setAddOpen(false)}
          onSuccess={(msg) => {
            setFeedback(msg)
            setAddOpen(false)
          }}
        />
      )}
    </div>
  )
}

function AddRuleModal({
  hostId,
  onClose,
  onSuccess,
}: {
  hostId: string
  onClose: () => void
  onSuccess: (msg: string) => void
}) {
  const [verb, setVerb] = useState<'allow' | 'deny'>('allow')
  const [protocol, setProtocol] = useState<'tcp' | 'udp'>('tcp')
  const [port, setPort] = useState('')
  const [sourceCidr, setSourceCidr] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function submit() {
    setError(null)
    setSubmitting(true)
    try {
      await api.post<ScanAction>(`/api/v1/hosts/${hostId}/firewall-rule`, {
        verb,
        protocol,
        port,
        source_cidr: sourceCidr,
        reason: 'manual_ui',
      })
      onSuccess(`Regra ${verb} ${protocol}/${port} agendada.`)
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
        <h3 className="text-base font-semibold mb-3">Adicionar regra ao firewall</h3>
        <p className="text-xs text-zinc-500 mb-4">
          Regra é aplicada como permanente + recarregada (firewalld) ou
          adicionada (ufw). Aplica também em runtime — efeito imediato.
        </p>

        <div className="grid grid-cols-2 gap-3 mb-3">
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">Ação</label>
            <select
              value={verb}
              onChange={(e) => setVerb(e.target.value as 'allow' | 'deny')}
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900"
            >
              <option value="allow">allow (permitir)</option>
              <option value="deny">deny (bloquear)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">Protocolo</label>
            <select
              value={protocol}
              onChange={(e) => setProtocol(e.target.value as 'tcp' | 'udp')}
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900"
            >
              <option value="tcp">tcp</option>
              <option value="udp">udp</option>
            </select>
          </div>
        </div>

        <div className="space-y-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">
              Porta(s) <span className="text-zinc-400">(ex: 22, 80,443, 1000:2000)</span>
            </label>
            <input
              type="text"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="22"
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-zinc-500 mb-1">
              Source CIDR <span className="text-zinc-400">(opcional)</span>
            </label>
            <input
              type="text"
              value={sourceCidr}
              onChange={(e) => setSourceCidr(e.target.value)}
              placeholder="203.0.113.0/24"
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
            disabled={submitting || !port.trim()}
            className="px-3 py-2 text-sm rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 disabled:opacity-50"
          >
            {submitting ? 'Adicionando…' : 'Adicionar regra'}
          </button>
        </div>
      </div>
    </div>
  )
}

function parseRaw(json: string | null): string {
  if (!json) return ''
  try {
    const parsed = JSON.parse(json) as { raw?: string }
    return typeof parsed.raw === 'string' ? parsed.raw : ''
  } catch {
    return ''
  }
}

interface UFWRule {
  num: string
  text: string
}

// parseUFWRules extrai linhas "[ N] To Action From" do output de
// `ufw status numbered`. Ignora cabecalho e linhas vazias.
function parseUFWRules(raw: string): UFWRule[] {
  if (!raw) return []
  const out: UFWRule[] = []
  for (const line of raw.split('\n')) {
    const m = line.match(/^\[\s*(\d+)\]\s+(.+)$/)
    if (m) out.push({ num: m[1], text: m[2].trim() })
  }
  return out
}

// parseFirewalldRichRules extrai linhas que comecem com "rule" no output de
// `firewall-cmd --list-all`. Heuristica simples — funciona pro formato padrao.
function parseFirewalldRichRules(raw: string): string[] {
  if (!raw) return []
  const out: string[] = []
  for (const line of raw.split('\n')) {
    const trimmed = line.trim()
    if (trimmed.startsWith('rule ')) out.push(trimmed)
  }
  return out
}

function formatError(err: unknown): string {
  if (err instanceof ApiError) {
    return typeof err.detail === 'string' ? err.detail : `HTTP ${err.status}`
  }
  return 'erro desconhecido'
}
