/**
 * <LabPage> — controle de VMs OrbStack do demo (so visivel em lab_mode).
 *
 * Lista VMs lab-* (debian, ubuntu, fedora, rocky, alpine, vuln-lab) com
 * estado (running/stopped) + botoes para start/stop/atacar de novo + um
 * "Reset demo" pra apagar alerts/actions e recomecar do zero.
 *
 * Quando lab_mode=false, redireciona pra "/" (a aba nem aparece no header).
 */

import { Icon } from '@iconify/react'
import { useEffect, useState } from 'react'
import { Navigate } from 'react-router-dom'

import AppHeader from '@/components/AppHeader'
import ConfirmDialog from '@/components/ConfirmDialog'
import { ApiError, api } from '@/lib/api'
import { useLabMode } from '@/lib/useLabMode'
import { usePolling } from '@/lib/usePolling'

interface VmInfo {
  name: string
  state: string
  distro: string
  arch: string
}

interface VmActionResponse {
  name: string
  action: string
  ok: boolean
  detail: string
}

interface ResetResponse {
  alerts_deleted: number
  actions_deleted: number
  detail: string
}

type Loading = Record<string, boolean>

export default function LabPage() {
  const labMode = useLabMode()
  const [vms, setVms] = useState<VmInfo[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<Loading>({})
  const [confirmReset, setConfirmReset] = useState(false)
  const [resetMsg, setResetMsg] = useState<string | null>(null)

  // loadVms eh useCallback-like: definida fora de useEffect pra ser reusada
  // pelos handlers (callVmAction, doReset). useEffect inicial chama-a, e
  // usePolling re-chama a cada 10s (visibility-aware).
  function loadVms() {
    api
      .get<VmInfo[]>('/api/v1/lab/vms')
      .then((list) => {
        setVms(list)
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof ApiError ? String(err.detail) : 'erro ao carregar VMs')
      })
  }

  useEffect(() => {
    if (labMode.enabled) loadVms()
  }, [labMode.enabled])
  usePolling(() => {
    if (labMode.enabled) loadVms()
  }, 10_000)

  if (labMode.loading) return <PageShell>Carregando…</PageShell>
  if (!labMode.enabled) return <Navigate to="/" replace />

  async function callVmAction(name: string, action: 'start' | 'stop' | 'attack') {
    setBusy((b) => ({ ...b, [`${name}:${action}`]: true }))
    try {
      const res = await api.post<VmActionResponse>(`/api/v1/lab/vms/${name}/${action}`)
      if (action === 'attack' && res.detail) {
        // Mostra ultimas linhas do attack.sh num toast simples.
        setResetMsg(`✓ ${name} re-atacada:\n${res.detail}`)
      }
      // Refresca lista pra mostrar novo estado da VM
      await loadVms()
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : `falha em ${action} ${name}`)
    } finally {
      setBusy((b) => ({ ...b, [`${name}:${action}`]: false }))
    }
  }

  async function doReset() {
    setConfirmReset(false)
    setBusy((b) => ({ ...b, reset: true }))
    try {
      const res = await api.post<ResetResponse>('/api/v1/lab/reset')
      setResetMsg(
        `Demo reset: ${res.alerts_deleted} alertas + ${res.actions_deleted} ações apagados.`,
      )
    } catch (err) {
      setError(err instanceof ApiError ? String(err.detail) : 'falha ao resetar demo')
    } finally {
      setBusy((b) => ({ ...b, reset: false }))
    }
  }

  return (
    <PageShell>
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <Icon icon="lucide:flask-conical" className="text-amber-600" aria-hidden />
            Laboratório
          </h1>
          <p className="text-sm text-zinc-500 mt-1">
            VMs propositalmente vulneráveis (OrbStack) para demonstrar detecção e resposta.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setConfirmReset(true)}
          disabled={busy.reset}
          className="flex items-center gap-2 px-3 py-2 text-sm rounded border border-red-300 dark:border-red-700 text-red-700 dark:text-red-300 hover:bg-red-50 dark:hover:bg-red-950/30 disabled:opacity-50"
        >
          <Icon icon="lucide:rotate-ccw" aria-hidden />
          {busy.reset ? 'Resetando…' : 'Resetar demo'}
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-md border border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950/30 p-3 text-sm text-red-900 dark:text-red-200"
        >
          {error}
        </div>
      )}
      {resetMsg && (
        <div
          role="status"
          className="mb-4 rounded-md border border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/30 p-3 text-sm text-emerald-900 dark:text-emerald-200 whitespace-pre-line"
        >
          {resetMsg}
          <button
            type="button"
            onClick={() => setResetMsg(null)}
            className="ml-3 text-xs underline"
          >
            fechar
          </button>
        </div>
      )}

      {vms === null ? (
        <p className="text-sm text-zinc-500">Carregando VMs…</p>
      ) : vms.length === 0 ? (
        <div className="rounded border border-zinc-200 dark:border-zinc-800 p-6 text-sm text-zinc-500">
          Nenhuma VM lab-* encontrada. Rode <code className="font-mono">make lab-up</code>{' '}
          no terminal para provisionar.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {vms.map((vm) => (
            <VmCard
              key={vm.name}
              vm={vm}
              busy={busy}
              onStart={() => callVmAction(vm.name, 'start')}
              onStop={() => callVmAction(vm.name, 'stop')}
              onAttack={() => callVmAction(vm.name, 'attack')}
            />
          ))}
        </div>
      )}

      <ConfirmDialog
        open={confirmReset}
        title="Resetar demo?"
        message={
          <>
            Apaga TODOS os alertas e ações da sua organização.
            <br />
            Hosts e logs de auditoria são preservados. As VMs continuam rodando.
          </>
        }
        confirmLabel="Resetar"
        variant="danger"
        onConfirm={doReset}
        onCancel={() => setConfirmReset(false)}
      />
    </PageShell>
  )
}

