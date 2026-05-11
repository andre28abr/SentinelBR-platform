# SentinelBR

[![ci](https://github.com/andre28abr/SentinelBR-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/andre28abr/SentinelBR-platform/actions/workflows/ci.yml)


> Plataforma open-source de segurança para servidores Linux (e Windows na fase 4), com foco em SMBs brasileiras: SIEM + Firewall + SELinux/AppArmor + Resposta a Incidentes + Compliance LGPD.

Monorepo. 3 componentes principais + docs + deploy.

```
sentinelbr-platform/
├── server/   # API central — Python 3.12 + FastAPI + Celery (ADR-001, 015)
├── agent/    # Coletor — Go 1.23 (ADR-002), 1 binário por OS
├── web/      # UI — React 18 + TS + Vite + Tailwind + shadcn (ADR-007/008/009)
├── proto/    # Contratos gRPC compartilhados (ADR-005)
├── deploy/   # Docker Compose + Helm (ADR-011)
├── docs/     # 17 documentos de arquitetura (ler começando pelo README.md de docs/)
└── .github/  # CI matriz multi-OS
```

## Quickstart (dev)

Pré-requisitos: macOS / Linux com `make`, `go`, `python3`, `node` (LTS), `pnpm`, `uv`, `mprocs`, e Docker via OrbStack/Docker Desktop.

**Mais simples (macOS, double-click no Finder):**
- `start-dev.command` → sobe docker + server + gRPC + web numa única janela com mprocs
- `stop-dev.command` → mata tudo

**Power user (terminal):**
```bash
make setup     # instala deps de cada componente (uma vez)
make up        # sobe stack docker + server/gRPC/web em paralelo via mprocs
make down      # derruba tudo
```

**Targets individuais** (se quiser cada um num terminal):
```bash
make dev       # só docker stack (postgres/redis/loki/minio)
make server    # FastAPI :8000
make grpc      # gRPC mTLS :9443
make web       # Vite :5173
make agent     # builda agente local
```

## Componentes

### server/
FastAPI + Pydantic v2 + SQLAlchemy + Celery + asyncpg. Veja `server/README.md`.

### agent/
Go com **interfaces por OS** (`PackageManager`, `FirewallExecutor`, `MACSystem`) — adicionar OS = implementar interfaces (ver `docs/15-suporte-multi-os.md`). Cross-compila para Linux/Windows/macOS via `make agent-cross`.

### web/
Vite + React + TypeScript strict + Tailwind + shadcn/ui. SPA pura, consome a API do server.

## Documentação

Toda a especificação está em `docs/` (17 arquivos). Comece pelo [README de docs](docs/README.md).

## Status

🟡 **Em desenvolvimento ativo** — sprint 0 (auth + CRUD de hosts) em andamento. Roadmap completo em `docs/07-roadmap-detalhado.md`.

## Licença

[AGPL-3.0](LICENSE) — protege contra "AWS effect" (cloud providers fechando forks como SaaS sem contribuir de volta). Se você usa o SentinelBR como serviço de rede, precisa abrir as modificações. Ver [ADR-018](docs/08-stack-decisions.md).
