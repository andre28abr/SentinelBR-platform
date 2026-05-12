/**
 * <SessionTimer> — countdown da sessao no header.
 *
 * Le exp do access token (JWT), atualiza segundo a segundo. Cores:
 *   normal   (>10min): zinc, icone clock
 *   warning  (<10min): yellow, icone clock
 *   critical (<2min):  red, icone triangle-alert + tooltip "renovando..."
 *
 * O api.ts ja faz auto-refresh transparente em 401. Esse timer eh so o
 * indicador visual — quando faltar pouco, o auto-refresh dispara no
 * proximo request e o exp atualiza pra +60min sozinho.
 */

import { Icon } from '@iconify/react'
import { useEffect, useState } from 'react'

import Tooltip from '@/components/Tooltip'
import { jwtPayload } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

const TICK_MS = 1_000

export default function SessionTimer() {
  const accessToken = useAuthStore((s) => s.accessToken)
  const [now, setNow] = useState(() => Math.floor(Date.now() / 1000))

  useEffect(() => {
    const t = setInterval(() => setNow(Math.floor(Date.now() / 1000)), TICK_MS)
    return () => clearInterval(t)
  }, [])

  if (!accessToken) return null

  const payload = jwtPayload(accessToken)
  if (!payload?.exp) return null

  const remaining = payload.exp - now
  if (remaining <= 0) {
    return (
      <Tooltip content="Sessão expirou. A próxima ação vai renovar automaticamente.">
        <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200 cursor-help font-medium">
          <Icon icon="lucide:triangle-alert" className="text-sm" aria-hidden />
          renovando…
        </span>
      </Tooltip>
    )
  }

  const cfg = config(remaining)
  const tooltip = buildTooltip(payload.iat, payload.exp, remaining)

  return (
    <Tooltip content={tooltip}>
      <span
        className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded cursor-help font-medium ${cfg.classes}`}
      >
        <Icon icon={cfg.icon} className="text-sm" aria-hidden />
        {fmtRemaining(remaining)}
      </span>
    </Tooltip>
  )
}

function config(remaining: number) {
  if (remaining < 120) {
    return {
      classes: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200',
      icon: 'lucide:triangle-alert',
    }
  }
  if (remaining < 600) {
    return {
      classes: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
      icon: 'lucide:clock',
    }
  }
  return {
    classes: 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900',
    icon: 'lucide:clock',
  }
}

function fmtRemaining(seconds: number): string {
  if (seconds >= 3600) {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    return `${h}h${m.toString().padStart(2, '0')}`
  }
  if (seconds >= 60) {
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    if (seconds < 600) return `${m}:${s.toString().padStart(2, '0')}`
    return `${m}min`
  }
  return `${seconds}s`
}

function buildTooltip(iat: number | undefined, exp: number, remaining: number): string {
  const expStr = new Date(exp * 1000).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
  })
  const iatStr = iat
    ? new Date(iat * 1000).toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit',
      })
    : null
  const auto =
    remaining < 600
      ? 'Renovação automática vai disparar na próxima ação.'
      : 'Renovação automática quando faltar menos de 10min.'
  return [
    `Sessão expira ${expStr}`,
    iatStr && `Iniciada às ${iatStr}`,
    auto,
  ]
    .filter(Boolean)
    .join('\n')
}
