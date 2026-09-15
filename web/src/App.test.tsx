import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import App from '@/App'
import { useAuthStore } from '@/stores/auth'

// O App usa BrowserRouter: controlamos a rota inicial pelo history do jsdom.
function at(path: string) {
  window.history.pushState({}, '', path)
}

function anyJson(body: unknown = {}) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } })),
  )
}

describe('App (roteamento e proteção de rotas)', () => {
  it('sem token, a raiz cai na tela de login', async () => {
    anyJson({ enabled: false })
    at('/')
    render(<App />)

    expect(await screen.findByRole('button', { name: 'Entrar' })).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })

  it('sem token, rota interna profunda também redireciona para /login', async () => {
    anyJson({ enabled: false })
    at('/hosts/abc-123')
    render(<App />)

    expect(await screen.findByRole('button', { name: 'Entrar' })).toBeInTheDocument()
    expect(window.location.pathname).toBe('/login')
  })

  it('rota desconhecida vai para a raiz (e daí para o login)', async () => {
    anyJson({ enabled: false })
    at('/nao-existe')
    render(<App />)

    await screen.findByRole('button', { name: 'Entrar' })
    expect(window.location.pathname).toBe('/login')
  })

  it('com token, a raiz NÃO mostra o login e carrega a página interna', async () => {
    // Qualquer chamada de API devolve lista vazia — só queremos ver o roteamento.
    anyJson([])
    useAuthStore.getState().setAccessToken('tok')
    useAuthStore.getState().setUser({ id: 'u', org_id: 'o', email: 'a@b.c', name: 'Admin', role: 'admin' })
    at('/')
    render(<App />)

    // A página é lazy: primeiro o loader, depois o conteúdo. Em nenhum momento o login.
    await vi.waitFor(() => expect(screen.queryByText('Carregando…')).not.toBeInTheDocument(), { timeout: 5000 })
    expect(screen.queryByRole('button', { name: 'Entrar' })).not.toBeInTheDocument()
    expect(window.location.pathname).toBe('/')
  })
})