function VmCard({
  vm,
  busy,
  onStart,
  onStop,
  onAttack,
}: {
  vm: VmInfo
  busy: Loading
  onStart: () => void
  onStop: () => void
  onAttack: () => void
}) {
  const running = vm.state === 'running'
  const stateColor = running
    ? 'text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-700 bg-emerald-50 dark:bg-emerald-950/30'
    : 'text-zinc-600 dark:text-zinc-400 border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900'
  const startBusy = busy[`${vm.name}:start`]
  const stopBusy = busy[`${vm.name}:stop`]
  const attackBusy = busy[`${vm.name}:attack`]

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="font-mono text-sm font-medium">{vm.name}</div>
          <div className="text-xs text-zinc-500 mt-0.5">
            {vm.distro} · {vm.arch}
          </div>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded border ${stateColor}`}>
          {vm.state}
        </span>
      </div>
      <div className="flex gap-2 flex-wrap">
        {running ? (
          <button
            type="button"
            onClick={onStop}
            disabled={stopBusy}
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900 disabled:opacity-50"
          >
            <Icon icon="lucide:square" aria-hidden />
            {stopBusy ? 'Parando…' : 'Parar'}
          </button>
        ) : (
          <button
            type="button"
            onClick={onStart}
            disabled={startBusy}
            className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900 disabled:opacity-50"
          >
            <Icon icon="lucide:play" aria-hidden />
            {startBusy ? 'Iniciando…' : 'Iniciar'}
          </button>
        )}
        <button
          type="button"
          onClick={onAttack}
          disabled={!running || attackBusy}
          title={!running ? 'Inicie a VM primeiro' : undefined}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs rounded border border-amber-300 dark:border-amber-700 text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-950/30 disabled:opacity-40"
        >
          <Icon icon="lucide:zap" aria-hidden />
          {attackBusy ? 'Atacando…' : 'Re-atacar'}
        </button>
      </div>
    </div>
  )
}

function PageShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="max-w-6xl mx-auto p-4 sm:p-6">
      <AppHeader />
      {children}
    </main>
  )
}
