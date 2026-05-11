import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, api } from '@/lib/api'

interface Playbook {
  id: string
  name: string
  description: string
  mitre?: string
  expected_alerts?: string[]
  expected_actions?: string[]
  expected_results?: string[]
  how_to_run: string
}

export default function PurpleTeamPage() {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<Playbook[]>('/api/v1/kb/playbooks')
      .then(setPlaybooks)
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : 'erro'))
  }, [])

  return (
    <main className="min-h-screen p-6 max-w-5xl mx-auto">
      <header className="mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800">
        <Link to="/" className="text-sm text-zinc-500 hover:underline">
          ← voltar
        </Link>
        <h1 className="text-2xl font-bold mt-2">Purple Team — Simulações</h1>
        <p className="text-sm text-zinc-500">
          Cenários "atacar + verificar detecção" usando o lab de VMs do SentinelBR.
          Cada playbook descreve o que esperar no UI depois.
        </p>
      </header>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      <div className="space-y-4">
        {playbooks.map((p) => (
          <article
            key={p.id}
            className="p-5 rounded-lg border border-zinc-200 dark:border-zinc-800"
          >
            <header className="flex items-center gap-2 mb-3">
              <h2 className="text-base font-semibold">{p.name}</h2>
              {p.mitre && (
                <Link
                  to="/kb"
                  className="text-[10px] px-2 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 font-mono hover:bg-zinc-200 dark:hover:bg-zinc-700"
                >
                  {p.mitre}
                </Link>
              )}
            </header>

            <p className="text-sm whitespace-pre-wrap mb-4">{p.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              {p.expected_alerts && (
                <section>
                  <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">
                    Alertas esperados
                  </h3>
                  <ul className="text-sm list-disc list-inside font-mono">
                    {p.expected_alerts.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                </section>
              )}
              {p.expected_actions && (
                <section>
                  <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">
                    Ações esperadas (auto)
                  </h3>
                  <ul className="text-sm list-disc list-inside font-mono">
                    {p.expected_actions.map((a) => (
                      <li key={a}>{a}</li>
                    ))}
                  </ul>
                </section>
              )}
              {p.expected_results && (
                <section>
                  <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">
                    Resultados
                  </h3>
                  <ul className="text-sm list-disc list-inside">
                    {p.expected_results.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                </section>
              )}
            </div>

            <section>
              <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">
                Como executar
              </h3>
              <pre className="text-xs bg-zinc-100 dark:bg-zinc-900 p-3 rounded overflow-x-auto whitespace-pre-wrap">
                {p.how_to_run}
              </pre>
            </section>
          </article>
        ))}
      </div>
    </main>
  )
}
