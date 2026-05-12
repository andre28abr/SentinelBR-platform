# SentinelBR — Architecture Decision Records (ADRs)

> Registro das principais decisões arquiteturais e técnicas. Cada ADR documenta o **contexto**, as **alternativas**, a **decisão** e as **consequências**. Pensado para ser o "porquê" do projeto — útil para você relembrar suas próprias decisões e para mostrar maturidade técnica em entrevistas.

---

## 📋 O que são ADRs?

ADR (Architecture Decision Record) é uma técnica popularizada por Michael Nygard para documentar decisões de arquitetura em formato curto e estruturado.

**Por que isso importa:**
- **Memória**: você esquece o "porquê" em meses
- **Onboarding**: novos colaboradores entendem rápido
- **Entrevistas**: "por que escolheu X em vez de Y?" tem resposta pronta
- **Evitar redebates**: quando alguém propõe trocar X por Y, ADR mostra que já foi pensado

### Estrutura de cada ADR

```
Status: [Proposto | Aceito | Substituído | Deprecado]

Contexto: qual problema?
Decisão: o que decidimos.
Alternativas: outras opções e por que não.
Consequências: positivas, negativas, neutras.
```

---

## 📑 Sumário de ADRs

| ID | Título | Status |
|----|--------|--------|
| ADR-001 | Python para o servidor central | ✅ |
| ADR-002 | Go para o agente | ✅ |
| ADR-003 | PostgreSQL como banco relacional | ✅ |
| ADR-004 | Loki em vez de Elasticsearch | ✅ |
| ADR-005 | gRPC com mTLS para agentes | ✅ |
| ADR-006 | Celery como task queue | ✅ |
| ADR-007 | React em vez de Vue/Svelte | ✅ |
| ADR-008 | shadcn/ui em vez de MUI/Chakra | ✅ |
| ADR-009 | Tailwind CSS em vez de CSS-in-JS | ✅ |
| ADR-010 | Monorepo em vez de multi-repo | ✅ |
| ADR-011 | Docker Compose como deploy MVP | ✅ |
| ADR-012 | Sigma rules como padrão de detecção | ✅ |
| ADR-013 | Redis multi-purpose | ✅ |
| ADR-014 | MinIO como object storage | ✅ |
| ADR-015 | FastAPI em vez de Django REST | ✅ |
| ADR-016 | Português como idioma primário | ✅ |
| ADR-017 | Versionamento conjunto dos componentes | ✅ |
| ADR-018 | AGPL-3.0 como licença | 🟡 |
| ADR-019 | JWT em vez de sessions server-side | ✅ |
| ADR-020 | Pydantic v2 para validação | ✅ |

---

## ADR-001: Python para o servidor central

**Status**: ✅ Aceito

### Contexto
Servidor central faz: API REST, processamento de eventos, ML (anomalias), integração com APIs, geração de relatórios. Precisamos de produtividade alta + ecossistema rico para todas essas áreas.

### Decisão
**Python 3.12+** com FastAPI.

### Alternativas
- **Go**: performance superior, mas ecossistema ML pobre, mais boilerplate para CRUD
- **Rust**: performance máxima, mas curva de aprendizado atrasaria muito o projeto
- **Node.js (TS)**: ecossistema bom, mas ML é território do Python
- **Java/Kotlin**: enterprise sólido, mas verbose e startup lento

### Consequências
- ✅ Produtividade alta, ecossistema ML inigualável (scikit-learn, etc.)
- ✅ FastAPI = OpenAPI auto-gerado, Pydantic = validação rápida
- ✅ Mercado quente, ótimo para portfólio
- ❌ Performance bruta inferior a Go/Rust (mitigada com async + workers)
- ❌ GIL pode limitar (mitigado: processos em vez de threads)
- ❌ Imagens Docker maiores (~150MB)

### Notas
- Versão mínima 3.12 por melhor performance
- Async-first em todo lugar (asyncio + asyncpg + httpx)
- Type hints obrigatórios (mypy strict)

---

## ADR-002: Go para o agente

**Status**: ✅ Aceito

