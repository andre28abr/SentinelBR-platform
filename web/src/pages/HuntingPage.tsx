import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, api } from '@/lib/api'

interface HuntingQuery {
  id: string
  name: string
  description: string
  mitre?: string
  events_filter?: {
    source?: string
    severity?: string
    hours?: number
  }
  search_text?: string
}

export default function HuntingPage() {
  const [queries, setQueries] = useState<HuntingQuery[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<HuntingQuery[]>('/api/v1/kb/hunting')
      .then(setQueries)
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : 'erro'))
  }, [])

  return (
    <main className="min-h-screen p-6 max-w-7xl mx-auto">
      <header className="mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <Link to="/" className="text-sm text-zinc-500 hover:underline">
          ← voltar
        </Link>
        <h1 className="text-2xl font-bold mt-2">Hunting Queries</h1>
        <p className="text-sm text-zinc-500">
          Buscas prontas que correlacionam padrões de ataque conhecidos. Clique em
          um host depois pra ver os eventos filtrados.
        </p>
      </header>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      <div className="space-y-3">
        {queries.map((q) => (
          <article
            key={q.id}
            className="p-4 rounded-lg border border-zinc-200 dark:border-zinc-800"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <header className="flex items-center gap-2 mb-2">
                  <h2 className="text-base font-semibold">{q.name}</h2>
                  {q.mitre && (
                    <Link
                      to="/kb"
                      className="text-[10px] px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-mono hover:bg-zinc-200 dark:hover:bg-zinc-700"
                    >
                      {q.mitre}
                    </Link>
                  )}
                </header>
                <p className="text-sm text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap mb-3">
                  {q.description}
                </p>
                <div className="text-xs text-zinc-500 space-x-3 font-mono">
                  {q.events_filter?.source && <span>source={q.events_filter.source}</span>}
                  {q.events_filter?.severity && <span>severity={q.events_filter.severity}</span>}
                  {q.events_filter?.hours && <span>hours={q.events_filter.hours}</span>}
                  {q.search_text && <span>contém="{q.search_text}"</span>}
                </div>
              </div>
            </div>
            <p className="text-xs text-zinc-500 italic mt-3">
              Pra ver resultados: vá a um host (Hosts → click) → aba "Eventos recentes",
              aplique os mesmos filtros mostrados acima.
            </p>
          </article>
        ))}
      </div>
    </main>
  )
}
