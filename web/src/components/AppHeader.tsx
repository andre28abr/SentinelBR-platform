/**
 * <AppHeader> — header reusavel em todas as pages internas (autenticadas).
 *
 * Linha 1: Logo · org · email · sair
 * Linha 2: AlertBadge | ATT&CK | Hunting | Purple Team | LGPD
 *
 * Usado em HostsPage, HostDetailPage, AlertsPage, etc. Mantem consistencia
 * visual e evita duplicar codigo de menu.
 */

import { Link } from 'react-router-dom'

import AlertBadge from '@/components/AlertBadge'
import Logo from '@/components/Logo'
import { useAuthStore } from '@/stores/auth'

export default function AppHeader() {
  const { user, logout } = useAuthStore()
  return (
    <header className="mb-4 pb-4 border-b border-zinc-200 dark:border-zinc-800 space-y-3">
      {/* Linha 1: logo + org + user + sair */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Link to="/" className="hover:opacity-80 transition" aria-label="ir pra home">
          <Logo size="md" />
        </Link>
        <div className="flex items-center gap-3 text-sm">
          {user?.org && (
            <span className="text-zinc-500">
              <span className="text-[10px] uppercase">org:</span>{' '}
              <span className="font-mono text-zinc-700 dark:text-zinc-300">{user.org.name}</span>
            </span>
          )}
          <span className="text-zinc-300 dark:text-zinc-700">·</span>
          <span className="text-zinc-500">{user?.email}</span>
          <button
            type="button"
            onClick={logout}
            className="text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            sair
          </button>
        </div>
      </div>

      {/* Linha 2: menu de navegacao */}
      <nav className="flex items-center gap-1 text-sm">
        <AlertBadge />
        <span className="text-zinc-300 dark:text-zinc-700 mx-2">|</span>
        <Link
          to="/"
          className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          Hosts
        </Link>
        <Link
          to="/alerts"
          className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          Alertas
        </Link>
        <Link
          to="/kb"
          className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          ATT&CK
        </Link>
        <Link
          to="/hunting"
          className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          Hunting
        </Link>
        <Link
          to="/purple-team"
          className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          Purple Team
        </Link>
        <Link
          to="/compliance"
          className="px-2 py-1 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-900 hover:text-zinc-900 dark:hover:text-zinc-100"
        >
          LGPD
        </Link>
      </nav>
    </header>
  )
}