### Contexto
Agente roda em todos os hosts monitorados. Requisitos: footprint mínimo, distribuição simples (1 binário), concorrência, sem dependências runtime.

### Decisão
**Go 1.22+**.

### Alternativas
- **Python (PyInstaller)**: binário grande (>50MB), startup lento
- **Rust**: comparável ao Go mas curva de aprendizado adicional
- **C/C++**: performance máxima mas memória manual = bugs de segurança

### Consequências
- ✅ Binário único de ~20MB
- ✅ ~30MB RAM em idle
- ✅ Compilação cruzada trivial (`GOOS=linux GOARCH=arm64 go build`)
- ✅ Goroutines simplificam coletas paralelas
- ❌ Linguagem diferente do servidor (mais context switching)
- ✅ Mostra polyglot no portfólio

### Notas
- Cobra para CLI, Viper para config
- gRPC oficial para comunicação
- GoReleaser para builds reproduzíveis

---

## ADR-003: PostgreSQL como banco relacional

**Status**: ✅ Aceito

### Contexto
Banco relacional para configurações, usuários, alertas, regras. Requisitos: ACID, tipos avançados (UUID, JSONB, IP/CIDR), open-source genuíno.

### Decisão
**PostgreSQL 16**.

### Alternativas
- **MySQL/MariaDB**: tipos avançados inferiores, JSONB menos poderoso
- **MongoDB**: SSPL não é open source genuíno, joins fracos
- **CockroachDB**: overkill para MVP, mudou licença
- **SQLite**: não suporta concorrência alta

### Consequências
- ✅ Tipos `inet`, `cidr`, `uuid`, `jsonb` simplificam schema
- ✅ Particionamento nativo essencial
- ✅ Extensions úteis (`pgcrypto`, `pg_partman`, `pgaudit`)
- ✅ Replicação streaming maduro
- ❌ Configuração inicial mais complexa que MySQL
- ❌ Connection pooling exige PgBouncer em alta carga

### Notas
- Versão 16 (LTS recente)
- PgBouncer em modo transaction
- Particionamento mensal para tabelas grandes

---

## ADR-004: Loki em vez de Elasticsearch

**Status**: ✅ Aceito

### Contexto
Logs são o dado mais volumoso (TBs/ano com 50 hosts). Storage caro = projeto inviável. Precisamos otimizar custo sem sacrificar usabilidade.

### Decisão
**Grafana Loki** como storage primário. OpenSearch como opção avançada futura.

### Alternativas
- **Elasticsearch**: indexação completa = storage 5-10x maior, RAM-hungry, mudança de licença
- **OpenSearch**: open-source mas mesmos custos de RAM/storage
- **ClickHouse**: ótimo para analytics, mas não para busca textual
- **TimescaleDB**: feito para métricas, não logs

### Consequências
- ✅ Custo ~10x menor que Elastic
- ✅ RAM modesta (centenas de MB vs dezenas de GB)
- ✅ Stack natural com Grafana
- ✅ LogQL fácil de aprender
- ❌ Full-text search lento (raramente fazemos isso)
- ❌ Cardinalidade de labels é gargalo (precisa design cuidadoso)

### Notas
- 30 dias quente, 90 em S3 cold
- Labels indexados: host, source, severity, environment

---

## ADR-005: gRPC com mTLS para agentes

**Status**: ✅ Aceito

### Contexto
Comunicação agente ↔ servidor é alta-frequência, precisa ser eficiente, segura, bidirecional e resiliente.

### Decisão
**gRPC com mTLS** (cada agente tem cert único validado contra CA própria).

### Alternativas
- **REST + API key**: overhead de JSON 3-5x, key simétrica
- **REST + JWT**: mesmos problemas, token rotation é dor
- **MQTT**: pub/sub não casa com request/response que precisamos
- **WebSocket custom**: reinventar protocolo

