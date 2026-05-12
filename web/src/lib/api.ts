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

// In-flight refresh promise — evita 5 requests simultaneos dispararem 5 refreshes.
// Outras requests aguardam o mesmo Promise.
let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setTokens, logout } = useAuthStore.getState()
  if (!refreshToken) return null
  try {
    const res = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) {
      // refresh expirou ou invalido — logout pra limpar state
      logout()
      return null
    }
    const data = (await res.json()) as { access_token: string; refresh_token: string }
    setTokens(data.access_token, data.refresh_token)
    return data.access_token
  } catch {
    logout()
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
    })
  }

  let token = useAuthStore.getState().accessToken
  let res = await exec(token)

  // Tenta refresh em 401, exceto pro endpoint de auth/refresh em si.
  if (res.status === 401 && !path.includes('/api/v1/auth/refresh') && !path.includes('/api/v1/auth/login')) {
    const newToken = await getOrRefreshToken()
    if (newToken) {
      token = newToken
      res = await exec(token)
    } else {
      // refresh falhou tambem — logout ja foi feito em refreshAccessToken
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

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  put: <T>(path: string, body?: unknown) => request<T>('PUT', path, body),
  delete: <T>(path: string, body?: unknown) => request<T>('DELETE', path, body),
}

/** Decodifica payload do JWT (sem validar assinatura) — usado pelo SessionTimer. */
export function jwtPayload(token: string): { exp?: number; iat?: number } | null {
  try {
    const part = token.split('.')[1]
    if (!part) return null
    // base64url -> base64
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/').padEnd(part.length + ((4 - (part.length % 4)) % 4), '=')
    return JSON.parse(atob(b64))
  } catch {
    return null
  }
}
