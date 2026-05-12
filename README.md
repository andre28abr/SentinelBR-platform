# SentinelBR

[![ci](https://github.com/andre28abr/SentinelBR-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/andre28abr/SentinelBR-platform/actions/workflows/ci.yml)

Plataforma open-source de segurança para servidores Linux com foco em SMBs brasileiras: SIEM + Firewall + SELinux/AppArmor + Resposta a Incidentes + Vulnerability Management + Compliance LGPD + Anti-malware YARA + Threat KB em português + Multi-tenancy.

```
sentinelbr-platform/
├── server/      # API central — Python 3.12+ FastAPI + Celery + PostgreSQL + Loki + Prometheus /metrics
├── agent/       # Coletor — Go 1.25, 1 binário por OS (Linux/macOS dev/Windows)
├── web/         # UI — React 19 + TS + Vite 8 + Tailwind 4 + Radix UI
├── proto/       # Contratos gRPC compartilhados (mTLS)
├── deploy/      # Docker Compose (dev) + Helm (prod, parcial)
├── docs/        # Documentação publicada (arquitetura, deployment, glossário, demo mode)
├── samples/     # Fixtures de log + lab de 6 VMs vulneráveis
│   └── labs/    # `make lab-up` cria VMs Debian/Ubuntu/Fedora/Rocky/Alpine/vuln com vulns plantadas
└── .github/     # CI matriz multi-OS (Linux/macOS/Windows)
```

## O que faz

- **Coleta**: agente lê `/var/log/auth.log` (sshd), denials SELinux/AppArmor, inventário de pacotes (apt/dnf/rpm). gRPC mTLS pro server.
- **Detecção**: 8 regras Sigma-style (brute-force SSH, root login, MAC denials, YARA matches). Avaliador nativo Python, ciclo de 30s.
- **Resposta**: policy auto-cria `block_ip` em alertas SSH (executa via nft/firewall-cmd) e `quarantine_file` em YARA crítico.
- **Vuln mgmt**: cross-ref de pacotes com OSV.dev (free, sem auth). Risk score 0-100 por host.
- **Anti-malware (YARA)**: scan manual (botão UI), scheduled (Celery beat), filewatcher (fsnotify), quarentena automática.
- **Compliance LGPD**: audit log append-only (Art. 37), retenção configurável (Art. 16), PII masking opcional em events.
- **Threat KB**: 12 técnicas MITRE ATT&CK em PT-BR com mitigações + 6 hunting queries + 3 purple team playbooks.
- **Multi-tenancy**: Org → User RBAC. Cross-org isolation enforced via filtros em todos os endpoints (404 leakage-safe).
- **Lab Mode opt-in** (`SENTINELBR_LAB_MODE=true`): aba `/lab` na UI controla VMs OrbStack do demo (start/stop/atacar/reset) — útil pra recordings/portfolio.
- **Docs in-app**: aba `/docs` renderiza markdown do diretório `docs/` com sidebar TOC.

## Quickstart (dev)

Pré-requisitos macOS: `brew install go python@3.12 node pnpm uv mprocs jq yara` + OrbStack (ou Docker Desktop).

**Mais simples — duplo-clique:**
- `start-dev.command` — sobe stack docker + server + gRPC + web + worker + beat em mprocs, abre o browser
- `stop-dev.command` — mata tudo

**Terminal:**
```bash
make setup     # uma vez: deps de cada componente
make up        # sobe tudo via mprocs

# OU targets individuais (cada um num terminal):
make dev       # docker stack (postgres :5433, redis, loki, minio)
make server    # FastAPI :8000 (escuta em 0.0.0.0 pra VMs do lab alcançarem)
make grpc      # gRPC mTLS :9443
make web       # Vite :5173
make worker    # Celery worker
make beat      # Celery beat (rule cycle 30s, vuln scheduler)
```

Login default: **admin@sentinelbr.io / admin1234** (criado por `cd server && uv run python -m app.scripts.seed`).

## Lab — VMs vulneráveis pra testar tudo end-to-end

```bash
make lab-build-agent   # cross-compila agente pra Linux/arm64
make lab-up            # cria 6 VMs no OrbStack + planta vulns (~10min primeira vez)
make lab-status        # status das VMs + DB
make lab-attack        # re-planta vulns (renova alertas)
make lab-down          # destrói tudo
```

As 6 VMs cobrem cenários diferentes:

| VM | Cenário | Detalhes |
|---|---|---|
| `lab-debian-11` | Brute-force SSH + auto-block | apt, systemd |
| `lab-ubuntu-22` | Webshell + auto-quarantine + LGPD/PII | apt, systemd |
| `lab-fedora`    | Hardening showcase (SELinux, auditd) | dnf, systemd |
| `lab-rocky-9`   | CVE/vulnerability management (OSV) | dnf + EPEL, systemd |
| `lab-alpine-3`  | Container/edge (musl + OpenRC) | apk, OpenRC |
| `lab-vuln`      | Buffet de ataques (estilo Metasploitable) | apt, multi-vetor |

Cada VM ganha: webshell + brute-force injetado + pacotes com CVEs reais + EICAR + dropper bash + reverse shell Python + cron backdoor. Detalhes individuais em [samples/labs/scenarios/](samples/labs/scenarios/) e [samples/labs/EXPECTED.md](samples/labs/EXPECTED.md).

## Páginas da UI

| Rota | O que tem |
|------|-----------|
| `/` | Lista de hosts + enrollment + heartbeat status |
| `/hosts/:id` | Detalhe do host: Vulnerabilidades (CVE/OSV), Anti-malware (YARA scan), Ações (auto-block/quarantine), Eventos |
| `/alerts` | Alertas com filtros (status/severity/host), ack/resolve |
| `/compliance` | Relatório LGPD: MTTR, logins, hosts/alerts/actions, audit log |
| `/kb` | MITRE ATT&CK PT-BR — 12 técnicas com mitigações |
| `/hunting` | 6 queries pré-prontas pra investigação |
| `/purple-team` | 3 cenários de simulação ataque + detecção esperada |
| `/docs` | Documentação completa renderizada (sidebar TOC + markdown) |
| `/lab` | (só com `SENTINELBR_LAB_MODE=true`) controle das VMs do demo + reset |

## Componentes

- **[server/](server/README.md)** — FastAPI + Pydantic v2 + SQLAlchemy 2 async + Celery + asyncpg + httpx (OSV/Loki) + grpcio (mTLS) + slowapi (rate limit) + structlog + Prometheus.
- **[agent/](agent/README.md)** — Go com interfaces por OS (`PackageManager`, `FirewallExecutor`, `MACSystem`). Cross-compila pra Linux/Windows/macOS.
- **[web/](web/README.md)** — Vite 8 + React 19 + TypeScript strict + Tailwind 4 + Radix UI + Zustand + Recharts. SPA pura com lazy load por rota.

## Arquitetura

```
┌──────────────┐ logs/inventory  ┌──────────────┐
│   Agente Go  │ ───stream──────▶│   FastAPI    │
│ (mTLS gRPC)  │ ◀──commands──── │   :8000      │
└──────────────┘                  └──────┬───────┘
       ▲                                 │
       │ /var/log/auth.log               ├─▶ PostgreSQL (state)
       │ rpm -qa / dpkg-query            ├─▶ Loki :3100 (eventos)
       │ yara scan                       ├─▶ Redis (Celery broker)
       │ nft/firewall-cmd                └─▶ OSV.dev (CVE cross-ref)
       ▼
   Host Linux
```

mTLS gRPC com CA própria (gerada no `make grpc`). Cada agente tem cert assinado com CN = host_id.

## Configuração via env vars (prefixo `SENTINELBR_`)

| Var | Default | Notas |
|-----|---------|-------|
| `JWT_SECRET` | (default barra boot em prod) | obrigatório se DEBUG=false |
| `DEBUG` | `false` | dev local: `true` (relaxa asserts) |
| `DATABASE_URL` | postgresql+asyncpg://… | dev usa porta 5433 |
| `REDIS_URL` | redis://localhost:6379/0 | broker do Celery |
| `LOKI_URL` | http://localhost:3100 | armazenamento de events |
| `CORS_ALLOWED_ORIGINS` | http://localhost:5173 | em prod: lista de FQDNs |
| `ACCESS_TOKEN_MINUTES` | `60` | reduzir em prod (~15-30min) |
| `REFRESH_TOKEN_DAYS` | `7` | em cookie httpOnly samesite=lax |
| `GRPC_PUBLIC_ENDPOINT` | localhost:9443 | que endereço o agente vê |
| `SERVER_CERT_SAN` | localhost,sentinelbr-server | SAN do cert mTLS |
| `AUDIT_RETENTION_DAYS` | `180` | LGPD Art. 16 |
| `YARA_SCHEDULED_PATHS` | /var/www,/tmp,/home | scan diário |
| `YARA_SCHEDULED_INTERVAL_SECONDS` | `86400` | 24h |
| `RKHUNTER_SCHEDULED_INTERVAL_SECONDS` | `86400` | 0 desabilita |
| `CHKROOTKIT_SCHEDULED_INTERVAL_SECONDS` | `86400` | 0 desabilita |
| `AIDE_SCHEDULED_INTERVAL_SECONDS` | `86400` | 0 desabilita |
| `LYNIS_SCHEDULED_INTERVAL_SECONDS` | `604800` | 7d (semanal) |
| `LAB_MODE` | `false` | habilita endpoints/UI do `/lab` (NUNCA em prod) |
| `LAB_ORB_BINARY` | `orb` | path do `orb` CLI (OrbStack) |
| `LAB_SCRIPTS_DIR` | `<repo>/samples/labs` | onde mora `attack.sh` |

Endpoints de saúde:
- `GET /api/v1/health` — status JSON pra readiness probe
- `GET /metrics` — Prometheus (latency, counts por endpoint)

## Status

🟢 **Fases 1-11 + hardening completo (Fases 2-9 do plano de auditoria).** 149 testes server, agent suite verde, CI multi-OS + security scans (govulncheck/pip-audit/Trivy). Documentação completa em [docs/](docs/) (também renderizada in-app em `/docs`).

Roadmap fechado:
- Fase 1: Enrollment + heartbeat mTLS
- Fase 2: Log collector + event streaming SSH
- Fase 3: Detection engine + alertas Sigma-style
- Fase 4: Auto-block on alert (IR + firewall real)
- Fase 5: SELinux/AppArmor parsers + MAC rules
- Fase 6: Vulnerability mgmt via OSV.dev
- Fase 7: Compliance LGPD (audit log + report + retenção)
- Fase 8: YARA scanner + 5 starter rules
- Fase 8.5: YARA manual (UI) + scheduled + filewatcher + auto-quarantine
- Fase 9: Threat KB MITRE ATT&CK PT-BR + Hunting + Purple Team
- Fase 10: Multi-tenancy (Org → User RBAC) com tenant isolation
- Fase H1-H8: Hardening tools (fail2ban, firewall write, rkhunter, chkrootkit, lynis, AIDE, auditd, SELinux/AppArmor)
- Hardening pos-auditoria: JWT assert + rate limit + httpOnly cookie + RBAC + indices DB + N+1 + agent recover/keepalive + lazy loading + Prometheus + structlog + Trivy/pip-audit/govulncheck no CI
- Fase 11: Lab Mode (opt-in via env), VMs especializadas (+ Rocky 9 + Alpine 3), 8 YARA rules novas (Dropper/ReverseShell/Persistence) + EICAR, 4 técnicas MITRE PT-BR novas, aba `/docs` em-app com react-markdown

## Licença

[AGPL-3.0](LICENSE) — protege contra "AWS effect" (cloud providers fechando forks como SaaS sem contribuir de volta). Se você usa o SentinelBR como serviço de rede, precisa abrir as modificações.

## Autor

Projeto pessoal de [André Souza](https://github.com/andre28abr) — desenvolvido como portfólio explorando arquitetura SIEM, mTLS, multi-tenancy, agentes Go cross-platform e UX de plataformas de segurança.
