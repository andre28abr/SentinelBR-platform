# SentinelBR — Roadmap Detalhado

> Plano de execução dividido em fases mensuráveis, com critérios claros de "pronto" para cada entrega. Pensado para servir tanto como **mapa de desenvolvimento solo** (você sabe sempre o próximo passo) quanto como **timeline de portfólio** (cada marco vira post no LinkedIn).

---

## 📋 Sumário

1. [Princípios do roadmap](#princípios-do-roadmap)
2. [Visão consolidada — timeline](#visão-consolidada--timeline)
3. [Fase 0 — Preparação (semana 1-2)](#fase-0--preparação)
4. [Fase 1 — MVP (mês 1-2)](#fase-1--mvp)
5. [Fase 2 — v1.0 (mês 3-4)](#fase-2--v10)
6. [Fase 3 — v2.0 (mês 5-6)](#fase-3--v20)
7. [Fase 4 — v3.0 e além](#fase-4--v30-e-além)
8. [Definição de "pronto"](#definição-de-pronto)
9. [Marcos de comunicação (LinkedIn)](#marcos-de-comunicação-linkedin)
10. [Riscos e mitigações](#riscos-e-mitigações)
11. [Métricas de progresso](#métricas-de-progresso)
12. [Cadência sugerida de trabalho](#cadência-sugerida-de-trabalho)

---

## Princípios do roadmap

### 1. 🎯 Vertical slices, não horizontais

**Errado**: "primeiro vou fazer todo o backend, depois todo o frontend, depois deploy".

**Certo**: cada milestone entrega uma **funcionalidade completa de ponta a ponta**, mesmo que pequena. Por exemplo: "login funcionando" significa: tabela no DB + endpoint de login + tela de login no frontend + deploy testado.

Por que? Porque vertical slices te dão **algo demonstrável a cada 2 semanas**, mantêm motivação, e são o que recrutador quer ver no portfólio.

### 2. 📦 Sempre deployável

Em qualquer ponto do roadmap, o que está em `main` deve funcionar e ser deployável. Nunca quebra a build. Use feature flags se precisar mesclar trabalho parcial.

### 3. 🚀 Show, don't tell

Cada fase termina com:
- ✅ Funcionalidade demonstrável
- ✅ Vídeo curto (3-5min) mostrando funcionando
- ✅ Post no LinkedIn contando o que aprendeu
- ✅ Commit message rico explicando decisões

### 4. 🧪 Testes desde o dia 1

Não "vou colocar testes depois". Cada PR vem com testes da nova funcionalidade. Sem isso, dívida técnica explode rapidamente em projeto solo.

### 5. 📚 Docs como código

Toda mudança importante atualiza a documentação no mesmo PR. Documentação que vive em wiki separada inevitavelmente desatualiza.

### 6. 🎨 Polish incremental

UI feia em MVP, ok. Sem testes em MVP, **não ok**. Refactor pesado só em pontos onde dor é real, não preventivo.

---

## Visão consolidada — timeline

```
┌────────────────────────────────────────────────────────────────────┐
│ FASE 0          FASE 1            FASE 2          FASE 3    FASE 4│
│ Preparação      MVP               v1.0            v2.0      v3.0+ │
│ 2 semanas       2 meses           2 meses         2 meses   ∞     │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│ Setup inicial   SIEM básico       SELinux         LGPD      Polish│
│ Docs            Firewall          Resposta IR     SSO       Plugin│
│ CI/CD vazio     Auth              ML detecção     HA        Comm. │
│                 Frontend essen.   Threat intel    K8s       Talks │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                                                                
LANÇAMENTO   "PRIMEIRO COMMIT"   "v1.0 RELEASE"    "ENTERPRISE"   "OSS COMMUNITY"
LINKEDIN     post mensal         post mensal       post mensal     posts contínuos
```

### Resumo de cada fase

| Fase | Duração | Entregável | Marco LinkedIn |
|------|---------|------------|----------------|
| 0 | 2 sem | Repositório com setup, docs, CI vazio | "Começando o projeto X" |
| 1 | 2 meses | MVP funcional: SIEM + Firewall + Login | "Primeira release que funciona" |
| 2 | 2 meses | Plataforma operacional completa | "v1.0 lançada com X módulos" |
| 3 | 2 meses | Enterprise-ready (multi-tenant, K8s, LGPD) | "Pronta para produção" |
| 4 | contínuo | Polimento, comunidade, integrações | Conteúdo regular |

---

## Fase 0 — Preparação

**Duração**: 2 semanas
**Objetivo**: ter base sólida para começar a codar sem refazer 100x.

### Sprint 0.1 — Setup do repositório (3 dias)

**Tarefas:**

- [ ] Criar repositório no GitHub: `sentinelbr/sentinelbr`
- [ ] Adicionar README inicial (overview do projeto)
- [ ] Adicionar LICENSE (sugestão: AGPL-3.0 ou MIT)
- [ ] Adicionar `.gitignore` apropriado (Python + Node + Go)
- [ ] Adicionar `CONTRIBUTING.md`
- [ ] Adicionar `CODE_OF_CONDUCT.md`
- [ ] Adicionar templates de Issue e PR
- [ ] Configurar branch protection no `main`
- [ ] Configurar secrets do GitHub (DOCKER_TOKEN, etc.)
- [ ] Setup de monorepo:
  ```
  sentinelbr/
  ├── docs/             ← documentação (já tem!)
  ├── server/           ← backend Python
  ├── agent/            ← agente Go
  ├── web/              ← frontend
  ├── deploy/           ← Docker Compose, K8s
  ├── proto/            ← gRPC schemas compartilhados
  └── scripts/          ← utilitários
  ```

**Critérios de pronto:**
- ✅ Repo público no GitHub
- ✅ README com badges (build, license)
- ✅ Pelo menos 5 docs em `docs/` (já tem 4!)

### Sprint 0.2 — CI/CD básico (3 dias)

**Tarefas:**

- [ ] GitHub Actions: workflow de PR
  - Lint Python (Ruff)
  - Lint TypeScript (ESLint)
  - Lint Go (golangci-lint)
  - Lint Dockerfile (hadolint)
  - Lint Markdown (markdownlint)
- [ ] GitHub Actions: workflow de release
  - Build de imagens Docker (placeholder por enquanto)
  - Push para GitHub Container Registry
  - Geração de changelog (cliff ou similar)
- [ ] Configuração de Dependabot
- [ ] Configuração de CodeQL (security scanning)
- [ ] Pre-commit hooks
  - Trailing whitespace
  - YAML válido
  - Conventional commits

**Critérios de pronto:**
- ✅ PR vazio executa todos os checks (mesmo se não tiver código real)
- ✅ Badge "build passing" no README
- ✅ Pre-commit instalado e funcionando localmente

### Sprint 0.3 — Ambiente de desenvolvimento (3 dias)

**Tarefas:**

- [ ] `docker-compose.dev.yml` com:
  - PostgreSQL 16
  - Redis 7
  - Loki + Grafana
  - MinIO
- [ ] Script `scripts/dev-up.sh`: sobe tudo + roda migrations
- [ ] Script `scripts/dev-down.sh`: para tudo
- [ ] Script `scripts/dev-reset.sh`: limpa volumes
- [ ] `Makefile` com targets úteis (`make up`, `make test`, `make lint`)
- [ ] Documentar setup local em `CONTRIBUTING.md`
- [ ] Devcontainer configurado (VS Code)

**Critérios de pronto:**
- ✅ Clone do repo + `make up` = ambiente rodando em < 5 min
- ✅ Documentação testada em máquina limpa

### Sprint 0.4 — Estrutura inicial dos componentes (4 dias)

**Tarefas:**

- [ ] **Backend Python**:
  - `pyproject.toml` (uv ou poetry)
  - Estrutura de pastas (ver doc 05)
  - `core/config.py` com Pydantic Settings
  - `core/database.py` com SQLAlchemy
  - Alembic configurado
  - FastAPI app vazio rodando
  - Endpoint `/health/live` e `/health/ready`
- [ ] **Agente Go**:
  - `go.mod` setup
  - Estrutura de pastas (ver doc 05)
  - Cobra/Viper para CLI
  - Comando `version` funcionando
  - Hello-world: agente conecta no servidor (sem fazer nada útil)
- [ ] **Frontend**:
  - `pnpm create vite` com React + TS
  - Tailwind + shadcn/ui setup
  - TanStack Router setup
  - Tela "Hello World" no `/`
  - Build production funcionando

**Critérios de pronto:**
- ✅ `make up` sobe os 3 componentes
- ✅ `curl http://localhost:8000/health/live` retorna 200
- ✅ `http://localhost:5173` mostra página
- ✅ `./agent connect --server localhost:9090` log mostrando conexão

### 🏁 Final da Fase 0

**Marco LinkedIn (post 1):**

> Estou começando um projeto open-source que faz X (...). Vai me servir de portfólio para mostrar Y habilidades. Vou compartilhar a jornada aqui no LinkedIn. Hoje completei o setup inicial: monorepo, CI/CD, devcontainer, ambiente de dev em um comando. Próximo: implementar autenticação. Repo: github.com/...

**Validação:**
- Repo público, com documentação
- Build verde
- Ambiente local funcionando
- Esqueleto dos 3 componentes vazio mas vivo

---

## Fase 1 — MVP

**Duração**: 2 meses
**Objetivo**: ciclo completo log → coleta → análise → alerta → ação, em uma stack mínima mas operacional.

### Sprint 1.1 — Autenticação (semana 1-2)

**Tarefas backend:**
- [ ] Schema `auth` no PostgreSQL (users, roles, permissions, user_roles, role_permissions)
- [ ] Migrations Alembic
- [ ] Seed data (roles padrão: admin, analyst, viewer, auditor)
- [ ] `core/security.py`: hash Argon2, JWT
- [ ] Endpoints:
  - `POST /auth/login`
  - `POST /auth/logout`
  - `POST /auth/refresh`
  - `GET /auth/me`
- [ ] Middleware de autenticação
- [ ] RBAC decorator: `@require_permission("...")`
- [ ] Rate limiting em endpoints de auth
- [ ] Schema `audit` + log de ações sensíveis

**Tarefas frontend:**
- [ ] Tela de login (/login)
- [ ] Auth store (Zustand)
- [ ] Axios interceptor com token
- [ ] Layout autenticado (sidebar + topbar vazios)
- [ ] Redirect lógico (autenticado vai pra `/`, não-autenticado pra `/login`)
- [ ] Logout funcional

**Tarefas testes:**
- [ ] Unit tests do AuthService
- [ ] Integration tests dos endpoints
- [ ] E2E: login → acessa página → logout

**Critérios de pronto:**
- ✅ Login funciona end-to-end
- ✅ Token expira em 15min, refresh funciona
- ✅ Tentativas de login com senha errada são rate-limited
- ✅ Audit log registra logins
- ✅ Coverage de auth ≥ 85%

### Sprint 1.2 — Inventário de hosts (semana 3-4)

**Tarefas backend:**
- [ ] Schema `inventory` (hosts, agent_heartbeats)
- [ ] Particionamento de heartbeats
- [ ] Endpoints:
  - `GET /hosts` (paginado, filtrado)
  - `POST /hosts` (com geração de enrollment token)
  - `GET /hosts/{id}`
  - `PATCH /hosts/{id}`
  - `DELETE /hosts/{id}`
- [ ] Geração de cert mTLS no enrollment
- [ ] Servidor gRPC inicial (apenas Heartbeat e Enrollment)

**Tarefas agente:**
- [ ] Comando `enroll` com token
- [ ] Geração de CSR
- [ ] Salva cert recebido em disco
- [ ] Loop de heartbeat (30s)
- [ ] Reporta info do sistema (OS, kernel, IPs)

**Tarefas frontend:**
- [ ] Tela `/hosts` com tabela
- [ ] Modal "Adicionar host" com geração de comando
- [ ] Drawer com detalhes do host
- [ ] Indicador de status (online/offline) baseado em last_seen_at
- [ ] Refresh automático

**Critérios de pronto:**
- ✅ Adicionar host gera comando que roda em servidor real (testar em VPS)
- ✅ Após `bash` do comando, host aparece como "online" em < 30s
- ✅ Se agente é parado, host fica "offline" em < 2min
- ✅ Sidebar mostra contagem de hosts online

### Sprint 1.3 — Coleta e ingestão de logs (semana 5-6)

**Tarefas agente:**
- [ ] Coletor de auth.log (regex para SSH events)
- [ ] Coletor de syslog
- [ ] Storage SQLite para buffer
- [ ] Worker de envio em batch
- [ ] Detecção de rotação de log
- [ ] Backpressure (drop oldest se buffer cheio)

**Tarefas backend:**
- [ ] gRPC: `SubmitEvents` endpoint
- [ ] Validação mTLS (identificar agente pelo cert)
- [ ] Stream processor (asyncio):
  - Consome Redis Stream `events:raw`
  - Normaliza ECS
  - Escreve no Loki via HTTP API
- [ ] Endpoints:
  - `GET /events` (busca no Loki)
  - `GET /events/aggregate`

**Tarefas frontend:**
- [ ] Tela `/events` com tabela virtualizada
- [ ] Filtros laterais (host, source, severity)
- [ ] Auto-refresh
- [ ] Linha expansível com detalhes
- [ ] Query simples (busca por texto)

**Critérios de pronto:**
- ✅ Tentativa de SSH em host monitorado aparece em `/events` em < 10s
- ✅ Logs sobrevivem a restart do servidor central (ficam no buffer)
- ✅ Dashboard mostra "eventos por minuto" em sparkline
- ✅ Loki retém 30 dias

### Sprint 1.4 — Detecção (regras Sigma) (semana 7-8)

**Tarefas backend:**
- [ ] Schema `detection.rules`
- [ ] Schema `alerts.alerts` + comments + timeline
- [ ] Lib `pysigma` integrada
- [ ] Conversor Sigma → LogQL (Loki)
- [ ] Engine de avaliação:
  - Para cada evento, avalia regras ativas
  - Sliding windows no Redis (sorted sets)
  - Cria alertas com fingerprint (dedup)
- [ ] Endpoints:
  - `GET /detection/rules`
  - `POST /detection/rules`
  - `PATCH /detection/rules/{id}`
  - `DELETE /detection/rules/{id}`
  - `POST /detection/rules/{id}/enable`
  - `POST /detection/rules/{id}/disable`
- [ ] Endpoints de alertas:
  - `GET /alerts`
  - `GET /alerts/{id}`
  - `PATCH /alerts/{id}`
  - `POST /alerts/{id}/acknowledge`
  - `POST /alerts/{id}/resolve`
- [ ] Pacote inicial de 10 regras Sigma (brute force, scan, escalada de privilégio, etc.)

**Tarefas frontend:**
- [ ] Tela `/alerts` com lista
- [ ] Drawer com detalhes do alerta
- [ ] Ações: acknowledge, resolve, marcar falso positivo
- [ ] Tela `/detection/rules` (lista, ligar/desligar)
- [ ] Editor YAML simples (Monaco editor)

**Critérios de pronto:**
- ✅ Brute force de SSH em host gera alerta em < 30s
- ✅ Múltiplas tentativas do mesmo IP geram 1 alerta com event_count++
- ✅ Resolver alerta atualiza UI em tempo real
- ✅ Pacote starter tem 10 regras testadas

### Sprint 1.5 — Firewall (semana 9-10)

**Tarefas agente:**
- [ ] Detecção de backend (nftables/iptables/firewalld)
- [ ] Lista regras ativas
- [ ] Recebe e executa comandos:
  - Adicionar regra
  - Remover regra
  - Bloquear IP (via ipset)
- [ ] Confirma execução

**Tarefas backend:**
- [ ] Schema `firewall.*`
- [ ] Endpoints:
  - `GET /firewall/rules/{host_id}`
  - `POST /firewall/rules/{host_id}`
  - `DELETE /firewall/rules/{host_id}/{rule_id}`
  - `GET /firewall/blocks`
  - `POST /firewall/blocks`
  - `DELETE /firewall/blocks/{id}`
  - `GET /firewall/allowlist`
  - `POST /firewall/allowlist`
- [ ] Job de expiração de blocks (Celery beat, cada 5min)

**Tarefas frontend:**
- [ ] Tela `/firewall` com seletor de host
- [ ] Tabela de regras
- [ ] Modal de criação de regra
- [ ] Aba "IPs Bloqueados"
- [ ] Aba "Allowlist"

**Critérios de pronto:**
- ✅ Criar regra na UI = regra aparece no `nft list ruleset` do host
- ✅ Bloquear IP via UI = `nft add element ... blacklist` executado
- ✅ Bloqueios temporários expiram automaticamente

### Sprint 1.6 — Integração Alert → Firewall (semana 11)

**Tarefas:**
- [ ] Quando alerta de tipo "brute force" é criado, automaticamente:
  - Bloqueia IP de origem por 1h
  - Adiciona ao timeline do alerta
  - Notifica (próximo sprint)
- [ ] Allowlist é respeitada (jamais bloqueia IPs nela)
- [ ] Configuração: ligar/desligar bloqueio automático
- [ ] Histórico de bloqueios automáticos vs manuais

**Critérios de pronto:**
- ✅ E2E: tentativa SSH → alerta → bloqueio automático em < 30s
- ✅ Atacante não consegue mais se conectar (testar com `telnet` da origem)

### Sprint 1.7 — Notificações (semana 12)

**Tarefas:**
- [ ] Worker Celery para notificações
- [ ] Provider Telegram (bot token + chat_id)
- [ ] Provider Slack (webhook URL)
- [ ] Provider Email (SMTP)
- [ ] Endpoints:
  - `GET /integrations/notifications/channels`
  - `POST /integrations/notifications/channels`
  - `POST /integrations/notifications/channels/{id}/test`
- [ ] Roteamento por severidade
- [ ] Throttling para evitar spam
- [ ] Frontend: tela de configuração

**Critérios de pronto:**
- ✅ Alerta crítico → mensagem no Telegram em < 10s
- ✅ Mensagem tem link para alerta na UI
- ✅ Testar canal (botão "Enviar teste") funciona

### Sprint 1.8 — Polimento e deploy MVP (semana 13)

**Tarefas:**
- [ ] Tela de Dashboard (KPIs + sparklines)
- [ ] Empty states em todas as listas
- [ ] Toasts de sucesso/erro consistentes
- [ ] Dark mode default
- [ ] Atalhos de teclado básicos (Cmd+K, J/K)
- [ ] Documentação de instalação:
  - Docker Compose em VPS Ubuntu
  - Configuração de domínio + Let's Encrypt
- [ ] Helm chart placeholder (não funcional ainda)
- [ ] Vídeo demo de 5 min
- [ ] Site simples em GitHub Pages com docs

**Critérios de pronto:**
- ✅ Deploy em VPS real funcionando (testado de máquina externa)
- ✅ Vídeo gravado e linkado no README
- ✅ Tutorial "Como instalar em 10 minutos"

### 🏁 Final da Fase 1 (MVP)

**Marco LinkedIn (post 4):**

> 🎉 Lançada a primeira versão funcional do SentinelBR! Plataforma open-source de segurança para Linux que faz: SIEM básico + Firewall integrado + Alertas em tempo real. 
> 
> O que aprendi nesses 2 meses:
> - gRPC com mTLS é mais simples do que parece (e muito mais eficiente que REST pra agentes)
> - Loki vs Elasticsearch: 10x mais barato, queries quase tão rápidas
> - Sigma rules como padrão da indústria me poupou MESES de trabalho
> 
> Veja a demo de 5 min: [link]
> Repo: github.com/...

---

## Fase 2 — v1.0

**Duração**: 2 meses
**Objetivo**: plataforma "operável de verdade" — features que diferenciam de um projeto de fim de semana.

### Sprint 2.1 — 2FA + API tokens (semana 1)

**Tarefas:**
- [ ] Implementação TOTP (RFC 6238)
- [ ] QR code generation
- [ ] Backup codes
- [ ] Endpoints `/auth/mfa/*`
- [ ] Schema `auth.api_tokens`
- [ ] Endpoints `/api-tokens/*`
- [ ] Frontend: enrollment de MFA (wizard com QR)
- [ ] Frontend: gestão de API tokens

### Sprint 2.2 — SELinux (semana 2-3)

**Tarefas agente:**
- [ ] Coletor de `/var/log/audit/audit.log` filtrando AVC
- [ ] Parser de denials
- [ ] Executor: `setsebool`, `semanage fcontext`, `audit2allow`

**Tarefas backend:**
- [ ] Schema `selinux.*`
- [ ] Base de conhecimento de contextos (CSV importável)
- [ ] Endpoints `/selinux/*`
- [ ] Lógica de tradução AVC → mensagem amigável

**Tarefas frontend:**
- [ ] Tela `/selinux` com abas (Status, Denials, Booleanos, Contextos, Policies)

### Sprint 2.3 — Threat Intel (semana 4)

**Tarefas:**
- [ ] Job de download de feeds (cron):
  - AbuseIPDB (CSV)
  - AlienVault OTX (API)
  - Feodo Tracker (CSV)
  - URLhaus (CSV)
- [ ] Storage em Redis (SET)
- [ ] Enrichment durante stream processing
- [ ] Frontend: configuração de feeds

### Sprint 2.4 — Detecção de anomalias com ML (semana 5-6)

**Tarefas:**
- [ ] Feature engineering: hora, geo, frequência por usuário/host
- [ ] Treino de Isolation Forest
- [ ] Job de re-treino semanal
- [ ] Detecção em tempo real durante stream
- [ ] Score de anomalia 0-100
- [ ] Explicabilidade com SHAP
- [ ] Frontend: visualização de anomalias

### Sprint 2.5 — Resposta a Incidentes (Playbooks) (semana 7-8)

**Tarefas:**
- [ ] Schema `playbook.*`
- [ ] DSL YAML com triggers, steps, conditions
- [ ] Engine executor (Python)
- [ ] Catálogo inicial de actions:
  - `firewall.block_ip`
  - `firewall.unblock_ip`
  - `host.kill_process`
  - `host.isolate`
  - `host.unisolate`
  - `forensics.collect`
  - `notify.telegram/slack/email`
  - `webhook.send`
- [ ] Aprovação humana via Telegram inline keyboard
- [ ] Coleta forense funcional (tar.gz no MinIO)
- [ ] Frontend: lista de playbooks, editor YAML, histórico de execuções

### Sprint 2.6 — Webhooks de saída + tracing (semana 9)

**Tarefas:**
- [ ] Schema de webhooks
- [ ] Sistema de retry com backoff
- [ ] Assinatura HMAC
- [ ] OpenTelemetry instrumentação
- [ ] Jaeger/Tempo no docker-compose
- [ ] Frontend: gestão de webhooks

### Sprint 2.7 — Onboarding wizard + i18n (semana 10)

**Tarefas:**
- [ ] Wizard de primeira instalação (5 passos)
- [ ] Internacionalização: PT-BR (default) + EN-US
- [ ] Documentação técnica em ambos os idiomas

### Sprint 2.8 — Backup, monitoramento próprio, demo pública (semana 11-12)

**Tarefas:**
- [ ] Job diário de backup PostgreSQL → MinIO
- [ ] WAL archiving configurado
- [ ] Script de restore testado
- [ ] Métricas Prometheus expostas
- [ ] Dashboard Grafana de "saúde do SentinelBR"
- [ ] Deploy de instância pública demo (Hetzner)
- [ ] Credenciais públicas read-only
- [ ] Página de "demo" com link

### 🏁 Final da Fase 2 (v1.0)

**Marco LinkedIn (post 8):**

> SentinelBR v1.0 é uma realidade! O que adicionei nestes 2 meses:
> - 🔐 2FA via TOTP
> - 🛡️ Módulo SELinux (com tradução amigável dos AVC denials)
> - 🤖 Detecção de anomalias com ML (Isolation Forest + SHAP)
> - ⚡ Engine de Playbooks para resposta automatizada
> - 🌐 Threat Intelligence integrado
> - 📡 Webhooks + OpenTelemetry tracing
> 
> Demo pública (read-only): demo.sentinelbr.io
> 
> Próximo: módulo LGPD e enterprise-readiness.

---

## Fase 3 — v2.0

**Duração**: 2 meses
**Objetivo**: enterprise-ready — multi-tenant, K8s, e o módulo de LGPD que é o diferencial brasileiro.

### Sprint 3.1 — Módulo LGPD parte 1 (semana 1-3)

**Tarefas:**
- [ ] Schema `lgpd.data_assets`
- [ ] CRUD de ativos sensíveis
- [ ] Configuração automática de auditd watches via agente
- [ ] Cross-reference: eventos relacionados a ativos LGPD são taggeados
- [ ] Frontend: tela `/lgpd/assets` + cadastro completo

### Sprint 3.2 — Módulo LGPD parte 2 (semana 4-5)

**Tarefas:**
- [ ] Schema `lgpd.data_subjects_requests`
- [ ] Schema `lgpd.privacy_incidents`
- [ ] Workflow de pedidos de titulares
- [ ] Detecção de vazamento (regras Sigma específicas)
- [ ] Geração de RIPD (PDF via WeasyPrint)
- [ ] Geração de relatório de operações (Art. 37)
- [ ] Frontend: telas de gestão de pedidos, incidentes, relatórios

### Sprint 3.3 — SSO (OIDC) (semana 6)

**Tarefas:**
- [ ] Integração com Keycloak (provider de teste)
- [ ] Suporte a Google Workspace
- [ ] Suporte a Microsoft Entra
- [ ] Mapeamento OIDC → roles internos
- [ ] Frontend: botão "Login com SSO"

### Sprint 3.4 — Multi-tenant (semana 7-8)

**Tarefas:**
- [ ] Schema com `tenant_id` em todas as tabelas relevantes
- [ ] Migration para adicionar coluna
- [ ] Row-level security no PostgreSQL
- [ ] Middleware que injeta tenant context
- [ ] Frontend: switcher de tenant (admin)

### Sprint 3.5 — Helm chart + Terraform (semana 9-10)

**Tarefas:**
- [ ] Helm chart funcional para K8s
  - Templates para todos os componentes
  - Values.yaml documentado
  - HPA, PDB, NetworkPolicies
- [ ] Terraform module para DigitalOcean
- [ ] Terraform module para Hetzner
- [ ] Documentação de deploy em K8s

### Sprint 3.6 — Replicação PostgreSQL + HA (semana 11)

**Tarefas:**
- [ ] Configuração de streaming replication
- [ ] Patroni para failover automático
- [ ] Read replicas para queries pesadas
- [ ] Documentação de DR procedures

### Sprint 3.7 — Editor visual de Playbooks (semana 12)

**Tarefas:**
- [ ] React Flow para drag-and-drop
- [ ] Catálogo lateral de blocos
- [ ] Validação visual
- [ ] Export para YAML

### 🏁 Final da Fase 3 (v2.0)

**Marco LinkedIn (post 12):**

> SentinelBR v2.0 — agora enterprise-ready!
> 
> 🇧🇷 Módulo LGPD completo: cadastro de ativos sensíveis, gestão de pedidos de titulares, geração de RIPD, detecção de vazamentos
> 🔑 SSO via OIDC (Google, Microsoft, Keycloak)
> 🏢 Multi-tenant com row-level security
> ⚓ Helm chart pronto para Kubernetes
> 🔄 Alta disponibilidade com Patroni
> 
> Estou recebendo as primeiras empresas testando em produção. 

---

## Fase 4 — v3.0 e além

**Duração**: contínua
**Objetivo**: comunidade, integrações, ecosystem.

### Direções possíveis

- **Plugins de comunidade**: SDK para que terceiros criem actions de playbook, parsers de log, etc.
- **Integrações**:
  - Wazuh (importar regras)
  - Suricata (consumir alertas IDS)
  - MISP (threat intel)
  - Jira/Linear (criar tickets a partir de alertas)
  - PagerDuty/Opsgenie (escalation)
- **App mobile**: aprovar playbooks no celular, ver alertas
- **CLI completa**: `sentinelctl` com todas as operações
- **SDKs oficiais**: Python, Go, JavaScript
- **Ansible collection**: instalar agente em massa
- **Marketplace de regras Sigma e playbooks**
- **Suporte a Windows hosts** (agente em Go já permite)
- **Dashboards customizáveis pelo usuário**

### Sprints de polish

- Performance: profiling, otimizações
- Acessibilidade WCAG 2.1 AAA
- Cobertura de testes 95%+
- Documentação em vídeo (curso completo no YouTube)
- Talks em meetups e conferências

---

## Definição de "pronto"

Para qualquer tarefa ser considerada **DONE**, ela precisa atender:

### Critérios de PR

- [ ] Código commitado segue convenções (naming, estrutura)
- [ ] Lint passa
- [ ] Testes unitários cobrem caminhos felizes e errors
- [ ] Testes de integração para mudanças que tocam DB/Redis
- [ ] Documentação atualizada (README, docs/, comentários)
- [ ] Migration testada em base limpa e existente
- [ ] PR revisado (mesmo que self-review com checklist)
- [ ] CI verde
- [ ] Sem TODO/FIXME pendentes (ou registrados como issues)

### Critérios de Sprint

- [ ] Demo funcional ao final
- [ ] Vídeo curto (1-2 min) gravado
- [ ] Changelog atualizado
- [ ] Issues fechadas no GitHub
- [ ] Backlog ajustado (próximo sprint planejado)

### Critérios de Fase

- [ ] Todos os sprints da fase completos
- [ ] Release tag no GitHub (v0.1, v1.0, etc.)
- [ ] Imagens Docker publicadas
- [ ] Documentação consolidada
- [ ] Post no LinkedIn
- [ ] Vídeo demo de 3-5 min
- [ ] Deploy em ambiente de demo público funcionando

---

## Marcos de comunicação (LinkedIn)

Calendário sugerido de posts:

### Mensais (durante desenvolvimento)

| Mês | Tema do post |
|-----|--------------|
| 1 | "Começando o projeto: o problema, a stack, os trade-offs" |
| 2 | "Os primeiros desafios técnicos: gRPC, mTLS, e por que escolhi Go pro agente" |
| 3 | "MVP lançado! Lições da primeira release" |
| 4 | "Sigma rules: como milhares de regras prontas economizaram meses do meu trabalho" |
| 5 | "Detecção de anomalias com ML em produção: o que ninguém te conta" |
| 6 | "v1.0 lançada — comparação com a v0.1" |
| 7 | "Multi-tenant em PostgreSQL: row-level security na prática" |
| 8 | "LGPD na arquitetura: privacy by design não é jargão" |

### Bonus (entre os principais)

- Tutorial: "Como detectar brute force SSH em < 30 segundos"
- Tutorial: "Implementando rate limiting com Redis (3 algoritmos comparados)"
- Caso técnico: "Quando o Loki me decepcionou (e como resolvi)"
- Reflexão: "10 erros que cometi no primeiro mês"

### Pequenas vitórias (compartilhar quando acontecem)

- Primeira PR de stranger no repo
- Primeira estrela no GitHub
- 100 estrelas
- 1.000 estrelas
- Primeira issue de bug reportada por usuário real
- Primeiro deploy em empresa
- Convite para falar em meetup
- Mencionado em newsletter da indústria

---

## Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Burnout por escopo grande | Alta | Alto | Sprints curtos, entregas pequenas, vertical slices |
| Perder motivação sem feedback | Alta | Alto | Posts regulares no LinkedIn, demo pública |
| Stack errada (decisão difícil de reverter) | Média | Alto | Validar com POC antes de comprometer |
| Testes ficam para depois | Alta | Alto | Política rígida de "PR sem teste = sem merge" |
| Documentação desatualiza | Alta | Médio | Atualizar no mesmo PR; revisão mensal |
| Performance ruim em escala | Média | Alto | Load testing com k6 ao final de cada fase |
| Vulnerabilidade de segurança | Baixa | Crítico | CodeQL, Dependabot, security review por fase |
| Conflito de licença de dependência | Baixa | Médio | License-checker no CI |
| Cloud bill explode | Média | Médio | Self-hosted; cap de gastos configurado |

---

## Métricas de progresso

### Para medir ao longo do desenvolvimento

**Engenharia:**
- Cobertura de testes (target: ≥80% no servidor, ≥70% no frontend)
- Tempo de build (target: <5min no CI)
- Tempo de startup do ambiente local (target: <2min)
- Bugs em aberto (target: <10 a qualquer momento)
- Pull requests abertos por mais de 7 dias (target: 0)

**Produto:**
- Tempo médio para primeiro alerta após instalação (target: <5min)
- Tempo médio entre evento e alerta (MTTD; target: <30s)
- Tempo médio entre alerta e ação automática (target: <10s)

**Portfólio/visibilidade:**
- Estrelas no GitHub
- Forks
- Issues abertas por estranhos (mostra que pessoas usam)
- Visualizações no LinkedIn dos posts
- Convites para entrevistas/conversas

### Painel de status (lugar para acompanhar)

Sugestão: criar um arquivo `STATUS.md` no repo com:

- Versão atual
- Funcionalidades por status (planejado, em desenvolvimento, beta, estável)
- Gráfico de burndown
- Issues por categoria

---

## Cadência sugerida de trabalho

### Para projeto solo + trabalho/estudos

**Semana típica:**

| Dia | Foco | Horas |
|-----|------|-------|
| Seg | Setup do sprint (planejamento) | 1-2h |
| Ter | Código (feature) | 2-3h |
| Qua | Código (feature) | 2-3h |
| Qui | Código + revisão própria | 2-3h |
| Sex | Testes + docs + commit | 2h |
| Sáb | Foco profundo (refactor, arquitetura) | 3-4h |
| Dom | Descanso ou conteúdo (post LinkedIn) | 0-2h |

**Total**: ~15h/semana = sustentável a longo prazo.

### Sprints de 2 semanas

Cada sprint termina com:
1. **Sexta da semana 2**: code freeze, testes, docs
2. **Sábado**: gravar vídeo, escrever post, criar release tag
3. **Domingo**: pausa total ou planejamento muito leve do próximo

### Em momentos de baixa motivação

- ✅ Foque em **uma única tarefa pequena** (criar uma issue, escrever um teste, atualizar uma doc)
- ✅ Releia seus posts antigos no LinkedIn — você já chegou longe
- ✅ Deixe o código por 1-2 dias se necessário; volta com clareza
- ❌ Não tente "compensar" com weekend de 12h direto — isso leva ao burnout

---

## Por que esse roadmap impressiona no portfólio

Esta documentação demonstra:

- **Pensamento de produto**: roadmap não é wishlist, é plano executável
- **Auto-conhecimento**: cadência sugerida considera realidade de quem trabalha/estuda
- **Maturidade técnica**: critérios de pronto, definição de fases, métricas
- **Visão de longo prazo**: pensar em comunidade, ecosystem, não só código
- **Comunicação**: integração com LinkedIn não é por vaidade, é estratégia de carreira
- **Gestão de risco**: identificar riscos antes deles materializarem
- **Disciplina**: testes desde o dia 1, docs sempre atualizados

Cada marco é um post potencial:

- "Meu plano de 6 meses para construir uma plataforma open-source enquanto trabalho fulltime"
- "Como divido sprints quando tenho só 15h/semana pro projeto"
- "Vertical slices vs horizontal: o que aprendi do hard way"
- "Critérios de 'pronto' em projeto solo: como evitar débito técnico"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
