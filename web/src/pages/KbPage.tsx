import { useEffect, useState } from 'react'

import AppHeader from '@/components/AppHeader'
import Breadcrumbs from '@/components/Breadcrumbs'
import ErrorBoundary from '@/components/ErrorBoundary'
import { ApiError, api } from '@/lib/api'

interface Technique {
  id: string
  name: string
  tactic: string
  severity: string
  url: string
  description: string
  detection?: { rules?: string[]; signals?: string } | null
  mitigation?: string[] | null
  references?: string[] | null
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
    <main className="min-h-screen p-6 max-w-7xl mx-auto">
      <AppHeader />
      <Breadcrumbs items={[{ label: 'Knowledge Base — MITRE ATT&CK' }]} />
      <section className="mb-6">
        <h1 className="text-2xl font-bold">MITRE ATT&CK — Knowledge Base PT-BR</h1>
        <p className="text-sm text-zinc-500">
          Técnicas que o SentinelBR detecta hoje, com mitigações e referências.
        </p>
      </section>

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
            <ErrorBoundary key={selected.id}>
              <TechniqueDetail t={selected} />
            </ErrorBoundary>
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
  const rules = Array.isArray(t.detection?.rules) ? t.detection!.rules : []
  const mitigation = Array.isArray(t.mitigation) ? t.mitigation : []
  const references = Array.isArray(t.references) ? t.references : []
  const signals = typeof t.detection?.signals === 'string' ? t.detection.signals : ''

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

      {(rules.length > 0 || signals) && (
        <section>
          <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">
            Detecção no SentinelBR
          </h3>
          {rules.length > 0 && (
            <ul className="text-sm list-disc list-inside mb-2">
              {rules.map((r, i) => (
                <li key={`${r}-${i}`} className="font-mono">
                  {String(r)}
                </li>
              ))}
            </ul>
          )}
          {signals && (
            <p className="text-sm whitespace-pre-wrap text-zinc-600 dark:text-zinc-400">
              {signals}
            </p>
          )}
        </section>
      )}

      {mitigation.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">Mitigação</h3>
          <ul className="text-sm list-disc list-inside space-y-1">
            {mitigation.map((m, i) => (
              <li key={i}>{typeof m === 'string' ? m : JSON.stringify(m)}</li>
            ))}
          </ul>
        </section>
      )}

      {references.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold uppercase text-zinc-500 mb-1">Referências</h3>
          <ul className="text-xs space-y-1">
            {references.map((r, i) => {
              const href = typeof r === 'string' ? r : ''
              return (
                <li key={`${href}-${i}`}>
                  {href ? (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline break-all"
                    >
                      {href}
                    </a>
                  ) : (
                    <span className="text-zinc-400 italic">referência inválida</span>
                  )}
                </li>
              )
            })}
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
