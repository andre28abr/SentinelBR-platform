import { renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { usePolling } from '@/lib/usePolling'

function setHidden(hidden: boolean) {
  Object.defineProperty(document, 'hidden', { configurable: true, get: () => hidden })
  document.dispatchEvent(new Event('visibilitychange'))
}

describe('usePolling', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    setHidden(false)
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('dispara imediatamente e depois a cada intervalo', () => {
    const fn = vi.fn()
    renderHook(() => usePolling(fn, 1000))

    expect(fn).toHaveBeenCalledTimes(1)
    vi.advanceTimersByTime(3000)
    expect(fn).toHaveBeenCalledTimes(4)
  })

  it('passa um AbortSignal e aborta o anterior a cada tick', () => {
    const signals: AbortSignal[] = []
    renderHook(() => usePolling((s) => { if (s) signals.push(s) }, 1000))

    vi.advanceTimersByTime(1000)
    expect(signals).toHaveLength(2)
    expect(signals[0].aborted).toBe(true)
    expect(signals[1].aborted).toBe(false)
  })

  it('pausa com a aba oculta e retoma na hora ao voltar', () => {
    const fn = vi.fn()
    renderHook(() => usePolling(fn, 1000))
    expect(fn).toHaveBeenCalledTimes(1)

    setHidden(true)
    vi.advanceTimersByTime(5000)
    expect(fn).toHaveBeenCalledTimes(1)

    setHidden(false) // visibilitychange dispara tick imediato
    expect(fn).toHaveBeenCalledTimes(2)
  })

  it('no unmount para o timer e aborta o request pendente', () => {
    const fn = vi.fn()
    let last: AbortSignal | undefined
    const { unmount } = renderHook(() => usePolling((s) => { last = s; fn() }, 1000))

    unmount()
    vi.advanceTimersByTime(5000)
    expect(fn).toHaveBeenCalledTimes(1)
    expect(last?.aborted).toBe(true)
  })

  it('erro na função não derruba o polling', () => {
    const fn = vi.fn(async () => { throw new Error('boom') })
    renderHook(() => usePolling(fn, 1000))
    vi.advanceTimersByTime(2000)
    expect(fn).toHaveBeenCalledTimes(3)
  })
})
