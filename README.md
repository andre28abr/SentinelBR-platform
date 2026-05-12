# SentinelBR — Plataforma open-source de SIEM + LGPD para Linux SMB

> Plataforma de segurança para servidores Linux pensada para a realidade brasileira: **SIEM** com detecção de ameaças em tempo real, **gestão de Firewall**, **SELinux/AppArmor**, **resposta automatizada a incidentes**, **vulnerability management** via OSV.dev, **anti-malware YARA**, **threat knowledge base em PT-BR** (MITRE ATT&CK traduzido) e **compliance LGPD** nativa — multi-tenant, com agente Go cross-compilado e UI React lazy-loaded.

[![ci](https://github.com/andre28abr/SentinelBR-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/andre28abr/SentinelBR-platform/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-fases%201--11%20completas-success)
![Python](https://img.shields.io/badge/python-3.12+-blue)
![Go](https://img.shields.io/badge/go-1.25-00add8)
![React](https://img.shields.io/badge/react-19-61dafb)
![Tests](https://img.shields.io/badge/tests-149%20server%20+%20Go%20suite-success)
![License](https://img.shields.io/badge/license-AGPL--3.0-orange)

---

## Sumário

1. [TL;DR](#tldr)
2. [O domínio em 60 segundos](#o-domínio-em-60-segundos)
3. [Por que essa plataforma existe](#por-que-essa-plataforma-existe)
4. [O que faz (módulos)](#o-que-faz-módulos)
5. [Arquitetura](#arquitetura)
6. [Stack completa & motivações](#stack-completa--motivações)
7. [Decisões arquiteturais notáveis](#decisões-arquiteturais-notáveis)
8. [Estrutura do projeto](#estrutura-do-projeto)
9. [Quickstart (dev)](#quickstart-dev)
10. [Lab — VMs vulneráveis pra testar](#lab--vms-vulneráveis-pra-testar-tudo-end-to-end)
11. [Páginas da UI](#páginas-da-ui)
12. [Configuração via env vars](#configuração-via-env-vars-prefixo-sentinelbr_)
13. [Segurança em camadas](#segurança-em-camadas)
14. [Comparação com mercado](#comparação-com-mercado)
15. [Métricas do código](#métricas-do-código)
16. [Roadmap](#roadmap)
17. [Documentação interna](#documentação-interna)
18. [Outro projeto do autor](#outro-projeto-do-autor)
19. [Licença](#licença)
20. [Autor](#autor)

---

## TL;DR

**O que é:** SIEM open-source self-hosted pensado pra PMEs brasileiras que precisam de segurança séria sem orçamento de multinacional nem dependência de SaaS estrangeiro.

**O que faz, em uma frase:** coleta logs e inventário de servidores Linux via agente Go, detecta ameaças em tempo real com regras Sigma-style + YARA + cross-ref OSV, responde automaticamente (block IP, quarantine file), e mantém audit trail LGPD-compliant — tudo em português, com UI moderna e multi-tenant.

**O que diferencia:**
- **LGPD nativa** (Art. 37 audit append-only, Art. 16 retenção configurável, PII masking opcional em events) — não é "compliance vendido depois".
- **Threat KB em PT-BR**: 12 técnicas MITRE ATT&CK traduzidas com summary leigo (`what_happened` / `should_worry` / `what_to_do` / `jargon`) + 6 hunting queries + 3 purple team playbooks.
- **mTLS gRPC nativo** entre agente e servidor, com CA própria e CN = host_id (não é "JWT em REST").
- **Multi-tenancy estrito**: cross-org leakage retorna 404 (não 403) em todos os endpoints — não vaza existência.
- **Lab de purple team integrado**: 6 VMs OrbStack propositalmente vulneráveis (Debian, Ubuntu, Fedora, Rocky, Alpine, vuln-lab) com cenários reais + botão "Resetar demo" na UI.
- **~19.5k LOC**, **149 testes server**, **55 rotas REST**, **17 migrations Alembic**, **16 regras YARA**, **23 packages no agent**, **CI matriz Linux/macOS/Windows verde**.

**Stack principal:** Python 3.12 / FastAPI / Pydantic v2 / SQLAlchemy 2 async / Celery + Redis · Go 1.25 (agente cross-platform) · React 19 / Vite 8 / Tailwind 4 / Radix UI · PostgreSQL 16 · Loki 3 · gRPC + mTLS · YARA · OSV.dev · structlog + Prometheus · Docker / OrbStack.

---

## O domínio em 60 segundos

Pra quem não vive de Blue Team — glossário rápido pra entender as decisões técnicas:

| Termo | Significado |
|---|---|
| **SIEM** | Security Information & Event Management. Plataforma que centraliza logs de várias fontes, correlaciona, detecta anomalias e gera alertas. Ex: Splunk, Wazuh, ELK Stack. |
| **SOC** | Security Operations Center. Equipe (ou serviço) que monitora SIEM 24×7 e responde a incidentes. |
| **SOAR** | Security Orchestration, Automation & Response. Camada que automatiza a resposta (block IP, quarentena, isolar host). |
| **MITRE ATT&CK** | Catálogo público de técnicas de ataque organizado por *tática* (Reconnaissance → Initial Access → Execution → Persistence → ...). Padrão de mercado pra "esse alerta significa que estágio do ataque?". |
| **IOC** | Indicator of Compromise. Sinal de que algo ruim aconteceu (IP malicioso, hash de arquivo, padrão em log). |
| **IR** | Incident Response. Processo de reagir quando um incidente é detectado. |
| **YARA** | Linguagem/ferramenta pra escrever regras que casam padrões em arquivos (texto, binários). Usado pra detectar webshell, miner, ransomware, etc. |
| **Sigma rules** | Formato YAML aberto pra escrever regras de detecção SIEM portáveis entre Splunk/Elastic/etc. SentinelBR usa um avaliador Sigma-style nativo. |
| **mTLS** | Mutual TLS. Ambos os lados (cliente E servidor) provam identidade com cert. Agente do SentinelBR tem CN = host_id no cert. |
| **DPO** | Data Protection Officer / Encarregado de Dados (LGPD Art. 41). Responsável pela conformidade com a Lei Geral de Proteção de Dados. |
| **LGPD** | Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018). Equivalente brasileiro do GDPR europeu. Exige audit log, retenção limitada, base legal pra tratamento. |
| **threat hunting** | Investigação proativa em logs procurando ameaças que escaparam dos alertas automáticos. |
| **purple team** | Exercício onde Red Team (atacante) e Blue Team (defensor) trabalham juntos — Red ataca, Blue valida que detectou. SentinelBR tem 3 playbooks. |
| **Multi-tenancy** | Várias organizações (tenants) compartilhando a mesma instância, com isolamento estrito por `org_id` em todas as queries. |

Por que isso importa: muita decisão do projeto reflete a realidade do operador brasileiro. KB em PT-BR não é tradução automática — é linguagem leiga ("o que aconteceu? deve me preocupar? o que faço?"). Audit log append-only não é capricho — é **LGPD Art. 37** (registro das operações de tratamento). mTLS no agente não é flex — é defesa em profundidade contra agentes sequestrados.

---

## Por que essa plataforma existe

Cenário típico de PME brasileira (10-200 servidores):

1. **SIEM enterprise é caro**: Splunk cobra por volume de log; orçamento de R$50k+/ano só pra licença.
2. **Wazuh é a alternativa óbvia**, mas: documentação em inglês, conceitos sem tradução cultural, threat KB em jargão técnico, sem suporte PT-BR oficial.
3. **LGPD virou obrigação** (multa até 2% do faturamento, máx R$50M). Empresas têm DPO, mas faltam **ferramentas operacionais** que entreguem audit trail + retenção + relatório de compliance prontos.
4. **Equipes pequenas não têm SOC 24×7** — precisam de **resposta automática** que confiavelmente bloqueia brute-force, quarentena webshell, etc.
5. **Stack técnica heterogênea**: misturam Debian, Ubuntu, Fedora, Rocky (RHEL clone), Alpine em containers. Agentes precisam ser um único binário cross-compilado.

A SentinelBR endereça isso: open-source, **PT-BR nativo**, **LGPD-first**, footprint pequeno (~150MB RAM por server + agente <30MB), agente single-binary, e UI moderna que um analista júnior consegue operar.

---

## O que faz (módulos)

- **Coleta** (agente Go): lê `/var/log/auth.log` (sshd), denials SELinux/AppArmor, inventário de pacotes (apt/dnf/rpm/apk), heartbeat 30s, detecção de ferramentas locais (fail2ban, rkhunter, chkrootkit, lynis, AIDE, auditd). Stream gRPC mTLS pro server.
- **Detecção** (server): 8 regras Sigma-style nativas (brute-force SSH, root login, user enumeration, MAC denials, YARA matches críticos + burst). Avaliador Python com `filter + group_by + threshold`, ciclo Celery beat a cada 30s, dedup via `UNIQUE(host, rule, dedup_key)`.
- **Resposta automatizada (SOAR-lite)**: policy YAML auto-cria `block_ip` em alertas SSH (executa via nft/ufw/firewall-cmd no host alvo) e `quarantine_file` em YARA crítico (move pra `/var/sentinelbr/quarantine/`).
- **Vulnerability mgmt**: cross-ref de pacotes (apt/dnf/rpm) com OSV.dev (free, sem auth). Risk score 0-100 por host com peso por severidade CVSS, scan async via Celery, página dedicada com filtros.
- **Anti-malware (YARA)**: 16 regras nativas (WebshellPHP, CryptoMiner, Dropper, ReverseShell, Persistence, EICAR, ransomware patterns). Scan manual via UI, scheduled (Celery beat 1×/dia em `/var/www`, `/tmp`, `/home`), filewatcher (fsnotify), auto-quarantine em severity critical.
- **Compliance LGPD**: audit log append-only (Art. 37), retenção configurável (`SENTINELBR_AUDIT_RETENTION_DAYS`, default 180d — Art. 16), PII masking opcional em events, relatório PDF de compliance com MTTR + logins + ações + audit trail.
- **Hardening tools (Tier 1+2)**: detecção e operação de fail2ban, rkhunter, chkrootkit, lynis, AIDE, auditd, SELinux, AppArmor. UI dedicada por ferramenta — scan/audit on-demand + scheduled.
- **Threat KB**: 12 técnicas MITRE ATT&CK em PT-BR com mitigações + `summary_simple` em linguagem leiga, 6 hunting queries pré-prontas, 3 purple team playbooks.
- **Multi-tenancy**: Org → User RBAC (admin / operator / viewer). Cross-org isolation enforced via filtros em todos os endpoints — leakage retorna 404 (não 403, pra não vazar existência).
- **Lab Mode opt-in** (`SENTINELBR_LAB_MODE=true`): aba `/lab` na UI controla 6 VMs OrbStack do demo (start/stop/atacar/reset) — útil pra recordings/portfolio. Banner amber na LoginPage avisa que é demo.
- **Docs in-app**: aba `/docs` renderiza os 18 markdowns de `docs/` com sidebar TOC (react-markdown + remark-gfm + syntax highlighter).

---

## Arquitetura

```
┌──────────────────────────┐  logs/inventory       ┌────────────────────────────┐
│   Agente Go (host)       │ ──stream────────────▶ │   FastAPI :8000 (server)   │
│                          │                       │                            │
│ • sshd parser            │ ◀──commands────────── │ • Routers REST (55)        │
│ • SELinux/AppArmor parser│      (block_ip,       │ • gRPC :9443 (mTLS)        │
│ • Inventory (apt/dnf/    │       quarantine_file)│ • Celery beat (rules 30s)  │
│   rpm/apk)               │                       │ • OSV.dev cross-ref        │
│ • YARA scan + filewatch  │                       │ • Loki push (events)       │
│ • Tools detect           │                       │ • Audit log append-only    │
│ • Firewall ops           │                       │                            │
└──────────────────────────┘                       └──────────────┬─────────────┘
                                                                  │
                              ┌──────────────────────────────────┼──────────────┐
                              ▼                                  ▼              ▼
                       ┌──────────────┐                  ┌──────────────┐ ┌──────────┐
                       │ PostgreSQL   │                  │ Loki :3100   │ │ Redis    │
                       │ (state, audit│                  │ (events,     │ │ (Celery  │
                       │  hosts, KB)  │                  │  retenção)   │ │  broker) │
                       └──────────────┘                  └──────────────┘ └──────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ React 19 UI  │
                       │ :5173 (Vite) │
                       │ lazy-loaded  │
                       └──────────────┘
```

**Fluxo típico de detecção** (brute-force SSH):
1. Agente tail-F em `/var/log/auth.log`, parser regex extrai `Failed password for X from IP`.
2. Batch de 50 events → `StreamEvents` gRPC mTLS → server.
3. Server valida CN do cert == host_id (anti-impersonation), grava batch no Loki.
4. Celery beat (30s) roda `rules.engine`: filter por `event.source=sshd` + group_by `source.ip` + threshold ≥5/5min.
5. Alert criado no PostgreSQL (`UNIQUE(host, rule, dedup_key)` previne duplicação).
6. Policy detecta alert SSH severity ≥high → cria `Action(type=block_ip, target=<ip>)`.
7. gRPC `Commands` envia pro agente do host. Agente executa `nft` / `ufw` / `firewall-cmd`.
8. UI faz polling de 5s e mostra o alert + ação executada.

---

## Stack completa & motivações

### Server (Python)
- **FastAPI** + **Pydantic v2**: tipagem estrita, OpenAPI auto-gerado, validação centralizada. Pydantic v2 (Rust-backed) eliminou bottleneck de serialização.
- **SQLAlchemy 2 async** + **asyncpg**: I/O concorrente sem GIL bloat. `asyncio.gather` paraleliza queries dependentes (compliance report tinha 14 sequential awaits → 1 round).
- **Celery + Redis**: rule engine roda a cada 30s, vuln scheduler 1×/dia, tools_schedule (rkhunter/chkrootkit/aide/lynis) configurável por env.
- **structlog** (JSON em prod, Console em dev) + **RequestIDMiddleware** + **prometheus-fastapi-instrumentator** (`/metrics`).
- **slowapi**: rate limit em `/auth/login` (10/min) e `/agents/enroll` (20/min).
- **grpcio** + **mTLS**: CA própria gerada na primeira execução, cert servidor + cert por agente assinados com `CN=host_id`.

### Agent (Go 1.25)
- **Cross-compile single binary** pra `linux/amd64`, `linux/arm64`, `darwin/arm64`, `windows/amd64` via matriz CI.
- **Interfaces por OS**: `PackageManager` (apt/dnf/rpm/apk), `FirewallExecutor` (nftables/ufw/firewalld), `MACSystem` (SELinux/AppArmor), `OSDetector`. Implementações concretas por OS, fácil portar.
- **fsnotify** pra filewatcher YARA real-time, **errgroup** pra orquestrar heartbeat + stream em paralelo, **gRPC keepalive** (Time=30s, Timeout=10s) anti-NAT-drop.
- **`defer recover()` em goroutines críticas** + **timeout coreutils** wrapping em scans externos (chkrootkit travava em I/O).

### Frontend (React)
- **React 19** + **Vite 8** + **TypeScript strict** + **Tailwind 4** + **Radix UI**.
- **Lazy load por rota**: bundle inicial 243kb gzip (era 782kb antes); CompliancePage (com Recharts) é chunk separado de 104kb.
- **Zustand** pra auth state, `localStorage` pra persistência de sessão.
- **usePolling visibility-aware** (pausa em `document.hidden`, AbortController por tick) aplicado em EventsTab, ActionsTab, AlertBadge, ScanProgressBadge.

### Integrações externas
- **OSV.dev** (free, sem auth) pra cross-ref de pacotes contra CVEs.
- **Loki 3.2** pra eventos (TSDB + retenção natural).
- **PostgreSQL 16** pra state (hosts, alerts, actions, audit_logs).
- **OrbStack** (macOS) pro lab de 6 VMs.

---

## Decisões arquiteturais notáveis

### 1. mTLS gRPC entre agente e server (não REST + JWT)
Agente é cliente *no host do usuário*. Pode ser sequestrado. Cert mTLS com `CN=host_id` permite ao server **rejeitar agentes desconhecidos no nível da conexão**, antes mesmo da mensagem chegar. JWT em REST permitiria replay; mTLS não.

### 2. Multi-tenancy: cross-org leakage retorna 404 (não 403)
403 vaza existência (`existe mas você não pode ver`). 404 mantém o atacante no escuro (`não existe`). Pequeno detalhe, mas padrão correto em multi-tenant SaaS.

### 3. Audit log append-only (LGPD Art. 37)
Tabela `audit_logs` sem UPDATE/DELETE no código. Migrations criam só ADD. Retenção via TTL configurável (`SENTINELBR_AUDIT_RETENTION_DAYS`, default 180d). Conforma com Art. 16 (manter pelo tempo necessário) E Art. 37 (registrar operações de tratamento).

### 4. Loki para events (não Elasticsearch)
Loki indexa só labels (low cardinality), payload fica em chunks comprimidos. Custo de storage ~10× menor que Elasticsearch pra mesmo volume. Trade-off: queries full-text mais lentas — aceito porque eventos de SIEM são consultados por labels (host, source, severity), não por texto livre.

### 5. PostgreSQL + JSONB (não MongoDB)
Eventos têm shape estável; estado tem FKs (host → alert → action). PostgreSQL ganha em transações ACID + JOIN performance + CHECK constraints (severity/status enum no DB). JSONB em `context` (event metadata) cobre o caso flexível sem trocar o DB.

### 6. Agente em Go (não Python)
Single binary cross-compilado (`GOOS=linux GOARCH=arm64`), sem runtime pra instalar, footprint <30MB. Python no agente exigiria embutir interpretador OU depender de Python local — frágil em containers minimalistas (Alpine sem Python).

### 7. Celery (não asyncio tasks puras)
Rule engine + vuln scheduler + scans hardening rodam em workers separados do API server. Crash no scan não derruba a API. Beat schedule documentado, observável via Flower opcional.

### 8. YARA (não regex próprio) pra anti-malware
YARA tem ecossistema enorme (regras públicas + privadas), formato padronizado, e o `meta` (severity/family/mitre) é lido pelo agente pra rotular alertas. Reinventar regex seria perda de tempo + perda de compatibilidade.

### 9. OSV.dev (não NVD direto)
OSV.dev agrega NVD + GitHub Security Advisories + ecosystem-specific (Debian, Ubuntu, Rocky security trackers). API JSON limpa, sem chave, sem rate limit agressivo. NVD direto exigiria parsing CVE JSON pesado.

### 10. AGPL-3.0 (não MIT)
Proteção contra "AWS effect" — cloud providers fechando o fork como SaaS sem contribuir de volta. AGPL exige que serviço-de-rede também abra modificações. Mantém contribuições no ecossistema open-source.

### 11. KB MITRE PT-BR com `summary_simple` em linguagem leiga
Cada técnica tem `what_happened`, `should_worry`, `what_to_do`, `jargon` em português. Analista júnior consegue triagem sem precisar googlar termo. Diferencial real vs. Wazuh (todo em inglês técnico).

### 12. Lab Mode como env var opt-in (não config persistido)
`SENTINELBR_LAB_MODE=true` habilita endpoints `/lab/*` (start/stop/atacar VMs OrbStack via shell). NUNCA por DB ou UI toggle — porque se está no DB, dump vazado expõe. Env var = decisão explícita do operador, ativa só onde foi setada.

---

## Estrutura do projeto

```
sentinelbr-platform/
├── server/                        # API Python — FastAPI + Celery
│   ├── app/
│   │   ├── api/                  # 20 routers REST (auth, hosts, agents, alerts, ...)
│   │   ├── grpc_server/          # AgentService (heartbeat + StreamEvents + Commands)
│   │   ├── models/               # 9 SQLAlchemy models
│   │   ├── schemas/              # Pydantic request/response
│   │   ├── services/             # auth, audit, enrollment, OSV, Loki, CA, PII, policy
│   │   ├── rules/                # 8 detection rules YAML (Sigma-style)
│   │   ├── kb/data/              # KB: 12 techniques + 6 hunting + 3 playbooks (YAML)
│   │   ├── workers/              # Celery tasks (detect, vuln_scan, tools_schedule)
│   │   ├── scripts/              # seed, retention, util
│   │   ├── config.py             # Pydantic Settings (SENTINELBR_* env vars)
│   │   ├── db.py                 # AsyncEngine + SessionLocal
│   │   └── main.py               # FastAPI app + lifespan + observability
│   ├── alembic/versions/         # 17 migrations lineares
│   ├── tests/                    # 149 testes em 19 arquivos
│   └── data/                     # PKI: ca.crt, ca.key, server.crt, server.key (gitignored)
│
├── agent/                         # Coletor Go
│   ├── cmd/sentinel-agent/       # main: subcommands `enroll` + `run` + `doctor`
│   ├── internal/                 # 23 packages
│   │   ├── parsers/{sshd,selinux,apparmor}/
│   │   ├── grpcclient/           # mTLS client + StreamEvents
│   │   ├── heartbeat/            # ciclo 30s
│   │   ├── hoststats/            # uptime, load, mem, disk
│   │   ├── packagemgr/           # apt/dnf/rpm/apk
│   │   ├── toolsdetect/          # fail2ban/rkhunter/chkrootkit/lynis/AIDE/SELinux/AppArmor
│   │   ├── yarascanner/          # scan + filewatcher
│   │   ├── cmddispatcher/        # handlers pra block_ip/quarantine/run_scans
│   │   ├── quarantine/           # move file + audit
│   │   ├── firewall/             # nft/ufw/firewalld executors
│   │   └── ... (osdetect, sysadmin, mac, eventstream, scan_runner, logging)
│   └── yara-rules/               # 8 .yar files (16 rules total)
│
├── web/                          # SPA React
│   ├── src/
│   │   ├── pages/                # 10 pages (Login, Hosts, HostDetail, Alerts, Compliance, KB, Hunting, PurpleTeam, Lab, Docs)
│   │   ├── components/           # 25+ componentes (panels, modals, headers, tabs)
│   │   ├── lib/                  # api.ts (auth + refresh), useModalShell, usePolling, useLabMode
│   │   └── stores/               # Zustand: auth
│   └── package.json              # React 19, Vite 8, Tailwind 4, Radix UI
│
├── proto/                        # Contratos gRPC compartilhados (mTLS)
├── deploy/                       # Docker Compose dev + Helm (parcial)
├── docs/                         # 18 documentos (renderizados in-app em /docs)
├── samples/
│   ├── labs/                     # `make lab-up` cria 6 VMs OrbStack
│   │   ├── distros/              # *.env por distro (debian-11, ubuntu-22, fedora, rocky-9, alpine-3, vuln-lab)
│   │   ├── scenarios/            # 6 docs detalhados por VM
│   │   ├── lib/                  # vm.sh, plant.sh, api.sh
│   │   └── up.sh, attack.sh, status.sh, down.sh
│   └── malicious-fixtures/       # EICAR + dropper + reverse_shell + cron_backdoor (inertes)
└── .github/workflows/            # CI matriz Linux/macOS/Windows + security scans
```

---

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

---

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

Com `SENTINELBR_LAB_MODE=true` no backend, a aba `/lab` na UI permite Start/Stop/Re-atacar/Resetar demo direto pelo navegador.

---

## Páginas da UI

| Rota | O que tem |
|------|-----------|
| `/` | Lista de hosts + enrollment + heartbeat status |
| `/hosts/:id` | Detalhe do host: Vulnerabilidades (CVE/OSV), Anti-malware (YARA scan), Ferramentas (fail2ban/rkhunter/...), Ações (auto-block/quarantine), Eventos |
| `/alerts` | Alertas com filtros (status/severity/host), ack/resolve |
| `/compliance` | Relatório LGPD: MTTR, logins, hosts/alerts/actions, audit log, export PDF |
| `/kb` | MITRE ATT&CK PT-BR — 12 técnicas com mitigações |
| `/hunting` | 6 queries pré-prontas pra investigação |
| `/purple-team` | 3 cenários de simulação ataque + detecção esperada |
| `/docs` | Documentação completa renderizada (sidebar TOC + markdown) |
| `/lab` | (só com `SENTINELBR_LAB_MODE=true`) controle das VMs do demo + reset |

---

## Componentes

- **[server/](server/README.md)** — FastAPI + Pydantic v2 + SQLAlchemy 2 async + Celery + asyncpg + httpx (OSV/Loki) + grpcio (mTLS) + slowapi (rate limit) + structlog + Prometheus.
- **[agent/](agent/README.md)** — Go com interfaces por OS (`PackageManager`, `FirewallExecutor`, `MACSystem`). Cross-compila pra Linux/Windows/macOS.
- **[web/](web/README.md)** — Vite 8 + React 19 + TypeScript strict + Tailwind 4 + Radix UI + Zustand + Recharts. SPA pura com lazy load por rota.

---

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

---

## Segurança em camadas

Defesa em profundidade — quando uma camada falha, a próxima segura.

### 1. Auth & sessão
- JWT access tokens curtos (60min default, configurável) + refresh tokens 7d em **cookie httpOnly samesite=lax path=/api/v1/auth** (anti-XSS exfil).
- **JTI rotation** com tabela `refresh_token_jtis` — replay de refresh detectado e bloqueado, revoga toda a cadeia.
- **bcrypt dummy hash** em login pra usuário inexistente (anti enumeração via timing attack).
- `/logout` apaga o cookie no backend (server-controlled).

### 2. mTLS no agente
- CA própria gerada na primeira execução (RSA 4096), cert servidor + cert por agente (RSA 2048).
- `CN=host_id` no cert do agente — server valida em `Heartbeat` e `StreamEvents` (anti-impersonation).
- `grpc_server` configurado com `require_client_auth=True`.

### 3. Rate limit (slowapi)
- `/auth/login`: 10/min por IP — anti brute-force credentials.
- `/agents/enroll`: 20/min por IP — anti enumeração de tokens de enrollment.
- Handler 429 retorna detail amigável.

### 4. Autorização RBAC
- Roles: `admin` (full) / `operator` (ações) / `viewer` (read-only).
- `require_role()` dependency factory + `AdminUser`/`OperatorUser` types em `deps.py`.
- Endpoints destrutivos (DELETE, PATCH) exigem `admin`; scans/ações exigem `operator`.

### 5. Tenant isolation
- **Cross-org leakage retorna 404** (não 403) em todos os endpoints REST.
- `host_in_org_or_404` helper centralizado, usado em hosts/alerts/actions/vulnerabilities/yara/events/audit/compliance.
- `audit.log_action` levanta `ValueError` se `org_id != actor.org_id` (anti privilege-escalation no audit trail).

### 6. LGPD compliance
- **Audit log append-only** (Art. 37): tabela `audit_logs` sem UPDATE/DELETE em código.
- **Retenção configurável** (Art. 16): `SENTINELBR_AUDIT_RETENTION_DAYS` + Celery beat task de purge.
- **PII masking opcional**: `services/pii.py` mascara CPF/CNPJ/email/phone em event metadata.
- **Endpoint `/compliance/report`**: PDF com MTTR, audit summary, retenção, ações executadas — pronto pra entregar à ANPD.

### 7. CSP + CORS estritos
- `CORS_ALLOWED_ORIGINS` exige lista explícita (sem wildcards). Boot fail se vazio em prod.
- `allow_credentials=True` (cookies httpOnly dependem); `allow_methods` e `allow_headers` listados.

### 8. DB integrity
- **CHECK constraints** no Postgres em campos enum: `severity` (`ck_alerts_severity`), `status` (`ck_actions_status`, `ck_alerts_status`).
- **Índices parciais** (`WHERE status = 'pending'`) pra hot paths de action dispatch.
- **UNIQUE partial** em `hosts.enrollment_token WHERE NOT NULL` — múltiplos NULL permitidos, token ativo é único.

### 9. Anti-injection
- **Path traversal allow-list** em clamav/yara scans (`/var/www`, `/tmp`, `/home`, `/opt`, `/srv` — nada fora).
- **VM names validados** no `/lab/*` contra `^lab-[a-z0-9-]+$` (bloqueia `"; rm -rf /"`).
- **subprocess.exec com argv list**, NUNCA `shell=True`. Timeout em todo subprocess externo.
- **Pydantic valida IP/CIDR/porta/proto** em endpoints de firewall; agente **re-valida** pra defesa em camadas.

### 10. CI security scans
- **govulncheck** (Go) cruza com Go vulndb.
- **pip-audit** (Python) cruza pyproject/uv.lock com OSV.
- **pnpm audit** (npm) high severity quebra.
- **Trivy fs** pega segredos commitados + IaC misconfig (`CRITICAL,HIGH`).
- Hoje report-only (`continue-on-error: true`) — escalável pra blocking conforme codebase resolve CVEs herdadas.

### 11. Resiliência do agente
- **`defer recover()`** em goroutines críticas (eventstream ackReader, source goroutines).
- **gRPC keepalive** (Time=30s, Timeout=10s, PermitWithoutStream=true) anti-NAT-drop.
- **`exec.CommandContext` com 15s timeout** em firewall executors (sem ctx travava em hosts lentos).
- **`scan_runner.go`**: `LimitReader` cap 10MB anti-OOM em scans com saída gigante.

### 12. Operacional
- **Boot fail em prod** sem `SENTINELBR_JWT_SECRET` configurado (assert em `config.py`).
- **Endpoint `/agents/enroll`** com `Cache-Control: no-store` + audit success/failure.
- **`server/data/` gitignored** (PKI inteira). Regeneração simples (apagar dir → próximo `make grpc` regenera).

---

## Comparação com mercado

| Critério | SentinelBR | Wazuh | Splunk | Elastic Stack | Graylog |
|---|---|---|---|---|---|
| **Licença** | AGPL-3.0 | GPL-2.0 | Comercial | Elastic License + AGPL | SSPL |
| **Idioma nativo** | **PT-BR** | EN | EN | EN | EN |
| **LGPD-first** | ✅ Art. 37/16 nativo | parcial | parcial | parcial | parcial |
| **Custo** | Free (self-host) | Free (self-host) | $$$ por GB | $$ Elastic Cloud | Free (self-host) |
| **Footprint** | ~150MB RAM server + <30MB agente | ~500MB | enterprise | enterprise | médio |
| **Curva** | Baixa (PT-BR) | Média (EN, docs densas) | Média (próprio query lang) | Alta (Lucene + Kibana) | Média |
| **Threat KB PT-BR** | ✅ 12 técnicas MITRE + leigo | ❌ | ❌ | ❌ | ❌ |
| **Multi-tenancy** | ✅ estrito (404 leak-safe) | parcial | sim | sim (RBAC) | sim |
| **mTLS agente** | ✅ CA própria + CN=host_id | ✅ | ✅ | ✅ | ✅ |
| **YARA built-in** | ✅ 16 rules + scheduled + filewatcher | ✅ via integração | via add-on | via plugin | via plugin |
| **OSV cross-ref** | ✅ nativo | parcial (CVE-Search) | sim (premium) | sim (Beats) | parcial |
| **SOAR-lite** | ✅ block_ip + quarantine_file | ✅ Active Response | sim (Phantom) | parcial | parcial |
| **Audiência** | **PME BR** | PME global | Enterprise | Enterprise | PME global |

**Diferencial real do SentinelBR**: ser o único da lista que **assume realidade brasileira como requisito de produto** (PT-BR, LGPD, jargão localizado, equipes pequenas). Não tenta competir em escala com Splunk — compete em **adoção fácil pra quem fala português e precisa de LGPD pronta**.

---

## Métricas do código

| Métrica | Valor |
|---|---|
| **Linhas de código (LOC)** | ~19.500 (Python 6.5k + Go 5.5k + TS/TSX 7.5k) |
| **Server testes automatizados** | 149 (em 19 arquivos, pytest-asyncio) |
| **Agent suite** | Go tests com cache + race detector no CI |
| **Rotas REST** | 55 (em 20 routers) |
| **Migrations Alembic** | 17 (lineares, idempotentes) |
| **Modelos SQLAlchemy** | 9 (org, user, host, alert, action, audit_log, host_package, host_vulnerability, refresh_token_jti) |
| **Detection rules (Sigma-style)** | 8 (brute-force, root login, user enum, MAC denials, YARA matches, ...) |
| **YARA rules** | 16 (em 8 arquivos: webshell, miner, dropper, reverse shell, persistence, ransomware, suspicious exec, linux apt) |
| **KB content** | 12 técnicas MITRE PT-BR + 6 hunting queries + 3 purple team playbooks |
| **Pages frontend** | 10 (Login, Hosts, HostDetail, Alerts, Compliance, KB, Hunting, PurpleTeam, Lab, Docs) |
| **Packages do agent** | 23 (parsers, grpcclient, heartbeat, hoststats, yarascanner, cmddispatcher, firewall, ...) |
| **Docs publicadas** | 18 (renderizadas in-app em `/docs`) |
| **Fases entregues** | 11 (1-10 + hardening pos-auditoria + Fase 11 lab/docs) |
| **CI matriz** | Linux + macOS + Windows + cross-compile (linux amd64/arm64, darwin arm64/amd64, windows amd64) |

---

## Roadmap

**Entregue (fases 1-11):**
- ✅ Fase 1: Enrollment + heartbeat mTLS
- ✅ Fase 2: Log collector + event streaming SSH
- ✅ Fase 3: Detection engine + alertas Sigma-style
- ✅ Fase 4: Auto-block on alert (IR + firewall real)
- ✅ Fase 5: SELinux/AppArmor parsers + MAC rules
- ✅ Fase 6: Vulnerability mgmt via OSV.dev
- ✅ Fase 7: Compliance LGPD (audit log + report + retenção)
- ✅ Fase 8: YARA scanner + 5 starter rules
- ✅ Fase 8.5: YARA manual (UI) + scheduled + filewatcher + auto-quarantine
- ✅ Fase 9: Threat KB MITRE ATT&CK PT-BR + Hunting + Purple Team
- ✅ Fase 10: Multi-tenancy (Org → User RBAC) com tenant isolation
- ✅ Fase H1-H8: Hardening tools (fail2ban, firewall write, rkhunter, chkrootkit, lynis, AIDE, auditd, SELinux/AppArmor)
- ✅ Hardening pós-auditoria: JWT assert + rate limit + httpOnly cookie + RBAC + indices DB + N+1 fix + agent recover/keepalive + lazy loading + Prometheus + structlog + Trivy/pip-audit/govulncheck no CI
- ✅ Fase 11: Lab Mode opt-in + VMs especializadas (+ Rocky 9 + Alpine 3) + 8 YARA rules novas + EICAR + 4 técnicas MITRE PT-BR + aba `/docs` in-app

**Em consideração (próximas fases):**
- 🔲 Fase 12: Cross-platform Windows agent (Event Log, PowerShell logging, Defender integration)
- 🔲 Fase 13: Log viewer/parser genérico (sshd, nginx, postgres, apache formats)
- 🔲 Fase 14: SAML/OIDC SSO + LDAP/AD integration
- 🔲 Fase 15: Webhook integrations (Slack, Discord, Teams pra alertas)
- 🔲 Fase 16: SIEM federado — agregar múltiplas instâncias num dashboard global

---

## Documentação interna

Tudo em `docs/` (também renderizado in-app em `/docs` depois de logar):

| # | Documento |
|---|-----------|
| 01 | [Visão geral dos módulos](docs/01-visao-geral-modulos.md) |
| 02 | [Funcionalidades detalhadas](docs/02-funcionalidades-detalhadas.md) |
| 03 | [Interface gráfica](docs/03-interface-grafica.md) |
| 04 | [Arquitetura de dados](docs/04-arquitetura-dados.md) |
| 05 | [Arquitetura técnica](docs/05-arquitetura-tecnica.md) |
| 06 | [API Reference](docs/06-api-reference.md) |
| 07 | [Roadmap detalhado](docs/07-roadmap-detalhado.md) |
| 08 | [Stack decisions (ADRs)](docs/08-stack-decisions.md) |
| 09 | [Deployment](docs/09-deployment.md) |
| 10 | [Diagramas visuais](docs/10-diagramas-visuais.md) |
| 11 | [Glossário](docs/11-glossario.md) |
| 12 | [Fixtures de eventos](docs/12-fixtures-eventos.md) |
| 13 | [Interface gráfica terminal](docs/13-interface-grafica-terminal.md) |
| 14 | [Vulnerability management](docs/14-vulnerability-management.md) |
| 15 | [Suporte multi-OS](docs/15-suporte-multi-os.md) |
| 16 | [Antivírus / malware](docs/16-antivirus-malware.md) |
| 17 | [Threat knowledge base](docs/17-threat-knowledge-base.md) |
| 18 | [Demo Mode (lab)](docs/18-demo-mode.md) |

---

## Outro projeto do autor

**SC Platform** — plataforma SaaS para gestão de licitações públicas brasileiras (PNCP, pregão eletrônico, robô de lances, simulador FSM da Lei 14.133, extração de PDF com IA local, multi-tenant).

> *Projeto privado, sob NDA — disponível para apresentação técnica em entrevistas mediante solicitação. 75k+ LOC, 420 testes, 30 modelos, 245 rotas, 29 migrations. Stack: Python 3.14 + Flask 3 + SQLAlchemy 2 + PostgreSQL 15 + Redis + Playwright + ReportLab + Docling + ChromaDB + Manifest V3 Chrome Extension.*

---

## Licença

[AGPL-3.0](LICENSE) — protege contra "AWS effect" (cloud providers fechando forks como SaaS sem contribuir de volta). Se você usa o SentinelBR como serviço de rede, precisa abrir as modificações.

Para reportar vulnerabilidades de segurança, ver [SECURITY.md](SECURITY.md).

---

## Autor

**André Augusto Azarias De Souza** — [LinkedIn](https://linkedin.com/in/adreaugusto-azariasdesouza) · [GitHub](https://github.com/andre28abr)

Projeto pessoal desenvolvido como portfólio explorando arquitetura SIEM, mTLS, multi-tenancy, agentes Go cross-platform e UX de plataformas de segurança. Conduzido como product owner técnico com auxílio de assistentes de IA generativa para a etapa de codificação, exercitando a tradução de exigências regulatórias (LGPD) e conceitos de threat detection em uma plataforma funcional.

Disponível para oportunidades em **DPO / Encarregado de Dados**, **Compliance & Governança (GRC)**, **Privacy Engineering** e **Security Analyst** — com diferencial de fluência em PT-BR/EN, formação Direito + TI + Administração, e portfólio técnico aplicado.
