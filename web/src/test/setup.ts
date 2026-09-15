import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, vi } from 'vitest'

import { useAuthStore } from '@/stores/auth'

// Cada teste começa deslogado, com localStorage limpo e sem fetch real:
// nenhum teste do frontend deve depender do servidor no ar.
beforeEach(() => {
  localStorage.clear()
  useAuthStore.getState().clearAuth()
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => {
      throw new Error('fetch não mockado neste teste')
    }),
  )
})

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})
