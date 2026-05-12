/**
 * <ClamavPanel> — UI pra escanear host com ClamAV (anti-virus tradicional).
 *
 * So aparece se o agente reportou ClamAV instalado (host.clamav_installed=true).
 * Padrao similar ao <YaraPanel>: botao "Escanear pasta...", modal com path,
 * cria Action que vai pro agente no proximo heartbeat.
 *
 * Tambem mostra info do signature DB (versao + idade) — base de ClamAV deve
 * ser atualizada diariamente via `freshclam` pra ser efetiva.
 */

import { Icon } from '@iconify/react'
import { useState } from 'react'

import Modal from '@/components/Modal'
import ScanProgressBadge from '@/components/ScanProgressBadge'
import Tooltip from '@/components/Tooltip'
import { ApiError, api } from '@/lib/api'

interface ScanAction {
  id: string
  status: string
  target: string
  reason: string
  created_at: string
}

interface Props {
  hostId: string
  /** se true, mostra UI de scan. Se false/null, mostra hint pra instalar. */
  installed?: boolean | null
  /** versao reportada pelo agente (string completa do --version). */
  version?: string | null
  /** idade do signature DB em dias. >7 alerta. */
  dbAgeDays?: number | null
}

const SUGGESTED_PATHS = ['/home', '/var/www', '/tmp', '/opt', '/srv']

