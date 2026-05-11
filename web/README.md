# sentinelbr-web

UI do SentinelBR. React 18 + TypeScript strict + Vite + Tailwind + Zustand. SPA pura — só consome a REST API do server.

## Setup

```bash
# do root:
make setup-web      # pnpm install

# OU direto:
cd web && pnpm install
```

## Dev

```bash
make web            # Vite :5173 (do root)
# OU:
cd web && pnpm dev
```

Vite tem proxy de `/api/*` pra `http://localhost:8000`. Login default: **admin@sentinelbr.io / admin1234**.

## Build / Lint

```bash
pnpm build      # tsc -b + vite build (output: dist/)
pnpm lint       # eslint .
pnpm preview    # serve dist/ pra teste
```

## Estrutura

```
web/
├── src/
│   ├── App.tsx                 # Router (react-router-dom v6)
│   ├── main.tsx                # entry + Tailwind import
│   ├── pages/
│   │   ├── LoginPage.tsx       # /login
│   │   ├── HostsPage.tsx       # / — lista + CRUD
│   │   ├── HostDetailPage.tsx  # /hosts/:id — vulns/yara/actions/events
│   │   ├── AlertsPage.tsx      # /alerts — filtros + ack/resolve
│   │   ├── CompliancePage.tsx  # /compliance — LGPD report
│   │   ├── KbPage.tsx          # /kb — MITRE ATT&CK PT-BR
│   │   ├── HuntingPage.tsx     # /hunting — queries pré-prontas
│   │   └── PurpleTeamPage.tsx  # /purple-team — cenários simulação
│   ├── components/
│   │   ├── AlertBadge.tsx      # contador no header (poll 5s)
│   │   ├── ActionsTab.tsx      # /hosts/:id ações de resposta
│   │   ├── EventsTab.tsx       # /hosts/:id eventos do Loki
│   │   ├── VulnerabilitiesTab.tsx
│   │   ├── YaraPanel.tsx       # botão "Escanear pasta…" + modal
│   │   └── ui/                 # primitives (button, input, etc)
│   ├── stores/
│   │   └── auth.ts             # Zustand: accessToken/refreshToken/user/org (persist localStorage)
│   └── lib/
│       └── api.ts              # wrapper fetch com Bearer + ApiError
├── public/
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

## Stack rationale

- **Vite** — HMR rápido, build com SWC
- **Tailwind** — utility-first; sem CSS modules nem styled-components
- **Zustand + persist** — auth state em localStorage, sobrevive a reload
- **react-router-dom v6** — `ProtectedRoute` checa `accessToken` no store
- **shadcn-ready** — primitives em `components/ui/`, mas usadas com moderação (a maioria das telas é Tailwind puro)

## Padrões

- Toda página tem auto-refresh via `setInterval` (5s default). Cancelado no unmount.
- Erros de API viram `ApiError` no `lib/api.ts`. 401 dispara logout automático.
- Cores: `zinc` (neutro) + `red/orange/yellow/green` (severidade). Suporte dark mode via `dark:` Tailwind.
- Texto em português brasileiro (sem traduções i18n por enquanto).

## CI

`pnpm build` + `pnpm lint` rodam no GitHub Actions a cada push. Falha bloqueia o merge.
