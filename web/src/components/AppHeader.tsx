/**
 * <AppHeader> — header reusavel em todas as pages internas (autenticadas).
 *
 * Linha 1: Logo · org · email · sair
 * Linha 2: Hosts | Alertas (com badge) | ATT&CK | Hunting | Purple Team | LGPD | Docs | Lab
 *
 * Usado em HostsPage, HostDetailPage, AlertsPage, etc. Mantem consistencia
 * visual e evita duplicar codigo de menu.
 */

import { Icon } from '@iconify/react'
import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import Logo from '@/components/Logo'
import SessionTimer from '@/components/SessionTimer'
import Tooltip from '@/components/Tooltip'
import { api, logout as apiLogout } from '@/lib/api'
import { useLabMode } from '@/lib/useLabMode'
import { REFRESH_MS, usePolling } from '@/lib/usePolling'
import { useAuthStore } from '@/stores/auth'

interface AlertCounts {
  open: number
  total: number
}

export default function AppHeader() {
  const { user } = useAuthStore()
  const labMode = useLabMode()
  const { pathname } = useLocation()
  const [alertCounts, setAlertCounts] = useState<AlertCounts>({ open: 0, total: 0 })

  // Polling visibility-aware do contador de alertas abertos.
  // Substitui o antigo <AlertBadge /> isolado — agora o badge fica
  // integrado ao NavItem "Alertas" pra evitar duplicacao no header.
  usePolling(
    async () => {
      try {
        setAlertCounts(await api.get<AlertCounts>('/api/v1/alerts/count'))
      } catch {
        // sem rede / nao autenticado — silencia
      }
    },
    REFRESH_MS,
    [],
  )

  return (
    <header className="mb-4 pb-4 border-b border-zinc-200 dark:border-zinc-800 space-y-3">
      {/* Linha 1: logo + org + user + sair */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Tooltip content="Voltar à página inicial (Hosts)">
          <Link to="/" className="hover:opacity-80 transition" aria-label="ir pra home">
            <Logo size="md" />
          </Link>
        </Tooltip>
        <div className="flex items-center gap-3 text-sm">
          {user?.org && (
            <Tooltip content="Organização atual (tenant). Cada usuário pertence a uma org.">
              <span className="text-zinc-500 cursor-help">
                <span className="text-[10px] uppercase">org:</span>{' '}
                <span className="font-mono text-zinc-700 dark:text-zinc-300">{user.org.name}</span>
              </span>
            </Tooltip>
          )}
          <span className="text-zinc-300 dark:text-zinc-700">·</span>
          <span className="text-zinc-500">{user?.email}</span>
          <SessionTimer />
          <Tooltip content="Encerrar sessão">
            <button
              type="button"
              onClick={() => apiLogout()}
              className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              sair
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Linha 2: menu de navegacao */}
      <nav className="flex items-center gap-1 text-sm">
        <NavItem to="/" label="Hosts" tooltip="Lista de servidores monitorados" />
        <NavItem
          to="/alerts"
          label="Alertas"
          tooltip="Alertas de segurança disparados pelas regras de detecção"
          badge={alertCounts.open}
        />
        <NavItem
          to="/kb"
          label="ATT&CK"
          tooltip="MITRE ATT&CK em PT-BR — catálogo de técnicas de ataque que o SentinelBR detecta"
        />
        <NavItem
          to="/hunting"
          label="Hunting"
          tooltip="Threat Hunting — queries pré-prontas para investigação proativa"
        />
        <NavItem
          to="/purple-team"
          label="Purple Team"
          tooltip="Purple Team — simulações de ataque + detecção esperada"
        />
        <NavItem
          to="/compliance"
          label="LGPD"
          tooltip="Relatórios de compliance LGPD (audit log, MTTR, retenção)"
        />
        <NavItem
          to="/docs"
          label="Docs"
          tooltip="Documentação completa do projeto (arquitetura, deployment, glossário, etc)"
        />
        {labMode.enabled && (
          <>
            <span className="text-zinc-300 dark:text-zinc-700 mx-2">|</span>
            <Tooltip content="Lab Mode — controle de VMs OrbStack do demo (start/stop/atacar de novo + reset)">
              <Link
                to="/lab"
                className={
                  isActive(pathname, '/lab')
                    ? 'px-2 py-1 rounded bg-amber-600 text-white font-medium flex items-center gap-1'
                    : 'px-2 py-1 rounded text-amber-700 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30 flex items-center gap-1'
                }
              >
                <Icon icon="lucide:flask-conical" aria-hidden />
                Lab
              </Link>
            </Tooltip>
          </>
        )}
      </nav>
    </header>
  )
}

function NavItem({
  to,
  label,
  tooltip,
  badge,
}: {
  to: string
  label: string
  tooltip: string
  badge?: number
}) {
  const { pathname } = useLocation()
  const active = isActive(pathname, to)
  const cls = active
    ? 'px-2 py-1 rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium flex items-center gap-1.5'
    : 'px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100 flex items-center gap-1.5'
  return (
    <Tooltip content={tooltip}>
      <Link to={to} className={cls} aria-current={active ? 'page' : undefined}>
        {label}
        {badge !== undefined && badge > 0 && (
          <span className="bg-red-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
            {badge}
          </span>
        )}
      </Link>
    </Tooltip>
  )
}

function isActive(pathname: string, to: string): boolean {
  if (to === '/') {
    return pathname === '/' || pathname.startsWith('/hosts')
  }
  return pathname === to || pathname.startsWith(`${to}/`)
}