export default function ClamavPanel({ hostId, installed, version, dbAgeDays }: Props) {
  const [open, setOpen] = useState(false)
  const [path, setPath] = useState(SUGGESTED_PATHS[0])
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastAction, setLastAction] = useState<ScanAction | null>(null)

  // Estado 1: ClamAV nao instalado no host
  if (!installed) {
    return (
      <div className="space-y-3 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
        <div className="flex items-baseline gap-2">
          <h3 className="text-sm font-semibold inline-flex items-center gap-1.5">
            <Tooltip content="ClamAV — antivírus open-source com 1M+ assinaturas atualizadas diariamente. Complementa o YARA detectando malware já catalogado globalmente.">
              <span className="cursor-help inline-flex items-center gap-1.5">
                <Icon icon="lucide:shield-check" className="text-base" aria-hidden />
                ClamAV
              </span>
            </Tooltip>
          </h3>
          <span className="text-xs px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-500 font-normal">
            não detectado
          </span>
        </div>
        <p className="text-sm text-zinc-500">
          ClamAV não está instalado neste host. Pra ativar antivírus baseado em
          assinaturas conhecidas, instale no servidor:
        </p>
        <div className="bg-zinc-100 dark:bg-zinc-900 p-3 rounded">
          <p className="text-[10px] uppercase text-zinc-500 mb-1">Debian / Ubuntu</p>
          <code className="text-xs font-mono block">
            sudo apt install clamav clamav-daemon && sudo freshclam
          </code>
        </div>
        <div className="bg-zinc-100 dark:bg-zinc-900 p-3 rounded">
          <p className="text-[10px] uppercase text-zinc-500 mb-1">RHEL / Fedora / Rocky</p>
          <code className="text-xs font-mono block">
            sudo dnf install clamav clamav-update && sudo freshclam
          </code>
        </div>
        <p className="text-xs text-zinc-500 italic">
          Depois de instalar, aguarde o próximo heartbeat (~30s) — esta página
          atualiza automaticamente.
        </p>
      </div>
    )
  }

  async function submit() {
    setError(null)
    setSubmitting(true)
    try {
      const action = await api.post<ScanAction>(
        `/api/v1/hosts/${hostId}/clamav-scan`,
        { path, reason: 'manual_ui' },
      )
      setLastAction(action)
      setOpen(false)
    } catch (err) {
      setError(
        err instanceof ApiError
          ? typeof err.detail === 'string' ? err.detail : `HTTP ${err.status}`
          : 'erro ao agendar scan',
      )
    } finally {
      setSubmitting(false)
    }
  }

  const dbStale = (dbAgeDays ?? 0) > 7
  const dbVeryStale = (dbAgeDays ?? 0) > 30

  return (
    <div className="space-y-3 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Tooltip content="ClamAV — antivírus open-source. Detecta malware conhecido via assinaturas atualizadas diariamente.">
            <span className="cursor-help inline-flex items-center gap-1.5">
              <Icon icon="lucide:shield-check" className="text-base" aria-hidden />
              ClamAV
            </span>
          </Tooltip>
          <span className="text-xs px-2 py-0.5 rounded bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200 font-normal">
            instalado
          </span>
        </h3>
        {version && (
          <Tooltip content={version}>
            <span className="text-xs text-zinc-500 font-mono cursor-help truncate max-w-xs">
              {version.split('/')[0]}
            </span>
          </Tooltip>
        )}
      </div>

      <p className="text-sm text-zinc-500">
        Escaneia o sistema procurando malware conhecido (1M+ assinaturas).
        Complementa o YARA — YARA pega padrões customizáveis, ClamAV pega
        ameaças já catalogadas globalmente.
      </p>

      {dbAgeDays !== null && dbAgeDays !== undefined && (
        <div
          className={`flex items-start gap-2 text-xs px-3 py-2 rounded ${
            dbVeryStale
              ? 'bg-red-50 dark:bg-red-950 text-red-700 dark:text-red-300'
              : dbStale
                ? 'bg-yellow-50 dark:bg-yellow-950 text-yellow-700 dark:text-yellow-300'
                : 'bg-green-50 dark:bg-green-950 text-green-700 dark:text-green-300'
          }`}
        >
          {dbVeryStale && (
            <Icon icon="lucide:triangle-alert" className="text-base mt-0.5 flex-shrink-0" aria-hidden />
          )}
          <span className="flex-1">
          {dbVeryStale
            ? `Signature DB desatualizado há ${dbAgeDays} dias. Rode `
            : dbStale
              ? `Signature DB com ${dbAgeDays} dias. Recomendado rodar `
              : `Signature DB com ${dbAgeDays} dia${dbAgeDays === 1 ? '' : 's'}. `}
          {(dbStale || dbVeryStale) && (
            <code className="font-mono bg-black/10 dark:bg-white/10 px-1 rounded">
              sudo freshclam
            </code>
          )}
          {(dbStale || dbVeryStale) && ' no host pra atualizar.'}
          </span>
        </div>
      )}

      <div className="flex items-center gap-3 flex-wrap">
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 px-4 py-2 text-sm font-medium"
        >
          Escanear pasta…
        </button>
        <ScanProgressBadge
          hostId={hostId}
          actionType="run_clamav_scan"
          label="Último scan:"
        />
      </div>
      {lastAction && (
        <p className="text-xs text-zinc-500">
          Recém agendado: <span className="font-mono">{lastAction.target}</span>
        </p>
      )}

      <Modal open={open} onClose={() => setOpen(false)} title="Escanear pasta com ClamAV">
          <p className="text-xs text-zinc-500 mb-3">
            ClamAV é mais lento que YARA (verifica contra DB extensa). Pra pastas
            grandes pode levar minutos. Resultados aparecem na aba "Eventos".
          </p>

          <div className="space-y-2 mb-4">
            <label className="block text-xs font-medium text-zinc-500">
              Caminho a escanear
            </label>
            <input
              type="text"
              value={path}
              onChange={(e) => setPath(e.target.value)}
              placeholder="/home"
              className="w-full px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 font-mono"
            />
            <div className="flex flex-wrap gap-1 pt-1">
              {SUGGESTED_PATHS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPath(p)}
                  className="text-[10px] px-2 py-0.5 rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 font-mono"
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-xs text-red-600 mb-3">{error}</p>}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={submit}
              disabled={submitting || !path.trim()}
              className="px-3 py-2 text-sm rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 disabled:opacity-50"
            >
              {submitting ? 'Agendando…' : 'Iniciar scan'}
            </button>
          </div>
      </Modal>
    </div>
  )
}
