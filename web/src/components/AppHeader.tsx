/**
 * <AppHeader> — header reusavel em todas as pages internas (autenticadas).
 *
 * Linha 1: Logo · org · email · sair
 * Linha 2: AlertBadge | Hosts | Alertas | ATT&CK | Hunting | Purple Team | LGPD
 *
 * Usado em HostsPage, HostDetailPage, AlertsPage, etc. Mantem consistencia
 * visual e evita duplicar codigo de menu.
 */

import { Link, useLocation } from 'react-router-dom'

import AlertBadge from '@/components/AlertBadge'
import Logo from '@/components/Logo'
import Tooltip from '@/components/Tooltip'
import { useAuthStore } from '@/stores/auth'

export default function AppHeader() {
  const { user, logout } = useAuthStore()
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
          <Tooltip content="Encerrar sessão">
            <button
              type="button"
              onClick={logout}
              className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
            >
              sair
            </button>
          </Tooltip>
        </div>
      </div>

      {/* Linha 2: menu de navegacao */}
      <nav className="flex items-center gap-1 text-sm">
        <AlertBadge />
        <span className="text-zinc-300 dark:text-zinc-700 mx-2">|</span>
        <NavItem to="/" label="Hosts" tooltip="Lista de servidores monitorados" />
        <NavItem
          to="/alerts"
          label="Alertas"
          tooltip="Alertas de segurança disparados pelas regras de detecção"
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
      </nav>
    </header>
  )
}

function NavItem({ to, label, tooltip }: { to: string; label: string; tooltip: string }) {
  const { pathname } = useLocation()
  const active = isActive(pathname, to)
  const cls = active
    ? 'px-2 py-1 rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium'
    : 'px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100'
  return (
    <Tooltip content={tooltip}>
      <Link to={to} className={cls} aria-current={active ? 'page' : undefined}>
        {label}
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