### Consequências
- ✅ Protobuf = 3-10x menos bytes que JSON
- ✅ Streaming bidirecional nativo
- ✅ Geração automática de clientes em Go e Python
- ✅ mTLS = autenticação forte, não-repúdio
- ❌ Curva de aprendizado (Protobuf, gRPC, mTLS, PKI)
- ❌ Debugging mais complexo (não é texto plano)
- ✅ Skill alta no portfólio (gRPC + PKI são tópicos hot)

### Notas
- CA própria gerada na primeira inicialização
- Certs de agentes válidos por 90 dias com rotação automática
- Frontend e API ainda usam REST

---

## ADR-006: Celery como task queue

**Status**: ✅ Aceito

### Contexto
Workloads assíncronos (ML, PDF, notificações, retenção) precisam rodar fora do request HTTP, com filas com prioridade, agendamento, retry.

### Decisão
**Celery 5.3+** com **Redis** como broker.

### Alternativas
- **RQ**: mais simples mas sem cron nativo
- **Dramatiq**: API mais moderna mas comunidade menor
- **Airflow**: overkill (DAGs complexas não é o caso)
- **Temporal**: mais robusto mas stack adicional pesada

### Consequências
- ✅ Maduro, battle-tested
- ✅ Celery Beat para cron jobs nativo
- ✅ Flower para monitoramento
- ✅ Múltiplas filas com prioridade
- ❌ API antiga em alguns lugares
- ❌ Configuração tem muitas opções

### Notas
- Filas: critical, correlation, enrichment, ml, reports, retention, notification
- Prefork com `--concurrency=4`

---

## ADR-007: React em vez de Vue/Svelte

**Status**: ✅ Aceito

### Contexto
Frontend SPA. Considerar comunidade, ecossistema, performance, atratividade no portfólio.

### Decisão
**React 18+** com TypeScript strict.

### Alternativas
- **Vue 3**: API mais limpa mas ecossistema menor para nosso caso
- **Svelte**: bundle menor mas componentes maduros (shadcn) só em React
- **Solid.js**: performance superior mas ecossistema imaturo
- **Angular**: opinionado demais, menos atrativo

### Consequências
- ✅ shadcn/ui nativo para React
- ✅ TanStack Query/Router/Table — todos React-first
- ✅ Mercado prefere React (currículo)
- ✅ Comunidade enorme
- ❌ Re-render hell se mal usado (mitigação: TanStack Query)
- ❌ Bundle maior que Svelte (mitigação: code splitting)

---

## ADR-008: shadcn/ui em vez de MUI/Chakra

**Status**: ✅ Aceito

### Contexto
Biblioteca de componentes UI. Critérios: visual moderno, customizável, acessível, bundle pequeno.

### Decisão
**shadcn/ui** (componentes Radix + Tailwind, copiados para o projeto).

### Alternativas
- **MUI**: completo mas aparência genérica "Material", difícil customizar
- **Chakra**: API agradável mas CSS-in-JS = overhead
- **Ant Design**: visual reconhecível ("é Ant")
- **Mantine**: bom mas comunidade menor

### Consequências
- ✅ Cada componente fica no nosso código (controle total)
- ✅ Tailwind = consistência com resto do projeto
- ✅ Sem CSS-in-JS = melhor performance
- ✅ Acessibilidade Radix
- ✅ Visual distinto e moderno
- ❌ Updates não vêm automaticamente (manual)
- ❌ Inicialmente: cópia manual de cada componente

---

## ADR-009: Tailwind CSS em vez de CSS-in-JS

**Status**: ✅ Aceito

### Contexto
Estilização do frontend.

### Decisão
**Tailwind CSS**.

### Alternativas
- **CSS Modules**: padrão mas verbose
- **Styled-components/Emotion**: runtime overhead, hidratação dolorida em SSR
- **Sass**: não casa bem com componentização
- **vanilla-extract**: CSS-in-JS sem runtime mas comunidade menor

### Consequências
- ✅ Velocidade (utility classes)
- ✅ Consistência forçada via design tokens
- ✅ Bundle final mínimo (purge)
- ✅ Sem runtime overhead
- ✅ Tema (dark/light) via classes utility
- ❌ "HTML poluído" é crítica comum (subjetiva)
- ❌ Curva inicial: memorizar utility names

