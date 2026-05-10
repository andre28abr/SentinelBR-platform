# SentinelBR — Arquitetura Técnica

> Documento de arquitetura técnica completa. Cobre componentes, fluxos de comunicação, padrões arquiteturais e decisões de stack. Complementa o documento de dados (`04-arquitetura-dados.md`) com a perspectiva de "como os pedaços conversam".

---

## 📋 Sumário

1. [Visão geral da arquitetura](#visão-geral-da-arquitetura)
2. [Componentes principais](#componentes-principais)
3. [Diagrama C4 — níveis de abstração](#diagrama-c4)
4. [Padrões arquiteturais aplicados](#padrões-arquiteturais-aplicados)
5. [Comunicação entre componentes](#comunicação-entre-componentes)
6. [O agente em detalhes](#o-agente-em-detalhes)
7. [O servidor central em detalhes](#o-servidor-central-em-detalhes)
8. [O frontend em detalhes](#o-frontend-em-detalhes)
9. [Workers e processamento assíncrono](#workers-e-processamento-assíncrono)
10. [Stack técnica completa](#stack-técnica-completa)
11. [Modelo de threads e concorrência](#modelo-de-threads-e-concorrência)
12. [Estratégia de testes](#estratégia-de-testes)
13. [Observabilidade](#observabilidade)
14. [Decisões arquiteturais resumidas](#decisões-arquiteturais-resumidas)

---

## Visão geral da arquitetura

O SentinelBR é uma plataforma **distribuída** composta de três grandes blocos:

1. **Agentes** — instalados em cada host monitorado, coletam dados localmente
2. **Servidor central** — recebe, processa, armazena e expõe dados; é onde a lógica vive
3. **Frontend** — interface web que consome a API do servidor central

```
┌──────────────────────────────────────────────────────────────────┐
│                         INTERNET / VPN                           │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
   ┌─────────┐              ┌──────────┐             ┌──────────┐
   │ Agente  │              │ Frontend │             │ Outros   │
   │ web-01  │              │ (browser)│             │ Agentes  │
   └────┬────┘              └────┬─────┘             └────┬─────┘
        │ gRPC + mTLS            │ HTTPS                  │
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                                 ▼
        ┌──────────────────────────────────────────────────┐
        │              SERVIDOR CENTRAL                    │
        │                                                  │
        │  ┌──────────┐ ┌──────────┐ ┌─────────────────┐ │
        │  │   API    │ │  Workers │ │  Stream Proc    │ │
        │  │ FastAPI  │ │  Celery  │ │  (correlação)   │ │
        │  └────┬─────┘ └────┬─────┘ └────────┬────────┘ │
        │       │            │                 │          │
        │       └────────────┼─────────────────┘          │
        │                    │                            │
        │  ┌─────────┬───────┴────┬─────────┬──────────┐  │
        │  ▼         ▼            ▼         ▼          ▼  │
        │ Postgres  Redis        Loki    MinIO      Métri  │
        └──────────────────────────────────────────────────┘
```

### Princípios arquiteturais

#### 1. Desacoplamento via mensageria

Componentes não se chamam diretamente quando possível. API recebe evento → publica em Redis Stream → workers consomem. Isso permite:

- **Falhas isoladas**: se worker cai, eventos enfileiram (não se perdem)
- **Escalabilidade**: adicionar mais workers sem mudar API
- **Backpressure**: pico de tráfego não derruba o sistema, só atrasa processamento

#### 2. Separação API / Workers

API é **stateless** e responde em **milissegundos** (UI rápida). Trabalho pesado (correlação, ML, geração de PDF) vai pra workers que rodam separados. Mesmo código, processos diferentes.

#### 3. Camadas claras

```
┌─────────────────────────────────────┐
│ API Routes (FastAPI)                │ ← HTTP, validação, auth
├─────────────────────────────────────┤
│ Services (lógica de negócio)        │ ← regras, orquestração
├─────────────────────────────────────┤
│ Repositories (acesso a dados)       │ ← queries, abstrai DB
├─────────────────────────────────────┤
│ Models (entidades de domínio)       │ ← Pydantic + SQLAlchemy
└─────────────────────────────────────┘
```

Cada camada conhece apenas a de baixo. Permite trocar implementações (PostgreSQL → outro DB) sem reescrever tudo.

#### 4. Configuration as code

Tudo configurável via variáveis de ambiente ou arquivos YAML versionados. Nada de "configuração mágica" no banco que ninguém sabe de onde vem.

#### 5. Falha graciosa

Cada dependência externa tem fallback ou comportamento degradado:

- Loki indisponível → API retorna "logs temporariamente indisponíveis"
- Redis indisponível → cache miss vira hit no DB direto (mais lento, mas funciona)
- MinIO indisponível → upload em fila para retry

---

## Componentes principais

### 🤖 Agente (sentinelbr-agent)

**Linguagem**: Go (binário único, baixo footprint)
**Footprint**: ~30 MB RAM em idle, ~2% CPU
**Comunicação saída**: gRPC com mTLS para o servidor central
**Permissão**: roda como root (necessário para acessar `/var/log/audit/audit.log`, executar `nft`, etc.)

**Sub-componentes:**

```
sentinelbr-agent
├── collectors/         ← coleta de logs e métricas
│   ├── auditd
│   ├── syslog
│   ├── journald
│   ├── nginx
│   └── apache
├── executors/          ← executa ações solicitadas pelo servidor
│   ├── firewall
│   ├── selinux
│   ├── forensics
│   └── process
├── transport/          ← gRPC client com retry + buffering
├── storage/            ← SQLite local (buffer)
├── config/             ← gerenciamento de config local
└── healthcheck/        ← reporta status próprio
```

### 🧠 Servidor Central — API (sentinelbr-api)

**Linguagem**: Python 3.12+
**Framework**: FastAPI
**Servidor ASGI**: Uvicorn (com workers via Gunicorn em prod)

**Responsabilidades:**

- Expor REST API para frontend e integrações
- Receber dados dos agentes via gRPC
- Validar requests, aplicar autenticação/autorização
- Publicar eventos para workers via Redis
- Operações CRUD em PostgreSQL
- Gerar tokens JWT, validar sessões

**Não faz**:

- Processamento pesado de eventos (workers fazem)
- Análise de regras Sigma (workers fazem)
- Geração de relatórios PDF (workers fazem)
- Treino de modelos ML (workers fazem)

### ⚙️ Servidor Central — Workers (sentinelbr-worker)

**Linguagem**: Python 3.12+
**Framework**: Celery 5.3+

**Tipos de worker** (queues separadas):

```
queue:critical    ← bloqueios automáticos, alertas críticos
queue:correlation ← engine Sigma, sliding windows
queue:enrichment  ← GeoIP, threat intel, reverse DNS
queue:ml          ← detecção de anomalias, treino
queue:reports     ← geração de PDF, exports
queue:retention   ← limpeza de dados antigos
queue:notification ← envio de telegram/slack/email
```

Cada queue pode escalar independentemente. Workers de critical têm prioridade, workers de retention rodam à noite.

### 📡 Stream Processor (sentinelbr-stream)

**Linguagem**: Python (asyncio)

Processo dedicado que consome `events:raw` do Redis Stream e faz:

1. Normalização ECS
2. Enriquecimento (chama workers se demorar)
3. Persistência no Loki
4. Avaliação de regras (correlação rápida)
5. Publicação de alerts em pub/sub

Por que separado do API? Throughput diferente: API responde a humanos (poucos req/s), stream processor digere milhares de eventos/s. Diferentes perfis de uso, diferentes dimensionamentos.

### 🌐 Frontend (sentinelbr-web)

**Stack**: React + TypeScript + Vite + Tailwind
**Build**: estático, servido por nginx ou CDN

Detalhado no documento `03-interface-grafica.md`.

### 💾 Persistência

Detalhado no documento `04-arquitetura-dados.md`:
- PostgreSQL (estado relacional)
- Loki (logs)
- Redis (cache, filas, streams)
- MinIO (arquivos)

---

## Diagrama C4

C4 é uma técnica de documentar arquitetura em 4 níveis de zoom. Vamos fazer os 3 mais úteis.

### Nível 1 — Contexto (visão de cima)

```
                    ┌──────────────────┐
                    │                  │
                    │   USUÁRIO/ADMIN  │
                    │   (operador,     │
                    │    DPO, auditor) │
                    │                  │
                    └────────┬─────────┘
                             │ usa via web
                             ▼
        ┌──────────────────────────────────────┐
        │                                      │
        │           SENTINELBR                 │
        │   Plataforma de segurança            │
        │                                      │
        └──┬────────────────────────────────┬──┘
           │                                │
           │ monitora                       │ notifica
           ▼                                ▼
    ┌─────────────────┐         ┌────────────────────┐
    │                 │         │                    │
    │ INFRA LINUX     │         │ CANAIS EXTERNOS    │
    │ (servidores)    │         │ Telegram, Slack,   │
    │                 │         │ Email              │
    └─────────────────┘         └────────────────────┘
           ▲
           │ consulta IOCs
           │
    ┌──────┴──────────┐
    │ THREAT INTEL    │
    │ AbuseIPDB,      │
    │ AlienVault OTX  │
    └─────────────────┘
```

### Nível 2 — Containers (componentes deployáveis)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          SENTINELBR                                 │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                        FRONTEND                              │   │
│  │  React SPA (servida por Nginx)                               │   │
│  │  HTTPS · WebSocket                                           │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                           │ REST + WS                               │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                          API                                 │   │
│  │  FastAPI · Uvicorn · Python 3.12                             │   │
│  │  Stateless · escalável horizontalmente                       │   │
│  └─┬───────────────┬────────────────┬────────────────┬──────────┘   │
│    │               │                │                │              │
│    │ SQL           │ Pub/Sub        │ gRPC           │ S3 API       │
│    ▼               ▼                ▼                ▼              │
│  ┌──────┐     ┌────────┐       ┌────────┐       ┌────────┐         │
│  │ PG   │     │ Redis  │       │ Agentes│       │ MinIO  │         │
│  │  16  │     │  7.2   │       │ (Go)   │       │        │         │
│  └──────┘     └───┬────┘       └────────┘       └────────┘         │
│                   │ stream                                          │
│                   ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    STREAM PROCESSOR                          │   │
│  │  Python asyncio · processa events:raw                        │   │
│  └────────────────────────┬─────────────────────────────────────┘   │
│                           │                                         │
│                           ▼                                         │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                          LOKI                                │   │
│  │  Logs storage · LogQL · 30d hot + 90d cold                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                       WORKERS                                │   │
│  │  Celery · múltiplas queues · processamento assíncrono        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Nível 3 — Componentes (zoom no servidor API)

```
┌────────────────────────────────────────────────────────────────────┐
│                          API SERVER                                │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  ROUTING LAYER                               │  │
│  │  /api/v1/auth/*   /api/v1/hosts/*   /api/v1/alerts/*  ...    │  │
│  └────┬───────────────────────────────────────────────────┬─────┘  │
│       │                                                   │        │
│       ▼                                                   ▼        │
│  ┌─────────┐                                       ┌──────────┐    │
│  │ AUTH    │←── JWT/RBAC middleware ──────────────►│ RATE LIM │    │
│  │ MIDDLE  │                                       │ MIDDLE   │    │
│  └─────────┘                                       └──────────┘    │
│       │                                                            │
│       ▼                                                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   SERVICE LAYER                              │  │
│  │ ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌────────────┐      │  │
│  │ │ AuthSvc   │ │ HostSvc   │ │ AlertSvc │ │ FirewallSvc│      │  │
│  │ └─────┬─────┘ └─────┬─────┘ └────┬─────┘ └─────┬──────┘      │  │
│  │       │             │             │             │              │  │
│  │  ┌────▼─────────────▼─────────────▼─────────────▼────┐       │  │
│  │  │         REPOSITORY LAYER                          │       │  │
│  │  │  UserRepo  HostRepo  AlertRepo  FirewallRepo     │       │  │
│  │  └────┬──────────────────────────────────────────┬───┘       │  │
│  │       │                                          │           │  │
│  └───────┼──────────────────────────────────────────┼───────────┘  │
│          │                                          │              │
│          ▼                                          ▼              │
│      PostgreSQL                                  Redis             │
└────────────────────────────────────────────────────────────────────┘
```

---

## Padrões arquiteturais aplicados

### 1. Repository pattern

Toda interação com banco passa por classe `Repository`. Services não escrevem SQL.

```python
# Errado:
class AlertService:
    def list_open(self):
        return db.execute("SELECT * FROM alerts WHERE status='open'")

# Certo:
class AlertRepository:
    async def list_by_status(self, status: str) -> list[Alert]:
        ...

class AlertService:
    def __init__(self, repo: AlertRepository):
        self.repo = repo
    
    async def list_open(self) -> list[Alert]:
        return await self.repo.list_by_status('open')
```

**Vantagens**: testes mockam repository, troca de DB não afeta service, queries centralizadas.

### 2. Dependency Injection

FastAPI tem DI nativo via `Depends()`. Usamos para tudo:

```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

def get_alert_service(
    db: AsyncSession = Depends(get_db_session),
) -> AlertService:
    return AlertService(repo=AlertRepository(db))

@app.get("/alerts")
async def list_alerts(
    service: AlertService = Depends(get_alert_service),
    user: User = Depends(get_current_user),
):
    return await service.list_for_user(user)
```

**Vantagens**: testabilidade, configurabilidade, separação de concerns.

### 3. CQRS (Command Query Responsibility Segregation) leve

Não fazemos CQRS completo (com event sourcing), mas separamos:

- **Commands** (mutam estado): vão pelos services com transação
- **Queries** (só leem): podem usar caches, materialized views, ou Loki direto

Em Python, isso se traduz em métodos separados (`create_*`, `update_*` vs `get_*`, `list_*`).

### 4. Event-driven em pontos críticos

Mudanças importantes geram eventos consumíveis:

```python
# Quando alerta é criado
await event_bus.publish("alert.created", {
    "alert_id": alert.id,
    "severity": alert.severity,
    "host_id": alert.host_id,
})

# Múltiplos consumers reagem:
# - Notifier envia Telegram
# - Playbook engine avalia triggers
# - WebSocket pusher avisa frontend
# - Métricas incrementa contadores
```

Reduz acoplamento e permite adicionar novos consumers sem mudar quem publica.

### 5. Circuit breaker

Para chamadas externas (threat intel, GeoIP, notificadores). Lib: `pybreaker`.

```python
@circuit(failure_threshold=5, recovery_timeout=60)
async def query_threat_intel(ip: str) -> ThreatScore:
    # Se falhar 5x, circuito abre por 60s
    # (retorna default em vez de tentar e falhar)
    ...
```

Evita cascade failures e thundering herd.

### 6. Idempotência

Operações críticas aceitam idempotency keys. Mesmo request retransmitido = mesma resposta, sem efeito duplicado.

```python
@app.post("/firewall/block")
async def block_ip(
    request: BlockIPRequest,
    idempotency_key: str = Header(...),
):
    if existing := await idempotency_repo.get(idempotency_key):
        return existing.response
    
    result = await firewall_service.block(request)
    await idempotency_repo.save(idempotency_key, result)
    return result
```

Crítico em sistemas distribuídos onde retries acontecem.

---

## Comunicação entre componentes

### API ↔ Frontend

**Protocolo**: HTTPS + WebSocket
**Formato**: JSON
**Autenticação**: JWT no header `Authorization: Bearer ...`

#### REST normal

```http
POST /api/v1/hosts HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: application/json

{"hostname": "web-01", "primary_ip": "10.0.1.5"}

HTTP/1.1 201 Created
Content-Type: application/json

{"id": "550e8400...", "hostname": "web-01", ...}
```

#### WebSocket para realtime

```javascript
const ws = new WebSocket('wss://api/ws?token=...');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  // {type: 'alert.new', data: {...}}
  // {type: 'host.status', data: {...}}
};
```

Servidor publica em canais Redis pub/sub, conector WebSocket assina e propaga.

### Agente ↔ API

**Protocolo**: gRPC com mTLS (mutual TLS)
**Por quê**: 
- gRPC é binário (3-5x menor que JSON em volume alto)
- Streaming bidirecional nativo (servidor empurra comandos para o agente)
- Schema versionado via Protobuf

#### Schema Protobuf (resumido)

```protobuf
service AgentService {
  // Agente envia eventos para o servidor
  rpc SubmitEvents(stream EventBatch) returns (SubmitResponse);
  
  // Servidor mantém canal de comandos abertos
  rpc CommandStream(AgentIdentity) returns (stream Command);
  
  // Heartbeat periódico
  rpc Heartbeat(HeartbeatRequest) returns (HeartbeatResponse);
  
  // Resultado de comando executado
  rpc CommandResult(CommandResultRequest) returns (CommandResultResponse);
}

message EventBatch {
  string agent_id = 1;
  repeated Event events = 2;
}

message Event {
  string id = 1;
  google.protobuf.Timestamp timestamp = 2;
  string source = 3;
  bytes raw_data = 4;          // gzipped JSON
  EventMetadata metadata = 5;
}

message Command {
  string command_id = 1;
  CommandType type = 2;        // BLOCK_IP, COLLECT_FORENSIC, etc.
  google.protobuf.Any payload = 3;
  google.protobuf.Timestamp deadline = 4;
}
```

#### Fluxo de conexão

```
1. Agente inicia
2. Carrega cert e chave do disco (/etc/sentinelbr/agent.crt, .key)
3. Estabelece conexão gRPC com mTLS
4. Servidor valida cert contra CA própria
5. Identifica agent_id pelo cert subject
6. Abre stream bidirecional persistente
7. Agente envia eventos quando tem
8. Servidor envia comandos quando precisa
9. Reconexão automática em caso de queda
```

### API ↔ Workers (via Redis)

**Protocolo**: Redis pub/sub + Celery message format
**Filas**: separadas por prioridade

```python
# API enfileira tarefa
@app.post("/reports/generate")
async def generate_report(request: ReportRequest):
    task = generate_report_task.apply_async(
        args=[request.dict()],
        queue='reports',
        countdown=0,
    )
    return {"task_id": task.id, "status": "queued"}

# Worker consome
@celery_app.task(queue='reports', bind=True, max_retries=3)
def generate_report_task(self, request_dict):
    try:
        # processamento
    except Exception as e:
        raise self.retry(exc=e, countdown=60)
```

### API/Workers ↔ PostgreSQL

**Protocolo**: TCP com SSL
**Lib**: SQLAlchemy 2.0 + asyncpg
**Pool**: PgBouncer em modo transaction (até 100 conexões para o DB, milhares de clientes)

### API/Workers ↔ Loki

**Protocolo**: HTTP
**Lib**: cliente HTTP simples (não há lib oficial Python tão boa, fazemos wrappers)

```python
async def query_loki(query: str, start: datetime, end: datetime) -> list[dict]:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{LOKI_URL}/loki/api/v1/query_range", params={
            "query": query,
            "start": start.isoformat(),
            "end": end.isoformat(),
        })
        return r.json()
```

### API/Workers ↔ MinIO

**Protocolo**: S3 API (HTTP)
**Lib**: `boto3` (compatível com qualquer S3)

```python
s3 = boto3.client('s3', endpoint_url=MINIO_URL, ...)
s3.put_object(Bucket='sentinelbr-evidences', Key='...', Body=data)
```

---

## O agente em detalhes

### Por que Go?

- **Binário único**: sem dependências, copia pro servidor e roda
- **Footprint baixo**: agente em servidor de cliente não pode comer recursos
- **Compilação cruzada**: builds para amd64, arm64, com mesma toolchain
- **Concorrência simples**: goroutines + channels resolve coletas paralelas elegantemente
- **Maturidade em CLI tools**: ecossistema rico (Cobra, Viper)

Alternativa: Python com PyInstaller. Funciona, mas binário fica grande (>50MB) e startup mais lento.

### Estrutura de pastas do projeto

```
sentinelbr-agent/
├── cmd/
│   └── agent/
│       └── main.go              ← entry point
├── internal/
│   ├── config/                  ← parsing de YAML, validação
│   ├── transport/
│   │   ├── grpc_client.go
│   │   └── retry.go
│   ├── storage/
│   │   ├── sqlite.go            ← buffer local
│   │   └── migrations/
│   ├── collectors/
│   │   ├── auditd/
│   │   ├── syslog/
│   │   ├── nginx/
│   │   └── interface.go         ← Collector interface
│   ├── executors/
│   │   ├── firewall/
│   │   ├── selinux/
│   │   ├── forensics/
│   │   └── interface.go
│   ├── enrollment/              ← primeiro registro com servidor
│   └── healthcheck/
├── pkg/
│   └── proto/                   ← gerado do .proto
├── deploy/
│   ├── systemd/
│   │   └── sentinelbr-agent.service
│   └── packaging/
│       ├── deb/
│       └── rpm/
├── go.mod
├── go.sum
└── Makefile
```

### Lifecycle do agente

```
1. STARTUP
   ├── Carrega config (/etc/sentinelbr/agent.yaml)
   ├── Carrega cert mTLS (/etc/sentinelbr/agent.{crt,key})
   ├── Inicializa SQLite (/var/lib/sentinelbr/buffer.db)
   ├── Roda migrations
   └── Detecta capacidades (firewalld? nftables? auditd?)

2. ENROLLMENT (se primeira vez)
   ├── Lê token de enrollment
   ├── Gera CSR (certificate signing request)
   ├── Envia ao servidor
   ├── Recebe cert assinado
   └── Salva e remove token

3. CONNECT
   ├── Abre stream gRPC com servidor
   ├── Envia identidade (cert fingerprint)
   ├── Recebe config remota (regras de coleta, etc.)
   └── Mantém stream aberto

4. RUN LOOP (goroutines paralelas)
   ├── Goroutine: tail de cada arquivo de log
   ├── Goroutine: parser → estrutura ECS
   ├── Goroutine: insert em SQLite
   ├── Goroutine: read SQLite → envia em batches
   ├── Goroutine: heartbeat a cada 30s
   ├── Goroutine: escuta comandos do servidor
   └── Goroutine: executa comandos recebidos

5. SHUTDOWN
   ├── Para coletas (sem perder eventos em buffer)
   ├── Tenta flush final do SQLite
   ├── Fecha stream gRPC graciosamente
   └── Exit
```

### Coletor — interface

```go
type Collector interface {
    Name() string
    Start(ctx context.Context, eventChan chan<- *Event) error
    Stop() error
    HealthCheck() error
}

// Cada coletor implementa
type AuditdCollector struct {
    config Config
    state  *State
    file   *os.File
}

func (a *AuditdCollector) Start(ctx, ch) error {
    go func() {
        for {
            line, err := a.readLine()
            event := a.parse(line)
            ch <- event
        }
    }()
    return nil
}
```

### Detecção de rotação de log

Problema clássico: `logrotate` move `/var/log/auth.log` para `auth.log.1` e cria novo. Se o agente está com handle aberto, perde tudo.

**Solução**: comparar inode atual do path com inode salvo. Se diferente, fechar handle, reabrir, resetar position.

```go
func (a *AuditdCollector) checkRotation() {
    stat, _ := os.Stat(a.config.Path)
    currentInode := stat.Sys().(*syscall.Stat_t).Ino
    
    if currentInode != a.state.Inode {
        a.file.Close()
        a.file, _ = os.Open(a.config.Path)
        a.state.Inode = currentInode
        a.state.Position = 0
    }
}
```

### Backpressure

Se servidor central está lento ou caiu:

1. SQLite enche
2. Quando atinge 80% do limite (default 400MB de 500MB), agente entra em modo "drop oldest"
3. Eventos novos têm prioridade; mais antigos são descartados
4. Métrica `events_dropped_total` incrementa
5. Heartbeat reporta backlog ao servidor (quando reconectar)

### Auto-update (opcional)

Para v2:
- Agente checa nova versão a cada hora
- Se config remota habilitar, baixa novo binário em `/var/lib/sentinelbr/agent.new`
- Verifica assinatura (cosign)
- Faz `mv agent.new agent` + `systemctl restart`
- Versão é "pinnable" via config (cliente pode travar versão se quiser)

---

## O servidor central em detalhes

### Estrutura de pastas

```
sentinelbr-server/
├── pyproject.toml                ← dependências (uv)
├── Dockerfile
├── alembic.ini
├── alembic/
│   └── versions/                 ← migrations
├── src/
│   └── sentinelbr/
│       ├── api/                  ← FastAPI app
│       │   ├── main.py
│       │   ├── routers/
│       │   │   ├── auth.py
│       │   │   ├── hosts.py
│       │   │   ├── alerts.py
│       │   │   ├── firewall.py
│       │   │   ├── selinux.py
│       │   │   ├── playbooks.py
│       │   │   └── lgpd.py
│       │   ├── middleware/
│       │   │   ├── auth.py
│       │   │   ├── ratelimit.py
│       │   │   └── logging.py
│       │   ├── deps/             ← dependency injection
│       │   └── ws/               ← websocket handlers
│       │
│       ├── grpc/                 ← gRPC server (recebe agentes)
│       │   ├── server.py
│       │   ├── agent_service.py
│       │   └── proto/
│       │
│       ├── services/             ← lógica de negócio
│       │   ├── auth_service.py
│       │   ├── host_service.py
│       │   ├── alert_service.py
│       │   ├── correlation_service.py
│       │   ├── firewall_service.py
│       │   ├── selinux_service.py
│       │   ├── playbook_service.py
│       │   └── lgpd_service.py
│       │
│       ├── repositories/         ← acesso a dados
│       │   ├── base.py
│       │   ├── user_repository.py
│       │   ├── host_repository.py
│       │   └── ...
│       │
│       ├── models/               ← SQLAlchemy ORM
│       ├── schemas/              ← Pydantic (request/response)
│       │
│       ├── workers/              ← Celery tasks
│       │   ├── celery_app.py
│       │   ├── tasks/
│       │   │   ├── correlation.py
│       │   │   ├── enrichment.py
│       │   │   ├── ml.py
│       │   │   ├── reports.py
│       │   │   └── notifications.py
│       │   └── beat_schedule.py  ← jobs periódicos
│       │
│       ├── stream/               ← stream processor
│       │   ├── processor.py
│       │   └── enrichers/
│       │
│       ├── core/                 ← compartilhado
│       │   ├── config.py         ← Pydantic Settings
│       │   ├── database.py
│       │   ├── redis.py
│       │   ├── logging.py
│       │   ├── security.py
│       │   └── exceptions.py
│       │
│       └── integrations/         ← integrações externas
│           ├── geoip.py
│           ├── threat_intel/
│           ├── notifiers/
│           └── storage/
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

### Configuração via Pydantic Settings

```python
# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    url: str
    pool_size: int = 20
    max_overflow: int = 10
    echo: bool = False

class RedisSettings(BaseSettings):
    url: str
    cache_db: int = 0
    sessions_db: int = 1
    queue_db: int = 2

class SentinelSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_nested_delimiter='__',
    )
    
    debug: bool = False
    secret_key: str
    cors_origins: list[str] = []
    
    database: DatabaseSettings
    redis: RedisSettings
    
    # ...

settings = SentinelSettings()
```

`.env`:
```
DEBUG=false
SECRET_KEY=...
DATABASE__URL=postgresql+asyncpg://...
REDIS__URL=redis://localhost:6379
```

### FastAPI app setup

```python
# api/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_redis()
    yield
    # Shutdown
    await close_redis()
    await close_db()

app = FastAPI(
    title="SentinelBR API",
    version="1.0.0",
    lifespan=lifespan,
)

# Middlewares (ordem importa: bottom up na execução)
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(hosts.router, prefix="/api/v1/hosts", tags=["hosts"])
# ...

# Health
@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db_session)):
    await db.execute(text("SELECT 1"))
    await redis.ping()
    return {"status": "ready"}
```

### Padrão de router

```python
# api/routers/alerts.py
from fastapi import APIRouter, Depends, status

router = APIRouter()

@router.get("/", response_model=PageResponse[AlertResponse])
async def list_alerts(
    filters: AlertFilters = Depends(),
    pagination: Pagination = Depends(),
    service: AlertService = Depends(get_alert_service),
    user: User = Depends(get_current_user),
    _perm = Depends(require_permission("alerts.read")),
) -> PageResponse[AlertResponse]:
    items, total = await service.list_filtered(filters, pagination)
    return PageResponse(items=items, total=total, page=pagination.page)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_alert(...): ...

@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert(...): ...

@router.patch("/{alert_id}/status")
async def update_status(...): ...
```

### Service layer

```python
# services/alert_service.py
class AlertService:
    def __init__(
        self,
        repo: AlertRepository,
        event_bus: EventBus,
        cache: Cache,
    ):
        self.repo = repo
        self.event_bus = event_bus
        self.cache = cache
    
    async def list_filtered(
        self,
        filters: AlertFilters,
        pagination: Pagination,
    ) -> tuple[list[Alert], int]:
        cache_key = f"alerts:list:{filters.cache_key()}:{pagination.cache_key()}"
        if cached := await self.cache.get(cache_key):
            return cached
        
        items = await self.repo.list_filtered(filters, pagination)
        total = await self.repo.count_filtered(filters)
        
        await self.cache.set(cache_key, (items, total), ttl=30)
        return items, total
    
    async def create_or_update(self, event_data: dict) -> Alert:
        fingerprint = self._compute_fingerprint(event_data)
        
        existing = await self.repo.find_by_fingerprint(fingerprint)
        if existing:
            await self.repo.increment_count(existing.id)
            return existing
        
        alert = await self.repo.create(...)
        await self.event_bus.publish("alert.created", {...})
        return alert
```

### Repository layer

```python
# repositories/alert_repository.py
class AlertRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def list_filtered(
        self,
        filters: AlertFilters,
        pagination: Pagination,
    ) -> list[Alert]:
        query = select(AlertModel).where(AlertModel.deleted_at.is_(None))
        
        if filters.severity:
            query = query.where(AlertModel.severity == filters.severity)
        if filters.host_id:
            query = query.where(AlertModel.host_id == filters.host_id)
        # ...
        
        query = query.offset(pagination.offset).limit(pagination.limit)
        query = query.order_by(AlertModel.created_at.desc())
        
        result = await self.db.execute(query)
        return [Alert.from_orm(row) for row in result.scalars()]
    
    async def find_by_fingerprint(self, fp: str) -> Alert | None: ...
    async def increment_count(self, alert_id: UUID) -> None: ...
    async def create(self, data: dict) -> Alert: ...
```

---

## O frontend em detalhes

### Estrutura de pastas

```
sentinelbr-web/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.ts
├── public/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── routes/                   ← TanStack Router (file-based)
│   │   ├── __root.tsx
│   │   ├── index.tsx             ← /
│   │   ├── login.tsx             ← /login
│   │   ├── _authenticated.tsx    ← layout autenticado
│   │   └── _authenticated/
│   │       ├── dashboard.tsx
│   │       ├── hosts.tsx
│   │       ├── alerts/
│   │       │   ├── index.tsx
│   │       │   └── $alertId.tsx
│   │       └── ...
│   │
│   ├── components/
│   │   ├── ui/                   ← shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Topbar.tsx
│   │   │   └── CommandPalette.tsx
│   │   ├── charts/
│   │   ├── tables/
│   │   └── domain/               ← componentes específicos do domínio
│   │       ├── AlertCard.tsx
│   │       ├── HostStatusBadge.tsx
│   │       └── SeverityIcon.tsx
│   │
│   ├── features/                 ← organizado por feature/módulo
│   │   ├── auth/
│   │   │   ├── api.ts
│   │   │   ├── hooks.ts
│   │   │   ├── store.ts
│   │   │   └── types.ts
│   │   ├── alerts/
│   │   ├── firewall/
│   │   └── ...
│   │
│   ├── lib/
│   │   ├── api-client.ts         ← cliente HTTP
│   │   ├── ws-client.ts
│   │   ├── query-client.ts
│   │   ├── auth.ts
│   │   └── utils.ts
│   │
│   ├── hooks/                    ← hooks compartilhados
│   ├── stores/                   ← Zustand stores
│   ├── i18n/
│   │   ├── pt-BR.json
│   │   └── en-US.json
│   └── styles/
│       └── globals.css
│
└── tests/
```

### API client

```typescript
// lib/api-client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (r) => r,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshed = await tryRefreshToken();
      if (refreshed) return apiClient.request(error.config);
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);
```

### Server state com TanStack Query

```typescript
// features/alerts/api.ts
export const alertsApi = {
  list: async (filters: AlertFilters): Promise<AlertList> => {
    const r = await apiClient.get('/alerts', { params: filters });
    return r.data;
  },
  get: async (id: string): Promise<Alert> => { ... },
  updateStatus: async (id: string, status: string) => { ... },
};

// features/alerts/hooks.ts
export function useAlerts(filters: AlertFilters) {
  return useQuery({
    queryKey: ['alerts', filters],
    queryFn: () => alertsApi.list(filters),
    staleTime: 10_000,
    refetchInterval: 30_000,  // auto-refresh
  });
}

export function useUpdateAlertStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: alertsApi.updateStatus,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  });
}
```

### Client state com Zustand

```typescript
// stores/auth-store.ts
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      login: async (credentials) => {
        const { user, accessToken, refreshToken } = await authApi.login(credentials);
        set({ user, accessToken, refreshToken });
      },
      logout: () => set({ user: null, accessToken: null, refreshToken: null }),
    }),
    { name: 'auth' }
  )
);
```

### WebSocket realtime

```typescript
// lib/ws-client.ts
class WSClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  
  connect(token: string) {
    this.ws = new WebSocket(`${WS_URL}?token=${token}`);
    this.ws.onmessage = this.handleMessage;
    this.ws.onclose = this.handleClose;
  }
  
  private handleMessage = (event: MessageEvent) => {
    const msg = JSON.parse(event.data);
    eventBus.emit(msg.type, msg.data);
  };
  
  private handleClose = () => {
    const delay = Math.min(1000 * 2 ** this.reconnectAttempts, 30000);
    setTimeout(() => this.connect(token), delay);
    this.reconnectAttempts++;
  };
}

// hooks/use-realtime.ts
export function useRealtimeAlerts() {
  const qc = useQueryClient();
  
  useEffect(() => {
    return eventBus.on('alert.created', () => {
      qc.invalidateQueries({ queryKey: ['alerts'] });
      toast.error('Novo alerta detectado');
    });
  }, []);
}
```

---

## Workers e processamento assíncrono

### Celery setup

```python
# workers/celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    'sentinelbr',
    broker=settings.redis.queue_url,
    backend=settings.redis.queue_url,
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='America/Sao_Paulo',
    enable_utc=True,
    task_acks_late=True,           # ack só após sucesso
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # justo entre workers
    task_routes={
        'sentinelbr.workers.tasks.correlation.*': {'queue': 'correlation'},
        'sentinelbr.workers.tasks.ml.*': {'queue': 'ml'},
        'sentinelbr.workers.tasks.reports.*': {'queue': 'reports'},
        'sentinelbr.workers.tasks.notifications.*': {'queue': 'notification'},
    },
    beat_schedule={
        'cleanup-expired-blocks': {
            'task': 'sentinelbr.workers.tasks.firewall.cleanup_expired_blocks',
            'schedule': crontab(minute='*/5'),
        },
        'retention-daily': {
            'task': 'sentinelbr.workers.tasks.retention.run_retention',
            'schedule': crontab(hour=3, minute=0),
        },
        'backup-postgres-daily': {
            'task': 'sentinelbr.workers.tasks.backup.backup_postgres',
            'schedule': crontab(hour=2, minute=0),
        },
        'retrain-anomaly-models-weekly': {
            'task': 'sentinelbr.workers.tasks.ml.retrain_models',
            'schedule': crontab(day_of_week='sun', hour=4, minute=0),
        },
    },
)
```

### Tasks típicas

```python
# tasks/correlation.py
@celery_app.task(queue='correlation', bind=True, max_retries=3)
def evaluate_rule(self, event_id: str, rule_id: str):
    try:
        event = event_repo.get(event_id)
        rule = rule_repo.get(rule_id)
        
        if rule.matches(event):
            window_key = f"correlation:{rule_id}:{event.fingerprint}"
            redis.zadd(window_key, {event_id: event.timestamp.timestamp()})
            redis.zremrangebyscore(window_key, 0, time.time() - rule.timeframe)
            
            count = redis.zcard(window_key)
            if count >= rule.threshold:
                alert_service.create_or_update(...)
    except Exception as e:
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


# tasks/notifications.py
@celery_app.task(queue='notification')
def send_telegram_notification(alert_id: str, channel_id: str):
    alert = alert_repo.get(alert_id)
    message = render_alert_template(alert)
    telegram_client.send_message(channel_id, message)
```

### Stream processor (assíncrono, não Celery)

```python
# stream/processor.py
async def process_event_stream():
    redis = await get_redis()
    last_id = '$'  # pega só novos
    
    while True:
        items = await redis.xread(
            streams={'events:raw': last_id},
            count=100,
            block=5000,
        )
        
        for stream_name, events in items:
            for event_id, data in events:
                try:
                    await process_single_event(data)
                    last_id = event_id
                except Exception as e:
                    logger.exception("Error processing event")
                    # Move para DLQ
                    await redis.xadd('events:dlq', {**data, 'error': str(e)})


async def process_single_event(data: dict):
    # 1. Normaliza ECS
    normalized = ecs_normalizer.normalize(data)
    
    # 2. Enriquece
    enriched = await enricher.enrich(normalized)
    
    # 3. Persiste no Loki
    await loki_client.push(enriched)
    
    # 4. Avalia regras (async com workers)
    for rule_id in active_rules:
        evaluate_rule.delay(enriched['id'], rule_id)
```

---

## Stack técnica completa

### Backend

| Categoria | Tecnologia | Versão | Por quê |
|-----------|------------|--------|---------|
| Linguagem (servidor) | Python | 3.12+ | Ecossistema, produtividade |
| Linguagem (agente) | Go | 1.22+ | Binário único, baixo footprint |
| Web framework | FastAPI | 0.110+ | Type hints nativo, OpenAPI auto |
| ASGI server | Uvicorn + Gunicorn | latest | Padrão produção |
| ORM | SQLAlchemy | 2.0+ | Maduro, type-safe (2.0) |
| DB driver | asyncpg | latest | Mais rápido que psycopg |
| Migrations | Alembic | latest | Padrão SQLAlchemy |
| Validação | Pydantic | 2.x | Performance + ecosistema |
| Async tasks | Celery | 5.3+ | Maduro, bem documentado |
| Stream processing | asyncio + Redis Streams | — | Sem dependência extra |
| Cache | Redis | 7.2+ | Multi-uso |
| Banco | PostgreSQL | 16 | Versátil, robusto |
| Logs | Loki | 3.x | Custo-benefício |
| Storage | MinIO | latest | Compatível S3 |
| gRPC | grpcio | latest | Padrão para agentes |
| HTTP client | httpx | latest | Async-first |

### Frontend

| Categoria | Tecnologia |
|-----------|------------|
| Framework | React 18 |
| Linguagem | TypeScript 5 |
| Build tool | Vite |
| Routing | TanStack Router |
| Server state | TanStack Query |
| Client state | Zustand |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Forms | React Hook Form + Zod |
| Charts | Recharts + ECharts |
| Tables | TanStack Table + Virtual |
| Animations | Framer Motion |
| i18n | react-i18next |
| Icons | Lucide React |
| Testing | Vitest + Playwright |

### DevOps

| Categoria | Tecnologia |
|-----------|------------|
| Containers | Docker |
| Orchestration (dev) | Docker Compose |
| Orchestration (prod) | Kubernetes (opcional) |
| Helm chart | sim, para K8s |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Métricas | Prometheus |
| Dashboards | Grafana |
| Tracing | OpenTelemetry + Jaeger |
| Secrets | sealed-secrets ou vault |

### Ferramentas de qualidade

| Linguagem | Linter/Formatter | Testing |
|-----------|------------------|---------|
| Python | Ruff (lint+format) | Pytest + pytest-asyncio |
| TypeScript | ESLint + Prettier | Vitest + Playwright |
| Go | golangci-lint + gofmt | testing nativo |
| Dockerfile | hadolint | — |
| YAML | yamllint | — |

---

## Modelo de threads e concorrência

### Servidor API (Python)

- **Async/await em tudo**: I/O-bound (DB, Redis, Loki) não bloqueia
- **Workers Uvicorn**: 1 worker = 1 processo Python; em produção rodar `2 * cpu_cores` processos
- **Connection pooling**: SQLAlchemy + asyncpg gerenciam pool por worker

### Workers Celery

- **Worker = processo**: cada um consome de filas específicas
- **Concorrência**: prefork (default) ou gevent para I/O
- **Escala horizontal**: adicionar mais workers = mais throughput

### Stream processor

- **Single process, asyncio**: alta vazão de eventos pequenos
- **Múltiplas instâncias**: para escala, usar consumer groups do Redis Stream

### Agente (Go)

- **Goroutines** para coletas paralelas (uma por arquivo de log)
- **Channels** para comunicação entre goroutines
- **Context** para cancelamento limpo no shutdown

---

## Estratégia de testes

### Pirâmide de testes

```
         /\
        /  \    E2E (poucos, lentos)
       /────\
      /      \  Integration (DB real, mocks externos)
     /────────\
    /          \  Unit (muitos, rápidos)
   /────────────\
```

### Unit tests

- Mockam dependências externas
- Testam lógica isolada
- Devem rodar em <1s no total
- Coverage alvo: 80%+

```python
async def test_alert_service_creates_new_alert(mocker):
    repo = mocker.AsyncMock()
    repo.find_by_fingerprint.return_value = None
    repo.create.return_value = Alert(id=uuid4(), ...)
    
    service = AlertService(repo=repo, event_bus=mocker.AsyncMock(), cache=mocker.AsyncMock())
    
    result = await service.create_or_update({"foo": "bar"})
    
    assert repo.create.called
    assert result.id is not None
```

### Integration tests

- Banco de dados real (testcontainers ou pytest-postgresql)
- Testam interação entre camadas
- Lentos comparativamente

```python
@pytest.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()

async def test_alert_repository_creates_and_finds(db_session):
    repo = AlertRepository(db_session)
    alert = await repo.create(...)
    
    found = await repo.find_by_id(alert.id)
    assert found.id == alert.id
```

### E2E tests

- Sobem stack completa via docker-compose
- Frontend + API + DB
- Playwright para frontend
- Poucos cenários críticos: login, criar alerta, bloquear IP

```typescript
test('admin pode bloquear IP atacante', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name=email]', 'admin@test.com');
  await page.fill('[name=password]', 'password');
  await page.click('button:has-text("Entrar")');
  
  await page.goto('/alerts');
  await page.click('text=Brute force SSH');
  await page.click('button:has-text("Bloquear IP")');
  await page.click('button:has-text("Confirmar")');
  
  await expect(page.locator('.toast')).toContainText('IP bloqueado');
});
```

---

## Observabilidade

### Logs estruturados

Sempre JSON estruturado, nunca print/string interpolation. Lib: `structlog`.

```python
logger = structlog.get_logger()

