# CLAUDE.md

> **Antes de decidir qualquer coisa, leia `~/Documents/Dev/raiz/`** (PERFIL.md e o arquivo do assunto): é como o
> André trabalha. A decisão dele na conversa prevalece sobre qualquer documento; depois, atualize o documento.

Orientações para o Claude Code trabalhar neste repositório. Leia antes de agir.
Referência completa: [README.md](README.md) (visão geral, 580 linhas), [docs/](docs/README.md) (18 documentos, também
renderizados dentro do app em `/docs`), [server/README.md](server/README.md), [agent/README.md](agent/README.md),
[SECURITY.md](SECURITY.md).

## O que é

**SentinelBR** — plataforma open-source de **SIEM + LGPD** para servidores Linux de PMEs brasileiras, multi-tenant.
Três componentes num monorepo:

- **server/** — Python 3.12 + FastAPI + SQLAlchemy async + PostgreSQL 16 + Redis + Celery (worker e beat) + Loki.
  Detecção em tempo real (regras Sigma-style + YARA + OSV.dev), resposta automatizada (SOAR-lite), compliance LGPD,
  knowledge base MITRE ATT&CK em PT-BR. gRPC com mTLS na porta 9443 para os agentes.
- **agent/** — Go 1.25, cross-compilado para Linux/macOS/Windows (amd64 e arm64). Coleta logs (sshd, SELinux, AppArmor,
  arquivos), inventário de pacotes, heartbeat, YARA scanner, quarentena, firewall (nftables) e despacho de comandos.
- **web/** — React 19 + TypeScript + Vite, pnpm. 10 páginas lazy-loaded.

`proto/` define o contrato gRPC (regerar com `make proto`). `deploy/` tem o compose de dev e configs. `samples/` tem
fixtures de log e o **lab** (4 VMs vulneráveis no OrbStack).

## Como rodar / testar

```bash
make setup                  # uma vez: uv sync (server), pnpm install (web), go mod download (agent)
make dev                    # docker: postgres :5433, redis :6379, loki :3100, minio :9000/9001
make up                     # tudo em mprocs (server :8000, grpc :9443, web :5173, worker, beat) — ou start-dev.command
make dev-down / make down   # derruba

# o que o CI roda (.github/workflows/ci.yml):
cd agent  && go vet ./... && go build ./... && go test -race ./...     # 45 testes; CI em Linux, macOS e Windows + 5 cross-compiles
cd server && uv run ruff check . && uv run mypy app && uv run pytest   # mypy strict = 0 erros; 149 testes EXIGEM o `make dev` no ar
cd web    && pnpm lint && pnpm exec tsc -b && pnpm test                # ESLint, tipos e 31 testes (vitest + jsdom, sem servidor)
```

Login de dev: `admin@sentinelbr.io` / `admin1234` (seed: `make seed`). `start-dev.command` gera `.env-dev` com o JWT
secret local e liga `SENTINELBR_DEBUG` e `SENTINELBR_LAB_MODE`; nunca use esses valores em produção.

**mypy roda em `strict` e está em zero** — mantenha assim: stubs gerados (`grpc_server/pb`) e libs sem tipos já estão
tratados no `pyproject.toml`; código novo precisa de anotações completas.
**Web**: testes em `src/**/*.test.{ts,tsx}` com Vitest + Testing Library (`vitest.config.ts`, setup em `src/test/setup.ts`
que zera store, localStorage e `fetch` a cada teste). Toda chamada de rede é mockada — nenhum teste depende do servidor.

## Estrutura (o que importa)

- `server/app/` — `main.py` (FastAPI), `config.py` (settings `SENTINELBR_*`), `db.py`, `models/`, `schemas/`, `api/` (19 routers, 56 rotas),
  `services/`, `rules/` (detecção Sigma-style), `kb/` (MITRE PT-BR), `grpc_server/` (stubs em `pb/`, gerados), `workers/` (Celery), `scripts/seed.py`.
  `alembic/` — 17 migrations lineares. `tests/` — pytest-asyncio; o `conftest` recria o banco `sentinelbr_test` a cada sessão.
- `agent/cmd/sentinel-agent/` — CLI (cobra). `agent/internal/` — 23 packages; `pb/` é gerado. `yara-rules/` — 16 regras.
- `web/src/` — `pages/`, `components/`, `hooks/`, `stores/`, `lib/`. Build: `tsc -b && vite build`.

## Regras que não podem quebrar

- **Multi-tenant estrito**: toda query filtra por `org_id`; o JWT carrega a org. Há testes de isolamento — mantenha-os.
- **mTLS entre agente e servidor**: CA e certificados vivem em `server/data/` (gerados na primeira execução, ignorados pelo git).
  Nunca commite `.pem`, `.key`, `.crt`.
- **Segredos**: `SENTINELBR_JWT_SECRET` é obrigatório fora de debug (o `config.py` recusa subir com o valor padrão). `.env-dev` é local.
- **Ações automáticas são reversíveis e auditadas**: toda resposta (bloqueio de IP, quarentena, kill) gera `action` +
  `audit_log`. Não adicione ação sem trilha.
- **Contrato gRPC**: mudou `proto/*.proto` → `make proto` regenera Go e Python juntos; commite os dois lados.
- **Portabilidade do agente**: código específico de SO fica em arquivos `_linux.go` / `_darwin.go` / `_windows.go` com
  fallback; o CI compila nos três. Rode `gofmt` antes de commitar.
- Docs numeradas em `docs/01-…18-` são públicas e renderizadas no app; `docs/scratch/` e `docs/notes/` são ignoradas.

## Convenções

- Commits em português, imperativo, prefixo de área: `server:`, `agent:`, `web:`, `ui:`, `docs:`, `lab(fix):`, `ci:`.
- `main` é a única branch; sem tags ainda.
- Artefatos regeneráveis e ignorados: `agent/bin/`, `samples/labs/bin/`, `web/dist/`, `server/celerybeat-schedule*`,
  `proto/gen/`. Pode apagar à vontade.

## Runtimes e dependências: sempre na última versão

Regra do autor (2026-09): este projeto está em desenvolvimento e deve acompanhar as versões mais novas
de runtime (Python, Node, Go, Rust, Swift) e de bibliotecas. Ao começar a mexer aqui:

1. O Homebrew já foi conferido no início da sessão (hook `brew-check`). Se listou pacotes desatualizados,
   rode `brew upgrade && brew cleanup` antes de qualquer outra coisa.
2. Verifique se há versão nova do runtime e das dependências (`uv lock --upgrade`, `pnpm update`,
   `npm outdated`, `cargo update`, `go get -u ./...`, conforme o projeto) e atualize os pins:
   requirements/pyproject, package.json, Cargo.toml, go.mod, Dockerfile e a matriz do CI.
3. Rode a suíte completa e o lint; faça push e confira o CI. **Só commite atualização com tudo verde.**
4. Se uma dependência não acompanha a versão nova (ex.: sem wheel para o Python mais recente),
   fique na anterior e registre o motivo nesta seção, com data.