---

## ADR-010: Monorepo em vez de multi-repo

**Status**: ✅ Aceito

### Contexto
3 grandes componentes (server, agent, web) + docs + deploy.

### Decisão
**Monorepo** com diretórios para cada componente.

### Alternativas
- **Multi-repo**: isolamento mas PRs cross-repo dolorosos, refatoração espalhada
- **Nx/Turborepo**: cache de build mas overhead de tooling
- **Monorepo simples**: estrutura de pastas + Makefile

### Consequências
- ✅ Mudanças cross-component em 1 PR
- ✅ Schema Protobuf compartilhado em `/proto`
- ✅ Documentação unificada em `/docs`
- ✅ 1 CI/CD que entende tudo
- ❌ Repo cresce em tamanho
- ❌ CI pode ser mais demorado (mitigação: paths filters)

### Notas
```
sentinelbr/
├── server/   # Python
├── agent/    # Go
├── web/      # React
├── proto/    # Protobuf compartilhado
├── deploy/   # Docker Compose, Helm, Terraform
├── docs/     # Markdown
└── scripts/  # Utilities
```

---

## ADR-011: Docker Compose como deploy MVP

**Status**: ✅ Aceito

### Contexto
Como deploy de produção do MVP?

### Decisão
**Docker Compose** primário. Helm chart para K8s como opção (Fase 3).

### Alternativas
- **Kubernetes desde início**: overhead operacional gigante, excede MVP
- **Manual + systemd**: difícil reproduzir, updates dolorosos
- **AWS ECS / Cloud Run**: vendor lock-in, custo, não funciona on-premise
- **Docker Swarm**: tecnicamente vivo mas em declínio

### Consequências
- ✅ 1 comando sobe tudo (`docker compose up`)
- ✅ VPS de R$30/mês roda confortavelmente
- ✅ Fácil para SMBs (público alvo)
- ✅ Reproduzível
- ❌ Não escala para múltiplas máquinas (mitigação: oferecer Helm)
- ❌ Failover requer setup adicional

### Notas
- 2 compose files: `docker-compose.yml` (prod) e `docker-compose.dev.yml`
- Volumes nomeados para persistência
- Health checks em todos serviços

---

## ADR-012: Sigma rules como padrão de detecção

**Status**: ✅ Aceito

### Contexto
Engine de detecção precisa expressar regras "se X então alerta".

### Decisão
**Padrão Sigma** (YAML, mantido pela comunidade SOC Prime).

### Alternativas
- **Regras custom em YAML/JSON próprio**: reinventar roda
- **Regras em código Python**: risco de execução de código arbitrário
- **Elastic Detection Rules**: acoplado ao Elastic
- **YARA-L (Chronicle)**: acoplado ao Chronicle

### Consequências
- ✅ Centenas de regras prontas open-source (SigmaHQ)
- ✅ Padrão da indústria SOC
- ✅ pysigma converte para múltiplos backends
- ✅ Curva pequena para analistas
- ❌ Não cobre toda correlação complexa (extendemos com DSL própria)
- ❌ Conversão Sigma→LogQL pode falhar para regras exóticas

### Notas
- pysigma é a biblioteca principal
- Pacote starter de regras curadas
- Para correlação multi-evento, criamos extensão própria

---

## ADR-013: Redis multi-purpose

**Status**: ✅ Aceito

### Contexto
Cache, broker de filas, pub/sub, estado efêmero.

### Decisão
**Redis 7.2+** como solução única (databases separados por uso).

### Alternativas
- **Memcached + RabbitMQ + Redis**: 3 stacks pra operar
- **Apache Kafka para streams**: throughput maior mas overkill

### Consequências
- ✅ Uma única dependência
- ✅ Conhecimento concentrado
- ✅ Redis Streams para event ingestion
- ✅ Sorted sets perfeitos para sliding windows
- ❌ Single point of failure (mitigado com Sentinel/Cluster)
- ❌ Persistência tem trade-offs

