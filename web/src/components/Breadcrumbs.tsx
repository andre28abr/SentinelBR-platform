/**
 * <Breadcrumbs> — caminho de navegacao estilo "Hosts / Lab Debian 11"
 * pra dar cara de sistema (terminal/IDE) em vez de site.
 *
 * Uso:
 *   <Breadcrumbs items={[{ label: 'Hosts', to: '/' }, { label: 'Lab Debian 11' }]} />
 *
 * Ultimo item sem `to` renderiza como texto (current location).
 */

import { Link } from 'react-router-dom'

export interface Crumb {
  label: string
  to?: string
}

interface Props {
  items: Crumb[]
}

export default function Breadcrumbs({ items }: Props) {
  if (items.length === 0) return null
  return (
    <nav className="text-xs text-zinc-500 font-mono mb-3" aria-label="breadcrumb">
      {items.map((c, i) => (
        <span key={i}>
          {i > 0 && <span className="mx-1.5 text-zinc-300 dark:text-zinc-700">/</span>}
          {c.to ? (
            <Link
              to={c.to}
              className="hover:text-zinc-900 dark:hover:text-zinc-100 hover:underline"
            >
              {c.label}
            </Link>
          ) : (
            <span className="text-zinc-700 dark:text-zinc-300">{c.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
