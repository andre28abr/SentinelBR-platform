/**
 * usePolling — hook reusavel pra polling com:
 *   - pause automatico quando aba esta oculta (visibilitychange)
 *   - cleanup adequado em unmount
 *   - cancellation flag pra evitar setState pos-unmount
 *
 * Uso:
 *   usePolling(loadData, 5000, [hostId])
 *
 * loadData recebe um signal AbortSignal (opcional) — passe pra fetch pra
 * cancelar requests pendentes em unmount.
 */

import { useEffect } from 'react'

export const REFRESH_MS = 5_000  // default global pra polling de listas

export function usePolling(
  fn: (signal?: AbortSignal) => void | Promise<void>,
  intervalMs: number,
  deps: React.DependencyList = [],
) {
  useEffect(() => {
    let cancelled = false
    let controller = new AbortController()
    let timer: ReturnType<typeof setInterval> | null = null

    function tick() {
      if (cancelled) return
      if (document.hidden) return  // pausa silenciosamente quando aba oculta
      // Reset controller pra cada tick — se anterior pendente, aborta.
      controller.abort()
      controller = new AbortController()
      try {
        const r = fn(controller.signal)
        if (r instanceof Promise) {
          r.catch(() => {
            // Erros tratados pelo caller via try/catch internos.
          })
        }
      } catch {
        // sync throw — ignorar, mesmo motivo
      }
    }

    // Tick imediato + interval
    tick()
    timer = setInterval(tick, intervalMs)

    // Quando a aba volta a ficar visivel, dispara tick imediato pra
    // user nao ver dado stale.
    function onVisibility() {
      if (!document.hidden) tick()
    }
    document.addEventListener('visibilitychange', onVisibility)

    return () => {
      cancelled = true
      controller.abort()
      if (timer !== null) clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisibility)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
}
