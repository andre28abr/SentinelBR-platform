# SentinelBR — Diagramas Visuais (Mermaid)

> Diagramas renderizáveis em Mermaid (suportado nativamente pelo GitHub, GitLab e a maioria dos editores Markdown). Substituem os diagramas ASCII dos outros documentos por versões visuais, mais fáceis de compreender de relance.

---

## 📋 Sumário

1. [Como visualizar estes diagramas](#como-visualizar-estes-diagramas)
2. [Visão geral do sistema (Contexto C4)](#visão-geral-do-sistema-contexto-c4)
3. [Containers (componentes deployáveis)](#containers-componentes-deployáveis)
4. [Fluxo de evento (do log ao alerta)](#fluxo-de-evento-do-log-ao-alerta)
5. [Fluxo de bloqueio automático](#fluxo-de-bloqueio-automático)
6. [Modelo de dados — relacionamentos principais](#modelo-de-dados--relacionamentos-principais)
7. [Estados do alerta](#estados-do-alerta)
8. [Ciclo de vida do agente](#ciclo-de-vida-do-agente)
9. [Pipeline de processamento de eventos](#pipeline-de-processamento-de-eventos)
10. [Arquitetura de rede](#arquitetura-de-rede)
11. [Camadas de segurança](#camadas-de-segurança)
12. [Roadmap visual](#roadmap-visual)

---

## Como visualizar estes diagramas

Os diagramas estão escritos em **Mermaid**, uma linguagem de markup para diagramas. Eles renderizam automaticamente em:

- **GitHub** (em arquivos .md)
- **GitLab**
- **VS Code** com extensão "Markdown Preview Mermaid Support"
- **Notion**
- **Obsidian**
- **mermaid.live** (online, cole o código)

Se aparecer só código nas suas ferramentas, instale o plugin Mermaid.

---

## Visão geral do sistema (Contexto C4)

Como o SentinelBR se relaciona com usuários e sistemas externos.

```mermaid
graph TB
    subgraph "Usuários"
        Admin[👤 Admin / Operador]
        DPO[👤 DPO]
        Auditor[👤 Auditor]
    end
    
    subgraph "SentinelBR"
        Platform[🛡️ Plataforma SentinelBR<br/>SIEM + Firewall + SELinux<br/>+ Resposta + LGPD]
    end
    
    subgraph "Infraestrutura monitorada"
        Hosts[🖥️ Servidores Linux<br/>com agente instalado]
    end
    
    subgraph "Sistemas externos"
        TI[🌐 Threat Intelligence<br/>AbuseIPDB, OTX, etc.]
        Notif[📡 Canais de notificação<br/>Telegram, Slack, Email]
        Storage[☁️ Storage offsite<br/>S3, B2 para backups]
    end
    
    Admin -->|Usa via web| Platform
    DPO -->|Gerencia LGPD| Platform
    Auditor -->|Audita acessos| Platform
    
    Platform -->|Coleta logs| Hosts
    Platform -->|Envia comandos| Hosts
    Platform -->|Consulta IOCs| TI
    Platform -->|Envia alertas| Notif
    Platform -->|Backup automático| Storage
    
    style Platform fill:#00D9A3,stroke:#00B388,color:#0A0E1A
    style Admin fill:#3B82F6,color:#fff
    style DPO fill:#8B5CF6,color:#fff
    style Auditor fill:#F59E0B,color:#0A0E1A
```

---

## Containers (componentes deployáveis)

Componentes que rodam em produção e como se conectam.

```mermaid
graph TB
    subgraph "Frontend"
        Web[🌐 React SPA<br/>servido por Caddy/Nginx]
    end
    
    subgraph "Backend Application"
        API[⚡ API REST<br/>FastAPI + Python 3.12]
        Stream[🔄 Stream Processor<br/>Python asyncio]
        Workers[⚙️ Workers<br/>Celery]
        gRPC[📡 gRPC Server<br/>recebe agentes]
    end
    
    subgraph "Persistência"
        PG[(🐘 PostgreSQL 16<br/>estado relacional)]
        Redis[(🔴 Redis 7<br/>cache + queues + streams)]
        Loki[(📜 Loki<br/>logs)]
        MinIO[(📦 MinIO<br/>arquivos)]
    end
    
    subgraph "Hosts monitorados"
        Agent[🤖 Agente Go<br/>SQLite local]
    end
    
    Web -->|HTTPS REST| API
    Web -->|WebSocket| API
    
    Agent -->|gRPC + mTLS| gRPC
    gRPC --> Redis
    
    API --> PG
    API --> Redis
    API --> Loki
    API --> MinIO
    
    Stream -->|consome events:raw| Redis
    Stream --> Loki
    Stream --> PG
    
    Workers --> PG
    Workers --> Redis
    Workers --> MinIO
    Workers -->|envia comandos| gRPC
    
    style Web fill:#3B82F6,color:#fff
    style API fill:#00D9A3,color:#0A0E1A
    style gRPC fill:#00D9A3,color:#0A0E1A
    style Stream fill:#00D9A3,color:#0A0E1A
    style Workers fill:#00D9A3,color:#0A0E1A
    style Agent fill:#F59E0B,color:#0A0E1A
    style PG fill:#336791,color:#fff
    style Redis fill:#DC382D,color:#fff
    style Loki fill:#F46800,color:#fff
    style MinIO fill:#C72E29,color:#fff
```

---

## Fluxo de evento (do log ao alerta)

Como uma tentativa de SSH falha vira alerta na UI.

```mermaid
sequenceDiagram
    participant SSH as 🔓 sshd<br/>(no host)
    participant Agent as 🤖 Agente
    participant gRPC as 📡 gRPC Server
    participant Stream as 🔄 Stream Processor
    participant Loki as 📜 Loki
    participant Redis as 🔴 Redis
    participant Engine as 🎯 Detection Engine
    participant DB as 🐘 PostgreSQL
    participant WS as 🌐 WebSocket
    participant UI as 💻 Frontend
    
    SSH->>SSH: Failed password<br/>from 203.0.113.42
    Note over SSH: /var/log/auth.log
    
    Agent->>Agent: tail detecta linha
    Agent->>Agent: parse → ECS
    Agent->>Agent: salva em SQLite buffer
    
    Agent->>gRPC: SubmitEvents (gRPC + mTLS)
    gRPC->>Redis: XADD events:raw
    
    Stream->>Redis: XREAD events:raw
    Stream->>Stream: enriquece (GeoIP, threat intel)
    Stream->>Loki: push log
    
    Stream->>Engine: avalia regras
    Engine->>Redis: ZADD sliding window
    Engine->>Redis: ZCARD verifica contagem
    
    alt Contagem >= threshold
        Engine->>DB: INSERT alerts.alerts
        Engine->>WS: PUBLISH alert.created
        WS->>UI: notifica realtime
        UI->>UI: toast "Novo alerta crítico"
    end
```

---

## Fluxo de bloqueio automático

Como um alerta dispara bloqueio de IP automaticamente.

```mermaid
sequenceDiagram
    participant Alert as 🚨 Alert criado
    participant Engine as ⚡ Playbook Engine
    participant DB as 🐘 PostgreSQL
    participant gRPC as 📡 gRPC Server
    participant Agent as 🤖 Agente do host
    participant FW as 🛡️ nftables
    participant Telegram as 📱 Telegram
    participant User as 👤 Usuário
    
    Alert->>Engine: trigger: ssh_brute_force
    Engine->>DB: cria playbook.execution
    
    Engine->>Engine: Step 1: firewall.block_ip
    Engine->>DB: INSERT firewall.dynamic_blocks
    Engine->>gRPC: comando para o agente
    gRPC->>Agent: Command (CommandStream)
    Agent->>FW: nft add element blacklist 203.0.113.42
    FW-->>Agent: ok
    Agent-->>gRPC: CommandResult success
    gRPC-->>Engine: success
    Engine->>DB: step completed
    
    Engine->>Engine: Step 2: notify.telegram
    Engine->>Telegram: send message
    Telegram-->>User: 🚨 IP bloqueado
    Engine->>DB: step completed
    
    Engine->>Engine: Step 3: forensics.collect<br/>(require_approval)
    Engine->>Telegram: aprovação inline?
    User->>Telegram: clica [Aprovar]
    Telegram->>Engine: approval received
    Engine->>Agent: comando coleta
    Agent->>Agent: ps, ss, hashes
    Agent->>gRPC: upload tar.gz
    
    Engine->>DB: execution completed
```

---

## Modelo de dados — relacionamentos principais

Como as principais tabelas do PostgreSQL se relacionam.

```mermaid
erDiagram
    users ||--o{ user_roles : tem
    roles ||--o{ user_roles : pertence
    roles ||--o{ role_permissions : possui
    permissions ||--o{ role_permissions : concede
    
    users ||--o{ api_tokens : cria
    users ||--o{ audit_events : executa
    
    hosts ||--o{ agent_heartbeats : reporta
    hosts ||--o{ alerts : gera
    hosts ||--o{ rule_sets : possui
    hosts ||--o{ selinux_denials : registra
    
    detection_rules ||--o{ alerts : dispara
    detection_rules ||--o{ rule_versions : versiona
    
    alerts ||--o{ alert_comments : tem
    alerts ||--o{ alert_timeline : registra
    alerts ||--o{ playbook_executions : aciona
    
    playbooks ||--o{ playbook_executions : executa
    playbook_executions ||--o{ execution_steps : contém
    
    data_assets ||--o{ subject_requests : referencia
    
    users {
        uuid id PK
        citext email
        text password_hash
        boolean mfa_enabled
        timestamptz last_login_at
    }
    
    hosts {
        uuid id PK
        varchar hostname
        inet primary_ip
        varchar status
        timestamptz last_seen_at
    }
    
    alerts {
        uuid id PK
        varchar fingerprint
        uuid rule_id FK
        uuid host_id FK
        varchar severity
        varchar status
        integer event_count
    }
    
    detection_rules {
        uuid id PK
        text yaml_content
        varchar severity
        boolean enabled
    }
    
    playbooks {
        uuid id PK
        text yaml_content
        boolean enabled
    }
    
    data_assets {
        uuid id PK
        varchar name
        varchar asset_type
        varchar legal_basis
        interval retention_period
    }
```

---

## Estados do alerta

Ciclo de vida de um alerta na plataforma.

```mermaid
stateDiagram-v2
    [*] --> open: regra disparou
    
    open --> acknowledged: usuário reconhece
    open --> investigating: análise iniciada
    open --> false_positive: falso positivo
    open --> resolved: resolvido sem investigação
    
    acknowledged --> investigating: começa análise
    acknowledged --> resolved: resolvido rapidamente
    acknowledged --> false_positive: era falso positivo
    
    investigating --> resolved: investigação concluída
    investigating --> false_positive: confirmado FP
    
    false_positive --> [*]
    resolved --> [*]
    
    note right of open
        event_count incrementa
        para alertas duplicados
        (mesmo fingerprint)
    end note
```

---

## Ciclo de vida do agente

Estados pelos quais o agente passa.

```mermaid
stateDiagram-v2
    [*] --> Pending: criado na UI
    
    Pending --> Enrolling: usuário rodou install
    Enrolling --> Online: cert mTLS recebido<br/>e validado
    Enrolling --> Failed: erro no enrollment
    
    Online --> Slow: heartbeat atrasado<br/>(>2 min)
    Online --> Offline: sem heartbeat<br/>(>5 min)
    
    Slow --> Online: heartbeat normal
    Slow --> Offline: continua sem responder
    
    Offline --> Online: agente reconecta
    
    Online --> Disabled: admin desabilitou
    Disabled --> Online: admin reativou
    
    Failed --> [*]: removido
    
    note right of Online
        Estado normal de operação.
        Coleta logs, envia eventos,
        executa comandos remotos.
    end note
```

---

## Pipeline de processamento de eventos

Como eventos fluem pelos workers.

```mermaid
flowchart LR
    A[🤖 Agente<br/>coleta log] --> B[gRPC<br/>SubmitEvents]
    B --> C{Validação<br/>mTLS}
    C -->|falha| Z[❌ rejeita]
    C -->|ok| D[Redis Stream<br/>events:raw]
    
    D --> E[Stream Processor]
    E --> F[Normalizar<br/>ECS]
    F --> G[Enriquecer<br/>GeoIP + TI]
    G --> H[Loki<br/>persistir]
    G --> I[Redis<br/>sliding windows]
    
    I --> J{Match<br/>regra Sigma?}
    J -->|sim| K[Worker:<br/>create_alert]
    J -->|não| L[Fim]
    
    K --> M[(PostgreSQL<br/>alerts)]
    K --> N[Pub/Sub<br/>alert.created]
    
    N --> O[WebSocket<br/>frontend]
    N --> P[Worker:<br/>notify]
    N --> Q[Worker:<br/>playbook]
    
    P --> R[📱 Telegram]
    P --> S[💬 Slack]
    P --> T[📧 Email]
    
    Q --> U{Avalia<br/>triggers}
    U -->|match| V[Executa<br/>playbook]
    V --> W[Comando<br/>para agente]
    
    style A fill:#F59E0B,color:#0A0E1A
    style E fill:#00D9A3,color:#0A0E1A
    style K fill:#00D9A3,color:#0A0E1A
    style P fill:#00D9A3,color:#0A0E1A
    style Q fill:#00D9A3,color:#0A0E1A
    style M fill:#336791,color:#fff
    style D fill:#DC382D,color:#fff
    style I fill:#DC382D,color:#fff
    style N fill:#DC382D,color:#fff
    style H fill:#F46800,color:#fff
```

---

## Arquitetura de rede

Como os componentes se comunicam pela rede.

```mermaid
graph TB
    subgraph "Internet"
        User[👤 Usuário]
        Agents[🤖 Agentes<br/>em hosts diversos]
    end
    
    subgraph "VPS / Servidor central"
        subgraph "Edge"
            Caddy[🔒 Caddy<br/>Let's Encrypt<br/>portas 80, 443]
        end
        
        subgraph "Aplicação"
            APIInstance[API FastAPI<br/>:8000]
            gRPCInstance[gRPC Server<br/>:9090<br/>mTLS]
            WebInstance[Web Static<br/>:80]
        end
        
        subgraph "Backend interno (rede privada)"
            Postgres[(PostgreSQL<br/>:5432)]
            Redis[(Redis<br/>:6379)]
            LokiInst[(Loki<br/>:3100)]
            MinIOInst[(MinIO<br/>:9000)]
        end
    end
    
    User -->|HTTPS| Caddy
    Caddy -->|/api/*| APIInstance
    Caddy -->|/| WebInstance
    Caddy -->|/ws| APIInstance
    
    Agents -->|gRPC + mTLS| gRPCInstance
    
    APIInstance --> Postgres
    APIInstance --> Redis
    APIInstance --> LokiInst
    APIInstance --> MinIOInst
    
    gRPCInstance --> Redis
    gRPCInstance --> Postgres
    
    style User fill:#3B82F6,color:#fff
    style Agents fill:#F59E0B,color:#0A0E1A
    style Caddy fill:#00D9A3,color:#0A0E1A
```

---

## Camadas de segurança

Defesa em profundidade da plataforma.

```mermaid
graph TD
    A[🌍 Atacante] --> B{Camada 1<br/>Firewall de borda}
    B -->|bloqueado| Z1[❌]
    B -->|passa| C{Camada 2<br/>Caddy/Nginx<br/>Rate limit + TLS}
    
    C -->|429| Z2[❌]
    C -->|passa| D{Camada 3<br/>API Auth<br/>JWT/mTLS}
    
    D -->|401/403| Z3[❌]
    D -->|passa| E{Camada 4<br/>RBAC<br/>permissão por endpoint}
    
    E -->|sem permissão| Z4[❌]
    E -->|passa| F{Camada 5<br/>Validação<br/>Pydantic}
    
    F -->|inválido| Z5[❌]
    F -->|passa| G[Lógica de<br/>negócio]
    
    G --> H{Camada 6<br/>SQL injection<br/>protection<br/>SQLAlchemy}
    H --> I[(PostgreSQL)]
    
    G --> J{Camada 7<br/>Audit log}
    J --> K[(audit.events)]
    
    style A fill:#EF4444,color:#fff
    style Z1 fill:#EF4444,color:#fff
    style Z2 fill:#EF4444,color:#fff
    style Z3 fill:#EF4444,color:#fff
    style Z4 fill:#EF4444,color:#fff
    style Z5 fill:#EF4444,color:#fff
    style I fill:#10B981,color:#fff
    style K fill:#10B981,color:#fff
```

---

## Roadmap visual

Linha do tempo das fases do projeto.

```mermaid
gantt
    title SentinelBR - Roadmap de 6 meses
    dateFormat YYYY-MM-DD
    axisFormat %b
    
    section Fase 0 - Preparação
    Setup repositório         :p1, 2026-05-01, 3d
    CI/CD básico             :p2, after p1, 3d
    Ambiente de dev          :p3, after p2, 3d
    Estrutura inicial        :p4, after p3, 4d
    
    section Fase 1 - MVP
    Autenticação             :m1, 2026-05-15, 14d
    Inventário de hosts      :m2, after m1, 14d
    Coleta e ingestão        :m3, after m2, 14d
    Detecção Sigma           :m4, after m3, 14d
    Firewall                 :m5, after m4, 14d
    Notificações             :m6, after m5, 7d
    Polimento e deploy       :m7, after m6, 7d
    
    section Fase 2 - v1.0
    2FA + API tokens         :v1, 2026-09-01, 7d
    SELinux                  :v2, after v1, 14d
    Threat Intel             :v3, after v2, 7d
    ML anomalias             :v4, after v3, 14d
    Playbooks                :v5, after v4, 14d
    Webhooks + tracing       :v6, after v5, 7d
    Polish v1                :v7, after v6, 14d
    
    section Fase 3 - v2.0
    LGPD parte 1             :v8, 2026-11-01, 21d
    LGPD parte 2             :v9, after v8, 14d
    SSO OIDC                 :v10, after v9, 7d
    Multi-tenant             :v11, after v10, 14d
    Helm + Terraform         :v12, after v11, 14d
    HA Postgres              :v13, after v12, 7d
```

---

## Como editar e adicionar diagramas

Sempre que precisar adicionar diagrama novo:

1. Pense em **qual tipo melhor representa** o conceito:
   - `graph TB/LR`: relações entre componentes
   - `sequenceDiagram`: interações ao longo do tempo
   - `stateDiagram-v2`: estados e transições
   - `erDiagram`: modelo de dados
   - `flowchart`: fluxos de processo
   - `gantt`: cronogramas
   - `pie`: proporções
   - `journey`: jornada de usuário
   - `mindmap`: brainstorming

2. Use cores **consistentes** com o design system:
   - `#00D9A3`: brand (componentes principais)
   - `#3B82F6`: usuário/info
   - `#F59E0B`: warning/agente
   - `#EF4444`: danger/erro
   - `#10B981`: success
   - `#8B5CF6`: LGPD/compliance

3. Teste em mermaid.live antes de comitar

4. Mantenha **simples**: se diagrama tem >20 caixas, divida em dois

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
