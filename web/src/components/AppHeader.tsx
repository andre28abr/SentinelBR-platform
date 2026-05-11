/**
 * <AppHeader> — header reusavel em todas as pages internas (autenticadas).
 *
 * Linha 1: Logo · org · email · sair
 * Linha 2: AlertBadge | Hosts | Alertas | ATT&CK | Hunting | Purple Team | LGPD
 *
 * Usado em HostsPage, HostDetailPage, AlertsPage, etc. Mantem consistencia
 * visual e evita duplicar codigo de menu.
 */

import { Link } from 'react-router-dom'

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
        <Tooltip content="Lista de servidores monitorados">
          <Link
            to="/"
            className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Hosts
          </Link>
        </Tooltip>
        <Tooltip content="Alertas de segurança disparados pelas regras de detecção">
          <Link
            to="/alerts"
            className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Alertas
          </Link>
        </Tooltip>
        <Tooltip content="MITRE ATT&CK em PT-BR — catálogo de técnicas de ataque que o SentinelBR detecta">
          <Link
            to="/kb"
            className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            ATT&CK
          </Link>
        </Tooltip>
        <Tooltip content="Threat Hunting — queries pré-prontas para investigação proativa">
          <Link
            to="/hunting"
            className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Hunting
          </Link>
        </Tooltip>
        <Tooltip content="Purple Team — simulações de ataque + detecção esperada">
          <Link
            to="/purple-team"
            className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Purple Team
          </Link>
        </Tooltip>
        <Tooltip content="Relatórios de compliance LGPD (audit log, MTTR, retenção)">
          <Link
            to="/compliance"
            className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            LGPD
          </Link>
        </Tooltip>
      </nav>
    </header>
  )
}