### Notas
- DB 0: cache; DB 1: sessões; DB 2: Celery; DB 3: sliding windows; DB 4: rate limit; DB 5: pub/sub
- AOF habilitado (perde no máximo 1s)

---

## ADR-014: MinIO como object storage

**Status**: ✅ Aceito

### Contexto
Armazenamento de arquivos grandes (evidências forenses, relatórios PDF, backups).

### Decisão
**MinIO** (compatível S3 API).

### Alternativas
- **AWS S3 direto**: vendor lock-in, custo, não funciona on-premise
- **NFS**: protocolo arcaico, integração complexa
- **Ceph**: distributed object storage mas overhead de operação

### Consequências
- ✅ Compatível S3 (mesmo código funciona em AWS/GCP/Azure se quiser migrar)
- ✅ Roda self-hosted
- ✅ Maduro, performance boa
- ✅ SSE-S3 para criptografia em repouso
- ❌ Outra dependência para operar
- ❌ Backup do MinIO requer estratégia

---

## ADR-015: FastAPI em vez de Django REST

**Status**: ✅ Aceito

### Contexto
Framework Python para a API.

### Decisão
**FastAPI**.

### Alternativas
- **Django REST Framework**: maduro mas verbose, ORM Django pesa
- **Flask**: minimalista mas precisa montar tudo
- **Litestar**: similar a FastAPI mas comunidade menor
- **Starlette puro**: muito low-level

### Consequências
- ✅ OpenAPI/Swagger auto-gerado
- ✅ Pydantic 2 para validação rápida
- ✅ Async nativo
- ✅ Performance excelente para Python
- ✅ Documentação interativa em `/docs`
- ❌ Auth/admin/etc. precisam ser construídos (DRF traz mais)

---

## ADR-016: Português como idioma primário

**Status**: ✅ Aceito

### Contexto
Mercado alvo (SMBs brasileiras) sofre com ferramentas só em inglês. Diferencial competitivo.

### Decisão
**PT-BR como default**, EN-US como alternativa.

### Alternativas
- **Inglês primary, PT-BR opcional**: padrão tech mas perde diferencial

### Consequências
- ✅ Mercado nacional adoram
- ✅ Mensagens de erro úteis em português (não jargão técnico inglês)
- ✅ Documentação acessível
- ✅ Para LGPD, precisa ser em PT
- ❌ Comunidade global menor (mitigação: EN também disponível)

### Notas
- Strings via i18next
- Documentação técnica bilíngue
- Códigos de erro semânticos (em inglês), mensagens em PT

---

## ADR-017: Versionamento conjunto dos componentes

**Status**: ✅ Aceito

### Contexto
Server, agent, web podem ter versões independentes ou conjunta.

### Decisão
**Versionamento conjunto** (semver). Tag `v1.0.0` aplica a todos.

### Alternativas
- **Versões independentes**: cada componente seu semver
  - ✅ Releases mais granulares
  - ❌ Compatibilidade matrix vira pesadelo
  - ❌ "agent v1.2.3 compatível com server v1.4.x mas não v1.5"

### Consequências
- ✅ Simplicidade absoluta
- ✅ "Estou rodando v1.2.0" responde tudo
- ✅ CI/CD mais simples
- ❌ Patches de UX no frontend bumpam tudo (overhead minor)
- ❌ Quebra de compatibilidade força versionamento de protocolo gRPC

### Notas
- Quebra de compat agente↔servidor → bump de major + janela de compatibilidade
- Schema Protobuf versionado independentemente

---

## ADR-018: AGPL-3.0 como licença

**Status**: 🟡 Em discussão

### Contexto
Projeto será open-source. Qual licença escolher?

### Decisão atual
**AGPL-3.0** (forte copyleft). Aberto a revisão.

### Alternativas
- **MIT/Apache 2.0**: muito permissivas — empresas podem fechar fork e oferecer SaaS sem contribuir de volta
- **GPLv3**: copyleft mas não cobre uso em rede (saas)
- **BSL (Business Source License)**: pode virar AGPL após X anos

