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

Pré-requisitos: macOS / Linux com `make`, `go`, `python3`, `node` (LTS), `pnpm`, `uv`, e Docker via OrbStack/Docker Desktop.

```bash
make setup     # instala deps de cada componente
make dev       # sobe stack (server + db + redis + loki + minio) via docker compose
make agent     # builda agente local
make web       # roda web em modo dev (vite)
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
