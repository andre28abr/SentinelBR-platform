import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { ApiError, api } from '@/lib/api'

interface Technique {
  id: string
  name: string
  tactic: string
  severity: string
  url: string
  description: string
  detection?: { rules?: string[]; signals?: string }
  mitigation?: string[]
  references?: string[]
}

export default function KbPage() {
  const [techniques, setTechniques] = useState<Technique[]>([])
  const [selected, setSelected] = useState<Technique | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<Technique[]>('/api/v1/kb/techniques')
      .then(setTechniques)
      .catch((err) => setError(err instanceof ApiError ? String(err.detail) : 'erro'))
  }, [])

  return (
    <main className="min-h-screen p-6 max-w-6xl mx-auto">
      <header className="mb-6 pb-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
        <div>
          <Link to="/" className="text-sm text-zinc-500 hover:underline">
            ← voltar
          </Link>
          <h1 className="text-2xl font-bold mt-2">MITRE ATT&CK — Knowledge Base PT-BR</h1>
          <p className="text-sm text-zinc-500">
            Técnicas que o SentinelBR detecta hoje, com mitigações e referências.
          </p>
        </div>
      </header>

      {error && <p className="text-sm text-red-600 mb-4">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <aside className="md:col-span-1 space-y-1 max-h-[80vh] overflow-y-auto">
          {techniques.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setSelected(t)}
              className={`w-full text-left p-3 rounded border ${
                selected?.id === t.id
                  ? 'border-zinc-900 dark:border-zinc-100 bg-zinc-50 dark:bg-zinc-900'
                  : 'border-zinc-200 dark:border-zinc-800 hover:bg-zinc-50 dark:hover:bg-zinc-900'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono text-zinc-500">{t.id}</span>
                <SeverityBadge sev={t.severity} />
              </div>
              <p className="text-sm font-medium mt-1">{t.name}</p>
              <p className="text-xs text-zinc-500 mt-0.5">{t.tactic}</p>
            </button>
          ))}
        </aside>

        <section className="md:col-span-2">
          {selected ? (
            <TechniqueDetail t={selected} />
          ) : (
            <p className="text-sm text-zinc-500 italic">
              Selecione uma técnica à esquerda para ver detalhes.
            </p>
          )}
        </section>
      </div>
    </main>
  )
}

function TechniqueDetail({ t }: { t: Technique }) {
  return (
    <article className="space-y-4">
      <header>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-mono text-zinc-500">{t.id}</span>
          <SeverityBadge sev={t.severity} />
        </div>
        <h2 className="text-xl font-bold">{t.name}</h2>
        <p className="text-sm text-zinc-500">{t.tactic}</p>
      </header>

      <section>
        <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">Descrição</h3>
        <p className="text-sm whitespace-pre-wrap">{t.description}</p>
      </section>

      {t.detection && (
        <section>
          <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">
            Detecção no SentinelBR
          </h3>
          {t.detection.rules && (
            <ul className="text-sm list-disc list-inside mb-2">
              {t.detection.rules.map((r) => (
                <li key={r} className="font-mono">{r}</li>
              ))}
            </ul>
          )}
          {t.detection.signals && (
            <p className="text-sm whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">
              {t.detection.signals}
            </p>
          )}
        </section>
      )}

      {t.mitigation && (
        <section>
          <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">Mitigação</h3>
          <ul className="text-sm list-disc list-inside space-y-1">
            {t.mitigation.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </section>
      )}

      {t.references && (
        <section>
          <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">Referências</h3>
          <ul className="text-xs space-y-1">
            {t.references.map((r) => (
              <li key={r}>
                <a
                  href={r}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline break-all"
                >
                  {r}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  )
}

function SeverityBadge({ sev }: { sev: string }) {
  const color =
    sev === 'critical'
      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
      : sev === 'high'
        ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200'
        : sev === 'medium'
          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200'
          : 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
  return <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${color}`}>{sev}</span>
}