### Consequências
- ✅ Quem oferecer SentinelBR como SaaS deve abrir mods
- ✅ Protege contra "AWS effect" (ElasticSearch, Redis)
- ✅ Comunidade orgânica (contribuições voltam)
- ❌ Algumas empresas evitam AGPL (medo legal)
- ❌ Pode reduzir adoção em corporações grandes

### Notas
- Reavaliar quando tiver tração
- Considerar dual licensing (AGPL para comunidade + comercial para empresas)

---

## ADR-019: JWT em vez de sessions server-side

**Status**: ✅ Aceito

### Contexto
Como gerenciar autenticação?

### Decisão
**JWT (access + refresh tokens)** com blocklist em Redis para logout.

### Alternativas
- **Session cookies + Redis**: padrão Django, requer sticky sessions ou backend compartilhado
- **OAuth2 puro**: complexidade desnecessária para internal users

### Consequências
- ✅ Stateless API (mais fácil escalar horizontalmente)
- ✅ Padrão da indústria
- ✅ Frontend pode armazenar e enviar facilmente
- ❌ Logout não é instantâneo (mitigado: blocklist com TTL)
- ❌ Tokens grandes (algumas dezenas de KB se claims pesados)

### Notas
- Access token: 15min
- Refresh token: 7 dias
- Algoritmo: RS256 (assimétrico)
- Logout adiciona JTI ao blocklist Redis até expirar

---

## ADR-020: Pydantic v2 para validação

**Status**: ✅ Aceito

### Contexto
Validação de input/output da API.

### Decisão
**Pydantic v2** em todo lugar (request, response, settings).

### Alternativas
- **Marshmallow**: maduro mas mais verbose
- **attrs + cattrs**: low-level, mais controle mas mais código
- **Validação manual**: nem pensar

### Consequências
- ✅ Performance excepcional (Rust core)
- ✅ Type hints nativo (uma fonte de verdade)
- ✅ Integração nativa com FastAPI
- ✅ Pydantic Settings para config via env
- ❌ Migração de v1 → v2 quebra coisas (mitigado: começamos em v2)

### Notas
- Schemas em `schemas/` separados de models ORM em `models/`
- Validators customizados para regras de negócio
- `model_config = ConfigDict(from_attributes=True)` para mapping ORM

---

## Como manter este documento

### Quando criar novo ADR

Sempre que decisão atender pelo menos um critério:
- Afeta múltiplos componentes
- Trade-off significativo entre alternativas
- Difícil de reverter depois
- Vai gerar perguntas em revisões/entrevistas
- Você levou >1 dia escolhendo

### Quando NÃO criar ADR

- Decisões locais (variável bem nomeada, refactor pequeno)
- "Padrão da comunidade" óbvio (usar package.json em projeto Node)
- Coisas que não afetam arquitetura

### Status

- **Proposto**: discussão aberta
- **Aceito**: decidido e implementado
- **Substituído**: novo ADR mudou o caminho (linkar)
- **Deprecado**: não vale mais, mas mantemos por contexto histórico

### Imutabilidade

ADRs **não são editados** depois de aceitos. Se mudou, cria novo ADR substituindo. Mantém histórico de "pensava-se isso em janeiro, hoje pensamos isso".

---

## Por que esta documentação impressiona

- **Pensamento estruturado**: cada decisão tem contexto, alternativas, consequências
- **Auto-conhecimento técnico**: você sabe exatamente por que escolheu cada coisa
- **Maturidade**: ADRs são padrão de empresas seniores (Google, ThoughtWorks)
- **Honestidade**: lista trade-offs negativos abertamente
- **Lessons learned**: ADRs revelam evolução de pensamento

Em entrevistas: "explica suas escolhas de stack" → você abre este doc e tem uma masterclass pronta.

Posts potenciais no LinkedIn:
- "20 decisões arquiteturais documentadas: o que aprendi escrevendo ADRs"
- "Por que escolhi Loki em vez de Elasticsearch (e quando o oposto faz sentido)"
- "AGPL-3.0 em projeto open-source: o que considerar"
- "JWT vs Sessions em 2026: ainda vale a pena escolher?"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
