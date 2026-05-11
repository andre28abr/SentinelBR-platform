# sentinelbr-server

API central do SentinelBR. Python 3.12+ FastAPI + Pydantic v2 + SQLAlchemy 2 async + Celery + Redis + Loki + PostgreSQL + grpcio (mTLS).

## Setup

```bash
make setup-server    # uv sync (root) — ou direto: cd server && uv sync
```

## Run

```bash
# requer postgres+redis+loki rodando (do root: `make dev`)
make server          # FastAPI :8000 (0.0.0.0)
make grpc            # gRPC mTLS :9443
make worker          # Celery worker
make beat            # Celery beat (detection cycle 30s, vuln schedule 1x/dia)

# bootstrap inicial — cria org default + admin:
uv run python -m app.scripts.seed
# OU override:
SEED_EMAIL=you@x.com SEED_PASSWORD=segredo SEED_ORG_SLUG=acme uv run python -m app.scripts.seed
```

Docs OpenAPI live em http://localhost:8000/docs depois do `make server`.

## Migrations

```bash
uv run alembic upgrade head             # aplica todas pendentes
uv run alembic revision --autogenerate -m "msg"  # gera nova (revisar antes de aplicar)
uv run alembic downgrade -1             # reverte 1
```

## Estrutura

```
server/
├── app/
│   ├── main.py                 # FastAPI app + routers
│   ├── config.py               # Pydantic Settings (env: SENTINELBR_*)
│   ├── db.py                   # engine async + SessionLocal
│   ├── api/                    # routers REST
│   │   ├── auth.py             # /api/v1/auth (login/refresh/me)
│   │   ├── hosts.py            # /api/v1/hosts CRUD + enrollment-token
│   │   ├── agents.py           # /api/v1/agents/enroll (público)
│   │   ├── events.py           # /api/v1/hosts/:id/events (query Loki)
│   │   ├── alerts.py           # /api/v1/alerts CRUD + ack/resolve
│   │   ├── actions.py          # /api/v1/actions (block_ip, quarantine_file)
│   │   ├── vulnerabilities.py  # /api/v1/hosts/:id/{packages,vulnerabilities,scan}
│   │   ├── yara.py             # /api/v1/hosts/:id/yara-scan
│   │   ├── audit.py            # /api/v1/audit-logs + /compliance/report
│   │   ├── kb.py               # /api/v1/kb/{techniques,hunting,playbooks}
│   │   ├── organizations.py    # /api/v1/organizations CRUD
│   │   └── deps.py             # CurrentUser, DbSession dependencies
│   ├── grpc_server/            # AgentService gRPC (mTLS): Enroll/Heartbeat/StreamEvents/SubmitInventory
│   ├── models/                 # SQLAlchemy: Organization, User, Host, Alert, Action, AuditLog,
│   │                           # HostPackage, HostVulnerability
│   ├── schemas/                # Pydantic request/response
│   ├── services/
│   │   ├── auth.py             # JWT bcrypt
│   │   ├── ca.py               # PKI própria (CA RSA 4096, certs RSA 2048)
│   │   ├── enrollment.py       # token one-shot + assinar client cert
│   │   ├── loki.py             # cliente httpx push/query
│   │   ├── osv.py              # cliente OSV.dev batch
│   │   ├── vuln_scan.py        # cross-ref inventory ↔ OSV → host_vulnerabilities
│   │   ├── policy.py           # alert → Action (block_ip, quarantine_file)
│   │   ├── pii.py              # masking LGPD (email/IPv4/CPF)
│   │   ├── audit.py            # append-only audit log
│   │   ├── kb.py               # loader YAML (techniques/hunting/playbooks)
│   │   └── rules/              # engine + evaluator + loader Sigma-style
│   ├── workers/                # Celery
│   │   ├── detect.py           # run_cycle a cada 30s
│   │   ├── vuln.py             # scan_host (OSV)
│   │   ├── yara_schedule.py    # cria Action(run_yara_scan) periódico
│   │   └── retention.py        # cleanup audit_logs (LGPD Art. 16)
│   ├── rules/                  # 8 YAML rules (ssh_*, yara_*, *_denials_burst)
│   ├── kb/data/                # 8 techniques + 6 hunting + 3 playbooks (YAML)
│   └── scripts/seed.py         # bootstrap org default + admin
├── tests/                      # pytest async, 100+ tests
├── alembic/                    # migrations
├── data/                       # CA + server cert (gitignored)
└── pyproject.toml              # uv + ruff
```

## Testes

```bash
uv run pytest -q          # full suite
uv run pytest -k tenant   # subset
uv run pytest -x          # stop on first failure
uv run ruff check .       # lint
```

Tests usam DB `sentinelbr_test` criado/destruído por fixture. Loki/Redis mockados onde necessário.

## Endpoints principais

Todos requerem `Authorization: Bearer <jwt>`, exceto `/auth/login`, `/auth/refresh`, `/agents/enroll`, `/health`.

| Método | Path | O quê |
|--------|------|-------|
| POST | `/api/v1/auth/login` | email+senha → access+refresh JWT |
| GET | `/api/v1/auth/me` | usuário atual + org (nested) |
| GET/POST | `/api/v1/hosts` | listar/criar (filtrado por org) |
| POST | `/api/v1/hosts/:id/enrollment-token` | gera token one-shot pro agente |
| POST | `/api/v1/agents/enroll` | (público) agente troca token por cert mTLS |
| GET | `/api/v1/hosts/:id/events` | query Loki (filtros: source, hours, mask_pii) |
| GET/PATCH | `/api/v1/alerts` | listar / ack / resolve |
| GET | `/api/v1/alerts/count` | badge counters (open, total) |
| GET/PATCH/DELETE | `/api/v1/actions/:id` | listar / revert (gera unblock_ip) |
| GET | `/api/v1/hosts/:id/{packages,vulnerabilities}` | inventário + CVEs |
| POST | `/api/v1/hosts/:id/yara-scan` | dispara YARA scan async |
| GET | `/api/v1/compliance/report` | métricas LGPD do período |
| GET | `/api/v1/kb/{techniques,hunting,playbooks}` | KB MITRE ATT&CK |
| GET/POST/PUT | `/api/v1/organizations` | tenants |

## Stack rationale rápido

- **uv** em vez de pip/poetry — mais rápido, lock file determinístico
- **Pydantic v2** — performance + better DX (model_validate)
- **asyncpg** direto em vez de psycopg — async nativo
- **Loki** em vez de Elasticsearch — barato, labels low-cardinality (host_id, source, severity), JSON na linha
- **OSV.dev** em vez de NVD — free, sem API key, batch endpoint
