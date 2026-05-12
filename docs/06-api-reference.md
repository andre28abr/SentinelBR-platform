# SentinelBR — API Reference

> Documentação da API REST. Lista todos os endpoints, autenticação, formatos de request/response, códigos de status e exemplos práticos. Serve como contrato entre frontend e backend, e como guia para integrações de terceiros.

---

## 📋 Sumário

1. [Conceitos básicos](#conceitos-básicos)
2. [Autenticação](#autenticação)
3. [Convenções](#convenções)
4. [Códigos de status HTTP](#códigos-de-status-http)
5. [Formato de erros](#formato-de-erros)
6. [Paginação](#paginação)
7. [Filtros e ordenação](#filtros-e-ordenação)
8. [Rate limiting](#rate-limiting)
9. [Endpoints por módulo](#endpoints-por-módulo)
10. [WebSocket](#websocket)
11. [Webhooks](#webhooks)
12. [SDK e clientes](#sdk-e-clientes)
13. [Exemplos práticos completos](#exemplos-práticos-completos)

---

## Conceitos básicos

### O que é uma API REST?

API (Application Programming Interface) é um "cardápio" que o servidor oferece para que outros programas conversem com ele. REST é o **estilo arquitetural** mais usado: cada coisa que existe (usuário, alerta, regra) tem uma URL única, e você usa **verbos HTTP** para agir sobre ela:

| Verbo | Significa | Exemplo |
|-------|-----------|---------|
| GET | Buscar/listar | `GET /alerts` → lista alertas |
| POST | Criar | `POST /alerts` → cria alerta |
| PATCH | Atualizar parcial | `PATCH /alerts/123` → muda só status |
| PUT | Substituir completo | `PUT /alerts/123` → substitui tudo |
| DELETE | Remover | `DELETE /alerts/123` → apaga |

### Base URL

```
https://sua-instancia.exemplo.com/api/v1
```

A versão `v1` está na URL. Quando lançarmos breaking changes, `v2` coexistirá com `v1` por período de deprecation.

### Formato

- **Request body**: JSON
- **Response body**: JSON
- **Encoding**: UTF-8
- **Content-Type**: `application/json`

### Documentação interativa

A própria API expõe documentação navegável:

- **Swagger UI**: `https://sua-instancia.exemplo.com/docs`
- **ReDoc**: `https://sua-instancia.exemplo.com/redoc`
- **OpenAPI JSON**: `https://sua-instancia.exemplo.com/openapi.json`

Você pode testar endpoints direto no Swagger UI sem precisar de Postman.

---

## Autenticação

### Métodos suportados

#### 1. JWT (sessão de usuário)

Para uso pelo frontend e usuários humanos.

**Fluxo:**

```
1. POST /auth/login → recebe access_token + refresh_token
2. Em cada request: Authorization: Bearer <access_token>
3. Quando access_token expira (15min): POST /auth/refresh
4. Logout: POST /auth/logout
```

#### 2. API Token (PAT — Personal Access Token)

Para integração programática (scripts, CI/CD, outras ferramentas).

```
Authorization: Bearer sbr_abc123...
```

Tokens não expiram (a menos que configurado), têm escopos limitados, e podem ser revogados a qualquer momento.

#### 3. mTLS (apenas para agentes)

Não exposto via HTTP — agentes usam gRPC com certificado mútuo.

### Permissões (RBAC)

Cada endpoint exige uma ou mais permissões. O usuário precisa ter um role que contenha aquela permissão.

Permissões seguem o formato `<modulo>.<recurso>.<ação>`:

```
auth.users.create
auth.users.read
auth.users.update
auth.users.delete
firewall.rules.create
firewall.rules.read
firewall.rules.update
firewall.rules.delete
alerts.read
alerts.update
playbooks.execute
lgpd.reports.generate
```

Roles padrão:

| Role | Permissões |
|------|-----------|
| `admin` | Tudo (`*`) |
| `analyst` | Leitura geral, escrita em alertas e firewall |
| `viewer` | Apenas leitura |
| `auditor` | Leitura + acesso à auditoria |
| `dpo` | Tudo de LGPD + leitura de eventos relacionados |

---

## Convenções

### URLs

- **Plurais para coleções**: `/alerts`, `/hosts`, `/rules`
- **IDs em UUIDs**: `/alerts/550e8400-e29b-41d4-a716-446655440000`
- **Sub-recursos aninhados quando faz sentido**: `/alerts/{id}/comments`
- **Ações não-CRUD em verbos**: `/alerts/{id}/acknowledge`, `/playbooks/{id}/execute`
- **Snake_case nos campos JSON**: `created_at`, não `createdAt`
- **kebab-case nas URLs**: `/data-assets`, não `/dataAssets`

### Datas

Sempre **ISO 8601 com timezone**:

```json
{
  "created_at": "2026-05-09T14:23:45.123Z",
  "expires_at": "2026-05-09T15:23:45.123-03:00"
}
```

### IDs

UUIDs v4 em texto:

```json
{"id": "550e8400-e29b-41d4-a716-446655440000"}
```

### Booleanos

```json
{"enabled": true, "deleted": false}
```

Não use 0/1, "yes"/"no", "true"/"false" como strings.

### Campos null vs ausentes

- **Campo presente com `null`**: explicitamente "sem valor"
- **Campo ausente**: não foi tocado (importante em PATCH)

Em PATCH, omitir um campo significa "não mexa". Para limpar um campo, mande explicitamente `null`.

---

## Códigos de status HTTP

Usamos códigos HTTP semanticamente corretos:

### Sucesso (2xx)

| Código | Quando |
|--------|--------|
| `200 OK` | GET/PATCH com sucesso |
| `201 Created` | POST criou recurso |
| `202 Accepted` | Request aceito, processamento assíncrono |
| `204 No Content` | DELETE bem-sucedido (sem body) |

### Cliente errou (4xx)

| Código | Quando |
|--------|--------|
| `400 Bad Request` | JSON inválido ou regra de negócio violada |
| `401 Unauthorized` | Sem autenticação ou token inválido |
| `403 Forbidden` | Autenticado mas sem permissão |
| `404 Not Found` | Recurso não existe |
| `409 Conflict` | Conflito (ex: criar duplicata, race condition) |
| `422 Unprocessable Entity` | Validação de schema falhou |
| `429 Too Many Requests` | Rate limit excedido |

### Servidor errou (5xx)

| Código | Quando |
|--------|--------|
| `500 Internal Server Error` | Bug no servidor |
| `502 Bad Gateway` | Dependência externa falhou |
| `503 Service Unavailable` | Manutenção ou sobrecarga |
| `504 Gateway Timeout` | Dependência demorou demais |

---

## Formato de erros

Todos os erros seguem o mesmo formato JSON:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "O campo 'severity' deve ser um dos valores: low, medium, high, critical",
    "details": [
      {
        "field": "severity",
        "value": "extreme",
        "constraint": "enum",
        "message": "Valor 'extreme' não permitido"
      }
    ],
    "request_id": "req_abc123",
    "timestamp": "2026-05-09T14:23:45.123Z"
  }
}
```

### Códigos de erro semânticos

| Code | Significado |
|------|-------------|
| `VALIDATION_ERROR` | Schema/dados inválidos |
| `AUTHENTICATION_REQUIRED` | Sem autenticação |
| `INVALID_CREDENTIALS` | Login falhou |
| `TOKEN_EXPIRED` | JWT expirou |
| `PERMISSION_DENIED` | Sem permissão |
| `RESOURCE_NOT_FOUND` | Recurso não existe |
| `RESOURCE_CONFLICT` | Conflito (duplicata, etc.) |
| `RATE_LIMIT_EXCEEDED` | Muitas requests |
| `BUSINESS_RULE_VIOLATION` | Regra de negócio violada |
| `INTERNAL_ERROR` | Erro inesperado |
| `EXTERNAL_SERVICE_ERROR` | Dep. externa falhou |

### `request_id`

Toda response tem um `request_id` (também no header `X-Request-ID`). Ao reportar bug, incluir esse ID acelera muito o debug — permite achar logs estruturados completos.

---

## Paginação

### Padrão: page + size

```
GET /alerts?page=1&size=50
```

Response:

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "size": 50,
    "total_items": 1234,
    "total_pages": 25,
    "has_next": true,
    "has_previous": false
  }
}
```

**Limites:**
- `size` máximo: 100 (default 50)
- `page` começa em 1

### Paginação por cursor (para listas grandes)

Em endpoints de alta cardinalidade (ex: `/events`), usamos cursor para evitar problemas de paginação clássica (offset alto é lento, dados podem mudar entre páginas):

```
GET /events?cursor=eyJ0aW1l...&limit=100
```

Response:

```json
{
  "items": [...],
  "cursor": {
    "next": "eyJ0aW1l...",
    "has_more": true
  }
}
```

---

## Filtros e ordenação

### Filtros simples

Via query params:

```
GET /alerts?severity=high&status=open&host_id=550e8400-...
```

### Filtros com operadores

Para comparações (>, <, >=, <=, !=), sintaxe `[op]`:

```
GET /alerts?created_at[gte]=2026-05-01&created_at[lt]=2026-06-01
GET /events?event_count[gt]=10
```

Operadores suportados: `eq` (default), `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `nin`, `contains`, `startswith`.

### Filtros multi-valor

```
GET /alerts?severity[in]=high,critical
GET /hosts?tags[contains]=prod,web
```

### Ordenação

```
GET /alerts?sort=created_at:desc
GET /alerts?sort=severity:desc,created_at:asc
```

### Seleção de campos (sparse fieldsets)

Para reduzir payload:

```
GET /alerts?fields=id,severity,created_at
```

Retorna apenas esses campos por item. Útil para dashboards.

---

## Rate limiting

Todos os endpoints têm rate limiting. Headers retornam status:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1715269500
```

### Limites por tipo

| Tipo de auth | Limite |
|--------------|--------|
| Não autenticado (login, etc.) | 10/min por IP |
| Usuário JWT | 60/min |
| API token (read scope) | 600/min |
| API token (write scope) | 120/min |
| Admin | 600/min |

Quando excedido: `429 Too Many Requests` com `Retry-After` header.

---

## Endpoints por módulo

### 🔐 Auth — Autenticação

#### `POST /auth/login`

Login com usuário/senha.

**Permissões**: nenhuma (público)

**Request:**

```json
{
  "email": "admin@empresa.com",
  "password": "senha-forte-aqui",
  "remember_me": false
}
```

**Response 200:**

```json
{
  "user": {
    "id": "550e8400-...",
    "email": "admin@empresa.com",
    "username": "admin",
    "full_name": "Admin",
    "roles": ["admin"]
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Response 401:**

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Credenciais inválidas"
  }
}
```

**Erros possíveis**: 401 (credenciais), 403 (conta bloqueada), 429 (rate limit).

#### `POST /auth/login/mfa`

Segundo fator (TOTP) após login bem-sucedido em conta com MFA habilitado.

**Request:**

```json
{
  "mfa_token": "tok_abc123",
  "code": "123456"
}
```

**Response 200**: igual ao `/auth/login`.

#### `POST /auth/refresh`

Renova access token usando refresh token.

**Request:**

```json
{"refresh_token": "eyJ..."}
```

**Response 200:**

```json
{
  "access_token": "eyJ...",
  "expires_in": 900
}
```

#### `POST /auth/logout`

Invalida sessão atual.

**Permissões**: autenticado

**Response 204**: sem body.

#### `GET /auth/me`

Dados do usuário atual.

**Response 200:**

```json
{
  "id": "550e8400-...",
  "email": "admin@empresa.com",
  "username": "admin",
  "full_name": "Admin",
  "roles": ["admin"],
  "permissions": ["*"],
  "mfa_enabled": true,
  "last_login_at": "2026-05-09T10:00:00Z"
}
```

#### `POST /auth/password/change`

Trocar senha (autenticado).

**Request:**

```json
{
  "current_password": "...",
  "new_password": "..."
}
```

#### `POST /auth/password/reset/request`

Solicitar reset de senha.

#### `POST /auth/password/reset/confirm`

Confirmar reset com token enviado por email.

#### `POST /auth/mfa/enroll`

Iniciar enrollment de MFA (gera QR code).

**Response 200:**

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_url": "data:image/png;base64,iVBOR...",
  "backup_codes": ["abc-def-ghi", ...]
}
```

#### `POST /auth/mfa/verify`

Verifica código TOTP para finalizar enrollment.

#### `DELETE /auth/mfa`

Desabilita MFA (requer senha + código atual).

### 👥 Users — Gestão de usuários

#### `GET /users`

Lista usuários (paginado).

**Permissões**: `auth.users.read`

**Query params**: filtros padrão (`is_active`, `role`), paginação, ordenação.

**Response 200:**

```json
{
  "items": [
    {
      "id": "550e8400-...",
      "email": "user@empresa.com",
      "username": "user1",
      "full_name": "Usuário 1",
      "is_active": true,
      "roles": ["analyst"],
      "last_login_at": "2026-05-09T10:00:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ],
  "pagination": {...}
}
```

#### `POST /users`

Cria usuário.

**Permissões**: `auth.users.create`

**Request:**

```json
{
  "email": "novo@empresa.com",
  "username": "novouser",
  "full_name": "Novo Usuário",
  "password": "...",
  "roles": ["analyst"],
  "send_welcome_email": true
}
```

**Response 201**: dados do usuário criado.

#### `GET /users/{id}`

Detalhes do usuário.

#### `PATCH /users/{id}`

Atualiza usuário.

#### `DELETE /users/{id}`

Soft delete (marca `deleted_at`).

#### `POST /users/{id}/roles`

Atribui roles.

```json
{"roles": ["analyst", "auditor"]}
```

#### `DELETE /users/{id}/roles/{role_name}`

Remove role específica.

#### `POST /users/{id}/lock`

Bloqueia conta.

#### `POST /users/{id}/unlock`

Desbloqueia.

### 🔑 API Tokens

#### `GET /api-tokens`

Lista tokens do usuário atual.

#### `POST /api-tokens`

Cria novo token.

**Request:**

```json
{
  "name": "CI/CD Pipeline",
  "scopes": ["alerts.read", "firewall.write"],
  "expires_at": "2027-01-01T00:00:00Z"
}
```

**Response 201:**

```json
{
  "id": "550e8400-...",
  "name": "CI/CD Pipeline",
  "token": "sbr_live_abc123def456...",
  "token_prefix": "sbr_live_abc1",
  "scopes": ["alerts.read", "firewall.write"],
  "expires_at": "2027-01-01T00:00:00Z",
  "created_at": "2026-05-09T14:23:45Z"
}
```

⚠️ **O token completo só é mostrado uma vez**. Após isso, apenas o prefix.

#### `DELETE /api-tokens/{id}`

Revoga token.

### 🖥️ Hosts — Inventário

#### `GET /hosts`

Lista hosts.

**Permissões**: `inventory.hosts.read`

**Query params**: `status`, `tags`, `os_distribution`.

**Response 200:**

```json
{
  "items": [
    {
      "id": "550e8400-...",
      "hostname": "web-01.prod",
      "display_name": "Web Server 01",
      "primary_ip": "10.0.1.5",
      "all_ips": ["10.0.1.5", "192.168.1.5"],
      "os_family": "linux",
      "os_distribution": "ubuntu",
      "os_version": "22.04",
      "kernel_version": "5.15.0-91-generic",
      "architecture": "x86_64",
      "tags": ["prod", "web", "critical"],
      "agent_version": "1.0.3",
      "status": "online",
      "last_seen_at": "2026-05-09T14:23:00Z",
      "created_at": "2026-01-15T08:00:00Z"
    }
  ],
  "pagination": {...}
}
```

#### `POST /hosts`

Cria host (gera enrollment token).

**Request:**

```json
{
  "hostname": "web-01.prod",
  "display_name": "Web Server 01",
  "tags": ["prod", "web"],
  "metadata": {
    "cloud_provider": "aws",
    "region": "sa-east-1"
  }
}
```

**Response 201:**

```json
{
  "id": "550e8400-...",
  "hostname": "web-01.prod",
  "status": "pending",
  "enrollment": {
    "token": "enr_xyz123...",
    "command": "curl -fsSL https://.../install.sh | sudo bash -s -- --token=enr_xyz123...",
    "expires_at": "2026-05-09T15:23:45Z"
  }
}
```

#### `GET /hosts/{id}`

Detalhes do host (incluindo métricas atuais).

#### `PATCH /hosts/{id}`

Atualiza host (tags, display_name, metadata).

#### `DELETE /hosts/{id}`

Remove host (revoga cert, agente para de funcionar).

#### `GET /hosts/{id}/metrics`

Métricas do host (CPU, memória, disco).

**Query params**: `from`, `to`, `interval`.

**Response 200:**

```json
{
  "host_id": "550e8400-...",
  "from": "2026-05-09T13:23:00Z",
  "to": "2026-05-09T14:23:00Z",
  "interval": "1m",
  "series": {
    "cpu_usage": [
      {"timestamp": "2026-05-09T13:23:00Z", "value": 23.4},
      {"timestamp": "2026-05-09T13:24:00Z", "value": 25.1},
      ...
    ],
    "mem_usage": [...],
    "disk_usage": {
      "/": [...],
      "/var": [...]
    }
  }
}
```

#### `POST /hosts/{id}/isolate`

Isola host (corta rede exceto management).

**Permissões**: `inventory.hosts.isolate`

**Request:**

```json
{
  "reason": "Suspeita de comprometimento",
  "duration_seconds": 3600
}
```

**Response 202**: ação assíncrona, retorna task_id.

#### `POST /hosts/{id}/unisolate`

Reverte isolamento.

#### `POST /hosts/{id}/collect-forensics`

Coleta evidências.

**Request:**

```json
{
  "types": ["processes", "network", "memory"],
  "incident_id": "550e8400-..."
}
```

### 📊 Events — Eventos/Logs

Os eventos ficam no Loki, mas a API expõe abstração.

#### `GET /events`

Busca eventos.

**Permissões**: `siem.events.read`

**Query params:**
- `query`: linguagem Lucene-like (`host:web-01 AND severity:high`)
- `from`, `to`: período (default: últimas 24h)
- `limit`: máx 1000
- `cursor`: paginação por cursor

**Response 200:**

```json
{
  "items": [
    {
      "id": "evt_abc123",
      "@timestamp": "2026-05-09T14:23:45.123Z",
      "host": {"name": "web-01", "ip": "10.0.1.5"},
      "source": "sshd",
      "severity": "high",
      "event": {
        "category": "authentication",
        "action": "failed_login",
        "outcome": "failure"
      },
      "user": {"name": "root"},
      "source": {
        "ip": "203.0.113.42",
        "geo": {"country": "CN", "city": "Beijing"}
      },
      "raw": "Failed password for root from 203.0.113.42 ...",
      "rule_matches": ["ssh_brute_force"]
    }
  ],
  "cursor": {
    "next": "eyJ...",
    "has_more": true
  }
}
```

#### `POST /events/search/saved`

Salva busca para reutilizar.

#### `GET /events/search/saved`

Lista buscas salvas.

#### `GET /events/aggregate`

Agregações (contagens por dimensão).

**Query params:**
- `query`: filtro
- `from`, `to`
- `group_by`: campo (ex: `host.name`, `severity`)
- `metric`: `count` (default), `sum`, `avg`, `min`, `max`
- `interval`: para séries temporais (`1m`, `1h`, `1d`)

**Response 200:**

```json
{
  "buckets": [
    {"key": "web-01", "count": 1234},
    {"key": "db-01", "count": 567},
    ...
  ]
}
```

### 🚨 Alerts — Alertas

#### `GET /alerts`

Lista alertas.

**Filtros típicos**: `status`, `severity`, `host_id`, `assigned_to`, `created_at[gte]`.

#### `GET /alerts/{id}`

Detalhes completos do alerta.

**Response 200:**

```json
{
  "id": "550e8400-...",
  "title": "Brute force SSH",
  "description": "47 tentativas de login falhas...",
  "severity": "high",
  "status": "open",
  "fingerprint": "abc123...",
  "host": {
    "id": "...",
    "hostname": "web-01.prod",
    "primary_ip": "10.0.1.5"
  },
  "rule": {
    "id": "...",
    "title": "Brute Force SSH",
    "mitre_techniques": ["T1110.001"]
  },
  "source_ip": "203.0.113.42",
  "source_geo": {
    "country": "CN",
    "city": "Beijing"
  },
  "event_count": 47,
  "first_seen_at": "2026-05-09T14:22:00Z",
  "last_seen_at": "2026-05-09T14:23:45Z",
  "assigned_to": null,
  "enrichment": {
    "threat_intel": {
      "abuseipdb_score": 95,
      "categories": ["ssh", "brute-force"]
    }
  },
  "actions_taken": [
    {
      "type": "firewall.block_ip",
      "executed_at": "2026-05-09T14:23:46Z",
      "result": "success"
    }
  ],
  "comments_count": 0,
  "timeline_events_count": 5
}
```

#### `PATCH /alerts/{id}`

Atualiza alerta.

**Request:**

```json
{
  "status": "investigating",
  "assigned_to": "550e8400-..."
}
```

#### `POST /alerts/{id}/acknowledge`

Marca como reconhecido.

#### `POST /alerts/{id}/resolve`

Resolve alerta.

**Request:**

```json
{
  "resolution_note": "IP bloqueado, sem acesso confirmado"
}
```

#### `POST /alerts/{id}/false-positive`

Marca como falso positivo.

#### `GET /alerts/{id}/comments`

Lista comentários.

#### `POST /alerts/{id}/comments`

Adiciona comentário.

```json
{"content": "Investigando logs adicionais..."}
```

#### `GET /alerts/{id}/timeline`

Timeline do alerta (criação, mudanças de status, ações tomadas).

#### `GET /alerts/{id}/related-events`

Eventos relacionados ao alerta.

### 📜 Detection Rules — Regras Sigma

#### `GET /detection/rules`

Lista regras.

#### `POST /detection/rules`

Cria regra.

**Request:**

```json
{
  "yaml_content": "title: Brute Force SSH\ndescription: ...\n..."
}
```

A API valida o YAML, extrai metadata, e armazena.

#### `GET /detection/rules/{id}`

Detalhes da regra.

#### `PATCH /detection/rules/{id}`

Atualiza regra (gera nova versão).

#### `DELETE /detection/rules/{id}`

Soft delete.

#### `POST /detection/rules/{id}/enable`
#### `POST /detection/rules/{id}/disable`

Liga/desliga regra sem deletar.

#### `GET /detection/rules/{id}/versions`

Histórico de versões.

#### `POST /detection/rules/{id}/test`

Testa regra contra eventos históricos (sem disparar alertas).

**Request:**

```json
{
  "from": "2026-05-01T00:00:00Z",
  "to": "2026-05-09T00:00:00Z"
}
```

**Response 200:**

```json
{
  "matches": 47,
  "samples": [
    {"event_id": "...", "timestamp": "...", "host": "..."}
  ]
}
```

#### `POST /detection/rules/import`

Importa pacote de regras (Sigma rules zip).

### 🛡️ Firewall

#### `GET /firewall/rules/{host_id}`

Lista regras do host.

#### `POST /firewall/rules/{host_id}`

Adiciona regra.

**Request:**

```json
{
  "chain": "INPUT",
  "action": "ACCEPT",
  "protocol": "tcp",
  "source_ip": "10.0.0.0/8",
  "dest_port": 22,
  "comment": "SSH interno"
}
```

#### `PATCH /firewall/rules/{host_id}/{rule_id}`

Atualiza regra.

#### `DELETE /firewall/rules/{host_id}/{rule_id}`

Remove regra.

#### `GET /firewall/rules/{host_id}/snapshots`

Histórico de snapshots.

#### `POST /firewall/rules/{host_id}/rollback`

Volta para snapshot anterior.

```json
{"snapshot_id": "550e8400-..."}
```

#### `GET /firewall/templates`

Lista templates.

#### `POST /firewall/templates/apply`

Aplica template a host(s).

```json
{
  "template_id": "web-server-template",
  "host_ids": ["550e8400-..."]
}
```

#### `GET /firewall/blocks`

Lista IPs bloqueados.

#### `POST /firewall/blocks`

Bloqueia IP.

```json
{
  "ip": "203.0.113.42",
  "reason": "Brute force SSH",
  "duration_seconds": 3600,
  "scope": "global"
}
```

#### `DELETE /firewall/blocks/{id}`

Remove bloqueio.

#### `GET /firewall/allowlist`
#### `POST /firewall/allowlist`

Lista de IPs nunca bloqueáveis.

#### `GET /firewall/geoblock`
#### `PUT /firewall/geoblock`

Configuração de bloqueio por país.

```json
{
  "mode": "allowlist",
  "countries": ["BR", "US", "PT"]
}
```

### 🔒 SELinux

#### `GET /selinux/hosts`

Status SELinux de cada host.

#### `GET /selinux/denials`

Lista AVC denials.

**Filtros**: `host_id`, `status`, `scontext`, `tcontext`.

#### `GET /selinux/denials/{id}`

Detalhes do denial com sugestão.

#### `POST /selinux/denials/{id}/fix`

Aplica correção sugerida.

#### `POST /selinux/denials/{id}/ignore`

Ignora denial.

#### `GET /selinux/booleans/{host_id}`

Lista booleanos do host.

#### `PATCH /selinux/booleans/{host_id}/{boolean_name}`

Liga/desliga boolean.

```json
{"enabled": true, "persistent": true}
```

#### `GET /selinux/policies/{host_id}`
#### `POST /selinux/policies/{host_id}`

Gestão de policies customizadas.

#### `PATCH /selinux/mode/{host_id}`

Muda modo (enforcing/permissive).

```json
{"mode": "enforcing"}
```

### ⚡ Playbooks

#### `GET /playbooks`

Lista playbooks.

#### `POST /playbooks`

Cria playbook.

```json
{
  "name": "Brute Force SSH Response",
  "yaml_content": "...",
  "enabled": true
}
```

#### `GET /playbooks/{id}`
#### `PATCH /playbooks/{id}`
#### `DELETE /playbooks/{id}`

CRUD padrão.

#### `POST /playbooks/{id}/execute`

Executa manualmente.

```json
{
  "context": {
    "alert_id": "...",
    "ip": "203.0.113.42"
  }
}
```

**Response 202:**

```json
{
  "execution_id": "550e8400-...",
  "status": "running"
}
```

#### `GET /playbooks/{id}/executions`

Histórico de execuções.

#### `GET /playbooks/executions/{exec_id}`

Detalhes de execução.

#### `POST /playbooks/executions/{exec_id}/approve`

Aprova step pausado.

#### `POST /playbooks/executions/{exec_id}/reject`

Rejeita.

#### `GET /playbooks/actions`

Catálogo de ações disponíveis.

### ⚖️ LGPD

#### `GET /lgpd/assets`

Lista ativos sensíveis.

#### `POST /lgpd/assets`

Cadastra ativo.

```json
{
  "name": "Banco de clientes",
  "asset_type": "db_table",
  "location": "postgres://prod_db.customers",
  "host_id": "550e8400-...",
  "data_categories": ["personal"],
  "legal_basis": "contract",
  "purpose": "Atendimento contratual",
  "retention_period": "P5Y",
  "dpo_id": "550e8400-..."
}
```

#### `GET /lgpd/assets/{id}`
#### `PATCH /lgpd/assets/{id}`
#### `DELETE /lgpd/assets/{id}`

CRUD padrão.

#### `GET /lgpd/subject-requests`

Pedidos de titulares.

#### `POST /lgpd/subject-requests`

Cria pedido.

```json
{
  "request_type": "deletion",
  "subject_name": "João Silva",
  "subject_email": "joao@email.com",
  "request_details": "Quero apagar todos meus dados"
}
```

#### `POST /lgpd/subject-requests/{id}/discover`

Faz busca cross-system pelos dados do titular.

#### `POST /lgpd/subject-requests/{id}/respond`

Marca como respondido.

#### `GET /lgpd/incidents`
#### `POST /lgpd/incidents`

Gestão de incidentes de privacidade.

#### `GET /lgpd/reports`

Relatórios disponíveis.

#### `POST /lgpd/reports/generate`

Gera relatório.

```json
{
  "report_type": "operations_record",
  "period_start": "2026-01-01",
  "period_end": "2026-12-31"
}
```

**Response 202**: assíncrono.

#### `GET /lgpd/reports/{id}/download`

Baixa relatório (presigned URL do MinIO).

### 🔌 Integrations

#### `GET /integrations/notifications/channels`
#### `POST /integrations/notifications/channels`

Gestão de canais (Telegram, Slack, etc.).

#### `POST /integrations/notifications/channels/{id}/test`

Envia mensagem de teste.

#### `GET /integrations/threat-intel/feeds`

Feeds de threat intel ativos.

### 📚 Audit

#### `GET /audit/events`

Log de auditoria.

**Filtros**: `actor_id`, `action`, `target_type`, `from`, `to`.

**Permissões**: `audit.read`

### ⚙️ System

#### `GET /system/info`

Informações da instalação.

```json
{
  "version": "1.0.0",
  "build": "abc123",
  "started_at": "2026-05-09T08:00:00Z",
  "components": {
    "api": "ok",
    "database": "ok",
    "redis": "ok",
    "loki": "ok",
    "minio": "ok"
  }
}
```

#### `GET /system/metrics`

Métricas Prometheus (formato texto).

#### `GET /system/health/live`
#### `GET /system/health/ready`

Health checks Kubernetes-friendly.

---

## WebSocket

### Conexão

```
wss://sua-instancia/ws?token=<jwt>
```

### Mensagens recebidas pelo cliente

Formato:

```json
{
  "type": "alert.created",
  "data": { ... },
  "timestamp": "2026-05-09T14:23:45Z"
}
```

### Tipos de evento

| Type | Quando |
|------|--------|
| `alert.created` | Novo alerta |
| `alert.updated` | Alerta mudou status |
| `host.status_changed` | Host ficou online/offline |
| `playbook.execution_started` | Playbook iniciou |
| `playbook.approval_required` | Aprovação pendente |
| `system.notification` | Notificação geral |

### Subscrição (filtros)

Cliente pode filtrar:

```json
{
  "action": "subscribe",
  "channels": ["alerts.high_critical", "host.status"]
}
```

### Reconexão

Cliente deve implementar reconexão automática com backoff exponencial.

---

## Webhooks

A plataforma pode enviar eventos para URLs externas.

### Configuração

```
POST /integrations/webhooks
{
  "url": "https://meu-app.com/webhook",
  "events": ["alert.created", "incident.opened"],
  "secret": "minha-chave-hmac",
  "active": true
}
```

### Payload

```json
POST https://meu-app.com/webhook
Content-Type: application/json
X-Sentinel-Event: alert.created
X-Sentinel-Signature: sha256=abc123...
X-Sentinel-Delivery: 550e8400-...

{
  "event": "alert.created",
  "delivered_at": "2026-05-09T14:23:45Z",
  "data": { ... }
}
```

### Verificação de assinatura

```python
import hmac, hashlib

def verify_webhook(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Retry

Em caso de falha (não-2xx), retry com backoff:
- 1ª tentativa: imediata
- 2ª: 30s depois
- 3ª: 5min depois
- 4ª: 30min depois
- 5ª: 2h depois
- Após 5 falhas: webhook é desabilitado e admin notificado.

---

## SDK e clientes

### Python (oficial)

```python
from sentinelbr import SentinelClient

client = SentinelClient(
    base_url="https://sua-instancia.exemplo.com",
    api_token="sbr_live_abc...",
)

alerts = client.alerts.list(severity="high", status="open")
for alert in alerts:
    print(alert.title)

client.firewall.block_ip(
    ip="203.0.113.42",
    reason="Manual block",
    duration_seconds=3600,
)
```

### CLI

```bash
sentinelctl alerts list --severity high
sentinelctl firewall block 203.0.113.42 --duration 1h
sentinelctl hosts add web-01 --tags prod,web
```

### Outros (planejados)

- JavaScript/TypeScript (npm: `@sentinelbr/client`)
- Go (`github.com/sentinelbr/sentinel-go`)
- Ansible collection
- Terraform provider

---

## Exemplos práticos completos

### Exemplo 1: Login e listar alertas

```bash
# 1. Login
RESPONSE=$(curl -s -X POST https://api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@empresa.com","password":"..."}')

ACCESS_TOKEN=$(echo $RESPONSE | jq -r .access_token)

# 2. Listar alertas críticos abertos
curl -s "https://api/v1/alerts?severity=critical&status=open" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

### Exemplo 2: Bloquear IP via API token

```python
import httpx

API_TOKEN = "sbr_live_abc..."
BASE_URL = "https://sua-instancia.exemplo.com/api/v1"

with httpx.Client(headers={"Authorization": f"Bearer {API_TOKEN}"}) as client:
    response = client.post(
        f"{BASE_URL}/firewall/blocks",
        json={
            "ip": "203.0.113.42",
            "reason": "Detected by external SIEM",
            "duration_seconds": 3600,
            "scope": "global",
        },
    )
    response.raise_for_status()
    print(response.json())
```

### Exemplo 3: Webhook de Slack para alertas

```python
from fastapi import FastAPI, Request, HTTPException
import hmac, hashlib

app = FastAPI()
WEBHOOK_SECRET = "..."

@app.post("/sentinel-webhook")
async def receive_alert(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Sentinel-Signature", "")
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    
    if not hmac.compare_digest(f"sha256={expected}", signature):
        raise HTTPException(401, "Invalid signature")
    
    payload = await request.json()
    
    if payload["event"] == "alert.created":
        alert = payload["data"]
        send_to_slack(f"🚨 {alert['title']} em {alert['host']['hostname']}")
    
    return {"ok": True}
```

### Exemplo 4: Onboarding de novo host

```bash
# 1. Criar host
RESPONSE=$(curl -s -X POST https://api/v1/hosts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname":"new-server-01","tags":["prod"]}')

ENROLL_CMD=$(echo $RESPONSE | jq -r .enrollment.command)

# 2. Imprimir comando para rodar no servidor alvo
echo "Execute no servidor:"
echo "$ENROLL_CMD"

# 3. Aguardar primeira conexão
HOST_ID=$(echo $RESPONSE | jq -r .id)
while true; do
    STATUS=$(curl -s "https://api/v1/hosts/$HOST_ID" \
        -H "Authorization: Bearer $TOKEN" | jq -r .status)
    
    if [ "$STATUS" == "online" ]; then
        echo "Host conectado!"
        break
    fi
    
    sleep 5
done
```

---

## Por que essa API impressiona

Esta especificação demonstra:

- **REST maturo (Richardson nível 3)**: HATEOAS, verbos corretos, status codes precisos
- **OpenAPI auto-gerado**: contrato sempre atualizado
- **Versionamento explícito**: pensado para evolução
- **Erros estruturados**: códigos semânticos, request_id, detalhes
- **Paginação dupla**: page+size para UI, cursor para alta cardinalidade
- **Filtros poderosos**: operadores ricos, sparse fieldsets
- **Rate limiting transparente**: headers informativos
- **WebSocket + Webhooks**: realtime e integração
- **Exemplos reais**: não só schema, código que funciona
- **SDK + CLI**: developer experience completa

Posts potenciais no LinkedIn:

- "10 detalhes que separam APIs amadoras de profissionais"
- "Por que usar cursor pagination (e quando offset basta)"
- "OpenAPI auto-gerado: nunca mais documentação desatualizada"
- "RBAC granular: como modelar permissões que escalam"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
