import { useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '@/lib/api'
import { REFRESH_MS, usePolling } from '@/lib/usePolling'

interface Counts {
  open: number
  total: number
}

export default function AlertBadge() {
  const [counts, setCounts] = useState<Counts>({ open: 0, total: 0 })

  usePolling(
    async () => {
      try {
        setCounts(await api.get<Counts>('/api/v1/alerts/count'))
      } catch {
        // sem rede / nao autenticado — esconde silencioso
      }
    },
    REFRESH_MS,
    [],
  )

  return (
    <Link
      to="/alerts"
      className="text-sm text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 flex items-center gap-1"
    >
      Alertas
      {counts.open > 0 && (
        <span className="bg-red-600 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full">
          {counts.open}
        </span>
      )}
    </Link>
  )
}
