# SentinelBR — Arquitetura de Dados e Armazenamento

> Documento técnico-explicativo sobre **toda a camada de dados** da plataforma. Cobre desde conceitos fundamentais (para quem está começando) até detalhes de implementação (schemas, índices, retenção, backup). Pensado para ser lido linearmente: cada seção constrói sobre a anterior.

---

## 📋 Sumário

1. [Antes de começar: conceitos básicos](#antes-de-começar-conceitos-básicos)
2. [Por que múltiplos bancos? (estratégia poliglota)](#por-que-múltiplos-bancos)
3. [Visão geral: quem guarda o quê](#visão-geral-quem-guarda-o-quê)
4. [PostgreSQL — o coração relacional](#postgresql--o-coração-relacional)
5. [Loki — armazenamento de logs](#loki--armazenamento-de-logs)
6. [Redis — cache, filas e estado efêmero](#redis--cache-filas-e-estado-efêmero)
7. [MinIO/S3 — armazenamento de arquivos](#miniots3--armazenamento-de-arquivos)
8. [SQLite — banco local do agente](#sqlite--banco-local-do-agente)
9. [Fluxos de dados ponta-a-ponta](#fluxos-de-dados-ponta-a-ponta)
10. [Estratégia de retenção](#estratégia-de-retenção)
11. [Backup e disaster recovery](#backup-e-disaster-recovery)
12. [Performance e escalabilidade](#performance-e-escalabilidade)
13. [Segurança dos dados](#segurança-dos-dados)
14. [Migrations e versionamento](#migrations-e-versionamento)
15. [Custos estimados](#custos-estimados)
16. [Checklist de implementação](#checklist-de-implementação)

---

## Antes de começar: conceitos básicos

> Esta seção explica conceitos-chave em linguagem simples. Se você já é confortável com bancos de dados, pode pular para [Por que múltiplos bancos](#por-que-múltiplos-bancos).

### O que é um banco de dados?

É um **lugar organizado** para guardar informação que precisa ser acessada depois. Pense numa estante de arquivo gigante onde cada gaveta tem uma etiqueta clara.

A diferença entre "guardar num arquivo de texto" e "guardar num banco de dados" é como a diferença entre **anotar coisas num caderno** versus **ter um sistema de fichário organizado por categoria**:

- Caderno: você anota e depois precisa procurar página por página
- Fichário: você sabe onde cada coisa está, encontra em segundos, várias pessoas podem usar ao mesmo tempo

### Tipos principais de banco

Existem vários "estilos" de banco, cada um bom para um tipo de dado:

#### 1. Relacional (SQL) — tabelas

Imagine **planilhas do Excel conectadas entre si**. Você tem uma tabela de "Usuários" e outra de "Pedidos", e cada pedido tem um link apontando para o usuário que fez. Cada linha é um registro, cada coluna é uma propriedade.

Exemplos: PostgreSQL, MySQL, SQLite.

**Quando usar**: dados estruturados que se relacionam (usuários ↔ permissões, hosts ↔ regras de firewall, etc.).

#### 2. Time-series — série temporal

Otimizados para guardar **muitos dados ao longo do tempo**. Pense num medidor de temperatura que registra valor a cada segundo: você nunca vai querer "atualizar" uma medição passada, só guardar e consultar por período.

Exemplos: Loki (para logs), Prometheus (para métricas), InfluxDB.

**Quando usar**: logs, métricas, eventos com timestamp.

#### 3. Key-value — chave/valor

Como um **dicionário gigante**: você dá uma chave, ele te devolve um valor. Super rápido, mas simples (sem relacionamentos complexos).

Exemplos: Redis, Memcached.

**Quando usar**: cache (guardar resposta para não calcular de novo), sessões de usuário, filas de tarefas.

#### 4. Object storage — armazenamento de arquivos

Como o **Google Drive ou Dropbox**, mas programável. Você guarda arquivos (binários, PDFs, imagens) e recebe uma URL ou ID para baixar depois.

Exemplos: AWS S3, MinIO (versão open-source).

**Quando usar**: arquivos grandes (evidências forenses, relatórios PDF, backups).

### Conceitos importantes

- **Schema**: a "planta baixa" do banco — quais tabelas existem, quais campos cada uma tem, qual é a relação entre elas.
- **Index (índice)**: como o índice de um livro. Em vez de procurar página por página (lento), o banco consulta o índice e vai direto. Sem índices apropriados, qualquer banco fica lento.
- **Migration**: mudança no schema (ex: adicionar uma nova coluna). Migrations são versionadas (igual git) para que todo time aplique na ordem certa.
- **Transaction**: agrupar várias operações em "tudo ou nada" — se uma falha, todas voltam atrás. Crítico para consistência.
- **Replication**: ter cópias do banco em servidores diferentes (para resiliência).
- **Backup**: cópia em outro lugar, fora do servidor principal. Diferente de replication: backup é "foto do passado", replication é "cópia em tempo real".

---

## Por que múltiplos bancos

A primeira reação de quem começa é: **"vou guardar tudo num banco só, é mais simples"**. E está parcialmente certo — para projetos pequenos, isso funciona.

Mas o SentinelBR tem necessidades **muito diferentes** dependendo do tipo de dado:

| Tipo de dado | Volume | Padrão de acesso | Necessidade |
|--------------|--------|------------------|-------------|
| Configurações (usuários, regras) | Pequeno (~MB) | Leitura/escrita constante | Consistência forte, transações |
| Logs/eventos | Enorme (~TB/ano) | Escrita massiva, leitura por período | Compressão, time-based queries |
| Cache de resultados | Pequeno | Leitura ultra-rápida | Latência baixíssima (<5ms) |
| Filas de processamento | Pequeno-médio | FIFO, alta vazão | Pub/sub eficiente |
| Evidências forenses | Médio-grande (arquivos) | Escrita rara, leitura rara | Storage barato e durável |

**Tentar resolver tudo isso com um banco só** ou:
- Usar PostgreSQL para logs → fica caro e lento (não foi feito pra isso)
- Usar Loki para configurações → não tem transações, é horrível pra isso
- Usar Redis para tudo → perde dados quando reinicia, RAM cara

A estratégia **poliglota** (vários bancos, cada um especialista) é o padrão da indústria hoje. **Cada banco faz o que sabe fazer melhor.**

---

## Visão geral: quem guarda o quê

```
┌─────────────────────────────────────────────────────────────┐
│                     SENTINELBR PLATFORM                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────┐
│  PostgreSQL   │   │     Loki      │   │       Redis       │
│               │   │               │   │                   │
│ • Usuários    │   │ • Logs brutos │   │ • Cache           │
│ • Hosts       │   │ • Eventos ECS │   │ • Filas           │
│ • Regras      │   │ • Histórico   │   │ • Sessões         │
│ • Alertas     │   │   completo    │   │ • Sliding windows │
│ • Firewall    │   │   (queryable) │   │ • Rate limiting   │
│ • SELinux cfg │   │               │   │                   │
│ • LGPD        │   └───────────────┘   └───────────────────┘
│ • Auditoria   │
│ • Configs     │   ┌───────────────┐   ┌───────────────────┐
│               │   │   MinIO/S3    │   │  SQLite (Agente)  │
└───────────────┘   │               │   │                   │
                    │ • Evidências  │   │ • Buffer offline  │
                    │ • Relatórios  │   │ • Estado local    │
                    │   PDF         │   │ • Posições logs   │
                    │ • Backups DB  │   │                   │
                    │ • Forense     │   └───────────────────┘
                    │               │
                    └───────────────┘
```

### Resumo rápido por tipo de dado

| O quê | Onde fica | Por quê |
|-------|-----------|---------|
| Usuário e senha | PostgreSQL | Relacional, consistência crítica |
| Permissões/RBAC | PostgreSQL | Relações complexas |
| Inventário de hosts | PostgreSQL | Pequeno, atualizado frequentemente |
| Regras de firewall | PostgreSQL | Configuração versionada |
| Regras Sigma | PostgreSQL (metadata) + arquivos | Metadata estruturada, conteúdo em YAML |
| Alertas | PostgreSQL | Estado, ciclo de vida, comentários |
| Logs brutos | Loki | TBs/ano, queries por período |
| Eventos normalizados | Loki | Mesmo motivo |
| Cache de queries | Redis | Latência baixíssima |
| Sessões JWT (blocklist) | Redis | TTL nativo |
| Filas Celery | Redis | Pub/sub eficiente |
| Sliding windows (correlação) | Redis | Sorted sets ideais para isso |
| Evidências forenses (.tar.gz) | MinIO/S3 | Arquivos grandes, raros |
| Relatórios PDF gerados | MinIO/S3 | Idem |
| Backups do PostgreSQL | MinIO/S3 | Storage frio |
| Buffer local do agente | SQLite | Embedded, sem dependência |

---

## PostgreSQL — o coração relacional

### Por que PostgreSQL (e não MySQL, MariaDB, SQL Server)?

- **Maduro e battle-tested**: 25+ anos, usado por Apple, Instagram, Reddit
- **JSON nativo (JSONB)**: indexável, com operadores ricos — útil para campos flexíveis (ex: contexto de evento)
- **Tipos avançados**: arrays, IP/CIDR nativo (`inet`, `cidr`), UUID, intervalos
- **Extensões poderosas**: pg_partman (particionamento), pgcrypto (criptografia), pgaudit (auditoria), TimescaleDB (time-series sobre PG)
- **Open-source de verdade** (PostgreSQL License, sem pegadinha tipo MongoDB SSPL)
- **Comunidade** brasileira ativa

**Versão alvo**: PostgreSQL 16 (LTS recente, performance melhor que 15).

### Estrutura geral do schema

Vamos organizar em **schemas lógicos** (namespaces dentro do mesmo banco) para evitar bagunça:

```
sentinelbr (database)
├── auth.*         ← usuários, sessões, tokens
├── inventory.*    ← hosts, agentes, tags
├── detection.*    ← regras Sigma, padrões
├── alerts.*       ← alertas, comentários, histórico
├── firewall.*     ← regras, snapshots, blacklist
├── selinux.*      ← denials, policies, booleanos
├── playbook.*     ← playbooks, execuções, actions
├── lgpd.*         ← ativos, tratamentos, incidentes
├── audit.*        ← log de ações da plataforma
└── system.*       ← configs, feature flags, versões
```

### Schema `auth` — autenticação e autorização

#### Tabela `auth.users`

```sql
CREATE TABLE auth.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           CITEXT NOT NULL UNIQUE,
    username        VARCHAR(64) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,           -- Argon2id
    full_name       VARCHAR(120),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_enabled     BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret      TEXT,                    -- TOTP secret (criptografado)
    last_login_at   TIMESTAMPTZ,
    last_login_ip   INET,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ              -- soft delete
);

CREATE INDEX idx_users_email ON auth.users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_active ON auth.users(is_active) WHERE deleted_at IS NULL;
```

**Decisões importantes:**

- `UUID` em vez de `BIGSERIAL`: não vaza informação (quantos usuários existem) e funciona bem em sistemas distribuídos
- `CITEXT` para email: comparação case-insensitive automática
- `password_hash` é Argon2id, não bcrypt (Argon2 é o padrão atual da indústria, vencedor do Password Hashing Competition)
- `mfa_secret` é criptografado em coluna usando `pgcrypto` (chave em variável de ambiente)
- **Soft delete** (`deleted_at`): nunca apagamos usuários de verdade, apenas marcamos. Importante para auditoria LGPD.
- `failed_attempts` + `locked_until`: defesa contra brute force no próprio login

#### Tabela `auth.roles` e `auth.permissions`

```sql
CREATE TABLE auth.roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(64) NOT NULL UNIQUE,
    description TEXT,
    is_system   BOOLEAN NOT NULL DEFAULT FALSE,  -- não pode ser editado
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Roles padrão pré-populados:
-- 'admin', 'analyst', 'viewer', 'auditor', 'dpo'

CREATE TABLE auth.permissions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(128) NOT NULL UNIQUE,  -- ex: 'firewall.rules.create'
    description TEXT NOT NULL,
    module      VARCHAR(32) NOT NULL           -- 'siem', 'firewall', 'selinux', etc.
);

CREATE TABLE auth.role_permissions (
    role_id       UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES auth.permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE auth.user_roles (
    user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_id    UUID NOT NULL REFERENCES auth.roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    granted_by UUID REFERENCES auth.users(id),
    PRIMARY KEY (user_id, role_id)
);
```

**Por que separar permissions de roles?** Porque você pode adicionar uma permissão nova (ex: `firewall.geoblock.manage`) e dar para múltiplos roles sem refatoração. RBAC bem feito.

#### Tabela `auth.api_tokens`

```sql
CREATE TABLE auth.api_tokens (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name         VARCHAR(120) NOT NULL,
    token_hash   TEXT NOT NULL UNIQUE,        -- SHA-256 do token (token real só visto uma vez)
    token_prefix VARCHAR(16) NOT NULL,        -- "sbr_xxxx" (para identificar visualmente)
    scopes       TEXT[] NOT NULL DEFAULT '{}', -- ['siem.read', 'firewall.write']
    expires_at   TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    last_used_ip INET,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at   TIMESTAMPTZ
);

CREATE INDEX idx_tokens_user ON auth.api_tokens(user_id) WHERE revoked_at IS NULL;
CREATE INDEX idx_tokens_hash ON auth.api_tokens(token_hash) WHERE revoked_at IS NULL;
```

**Padrão importante**: nunca guardamos o token em texto puro. Geramos, mostramos UMA VEZ pro usuário, e guardamos só o hash. Se vazar o banco, o atacante não consegue usar os tokens.

### Schema `inventory` — hosts e agentes

#### Tabela `inventory.hosts`

```sql
CREATE TABLE inventory.hosts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hostname        VARCHAR(255) NOT NULL,
    display_name    VARCHAR(120),
    primary_ip      INET,
    all_ips         INET[],                  -- IPs adicionais
    os_family       VARCHAR(32),             -- 'linux', 'windows' (futuro)
    os_distribution VARCHAR(64),             -- 'ubuntu', 'rhel', 'debian'
    os_version      VARCHAR(32),
    kernel_version  VARCHAR(64),
    architecture    VARCHAR(16),             -- 'x86_64', 'aarch64'
    tags            VARCHAR(64)[] NOT NULL DEFAULT '{}',
    metadata        JSONB NOT NULL DEFAULT '{}',  -- campos flexíveis
    enrollment_token TEXT,                   -- token para primeiro registro
    cert_fingerprint TEXT,                   -- fingerprint do cert mTLS
    cert_expires_at  TIMESTAMPTZ,
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
                    -- 'pending', 'online', 'offline', 'disabled'
    last_seen_at    TIMESTAMPTZ,
    agent_version   VARCHAR(32),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_hosts_status ON inventory.hosts(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_hosts_tags ON inventory.hosts USING GIN(tags);
CREATE INDEX idx_hosts_metadata ON inventory.hosts USING GIN(metadata);
CREATE INDEX idx_hosts_last_seen ON inventory.hosts(last_seen_at DESC) WHERE deleted_at IS NULL;
```

**Decisões interessantes:**

- `INET[]`: array de IPs nativo (PostgreSQL é forte nisso)
- `tags VARCHAR[]` com índice GIN: permite query rápida tipo "todos os hosts com tag 'prod'"
- `metadata JSONB`: campos extras que não sabemos de antemão (ex: tipo da VM na cloud, custo mensal, etc.) — flexível sem migrations
- `cert_fingerprint`: identidade criptográfica do agente (evita spoofing)

#### Tabela `inventory.agent_heartbeats` (particionada por tempo)

```sql
CREATE TABLE inventory.agent_heartbeats (
    host_id     UUID NOT NULL REFERENCES inventory.hosts(id) ON DELETE CASCADE,
    received_at TIMESTAMPTZ NOT NULL,
    cpu_usage   REAL,
    mem_usage   REAL,
    disk_usage  JSONB,                       -- {"/": 78.2, "/var": 45.0}
    metrics     JSONB
) PARTITION BY RANGE (received_at);

-- Cria partições mensais (gerenciadas por pg_partman)
CREATE TABLE inventory.agent_heartbeats_2026_05 
    PARTITION OF inventory.agent_heartbeats
    FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
```

**Por que particionar?** Heartbeats são gerados a cada minuto por host. Com 50 hosts, são ~72k registros/dia, ~26M/ano. Sem particionamento, queries ficam lentas e DELETE de dados antigos trava o banco. Com partições mensais, basta `DROP TABLE` da partição antiga para liberar espaço — instantâneo.

### Schema `detection` — regras Sigma

#### Tabela `detection.rules`

```sql
CREATE TABLE detection.rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sigma_id        UUID UNIQUE,             -- ID original da regra Sigma
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    author          VARCHAR(120),
    severity        VARCHAR(16) NOT NULL,    -- 'info','low','medium','high','critical'
    status          VARCHAR(16) NOT NULL DEFAULT 'experimental',
                    -- 'stable', 'test', 'experimental', 'deprecated'
    yaml_content    TEXT NOT NULL,           -- conteúdo bruto do YAML Sigma
    parsed_query    TEXT,                    -- query convertida para LogQL/OpenSearch
    tags            VARCHAR(64)[] NOT NULL DEFAULT '{}',
    mitre_techniques VARCHAR(32)[] NOT NULL DEFAULT '{}',  -- ['T1110.001']
    references      TEXT[] NOT NULL DEFAULT '{}',
    false_positives TEXT[] NOT NULL DEFAULT '{}',
    enabled         BOOLEAN NOT NULL DEFAULT TRUE,
    triggered_count BIGINT NOT NULL DEFAULT 0,
    last_triggered_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID REFERENCES auth.users(id),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_rules_enabled ON detection.rules(enabled) WHERE deleted_at IS NULL;
CREATE INDEX idx_rules_severity ON detection.rules(severity) WHERE enabled AND deleted_at IS NULL;
CREATE INDEX idx_rules_tags ON detection.rules USING GIN(tags);
CREATE INDEX idx_rules_mitre ON detection.rules USING GIN(mitre_techniques);
```

#### Tabela `detection.rule_versions` (histórico)

```sql
CREATE TABLE detection.rule_versions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id      UUID NOT NULL REFERENCES detection.rules(id) ON DELETE CASCADE,
    version      INTEGER NOT NULL,
    yaml_content TEXT NOT NULL,
    changed_by   UUID REFERENCES auth.users(id),
    change_note  TEXT,
    changed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(rule_id, version)
);
```

**Padrão importante**: toda regra tem histórico completo. Se alguém quebra a detecção, basta voltar a versão anterior.

### Schema `alerts` — alertas e investigação

#### Tabela `alerts.alerts`

```sql
CREATE TABLE alerts.alerts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fingerprint     VARCHAR(64) NOT NULL,    -- hash para deduplicação
    rule_id         UUID REFERENCES detection.rules(id),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    severity        VARCHAR(16) NOT NULL,
    status          VARCHAR(16) NOT NULL DEFAULT 'open',
                    -- 'open', 'acknowledged', 'investigating', 'resolved', 'false_positive'
    host_id         UUID REFERENCES inventory.hosts(id),
    source_ip       INET,
    target_user     VARCHAR(120),
    event_count     INTEGER NOT NULL DEFAULT 1,
    first_seen_at   TIMESTAMPTZ NOT NULL,
    last_seen_at    TIMESTAMPTZ NOT NULL,
    enrichment      JSONB NOT NULL DEFAULT '{}',  -- geo, threat intel, contexto
    related_events  TEXT[] NOT NULL DEFAULT '{}',  -- IDs de eventos no Loki
    mitre_techniques VARCHAR(32)[] NOT NULL DEFAULT '{}',
    assigned_to     UUID REFERENCES auth.users(id),
    resolved_at     TIMESTAMPTZ,
    resolved_by     UUID REFERENCES auth.users(id),
    resolution_note TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_alerts_status ON alerts.alerts(status, severity, created_at DESC);
CREATE INDEX idx_alerts_host ON alerts.alerts(host_id, created_at DESC);
CREATE INDEX idx_alerts_fingerprint ON alerts.alerts(fingerprint, status) 
    WHERE status IN ('open', 'acknowledged', 'investigating');
CREATE INDEX idx_alerts_assigned ON alerts.alerts(assigned_to) WHERE status != 'resolved';
```

**Sobre deduplicação por fingerprint**: quando a mesma regra dispara repetidamente para o mesmo IP/host, em vez de criar 100 alertas, agrupamos em um só com `event_count` incrementando e `last_seen_at` atualizando. Reduz fadiga de alerta drasticamente.

#### Tabela `alerts.comments`

```sql
CREATE TABLE alerts.comments (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id   UUID NOT NULL REFERENCES alerts.alerts(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES auth.users(id),
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at  TIMESTAMPTZ
);

CREATE INDEX idx_comments_alert ON alerts.comments(alert_id, created_at);
```

#### Tabela `alerts.timeline`

```sql
CREATE TABLE alerts.timeline (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id   UUID NOT NULL REFERENCES alerts.alerts(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,         -- 'created', 'status_changed', 'action_taken'
    actor_type VARCHAR(16) NOT NULL,         -- 'user', 'system', 'playbook'
    actor_id   UUID,
    details    JSONB NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_timeline_alert ON alerts.timeline(alert_id, occurred_at);
```

### Schema `firewall` — regras e bloqueios

#### Tabela `firewall.rule_sets` (snapshots de configuração)

```sql
CREATE TABLE firewall.rule_sets (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host_id     UUID NOT NULL REFERENCES inventory.hosts(id),
    version     INTEGER NOT NULL,
    backend     VARCHAR(16) NOT NULL,        -- 'nftables', 'iptables', 'firewalld'
    rules       JSONB NOT NULL,              -- array de regras estruturadas
    raw_output  TEXT,                        -- output original do comando
    applied     BOOLEAN NOT NULL DEFAULT FALSE,
    applied_at  TIMESTAMPTZ,
    rollback_of UUID REFERENCES firewall.rule_sets(id),
    created_by  UUID REFERENCES auth.users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(host_id, version)
);

CREATE INDEX idx_rulesets_host_version ON firewall.rule_sets(host_id, version DESC);
CREATE INDEX idx_rulesets_applied ON firewall.rule_sets(host_id, applied_at DESC) WHERE applied;
```

**Padrão IaC**: cada conjunto de regras é uma versão imutável. Aplicar = marcar `applied=true`. Rollback = aplicar uma versão antiga (cria nova versão referenciando a antiga em `rollback_of`). Histórico completo.

#### Tabela `firewall.dynamic_blocks`

```sql
CREATE TABLE firewall.dynamic_blocks (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip          INET NOT NULL,
    host_id     UUID REFERENCES inventory.hosts(id),  -- NULL = global
    reason      VARCHAR(255) NOT NULL,
    source      VARCHAR(32) NOT NULL,        -- 'manual', 'siem', 'playbook'
    triggered_by UUID,                       -- alert_id ou playbook_execution_id
    expires_at  TIMESTAMPTZ,                 -- NULL = permanente
    created_by  UUID REFERENCES auth.users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    removed_at  TIMESTAMPTZ,
    removed_by  UUID REFERENCES auth.users(id)
);

CREATE INDEX idx_blocks_active ON firewall.dynamic_blocks(ip) 
    WHERE removed_at IS NULL AND (expires_at IS NULL OR expires_at > NOW());
CREATE INDEX idx_blocks_expires ON firewall.dynamic_blocks(expires_at) 
    WHERE removed_at IS NULL AND expires_at IS NOT NULL;
```

**Job recorrente**: a cada 5 minutos, rodar `UPDATE ... SET removed_at = NOW() WHERE expires_at < NOW()` para expirar blocos automaticamente.

#### Tabela `firewall.allowlist`

```sql
CREATE TABLE firewall.allowlist (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_range   CIDR NOT NULL,                -- aceita IP único ou rede
    description TEXT NOT NULL,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Regra de negócio: NUNCA bloquear IPs nesta lista, mesmo com SIEM acionando
```

### Schema `selinux`

#### Tabela `selinux.host_status`

```sql
CREATE TABLE selinux.host_status (
    host_id     UUID PRIMARY KEY REFERENCES inventory.hosts(id) ON DELETE CASCADE,
    mode        VARCHAR(16) NOT NULL,        -- 'enforcing', 'permissive', 'disabled'
    policy_type VARCHAR(32),                 -- 'targeted', 'mls'
    policy_version INTEGER,
    last_checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Tabela `selinux.denials`

```sql
CREATE TABLE selinux.denials (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host_id       UUID NOT NULL REFERENCES inventory.hosts(id),
    fingerprint   VARCHAR(64) NOT NULL,      -- para dedup
    scontext      VARCHAR(255) NOT NULL,
    tcontext      VARCHAR(255) NOT NULL,
    tclass        VARCHAR(64) NOT NULL,
    permission    VARCHAR(64) NOT NULL,
    path          TEXT,
    process_comm  VARCHAR(64),
    process_pid   INTEGER,
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_seen_at  TIMESTAMPTZ NOT NULL,
    suggested_fix TEXT,
    status        VARCHAR(16) NOT NULL DEFAULT 'open',
                  -- 'open', 'fixed', 'ignored', 'allowed_via_policy'
    resolved_at   TIMESTAMPTZ,
    resolved_by   UUID REFERENCES auth.users(id),
    UNIQUE(host_id, fingerprint)             -- dedup natural
);

CREATE INDEX idx_denials_host_status ON selinux.denials(host_id, status, last_seen_at DESC);
```

#### Tabela `selinux.applied_policies`

```sql
CREATE TABLE selinux.applied_policies (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host_id      UUID NOT NULL REFERENCES inventory.hosts(id),
    name         VARCHAR(120) NOT NULL,
    te_content   TEXT NOT NULL,              -- conteúdo do .te
    pp_hash      VARCHAR(64) NOT NULL,       -- hash do .pp aplicado
    applied_by   UUID REFERENCES auth.users(id),
    applied_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    rolled_back_at TIMESTAMPTZ
);
```

### Schema `playbook`

#### Tabela `playbook.playbooks`

```sql
CREATE TABLE playbook.playbooks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name         VARCHAR(120) NOT NULL UNIQUE,
    description  TEXT,
    yaml_content TEXT NOT NULL,
    triggers     JSONB NOT NULL,             -- ex: {"rule_ids": ["..."], "manual": true}
    enabled      BOOLEAN NOT NULL DEFAULT TRUE,
    requires_approval BOOLEAN NOT NULL DEFAULT FALSE,
    timeout_seconds INTEGER NOT NULL DEFAULT 300,
    created_by   UUID REFERENCES auth.users(id),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### Tabela `playbook.executions` (particionada)

```sql
CREATE TABLE playbook.executions (
    id            UUID NOT NULL DEFAULT gen_random_uuid(),
    playbook_id   UUID NOT NULL REFERENCES playbook.playbooks(id),
    triggered_by_alert UUID REFERENCES alerts.alerts(id),
    triggered_by_user  UUID REFERENCES auth.users(id),
    triggered_manually BOOLEAN NOT NULL DEFAULT FALSE,
    context       JSONB NOT NULL,            -- variáveis disponíveis no playbook
    status        VARCHAR(16) NOT NULL,      -- 'running','completed','failed','approval_pending'
    started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at  TIMESTAMPTZ,
    error_message TEXT,
    PRIMARY KEY (id, started_at)
) PARTITION BY RANGE (started_at);
```

#### Tabela `playbook.execution_steps`

```sql
CREATE TABLE playbook.execution_steps (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID NOT NULL,
    execution_started_at TIMESTAMPTZ NOT NULL,  -- para FK em tabela particionada
    step_index   INTEGER NOT NULL,
    action_name  VARCHAR(64) NOT NULL,
    inputs       JSONB NOT NULL,
    outputs      JSONB,
    status       VARCHAR(16) NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT
);
```

### Schema `lgpd`

#### Tabela `lgpd.data_assets`

```sql
CREATE TABLE lgpd.data_assets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    asset_type      VARCHAR(32) NOT NULL,    -- 'file','directory','db_table','api_endpoint','bucket'
    location        TEXT NOT NULL,           -- caminho/URI
    host_id         UUID REFERENCES inventory.hosts(id),
    data_categories VARCHAR(32)[] NOT NULL,  -- ['personal','sensitive','minor']
    legal_basis     VARCHAR(64) NOT NULL,    -- 'consent','contract','legitimate_interest','legal_obligation','vital_interests','public_interest'
    purpose         TEXT NOT NULL,
    retention_period INTERVAL,               -- '5 years', '6 months'
    retention_after_what TEXT,               -- "fim do contrato"
    dpo_id          UUID REFERENCES auth.users(id),
    auto_audit_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);
```

#### Tabela `lgpd.data_subjects_requests`

```sql
CREATE TABLE lgpd.data_subjects_requests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type    VARCHAR(32) NOT NULL,    -- 'access','rectification','deletion','portability','objection'
    subject_name    VARCHAR(255) NOT NULL,
    subject_email   CITEXT,
    subject_document VARCHAR(32),            -- CPF/CNPJ (criptografado)
    request_details TEXT NOT NULL,
    status          VARCHAR(32) NOT NULL DEFAULT 'received',
                    -- 'received','identifying','processing','completed','rejected'
    received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deadline_at     TIMESTAMPTZ NOT NULL,    -- prazo legal LGPD
    completed_at    TIMESTAMPTZ,
    response_summary TEXT,
    handled_by      UUID REFERENCES auth.users(id),
    evidence_uri    TEXT                     -- caminho no MinIO
);
```

#### Tabela `lgpd.privacy_incidents`

```sql
CREATE TABLE lgpd.privacy_incidents (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title                VARCHAR(255) NOT NULL,
    description          TEXT NOT NULL,
    severity             VARCHAR(16) NOT NULL,
    affected_subjects    INTEGER,
    affected_data_categories VARCHAR(32)[],
    detected_at          TIMESTAMPTZ NOT NULL,
    contained_at         TIMESTAMPTZ,
    anpd_notified        BOOLEAN NOT NULL DEFAULT FALSE,
    anpd_notified_at     TIMESTAMPTZ,
    subjects_notified    BOOLEAN NOT NULL DEFAULT FALSE,
    subjects_notified_at TIMESTAMPTZ,
    related_alert_ids    UUID[] NOT NULL DEFAULT '{}',
    investigation_notes  TEXT,
    status               VARCHAR(32) NOT NULL DEFAULT 'open',
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Schema `audit` — auditoria interna

```sql
CREATE TABLE audit.events (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_type   VARCHAR(16) NOT NULL,       -- 'user','system','api_token','agent'
    actor_id     UUID,
    actor_name   VARCHAR(255),               -- snapshot do nome
    actor_ip     INET,
    action       VARCHAR(64) NOT NULL,       -- 'firewall.rule.create','user.login.success'
    target_type  VARCHAR(64),
    target_id    UUID,
    target_name  VARCHAR(255),
    changes      JSONB,                      -- antes/depois
    metadata     JSONB NOT NULL DEFAULT '{}',
    success      BOOLEAN NOT NULL,
    error_message TEXT
) PARTITION BY RANGE (occurred_at);

CREATE INDEX idx_audit_actor ON audit.events(actor_id, occurred_at DESC);
CREATE INDEX idx_audit_target ON audit.events(target_type, target_id, occurred_at DESC);
CREATE INDEX idx_audit_action ON audit.events(action, occurred_at DESC);
```

**Crítico**: nunca expor endpoint de DELETE em audit. A integridade desse log é fundamental para LGPD/ISO. Apenas DBA pode tocar (via psql direto, com auditoria adicional no nível do PostgreSQL).

### Estimativa de tamanho do PostgreSQL

Com uma operação típica (50 hosts, 20 usuários, 100 regras, ~7 alertas/dia):

| Tabela | Linhas/ano | Tamanho médio | Total/ano |
|--------|-----------|---------------|-----------|
| auth.* | < 1.000 | < 1 KB | < 1 MB |
| inventory.hosts | 50 | 2 KB | 100 KB |
| inventory.agent_heartbeats | 26M | 200 B | ~5 GB |
| detection.rules | < 500 | 5 KB | 2.5 MB |
| alerts.* | ~3.000 | 5 KB | 15 MB |
| firewall.* | ~10.000 | 2 KB | 20 MB |
| selinux.denials | ~5.000 | 2 KB | 10 MB |
| playbook.executions | ~10.000 | 3 KB | 30 MB |
| lgpd.* | < 5.000 | 5 KB | 25 MB |
| audit.events | ~500.000 | 1 KB | 500 MB |

**Total**: ~6 GB/ano. Cabe num VPS de R$ 30/mês com folga. Particionamento garante crescimento controlado.

---

## Loki — armazenamento de logs

### Por que Loki (e não Elasticsearch)?

Loki é **muito mais barato** que Elastic para logs porque indexa apenas labels (não o conteúdo inteiro). Para o nosso caso de uso (consultar logs por host/severidade/período), isso é perfeito.

| Aspecto | Loki | Elasticsearch |
|---------|------|---------------|
| Custo de storage | ~10x menor | Alto |
| Custo de RAM | Muito baixo | Alto |
| Velocidade de busca textual | Lenta | Rápida |
| Velocidade por label | Rápida | Rápida |
| Setup | Simples | Complexo |
| Indicado para | Logs com queries por tempo+label | Busca textual avançada |

**Para o MVP**, Loki vence. Para v2, podemos oferecer OpenSearch como alternativa para clientes que precisam de full-text search.

### Como Loki organiza dados

Loki funciona com **streams** (fluxos), cada um identificado por **labels** (rótulos):

```
{host="web-01", source="sshd", severity="high"} 
  → linhas de log com timestamp + texto livre
```

### Estratégia de labels

**Importantíssimo**: labels têm "cardinalidade" — quanto mais valores distintos, mais lento o Loki fica. Regra de ouro:

✅ **Bons labels** (poucos valores possíveis):
- `host` (50 hosts = OK)
- `source` (sshd, nginx, auditd... ~20 valores)
- `severity` (5 valores)
- `module` (siem, firewall, selinux...)
- `environment` (prod, staging, dev)

❌ **Maus labels** (muitos valores possíveis):
- `user_id` (milhares de usuários)
- `request_id` (infinitos)
- `ip` (milhões possíveis)
- `timestamp` (todos diferentes)

Esses ficam **dentro do conteúdo do log** (queryable via LogQL com filtros), não como label.

### Estrutura de eventos enviados

Cada evento processado pelo agente vira uma linha em Loki:

```json
// Labels (indexados):
{
  "host": "web-01",
  "source": "sshd",
  "severity": "info",
  "environment": "prod"
}

// Conteúdo (texto livre estruturado em JSON):
{
  "@timestamp": "2026-05-09T14:23:45.123Z",
  "event": {
    "category": "authentication",
    "action": "failed_login",
    "outcome": "failure"
  },
  "source": {
    "ip": "203.0.113.42",
    "port": 38241,
    "geo": {
      "country": "CN",
      "city": "Beijing",
      "asn": 4134
    }
  },
  "user": {
    "name": "root",
    "target": true
  },
  "host": {
    "name": "web-01",
    "ip": "10.0.1.5",
    "os": {"family": "linux"}
  },
  "rule_matches": ["ssh_brute_force_v2"],
  "raw": "Failed password for root from 203.0.113.42 port 38241 ssh2"
}
```

### Queries LogQL típicas

```logql
# Todos os eventos de SSH no web-01 nas últimas 24h
{host="web-01", source="sshd"}

# Falhas de login no último hour
{source="sshd"} | json | event_action="failed_login"

# Eventos de severidade alta com IP de origem específico
{severity="high"} | json | source_ip="203.0.113.42"

# Taxa de eventos por minuto
rate({host="web-01"}[5m])
```

### Configuração de retenção

```yaml
# loki-config.yaml
limits_config:
  retention_period: 720h  # 30 dias quente

compactor:
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

# Eventos críticos: arquivados em S3 com retenção de 1 ano
storage_config:
  aws:
    s3: s3://sentinelbr-logs-cold
```

### Estimativa de volume

50 hosts gerando ~200 eventos/segundo no total = ~17M eventos/dia = ~6 bilhões/ano.

Com compressão típica do Loki (~10:1 para logs JSON), isso dá:
- 30 dias quentes: ~50 GB
- 90 dias frios: ~150 GB
- **Total**: 200 GB de armazenamento

Com S3 ($0.023/GB/mês), isso custa ~$5/mês. Mesmo no Hetzner local (storage NVMe), cabe num servidor de 500 GB.

---

## Redis — cache, filas e estado efêmero

Redis tem múltiplas funções na plataforma. Para evitar acoplamento, usamos **databases diferentes** (Redis suporta até 16 dbs numerados):

```
DB 0: Cache de queries
DB 1: Sessões e blocklist JWT
DB 2: Filas Celery
DB 3: Sliding windows (correlação SIEM)
DB 4: Rate limiting
DB 5: Pub/sub (notificações realtime)
```

### DB 0 — Cache

```
KEY: cache:host:550e8400-...:summary
VALUE: {"events_24h": 1234, "alerts": 2, ...}
TTL: 60 segundos
```

Usado para:
- Resumos de dashboard (evita hit no PostgreSQL toda hora)
- Resultados de enriquecimento GeoIP
- Reverse DNS

**Padrão**: cache-aside. Se não existe, busca no banco fonte e popula. Invalidação por TTL ou explícita em writes.

### DB 1 — Sessões e tokens

```
KEY: jwt:blocklist:<jti>
VALUE: 1
TTL: tempo restante até expirar o token

KEY: session:<session_id>
VALUE: {"user_id": "...", "ip": "...", "last_activity": "..."}
TTL: 3600 segundos (renovado a cada request)
```

### DB 2 — Filas Celery

Celery usa Redis como broker. Filas separadas por prioridade:

```
queue:critical   ← alertas críticos, ações de bloqueio
queue:high       ← processamento de regras, enriquecimento
queue:normal     ← jobs gerais
queue:low        ← relatórios, exports, manutenção
```

### DB 3 — Sliding windows (correlação)

Estrutura crítica do SIEM. Para detectar "5 falhas em 60s", usamos **sorted sets**:

```
KEY: window:ssh_failures:203.0.113.42
TYPE: ZSET
VALUE: [(timestamp1, event_id1), (timestamp2, event_id2), ...]

# Adicionar evento
ZADD window:ssh_failures:203.0.113.42 1715269425 "evt_abc123"

# Limpar eventos antigos (mais de 60s)
ZREMRANGEBYSCORE window:ssh_failures:203.0.113.42 -inf (NOW - 60)

# Contar quantos eventos restam
ZCARD window:ssh_failures:203.0.113.42

# Se >= 5, dispara alerta
```

**Por que sorted sets?** Operações `O(log N)`, fácil de limpar por range temporal, eficiente em memória.

### DB 4 — Rate limiting

Implementação **token bucket** para limitar requests:

```
KEY: ratelimit:user:<user_id>:minute
TYPE: STRING (counter)
TTL: 60 segundos

# Em cada request
INCR ratelimit:user:abc:minute
EXPIRE ratelimit:user:abc:minute 60 NX  # só se ainda não tem TTL

# Se valor > limite, recusa
```

Mais sofisticado: **sliding window** com sorted sets (igual correlação acima) para precisão.

### DB 5 — Pub/Sub

Para notificações em tempo real ao frontend (via WebSocket):

```
PUBLISH alerts:new {"alert_id": "...", "severity": "high"}
PUBLISH host:status:web-01 {"status": "offline"}
```

Backend assina canais e propaga via WebSocket aos clientes conectados.

### Persistência

Redis pode perder dados em crash. Estratégia:

- **Cache (DB 0)**: pode perder, irrelevante (recomputa)
- **Sessões (DB 1)**: pode perder (usuário só relogga)
- **Filas (DB 2)**: AOF (Append-Only File) com `everysec` — perde no máximo 1s de fila
- **Sliding windows (DB 3)**: pode perder (só perde correlação histórica curta)
- **Rate limiting (DB 4)**: pode perder
- **Pub/sub (DB 5)**: efêmero por natureza

**Configuração de produção**: AOF habilitado (custo: ~10% performance), snapshots RDB a cada 5min.

---

## MinIO/S3 — armazenamento de arquivos

### Por que MinIO?

MinIO é uma implementação **open-source compatível com S3** que você pode rodar no seu próprio servidor. Para clientes que querem cloud, é só apontar para AWS/GCP/Azure — **mesmo código**.

### Buckets e organização

```
sentinelbr-evidences/        ← evidências forenses
  /year=2026/month=05/day=09/
    /<incident_id>/
      ps_auxf.txt
      ss_tunap.txt
      proc_<pid>_core.gz
      hashes.txt
      manifest.json

sentinelbr-reports/           ← relatórios gerados
  /lgpd/
    /<year>/<month>/
      RIPD_<asset_id>.pdf
      operations_<period>.pdf
  /audit/
    ...

sentinelbr-backups/           ← backups do PostgreSQL
  /daily/
    backup_2026-05-09.dump.gz
  /weekly/
  /monthly/

sentinelbr-policies/          ← policies SELinux geradas
  /<host_id>/
    /<policy_id>/
      policy.te
      policy.pp
```

### Padrões de uso

**Upload de evidência forense:**

```python
# Backend gera presigned URL para o agente fazer upload direto
url = minio_client.presigned_put_object(
    bucket="sentinelbr-evidences",
    object_name=f"year=2026/month=05/.../{incident_id}/evidence.tar.gz",
    expires=timedelta(minutes=15)
)
# Retorna URL para o agente, que faz PUT direto no MinIO
# Backend não precisa ser proxy de bytes (escala melhor)
```

**Geração de relatório:**

```python
# Worker Celery gera PDF
pdf_bytes = generate_lgpd_report(...)

# Upload para MinIO
minio_client.put_object(
    bucket="sentinelbr-reports",
    object_name=f"lgpd/2026/05/RIPD_{asset_id}.pdf",
    data=io.BytesIO(pdf_bytes),
    length=len(pdf_bytes),
    content_type="application/pdf"
)

# Salva referência no PostgreSQL
INSERT INTO lgpd.generated_reports(...) VALUES (...)
```

### Lifecycle policies

Configurar lifecycle no bucket para mover/deletar automaticamente:

```json
{
  "Rules": [
    {
      "ID": "evidences-retention",
      "Status": "Enabled",
      "Transitions": [
        {"Days": 90, "StorageClass": "STANDARD_IA"},
        {"Days": 365, "StorageClass": "GLACIER"}
      ],
      "Expiration": {"Days": 1825}  // 5 anos
    },
    {
      "ID": "backups-retention",
      "Filter": {"Prefix": "daily/"},
      "Expiration": {"Days": 30}
    }
  ]
}
```

### Criptografia

- **Em trânsito**: TLS obrigatório
- **Em repouso**: SSE-S3 (gerenciado pelo MinIO) ou SSE-KMS (chaves do cliente para LGPD)

---

## SQLite — banco local do agente

O agente roda em todos os hosts monitorados. Ele precisa de um banco **embarcado** (sem dependência de servidor) para:

1. **Buffer offline**: se o servidor central cai, eventos não se perdem
2. **Estado de leitura**: posição em cada arquivo de log (para não duplicar)
3. **Cache de configuração**: regras de coleta locais

### Schema do agente

```sql
-- Eventos pendentes de envio
CREATE TABLE pending_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,           -- ISO 8601
    payload BLOB NOT NULL,             -- JSON gzipped
    attempts INTEGER NOT NULL DEFAULT 0,
    next_retry_at TEXT
);

CREATE INDEX idx_pending_retry ON pending_events(next_retry_at);

-- Estado de leitura de cada fonte
CREATE TABLE log_sources (
    path TEXT PRIMARY KEY,
    inode INTEGER NOT NULL,            -- detecta rotação
    position INTEGER NOT NULL,         -- byte offset
    last_read_at TEXT NOT NULL
);

-- Configuração local (pulled do servidor central)
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Métricas locais (CPU, RAM, etc.) bufferizadas
CREATE TABLE metrics (
    timestamp TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    value REAL NOT NULL
);

CREATE INDEX idx_metrics_time ON metrics(timestamp);
```

### Configuração

- **Tamanho máximo**: 500MB (configurável). Quando atinge, descarta eventos mais antigos com aviso.
- **Modo WAL** (`PRAGMA journal_mode=WAL`): permite leitura concorrente com escrita
- **Sync normal**: balanço entre durabilidade e performance
- **Backup**: nenhum (é apenas buffer)

### Comportamento de envio

```
1. Coletor lê linha de log → cria evento estruturado
2. INSERT em pending_events
3. Worker de envio: SELECT lote (~100 eventos)
4. POST para servidor central via gRPC com mTLS
5. Sucesso: DELETE dos eventos enviados
6. Falha: UPDATE attempts++, next_retry_at = now + backoff
```

Backoff exponencial: 5s, 10s, 30s, 1min, 5min, 15min, máximo 1h.

---

## Fluxos de dados ponta-a-ponta

### Fluxo 1: Login bem-sucedido

```
1. Frontend → POST /api/v1/auth/login (email, senha)
2. Backend:
   - SELECT FROM auth.users WHERE email = ?
   - Verifica password_hash com Argon2
   - Verifica failed_attempts e locked_until
   - UPDATE last_login_at, last_login_ip
   - Gera JWT com claims (user_id, roles, jti)
3. Backend → INSERT audit.events (action='user.login.success')
4. Frontend recebe access_token + refresh_token
5. Redis: SET session:<id> com TTL 1h
```

### Fluxo 2: Evento de log até alerta

```
1. Servidor "web-01": SSH falha de login registrada em /var/log/auth.log
2. Agente: tail detecta nova linha
3. Agente: parsing → estrutura ECS → INSERT em SQLite (pending_events)
4. Agente worker: SELECT batch → gRPC POST para servidor central
5. Servidor central API:
   - Valida mTLS do agente
   - Identifica host pelo cert fingerprint
   - PUBLISH evento no Redis Stream "events:raw"
6. Worker Celery (consumer):
   - Enriquece (GeoIP, threat intel)
   - INSERT no Loki como nova linha
   - Para cada regra Sigma habilitada:
     - Aplica filtro
     - Se match: incrementa sliding window no Redis
     - Se contagem excede limite:
       - INSERT alerts.alerts (ou UPDATE event_count se fingerprint existe)
       - INSERT alerts.timeline (event='created')
       - PUBLISH "alerts:new" no Redis pub/sub
       - Dispara playbooks aplicáveis (cria playbook.executions)
7. Frontend (WebSocket conectado): recebe evento "alerts:new"
8. UI atualiza badge de alertas
```

### Fluxo 3: Bloqueio automático de IP

```
1. Alerta criado (fluxo 2 acima)
2. Playbook engine: avalia triggers, encontra "Brute Force SSH"
3. Cria playbook.executions (status='running')
4. Executa step 1: firewall.block_ip
   - INSERT firewall.dynamic_blocks (ip, expires_at = NOW + 1h)
   - Envia comando ao agente do host alvo via gRPC
   - Agente: nft add element inet filter blacklist {203.0.113.42}
   - Agente confirma
   - INSERT execution_steps (status='completed')
5. Executa step 2: notify.telegram
   - HTTP POST para Telegram Bot API
   - INSERT execution_steps (status='completed')
6. UPDATE playbook.executions SET status='completed'
7. INSERT audit.events (action='firewall.block_ip.auto')
8. INSERT alerts.timeline (event='action_taken', action='block_ip')
```

### Fluxo 4: Geração de relatório LGPD

```
1. DPO no frontend: clica "Gerar relatório de operações"
2. Frontend → POST /api/v1/lgpd/reports/generate
3. Backend:
   - Valida permissão lgpd.reports.generate
   - INSERT lgpd.generated_reports (status='pending')
   - Envia job para Celery: queue:low
4. Worker Celery:
   - SELECT lgpd.data_assets
   - SELECT eventos relacionados no Loki
   - Renderiza template Jinja2 → HTML
   - WeasyPrint: HTML → PDF
   - PUT no MinIO: sentinelbr-reports/lgpd/2026/05/...
   - UPDATE lgpd.generated_reports SET status='completed', file_uri='...'
   - PUBLISH "report:ready:<user_id>" no Redis
5. Frontend recebe notificação, mostra link de download
6. Click no download → GET /api/v1/lgpd/reports/<id>/download
7. Backend gera presigned URL no MinIO (TTL 5min)
8. Browser baixa direto do MinIO
```

---

## Estratégia de retenção

### Princípios

1. **LGPD-friendly**: dados pessoais não podem ficar mais que o necessário
2. **Útil para investigação**: 30-90 dias quente, 1 ano frio é razoável
3. **Auditoria precisa**: logs de auditoria têm retenção mais longa
4. **Custo controlado**: dados antigos vão para storage frio (mais barato)

### Tabela de retenção

| Tipo de dado | Quente (online) | Frio (arquivado) | Hard delete |
|--------------|-----------------|------------------|-------------|
| Logs brutos (Loki) | 30 dias | 90 dias em S3 | 1 ano |
| Eventos de auditoria | 90 dias | 5 anos em S3 | 7 anos |
| Heartbeats de agente | 30 dias | — | 90 dias |
| Alertas resolvidos | 1 ano | 3 anos | 5 anos |
| Alertas abertos | infinito | — | nunca enquanto aberto |
| Execuções de playbook | 90 dias | 1 ano | 2 anos |
| Evidências forenses | 90 dias quente | 5 anos cold storage | conforme caso |
| SELinux denials resolvidos | 90 dias | — | 1 ano |
| Rule sets de firewall (snapshots) | últimos 100 | — | resto deletado |
| Backups DB | 30 daily, 12 weekly, 12 monthly | — | rotação |

### Implementação

**PostgreSQL**: jobs `pg_cron` ou Celery Beat:

```sql
-- Diário às 3h
DELETE FROM inventory.agent_heartbeats 
WHERE received_at < NOW() - INTERVAL '90 days';

-- Particionamento: drop de partição antiga é instantâneo
DROP TABLE inventory.agent_heartbeats_2025_11;
```

**Loki**: retenção nativa configurada (ver seção Loki).

**MinIO**: lifecycle policies (ver seção MinIO).

**Compliance LGPD**: para cada `data_asset`, respeitar `retention_period`. Job verifica e dispara processo de eliminação dos dados pessoais (com registro em `audit.events`).

---

## Backup e disaster recovery

### O que pode ser perdido

| Sistema | Aceitável perder | Por quê |
|---------|------------------|---------|
| Cache Redis | Tudo | Recomputável |
| Sessões Redis | Tudo | Usuário só relogga |
| SQLite agente | Buffer recente (até 5min) | Acceptable em crash |
| Loki recente (1h) | Em casos extremos | Re-ingestão possível se agente tem buffer |
| **PostgreSQL** | **Praticamente nada** | **Estado mestre da plataforma** |
| MinIO | Nada | Evidências legais, relatórios |

### Estratégia de backup do PostgreSQL

#### Backup full diário

```bash
#!/bin/bash
# /etc/cron.daily/sentinelbr-backup-pg

DATE=$(date +%Y-%m-%d)
PGPASSWORD=$DB_PASS pg_dump \
  -h localhost -U sentinelbr \
  --format=custom --compress=9 \
  --file=/tmp/sentinelbr_${DATE}.dump \
  sentinelbr

# Upload para MinIO
mc cp /tmp/sentinelbr_${DATE}.dump \
  minio/sentinelbr-backups/daily/sentinelbr_${DATE}.dump

# Verifica integridade
pg_restore --list /tmp/sentinelbr_${DATE}.dump > /dev/null
echo "Backup OK: ${DATE}"

# Cleanup local
rm /tmp/sentinelbr_${DATE}.dump
```

#### WAL archiving (recovery point < 1 min)

```ini
# postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'mc cp %p minio/sentinelbr-wal/%f'
```

Permite **Point-in-Time Recovery (PITR)**: restaurar para qualquer momento dos últimos 7 dias com precisão de segundos.

#### Replicação stream (alta disponibilidade)

Para v2.0 com HA: standby replica em outro servidor recebe WAL streaming. Failover manual ou automático com Patroni.

### Restore — testado regularmente

**Princípio**: backup que nunca foi testado **não é backup**. Mensalmente:

```bash
#!/bin/bash
# Cria container temporário, restaura backup, valida
docker run -d --name pg-restore-test postgres:16
sleep 10
docker exec pg-restore-test psql -U postgres -c "CREATE DATABASE test_restore;"
mc cp minio/sentinelbr-backups/daily/latest.dump /tmp/
docker cp /tmp/latest.dump pg-restore-test:/tmp/
docker exec pg-restore-test pg_restore -d test_restore /tmp/latest.dump

# Valida
docker exec pg-restore-test psql -d test_restore -c "
  SELECT count(*) FROM auth.users;
  SELECT count(*) FROM inventory.hosts;
  SELECT count(*) FROM alerts.alerts;
"

# Cleanup
docker rm -f pg-restore-test
```

### RTO e RPO (objetivos)

- **RPO (Recovery Point Objective)**: quanto de dados podemos perder
  - PostgreSQL: 1 minuto (com WAL archiving)
  - MinIO: 0 (replicação ativa)
  - Loki: 5 minutos
  
- **RTO (Recovery Time Objective)**: quanto tempo para voltar a operar
  - PostgreSQL standalone: 30 minutos (restore + start)
  - PostgreSQL com standby: 1 minuto (failover)
  - Plataforma completa: 1 hora (incluindo todos os componentes)

---

## Performance e escalabilidade

### Limites do MVP (single-server)

Numa VPS de 4 vCPU + 8 GB RAM (~R$ 100/mês):

- **Hosts monitorados**: até 100
- **Eventos/segundo**: até 500
- **Usuários simultâneos**: até 50
- **Alertas/dia**: até 1.000

### Pontos de gargalo previstos

#### 1. Inserção massiva no PostgreSQL

Heartbeats e alertas em volume podem saturar.

**Mitigações**:
- Particionamento (já planejado)
- Batch inserts (`COPY` em vez de `INSERT` quando possível)
- Connection pooling com PgBouncer
- Índices apenas no necessário (índice é caro em writes)

#### 2. Ingestão no Loki

500 eventos/s é OK; 5.000/s exige tunning.

**Mitigações**:
- Múltiplos ingestors (escala horizontal)
- Buffer no Redis Stream antes do Loki
- Compressão gzip dos batches do agente

#### 3. Queries lentas no dashboard

Dashboard roda dezenas de queries por refresh.

**Mitigações**:
- Cache agressivo no Redis (TTL 30s)
- Materialized views para agregações pesadas
- Refresh assíncrono (frontend mostra cached, atualiza em background)

#### 4. Sliding windows na correlação

Com muitos IPs únicos, milhões de chaves no Redis.

**Mitigações**:
- TTL agressivo nas chaves
- Limpeza periódica
- Sharding do Redis (futuro)

### Caminho para escalar (v2+)

```
MVP (single server)
  ↓
v1: separar componentes em VMs distintas
  - 1 VM: PostgreSQL
  - 1 VM: Redis
  - 1 VM: API + workers
  - 1 VM: Loki + MinIO
  ↓
v2: scale-out
  - PostgreSQL: streaming replication + read replicas
  - Redis: cluster mode
  - API: múltiplas instâncias atrás de load balancer
  - Workers: horizontal scaling no Celery
  - Loki: distributed mode
  ↓
v3: Kubernetes
  - HPA (autoscaling) por carga
  - Database operators (Zalando, CloudNativePG)
```

---

## Segurança dos dados

### Criptografia em repouso

| Dado | Onde | Como |
|------|------|------|
| Senhas (hash) | PostgreSQL | Argon2id (não é encrypt, é hash) |
| MFA secrets | PostgreSQL | pgcrypto AES-256 (chave em env) |
| API tokens | PostgreSQL | SHA-256 (apenas hash, não recuperável) |
| CPFs/CNPJs (LGPD) | PostgreSQL | pgcrypto AES-256 |
| Backups | MinIO | SSE-S3 |
| Evidências forenses | MinIO | SSE-S3 |

### Criptografia em trânsito

- **Frontend ↔ API**: HTTPS obrigatório (Let's Encrypt para certificados)
- **API ↔ PostgreSQL**: SSL com cert-based auth
- **API ↔ Redis**: TLS habilitado
- **Agente ↔ API**: mTLS (cliente e servidor autenticados)
- **API ↔ MinIO**: HTTPS

### Princípio do menor privilégio (banco)

Usuários PostgreSQL específicos por componente:

```sql
-- Usuário da API (CRUD na maioria)
CREATE USER sentinelbr_api WITH PASSWORD '...';
GRANT USAGE ON SCHEMA auth, inventory, alerts TO sentinelbr_api;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA auth TO sentinelbr_api;
-- DELETE proibido em audit.events

-- Usuário de leitura (relatórios, dashboards)
CREATE USER sentinelbr_readonly WITH PASSWORD '...';
GRANT USAGE ON SCHEMA inventory, alerts, lgpd TO sentinelbr_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA inventory, alerts, lgpd TO sentinelbr_readonly;

-- Usuário de migrações (apenas durante deploy)
CREATE USER sentinelbr_migrator WITH PASSWORD '...' SUPERUSER;
-- Habilitar/desabilitar conforme necessário
```

### LGPD: dados pessoais no próprio banco

**Reflexão importante**: a plataforma armazena dados pessoais (usuários, IPs, hostnames). Nós também precisamos seguir LGPD!

Práticas:
- Consentimento no cadastro
- Possibilidade de exportar dados do usuário (portabilidade)
- Soft delete + hard delete depois de período legal
- Pseudonimização em logs (hash de email em vez de email puro)
- DPO definido para o produto

---

## Migrations e versionamento

### Ferramenta: Alembic (Python)

Alembic é o padrão para SQLAlchemy/Python. Cada mudança de schema gera arquivo versionado:

```
migrations/
  versions/
    20260101_001_initial_schema.py
    20260115_002_add_mfa_to_users.py
    20260201_003_create_lgpd_schema.py
    ...
```

### Princípios

1. **Forward-only por padrão**: rollback de migration é arriscado em produção. Em vez de rollback, criar nova migration corrigindo.
2. **Backwards-compatible quando possível**: adicionar coluna opcional, depois deploy do código que usa, depois (em outra migration) torna obrigatória.
3. **Migrations rodam automaticamente em deploy**: idempotente, seguras de rodar múltiplas vezes.
4. **Sem código de aplicação dentro de migrations**: apenas DDL e DML simples.

### Exemplo de migration

```python
"""add mfa columns to users

Revision ID: 002_add_mfa
Revises: 001_initial_schema
Create Date: 2026-01-15
"""

from alembic import op
import sqlalchemy as sa

revision = '002_add_mfa'
down_revision = '001_initial_schema'

def upgrade():
    op.add_column('users',
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        schema='auth'
    )
    op.add_column('users',
        sa.Column('mfa_secret', sa.Text(), nullable=True),
        schema='auth'
    )

def downgrade():
    op.drop_column('users', 'mfa_secret', schema='auth')
    op.drop_column('users', 'mfa_enabled', schema='auth')
```

### Seed data

Dados iniciais necessários (roles, permissions, regras Sigma exemplo) entram em scripts separados:

```
seeds/
  001_default_roles.sql
  002_default_permissions.sql
  003_sigma_rules_starter_pack.py  # importa de arquivos YAML
```

Rodam após `alembic upgrade head` na primeira instalação.

---

## Custos estimados

### Cenário: empresa pequena (10 hosts, 5 usuários)

**Self-hosted em VPS:**
- 1 VPS Hetzner CPX21 (4 vCPU, 8 GB RAM, 80 GB SSD): ~€8/mês (~R$ 50)
- Backup S3-compatible (Backblaze B2): ~$1/mês (~R$ 5)
- Domínio + Let's Encrypt: ~R$ 50/ano
- **Total: ~R$ 60/mês**

**Cloud (AWS):**
- t3.medium (4 vCPU, 4 GB) Reserved 1y: ~$30/mês (~R$ 150)
- RDS PostgreSQL db.t3.micro: ~$15/mês (~R$ 75)
- S3 (50 GB): ~$1/mês
- **Total: ~R$ 230/mês**

### Cenário: empresa média (50 hosts, 20 usuários)

**Self-hosted:**
- 1 VPS Hetzner CPX41 (8 vCPU, 16 GB RAM, 240 GB): ~€30/mês (~R$ 180)
- Backup B2 (200 GB): ~$5/mês
- **Total: ~R$ 220/mês**

**Cloud:**
- 2 EC2 t3.large + RDS db.t3.medium + ElastiCache + S3: ~$200/mês (~R$ 1.000)

**Diferencial**: a plataforma roda **muito barato** quando self-hosted graças a escolhas de stack (Loki em vez de Elasticsearch é o maior fator).

---

## Checklist de implementação

Para você seguir quando começar a codar, na ordem sugerida:

### Fase 1 — Fundação

- [ ] Setup do PostgreSQL com extensions (`citext`, `pgcrypto`, `pg_partman`)
- [ ] Schema base: `auth`, `inventory`, `audit`, `system`
- [ ] Alembic configurado com primeira migration
- [ ] Seed data: roles e permissions padrão
- [ ] Setup do Redis (databases separados)
- [ ] Setup do Loki + Promtail/Grafana para visualização interna
- [ ] MinIO/S3 com buckets criados e lifecycle configurado
- [ ] Docker Compose com tudo acima
- [ ] Conexões TLS configuradas entre componentes
- [ ] Backup automático do PostgreSQL funcionando

### Fase 2 — Coleta e armazenamento

- [ ] Schema do agente SQLite
- [ ] Pipeline de ingestão: agente → API → Redis → Loki
- [ ] Particionamento de tabelas grandes (heartbeats, audit, executions)
- [ ] Schema `detection` + import de regras Sigma starter pack
- [ ] Schema `alerts` + lógica de fingerprint/dedup
- [ ] Schema `firewall` (rule_sets, dynamic_blocks, allowlist)
- [ ] Sliding windows no Redis para correlação

### Fase 3 — Operação

- [ ] Schema `selinux` + collectors de AVC
- [ ] Schema `playbook` + engine
- [ ] Schema `lgpd` completo
- [ ] Materialized views para dashboards
- [ ] Caching strategy completa
- [ ] Rate limiting em todos os endpoints

### Fase 4 — Robustez

- [ ] WAL archiving + PITR testado
- [ ] Restore mensal automatizado
- [ ] Replicação para HA (v2)
- [ ] Migrations testadas em ambiente de staging
- [ ] Documentação de runbooks (o que fazer se X cair)
- [ ] Alertas de saúde do próprio banco (espaço, slow queries, replication lag)

---

## Por que essa arquitetura impressiona no portfólio

Esta documentação demonstra:

- **Decisões técnicas justificadas**: cada escolha tem trade-off explicado (não copy-paste de tutorial)
- **Pensamento em escala**: design para 100 hosts mas com caminho claro para 10.000
- **Conhecimento poliglota**: 4 paradigmas de banco usados apropriadamente
- **Senioridade em modelagem**: schemas, índices, particionamento, criptografia
- **Operação em mente**: backup, retenção, custos, migrations
- **Compliance integrada**: LGPD não é gambiarra de última hora
- **Custo-consciente**: arquitetura roda a R$ 60/mês, não exige Kubernetes

Cada seção aqui é potencial **post de LinkedIn técnico**:

- "Por que escolhi Loki em vez de Elasticsearch (e quando o oposto faz sentido)"
- "Particionamento em PostgreSQL: salvei 10x performance com 3 linhas"
- "Como uso Redis para 5 problemas diferentes na mesma plataforma"
- "Backup e restore: o teste mensal que nunca pula"
- "LGPD na arquitetura: campos criptografados em coluna no PostgreSQL"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
