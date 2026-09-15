import { describe, expect, it, vi } from 'vitest'

import { ApiError, api, jwtPayload, logout } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

type FetchMock = ReturnType<typeof vi.fn>

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockFetch(...responses: Response[]): FetchMock {
  const fn = vi.fn()
  for (const r of responses) fn.mockResolvedValueOnce(r)
  vi.stubGlobal('fetch', fn)
  return fn
}

describe('api client', () => {
  it('envia Bearer quando há token e devolve o JSON', async () => {
    useAuthStore.getState().setAccessToken('tok-1')
    const fetchMock = mockFetch(jsonResponse(200, { ok: true }))

    const out = await api.get<{ ok: boolean }>('/api/v1/hosts')

    expect(out).toEqual({ ok: true })
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/v1/hosts')
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok-1')
    expect(init.credentials).toBe('include')
  })

  it('serializa o body em POST e não manda Authorization sem token', async () => {
    const fetchMock = mockFetch(jsonResponse(201, { id: 'x' }))

    await api.post('/api/v1/auth/login', { email: 'a@b.c', password: 's' })

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ email: 'a@b.c', password: 's' })
    expect((init.headers as Record<string, string>).Authorization).toBeUndefined()
  })

  it('204 devolve undefined em vez de tentar ler JSON', async () => {
    mockFetch(new Response(null, { status: 204 }))
    await expect(api.delete('/api/v1/hosts/1')).resolves.toBeUndefined()
  })

  it('erro HTTP vira ApiError com o detail do backend', async () => {
    mockFetch(jsonResponse(403, { detail: 'role insuficiente' }))

    const err = await api.get('/api/v1/admin').catch((e: unknown) => e)

    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).status).toBe(403)
    expect((err as ApiError).detail).toBe('role insuficiente')
    expect((err as ApiError).message).toBe('role insuficiente')
  })

  it('erro sem corpo JSON usa o statusText', async () => {
    mockFetch(new Response('gateway ruim', { status: 502, statusText: 'Bad Gateway' }))
    const err = (await api.get('/api/v1/x').catch((e: unknown) => e)) as ApiError
    expect(err.status).toBe(502)
    expect(err.detail).toBe('Bad Gateway')
  })

  it('401 → tenta refresh via cookie, guarda o token novo e repete a chamada', async () => {
    useAuthStore.getState().setAccessToken('velho')
    const fetchMock = mockFetch(
      jsonResponse(401, { detail: 'expirado' }),
      jsonResponse(200, { access_token: 'novo' }),
      jsonResponse(200, { hosts: [] }),
    )

    const out = await api.get('/api/v1/hosts')

    expect(out).toEqual({ hosts: [] })
    expect(useAuthStore.getState().accessToken).toBe('novo')
    const urls = fetchMock.mock.calls.map((c) => (c as [string])[0])
    expect(urls).toEqual(['/api/v1/hosts', '/api/v1/auth/refresh', '/api/v1/hosts'])
    const retry = fetchMock.mock.calls[2] as [string, RequestInit]
    expect((retry[1].headers as Record<string, string>).Authorization).toBe('Bearer novo')
  })

  it('refresh que falha limpa a sessão e lança 401 "sessão expirada"', async () => {
    useAuthStore.getState().setAccessToken('velho')
    useAuthStore.getState().setUser({ id: 'u', org_id: 'o', email: 'a@b.c', name: 'A', role: 'admin' })
    mockFetch(jsonResponse(401, { detail: 'expirado' }), jsonResponse(401, { detail: 'refresh inválido' }))

    const err = (await api.get('/api/v1/hosts').catch((e: unknown) => e)) as ApiError

    expect(err.status).toBe(401)
    expect(err.detail).toBe('sessão expirada')
    expect(useAuthStore.getState().accessToken).toBeNull()
    expect(useAuthStore.getState().user).toBeNull()
  })

  it('401 no próprio login NÃO dispara refresh (senha errada é senha errada)', async () => {
    const fetchMock = mockFetch(jsonResponse(401, { detail: 'credenciais inválidas' }))

    const err = (await api.post('/api/v1/auth/login', {}).catch((e: unknown) => e)) as ApiError

    expect(err.detail).toBe('credenciais inválidas')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('chamadas concorrentes com 401 compartilham UM refresh', async () => {
    useAuthStore.getState().setAccessToken('velho')
    const fetchMock = vi.fn(async (url: string) => {
      if (url === '/api/v1/auth/refresh') return jsonResponse(200, { access_token: 'novo' })
      const token = useAuthStore.getState().accessToken
      return token === 'novo' ? jsonResponse(200, { url }) : jsonResponse(401, {})
    })
    vi.stubGlobal('fetch', fetchMock)

    await Promise.all([api.get('/api/v1/a'), api.get('/api/v1/b'), api.get('/api/v1/c')])

    const refreshes = fetchMock.mock.calls.filter((c) => c[0] === '/api/v1/auth/refresh')
    expect(refreshes).toHaveLength(1)
  })
})

describe('jwtPayload', () => {
  it('decodifica o payload base64url sem validar assinatura', () => {
    const payload = { exp: 1700000000, iat: 1699990000 }
    const b64 = btoa(JSON.stringify(payload)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
    expect(jwtPayload(`h.${b64}.sig`)).toEqual(payload)
  })

  it('devolve null para token malformado', () => {
    expect(jwtPayload('nada')).toBeNull()
    expect(jwtPayload('a.###.b')).toBeNull()
  })
})

describe('logout', () => {
  it('chama o backend para apagar o cookie e limpa o estado local', async () => {
    useAuthStore.getState().setAccessToken('tok')
    const fetchMock = mockFetch(new Response(null, { status: 204 }))

    await logout()

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/logout', expect.objectContaining({ method: 'POST' }))
    expect(useAuthStore.getState().accessToken).toBeNull()
  })

  it('limpa o estado local mesmo se o backend estiver fora', async () => {
    useAuthStore.getState().setAccessToken('tok')
    vi.stubGlobal('fetch', vi.fn(async () => { throw new Error('offline') }))

    await logout()

    expect(useAuthStore.getState().accessToken).toBeNull()
  })
})
