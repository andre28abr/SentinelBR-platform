import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import LoginPage from '@/pages/LoginPage'
import { useAuthStore } from '@/stores/auth'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

/** Roteia por URL, como o App faz: /api/v1/lab/status é chamado pelo banner de lab. */
type FetchLike = (url: string, init?: RequestInit) => Promise<Response>

function routeFetch(handlers: Record<string, () => Response | Promise<Response>>) {
  const fn = vi.fn<FetchLike>(async (url) => {
    const h = handlers[url]
    if (!h) throw new Error(`fetch inesperado: ${url}`)
    return h()
  })
  vi.stubGlobal('fetch', fn)
  return fn
}

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<h1>Hosts (logado)</h1>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('LoginPage', () => {
  it('mostra o formulário com e-mail e organização pré-preenchidos para dev', async () => {
    routeFetch({ '/api/v1/lab/status': () => jsonResponse(200, { enabled: false }) })
    renderLogin()

    expect(screen.getByRole('button', { name: 'Entrar' })).toBeInTheDocument()
    expect(screen.getByDisplayValue('admin@sentinelbr.io')).toBeInTheDocument()
    expect(screen.getByDisplayValue('andre28abr')).toBeInTheDocument()
  })

  it('login com sucesso guarda token e usuário e navega para /', async () => {
    const fetchMock = routeFetch({
      '/api/v1/lab/status': () => jsonResponse(200, { enabled: false }),
      '/api/v1/auth/login': () => jsonResponse(200, { access_token: 'tok', refresh_token: 'r' }),
      '/api/v1/auth/me': () =>
        jsonResponse(200, { id: 'u1', org_id: 'o1', email: 'admin@sentinelbr.io', name: 'Admin', role: 'admin' }),
    })
    renderLogin()

    await userEvent.type(screen.getByLabelText('Senha'), 'admin1234')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    await screen.findByText('Hosts (logado)')
    expect(useAuthStore.getState().accessToken).toBe('tok')
    expect(useAuthStore.getState().user?.email).toBe('admin@sentinelbr.io')

    const loginCall = fetchMock.mock.calls.find((c) => c[0] === '/api/v1/auth/login') as [string, RequestInit]
    expect(JSON.parse(loginCall[1].body as string)).toEqual({
      email: 'admin@sentinelbr.io',
      password: 'admin1234',
      org_slug: 'andre28abr',
    })
  })

  it('credenciais inválidas mostram a mensagem do backend e não logam', async () => {
    routeFetch({
      '/api/v1/lab/status': () => jsonResponse(200, { enabled: false }),
      '/api/v1/auth/login': () => jsonResponse(401, { detail: 'credenciais invalidas' }),
    })
    renderLogin()

    await userEvent.type(screen.getByLabelText('Senha'), 'errada')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('credenciais invalidas')
    expect(useAuthStore.getState().accessToken).toBeNull()
    expect(screen.queryByText('Hosts (logado)')).not.toBeInTheDocument()
  })

  it('backend fora do ar mostra "erro ao conectar"', async () => {
    routeFetch({
      '/api/v1/lab/status': () => jsonResponse(200, { enabled: false }),
      '/api/v1/auth/login': () => Promise.reject(new Error('ECONNREFUSED')),
    })
    renderLogin()

    await userEvent.type(screen.getByLabelText('Senha'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('erro ao conectar')
  })

  it('organização em branco não vai no body (entra na org default)', async () => {
    const fetchMock = routeFetch({
      '/api/v1/lab/status': () => jsonResponse(200, { enabled: false }),
      '/api/v1/auth/login': () => jsonResponse(200, { access_token: 'tok', refresh_token: 'r' }),
      '/api/v1/auth/me': () => jsonResponse(200, { id: 'u', org_id: 'o', email: 'e', name: 'n', role: 'admin' }),
    })
    renderLogin()

    await userEvent.clear(screen.getByDisplayValue('andre28abr'))
    await userEvent.type(screen.getByLabelText('Senha'), 'x')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => expect(useAuthStore.getState().accessToken).toBe('tok'))
    const loginCall = fetchMock.mock.calls.find((c) => c[0] === '/api/v1/auth/login') as [string, RequestInit]
    expect(JSON.parse(loginCall[1].body as string)).not.toHaveProperty('org_slug')
  })

  it('já logado, /login redireciona para /', async () => {
    routeFetch({ '/api/v1/lab/status': () => jsonResponse(200, { enabled: false }) })
    useAuthStore.getState().setAccessToken('tok')
    renderLogin()

    expect(await screen.findByText('Hosts (logado)')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Entrar' })).not.toBeInTheDocument()
  })
})
