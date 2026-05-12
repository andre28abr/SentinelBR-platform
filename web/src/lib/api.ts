import { useAuthStore } from '@/stores/auth'

export class ApiError extends Error {
  status: number
  detail: unknown
  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : `HTTP ${status}`)
    this.status = status
    this.detail = detail
  }
}

// Mutex pra refresh: evita N requests concorrentes dispararem N refreshes.
let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const { setAccessToken, clearAuth } = useAuthStore.getState()
  try {
    // Sem body — refresh vai automaticamente via cookie httpOnly.
    const res = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    })
    if (!res.ok) {
      clearAuth()
      return null
    }
    const data = (await res.json()) as { access_token: string }
    setAccessToken(data.access_token)
    return data.access_token
  } catch {
    clearAuth()
    return null
  }
}

async function getOrRefreshToken(): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight
  refreshInFlight = refreshAccessToken().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const exec = (token: string | null) => {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    if (token) headers.Authorization = `Bearer ${token}`
    return fetch(path, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      credentials: 'include',  // garante cookie httpOnly em rotas que precisam
    })
  }

  let token = useAuthStore.getState().accessToken
  let res = await exec(token)

  if (
    res.status === 401 &&
    !path.includes('/api/v1/auth/refresh') &&
    !path.includes('/api/v1/auth/login')
  ) {
    const newToken = await getOrRefreshToken()
    if (newToken) {
      token = newToken
      res = await exec(token)
    } else {
      throw new ApiError(401, 'sessão expirada')
    }
  }

  if (!res.ok) {
    let detail: unknown = res.statusText
    try {
      const j = await res.json()
      detail = j.detail ?? j
    } catch {
      // body não era JSON
    }
    throw new ApiError(res.status, detail)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

async function requestBlob(method: string, path: string): Promise<Blob> {
  const exec = (token: string | null) => {
    const headers: Record<string, string> = {}
    if (token) headers.Authorization = `Bearer ${token}`
    return fetch(path, { method, headers, credentials: 'include' })
  }
  let token = useAuthStore.getState().accessToken
  let res = await exec(token)
  if (res.status === 401 && !path.includes('/api/v1/auth/')) {
    const newToken = await getOrRefreshToken()
    if (newToken) {
      token = newToken
      res = await exec(token)
    } else {
      throw new ApiError(401, 'sessão expirada')
    }
  }
  if (!res.ok) throw new ApiError(res.status, res.statusText)
  return res.blob()
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
  delete: <T>(path: string, body?: unknown) => request<T>('DELETE', path, body),
  /** Pra downloads (PDF, CSV) — passa por refresh igual aos outros. */
  getBlob: (path: string) => requestBlob('GET', path),
}

/** Decodifica payload do JWT (sem validar assinatura) — usado pelo SessionTimer. */
export function jwtPayload(token: string): { exp?: number; iat?: number } | null {
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/').padEnd(part.length + ((4 - (part.length % 4)) % 4), '=')
    return JSON.parse(atob(b64))
  } catch {
    return null
  }
}

/**
 * Logout completo: chama backend pra apagar cookie httpOnly de refresh,
 * depois limpa estado local. Usar nos botoes "sair".
 */
export async function logout(): Promise<void> {
  try {
    await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })
  } catch {
    // mesmo se request falhar, limpa local — usuario ja quer sair.
  }
  useAuthStore.getState().clearAuth()
}