logger.info(
    "alert_created",
    alert_id=alert.id,
    severity=alert.severity,
    host_id=alert.host_id,
    rule_id=alert.rule_id,
)
```

### Métricas Prometheus

```python
from prometheus_client import Counter, Histogram, Gauge

events_received = Counter(
    'sentinelbr_events_received_total',
    'Total events received from agents',
    ['source'],
)

api_request_duration = Histogram(
    'sentinelbr_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status'],
)

active_agents = Gauge(
    'sentinelbr_active_agents',
    'Number of active (online) agents',
)
```

### Tracing (OpenTelemetry)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("process_event")
async def process_event(event):
    span = trace.get_current_span()
    span.set_attribute("event.source", event.source)
    span.set_attribute("event.host", event.host)
    
    with tracer.start_as_current_span("normalize"):
        normalized = normalize(event)
    
    with tracer.start_as_current_span("enrich"):
        enriched = await enrich(normalized)
    
    with tracer.start_as_current_span("loki_push"):
        await loki.push(enriched)
```

Tracing flui de API → workers → DB, dando visibilidade completa de uma requisição.

---

## Decisões arquiteturais resumidas

Tabela ADR-style das principais decisões. Cada uma vai virar um arquivo próprio em `08-stack-decisions.md`.

| ID | Decisão | Status | Trade-off principal |
|----|---------|--------|---------------------|
| ADR-001 | Python para API | ✅ Aceita | Produtividade > performance bruta |
| ADR-002 | Go para agente | ✅ Aceita | Footprint baixo > unidade de stack |
| ADR-003 | PostgreSQL como DB principal | ✅ Aceita | Maturidade > performance NoSQL |
| ADR-004 | Loki em vez de Elastic | ✅ Aceita | Custo > full-text search avançado |
| ADR-005 | gRPC para agente | ✅ Aceita | Performance > simplicidade REST |
| ADR-006 | mTLS sempre | ✅ Aceita | Segurança > complexidade ops |
| ADR-007 | Celery em vez de RQ/Dramatiq | ✅ Aceita | Maturidade > minimalismo |
| ADR-008 | React em vez de Vue/Svelte | ✅ Aceita | Ecossistema > peso do bundle |
| ADR-009 | shadcn/ui em vez de MUI | ✅ Aceita | Customização > componentes prontos |
| ADR-010 | Docker Compose como deploy MVP | ✅ Aceita | Simplicidade > escala vertical |

---

## Por que essa arquitetura impressiona no portfólio

- **Decisões justificadas**: cada escolha tem motivo, não é "porque sim"
- **Padrões corretos**: Repository, DI, CQRS leve, Circuit Breaker são padrões enterprise
- **Camadas claras**: separation of concerns rigorosa
- **Async-first**: Python moderno, não código de 2015
- **Observabilidade desde o dia 1**: métricas, logs estruturados, tracing
- **Testes em camadas**: pyramid testing, não copy-paste
- **Ferramentas certas**: stack atual de 2026, não Django + jQuery
- **Pensamento em failure modes**: cada componente tem fallback documentado

Cada seção é potencial post de LinkedIn:

- "Por que escolhi Repository pattern mesmo em Python" 
- "gRPC + mTLS para agentes: o porquê e o como"
- "Celery vs Dramatiq vs RQ em 2026: a comparação que faltava"
- "Stream processing leve com Redis Streams (sem Kafka)"
- "Circuit breaker em Python: 50 linhas que evitam cascading failures"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
