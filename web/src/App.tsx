import { useEffect, useState } from 'react'

import { cn } from '@/lib/utils'

interface HealthResponse {
  status: string
  timestamp: string
  version: string
}

type ApiState =
  | { kind: 'loading' }
  | { kind: 'ok'; data: HealthResponse }
  | { kind: 'error'; message: string }

function App() {
  const [state, setState] = useState<ApiState>({ kind: 'loading' })

  useEffect(() => {
    fetch('/api/v1/health')
      .then(async (r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return (await r.json()) as HealthResponse
      })
      .then((data) => setState({ kind: 'ok', data }))
      .catch((e) => setState({ kind: 'error', message: e.message }))
  }, [])

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-xl w-full space-y-6">
        <header className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">SentinelBR</h1>
          <p className="text-zinc-500 dark:text-zinc-400">
            Plataforma open-source de segurança para servidores Linux
          </p>
        </header>

        <section className="rounded-xl border border-zinc-200 dark:border-zinc-800 p-6 space-y-3">
          <h2 className="font-semibold">Status do servidor</h2>
          <ApiStatus state={state} />
        </section>

        <footer className="text-center text-xs text-zinc-500">
          web: vite + react + ts · server: fastapi · agent: go
        </footer>
      </div>
    </main>
  )
}

function ApiStatus({ state }: { state: ApiState }) {
  if (state.kind === 'loading') {
    return <p className="text-sm text-zinc-500">Verificando…</p>
  }
  if (state.kind === 'error') {
    return (
      <div className="text-sm">
        <span className={cn('inline-block w-2 h-2 rounded-full bg-red-500 mr-2')} />
        Erro ao conectar ao servidor:{' '}
        <code className="text-red-600 dark:text-red-400">{state.message}</code>
        <p className="mt-2 text-zinc-500 text-xs">
          Suba a stack com <code>make dev</code> e o server com <code>make server</code>.
        </p>
      </div>
    )
  }
  return (
    <div className="text-sm space-y-1">
      <div className="flex items-center gap-2">
        <span className="inline-block w-2 h-2 rounded-full bg-green-500" />
        <span>{state.data.status}</span>
        <span className="text-zinc-500">v{state.data.version}</span>
      </div>
      <p className="text-xs text-zinc-500">
        timestamp: <code>{state.data.timestamp}</code>
      </p>
    </div>
  )
}

export default App
