import { describe, expect, it } from 'vitest'

import { useAuthStore } from '@/stores/auth'

describe('auth store', () => {
  it('começa deslogado', () => {
    expect(useAuthStore.getState().accessToken).toBeNull()
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('persiste o token em localStorage sob a chave sentinelbr-auth', () => {
    useAuthStore.getState().setAccessToken('tok')
    const raw = localStorage.getItem('sentinelbr-auth')
    expect(raw).not.toBeNull()
    expect(JSON.parse(raw!).state.accessToken).toBe('tok')
  })

  it('clearAuth zera token e usuário (o cookie de refresh é apagado pelo logout() da api)', () => {
    useAuthStore.getState().setAccessToken('tok')
    useAuthStore.getState().setUser({ id: 'u', org_id: 'o', email: 'a@b.c', name: 'A', role: 'admin' })
    useAuthStore.getState().clearAuth()
    expect(useAuthStore.getState().accessToken).toBeNull()
    expect(useAuthStore.getState().user).toBeNull()
    expect(JSON.parse(localStorage.getItem('sentinelbr-auth')!).state.accessToken).toBeNull()
  })
})
