/**
 * useLabMode — hook que retorna o flag SENTINELBR_LAB_MODE do backend.
 *
 * Consulta /api/v1/lab/status (publico, sem auth) uma vez por sessao.
 * Cacheado em memoria pra nao spammar o backend a cada componente que pergunta.
 *
 * Uso:
 *   const labMode = useLabMode()
 *   if (labMode.enabled) return <LabBanner />
 *
 * O hook ja trata rede caida e backend offline — retorna {enabled: false,
 * loading: true} no inicio e {enabled: false, loading: false} se falhar
 * (fail-closed: assume prod se nao consegue confirmar lab).
 */

import { useEffect, useState } from 'react'

import { api } from '@/lib/api'

interface LabStatusResponse {
  enabled: boolean
}

interface LabModeState {
  enabled: boolean
  loading: boolean
}

// Cache em modulo: 1 fetch por load da pagina, todos os componentes leem.
let cached: LabStatusResponse | null = null
let inflight: Promise<LabStatusResponse> | null = null

async function fetchStatus(): Promise<LabStatusResponse> {
  if (cached) return cached
  if (inflight) return inflight
  inflight = api
    .get<LabStatusResponse>('/api/v1/lab/status')
    .then((data) => {
      cached = data
      return data
    })
    .catch(() => {
      // Fail-closed: se backend nao responde, assume prod (sem banner ruidoso).
      const fallback = { enabled: false }
      cached = fallback
      return fallback
    })
    .finally(() => {
      inflight = null
    })
  return inflight
}

export function useLabMode(): LabModeState {
  // Initial state vem do cache (synchronous). Se cache esta populado quando
  // esse hook monta, ja temos o valor certo no 1o render — sem flicker.
  const [state, setState] = useState<LabModeState>(() => ({
    enabled: cached?.enabled ?? false,
    loading: cached === null,
  }))

  useEffect(() => {
    // Cache hit: state inicial ja esta correto, nada a fazer.
    if (cached !== null) return

    let canceled = false
    fetchStatus().then((data) => {
      if (!canceled) setState({ enabled: data.enabled, loading: false })
    })
    return () => {
      canceled = true
    }
  }, [])

  return state
}
