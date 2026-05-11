import { type FormEvent, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import Logo from '@/components/Logo'
import { ApiError, api } from '@/lib/api'
import { useAuthStore } from '@/stores/auth'

interface TokenPair {
  access_token: string
  refresh_token: string
}

interface OrgResponse {
  id: string
  name: string
  slug: string
}

interface MeResponse {
  id: string
  org_id: string
  email: string
  name: string
  role: string
  org?: OrgResponse
}

export default function LoginPage() {
  const { accessToken, setTokens, setUser } = useAuthStore()
  const navigate = useNavigate()
  const [email, setEmail] = useState('admin@sentinelbr.io')
  const [password, setPassword] = useState('')
  const [orgSlug, setOrgSlug] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  if (accessToken) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const body: { email: string; password: string; org_slug?: string } = {
        email,
        password,
      }
      if (orgSlug.trim()) body.org_slug = orgSlug.trim()
      const tokens = await api.post<TokenPair>('/api/v1/auth/login', body)
      setTokens(tokens.access_token, tokens.refresh_token)
      const me = await api.get<MeResponse>('/api/v1/auth/me')
      setUser(me)
      navigate('/')
    } catch (err) {
      if (err instanceof ApiError) {
        setError(typeof err.detail === 'string' ? err.detail : 'erro no login')
      } else {
        setError('erro ao conectar')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <form onSubmit={onSubmit} className="max-w-sm w-full space-y-5">
        <div className="text-center space-y-3">
          <div className="flex justify-center">
            <Logo size="lg" />
          </div>
          <p className="text-sm text-zinc-500">Entre na sua conta</p>
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
            className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 px-3 py-2 bg-transparent"
          />
        </div>

        <div className="space-y-2">
          <label className="block text-sm font-medium">Senha</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 px-3 py-2 bg-transparent"
          />
        </div>

        <div className="space-y-2">
          <label className="flex items-baseline justify-between text-sm font-medium">
            Organização
            <span className="text-xs font-normal text-zinc-400">opcional</span>
          </label>
          <input
            type="text"
            value={orgSlug}
            onChange={(e) => setOrgSlug(e.target.value.toLowerCase())}
            placeholder="default"
            autoComplete="off"
            className="w-full rounded-md border border-zinc-300 dark:border-zinc-700 px-3 py-2 bg-transparent font-mono text-sm"
          />
          <p className="text-xs text-zinc-500">
            Slug da organização (a-z, 0-9, -). Deixe em branco pra entrar na sua org default.
          </p>
        </div>

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 py-2 font-medium disabled:opacity-50"
        >
          {loading ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </main>
  )
}
