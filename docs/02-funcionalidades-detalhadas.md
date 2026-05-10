# SentinelBR — Especificação Detalhada de Funcionalidades

> Documento técnico-funcional. Lista cada funcionalidade que será implementada, organizada por módulo, com critérios de aceitação, prioridade (MVP/v1/v2) e habilidades técnicas demonstradas. Serve simultaneamente como **roadmap de desenvolvimento** e como **mapa de skills** para apresentação no LinkedIn.

---

## 📋 Sumário

1. [Princípios do projeto](#princípios-do-projeto)
2. [Escopo MVP vs Visão Completa](#escopo-mvp-vs-visão-completa)
3. [Funcionalidades transversais (toda a plataforma)](#funcionalidades-transversais)
4. [Módulo 1 — SIEM](#módulo-1--siem-funcionalidades)
5. [Módulo 2 — Firewall](#módulo-2--firewall-funcionalidades)
6. [Módulo 3 — SELinux](#módulo-3--selinux-funcionalidades)
7. [Módulo 4 — Resposta a Incidentes](#módulo-4--resposta-a-incidentes-funcionalidades)
8. [Módulo 5 — Compliance LGPD](#módulo-5--compliance-lgpd-funcionalidades)
9. [Frontend](#frontend-funcionalidades)
10. [DevOps & Deploy](#devops--deploy)
11. [Mapa de habilidades demonstradas](#mapa-de-habilidades-demonstradas)
12. [Roadmap por fases](#roadmap-por-fases)

---

## Princípios do projeto

Toda funcionalidade obedece a três pilares inegociáveis:

### 🎯 Funcional
Não é demo de currículo: precisa funcionar de verdade em produção pequena/média (até ~50 servidores monitorados, ~1000 eventos/segundo). Decisões técnicas priorizam confiabilidade sobre "o que parece mais bonito no GitHub".

### 📈 Escalável
Arquitetura permite crescer **horizontalmente** sem reescrita: workers paralelos, mensageria desacoplada, banco com índices pensados, cache estratégico. Limite definido para MVP, mas caminho para escalar documentado.

### 🚀 Fácil de implantar
**Comando único** sobe tudo localmente (`docker compose up`). Deploy em VPS de R$ 30/mês deve funcionar. Scripts e Helm chart para Kubernetes para quem quiser. Documentação de instalação em até 10 passos.

---

## Escopo MVP vs Visão Completa

| Fase | Duração estimada | Entregável |
|------|------------------|------------|
| **MVP** | 2 meses | SIEM básico + Firewall básico funcionando ponta-a-ponta |
| **v1.0** | +2 meses | SELinux + Resposta a Incidentes |
| **v2.0** | +2 meses | LGPD + Multi-tenant + Helm chart |
| **v3.0** | contínuo | Otimizações, integrações, polimento |

Cada funcionalidade abaixo está marcada com `[MVP]`, `[v1]` ou `[v2]`.

---

## Funcionalidades transversais

Funcionalidades que atravessam toda a plataforma.

### 🔐 Autenticação & Autorização

#### F-AUTH-01 — Login com usuário/senha `[MVP]`
- **O quê**: Tela de login, sessão persistente via JWT
- **Critérios**:
  - Senha hasheada com Argon2id
  - Tokens com expiração (access 15min, refresh 7 dias)
  - Logout invalida tokens (blocklist em Redis)
- **Skills**: criptografia aplicada, JWT, segurança de sessão

#### F-AUTH-02 — 2FA com TOTP `[v1]`
- **O quê**: Segundo fator via app authenticator (Google Auth, Authy)
- **Critérios**:
  - QR code para configuração inicial
  - Códigos de backup (10 códigos descartáveis)
  - Obrigatório para usuários admin
- **Skills**: implementação RFC 6238, UX de segurança

#### F-AUTH-03 — RBAC (Role-Based Access Control) `[MVP]`
- **O quê**: Sistema de permissões baseado em papéis
- **Roles iniciais**: `admin`, `analyst`, `viewer`, `auditor`
- **Critérios**:
  - Permissões granulares por módulo e ação (ex: `firewall.rules.create`)
  - Checagem em cada endpoint da API
  - UI esconde botões/menus que o usuário não pode usar
- **Skills**: modelagem de autorização, design de API segura

#### F-AUTH-04 — Audit log de ações sensíveis `[MVP]`
- **O quê**: Registro imutável de toda ação relevante
- **Critérios**:
  - Quem, o quê, quando, IP de origem, resultado
  - Não pode ser deletado pela UI (apenas via DBA)
  - Exportável em CSV/JSON
- **Skills**: design de auditoria, integridade de dados

#### F-AUTH-05 — Integração SSO via OIDC `[v2]`
- **O quê**: Login com Google Workspace, Microsoft Entra, Keycloak
- **Skills**: OIDC/OAuth2, integração enterprise

---

### 🔌 API REST + OpenAPI

#### F-API-01 — API REST documentada `[MVP]`
- **O quê**: Toda funcionalidade da UI também acessível via API
- **Critérios**:
  - OpenAPI 3.1 gerado automaticamente (FastAPI)
  - Swagger UI em `/docs`
  - Versionada (`/api/v1/`)
  - Códigos HTTP corretos (não retornar 200 para erro)
- **Skills**: API design, REST maturity, contratos

#### F-API-02 — Rate limiting `[MVP]`
- **O quê**: Limite de requisições por IP/usuário
- **Critérios**:
  - Default: 60 req/min por usuário
  - Configurável via variável de ambiente
  - Headers `X-RateLimit-*` na resposta
  - Backend Redis (sliding window)
- **Skills**: defesa contra abuso, algoritmos de rate limiting

#### F-API-03 — Webhooks de saída `[v1]`
- **O quê**: Plataforma envia eventos para URLs externas
- **Critérios**:
  - Eventos: alerta criado, regra de firewall mudada, incidente
  - HMAC para assinatura (cliente verifica autenticidade)
  - Retry com backoff exponencial
  - Histórico de envios + replay
- **Skills**: design de webhook, sistemas distribuídos

#### F-API-04 — API tokens (PAT) `[v1]`
- **O quê**: Tokens longos para integração programática
- **Critérios**:
  - Escopos limitados (read-only, ou específico de módulo)
  - Revogação imediata
  - Expiração configurável
- **Skills**: gestão de credenciais, princípio do menor privilégio

---

### 📊 Observabilidade da própria plataforma

#### F-OBS-01 — Métricas Prometheus `[MVP]`
- **O quê**: Endpoint `/metrics` expondo métricas internas
- **Critérios**:
  - Métricas: latência de endpoints, fila de eventos, workers ativos, taxa de erro
  - Labels apropriados (sem cardinalidade explosiva)
- **Skills**: observabilidade, Prometheus, SRE

#### F-OBS-02 — Health checks `[MVP]`
- **O quê**: Endpoints `/health/live` e `/health/ready`
- **Critérios**:
  - Liveness: processo está vivo
  - Readiness: dependências OK (DB, Redis, storage)
  - Compatível com Kubernetes probes
- **Skills**: padrões cloud-native

#### F-OBS-03 — Tracing distribuído `[v1]`
- **O quê**: Rastreamento de requisições atravessando agente → API → workers
- **Critérios**: OpenTelemetry, exportador para Jaeger ou Tempo
- **Skills**: tracing, debugging em sistemas distribuídos

---

## Módulo 1 — SIEM (Funcionalidades)

### 📥 Coleta de logs

#### F-SIEM-01 — Agente de coleta multi-plataforma `[MVP]`
- **O quê**: Binário leve instalado nos hosts monitorados
- **Critérios**:
  - Suporta Linux (Ubuntu, Debian, RHEL, Rocky)
  - Footprint < 30 MB de RAM em idle
  - Configuração via YAML
  - Auto-update opcional (com versão pinnable)
  - Roda como serviço systemd
- **Skills**: Go (ou Python), packaging Linux, systemd

#### F-SIEM-02 — Coletores nativos `[MVP]`
- **O quê**: Suporte a fontes comuns sem configuração extra
- **Fontes suportadas no MVP**:
  - `auth.log` / `secure` (autenticação)
  - `syslog` / `journald`
  - `audit.log` (auditd)
  - `nginx` access/error logs
  - Apache access/error logs
  - SSH server logs
- **Critérios**:
  - Detecção automática (se o arquivo existe, ativa)
  - Posição persistida (não duplica em restart)
  - Rotação de log respeitada (logrotate-aware)
- **Skills**: parsing de logs reais, edge cases de I/O

#### F-SIEM-03 — Coletores adicionais `[v1]`
- PostgreSQL, MySQL, Docker, Kubernetes audit, fail2ban, suricata

#### F-SIEM-04 — Buffer local resiliente `[MVP]`
- **O quê**: Agente continua funcionando se o servidor central cair
- **Critérios**:
  - SQLite local com fila de eventos
  - Limite configurável de tamanho (default 500 MB)
  - Flush quando central volta (sem perder ordem)
- **Skills**: design para falhas, idempotência

#### F-SIEM-05 — Comunicação segura `[MVP]`
- **O quê**: Canal entre agente e servidor é criptografado e autenticado
- **Critérios**:
  - mTLS (mutual TLS) com cert por agente
  - Cert provisionado via token de enrollment
  - Rotação automática de certificados (90 dias)
- **Skills**: PKI, mTLS, gestão de certificados

---

### 🔄 Pipeline de processamento

#### F-SIEM-06 — Normalização ECS `[MVP]`
- **O quê**: Toda fonte é traduzida para o Elastic Common Schema
- **Critérios**:
  - Campos obrigatórios: `@timestamp`, `host.*`, `event.*`
  - Enriquecimento com dados do host (hostname, IP, OS)
  - Versionamento do schema (compatibilidade futura)
- **Skills**: data engineering, padronização

#### F-SIEM-07 — Enriquecimento `[v1]`
- **O quê**: Adicionar contexto a cada evento
- **Critérios**:
  - GeoIP (MaxMind GeoLite2): país, cidade, ISP do IP
  - Reverse DNS (cache para não martelar resolver)
  - Reputação (consulta a feeds: AbuseIPDB, AlienVault OTX)
  - Tag de "dentro/fora da rede corporativa"
- **Skills**: integração com fontes externas, caching estratégico

#### F-SIEM-08 — Workers paralelos `[MVP]`
- **O quê**: Processamento horizontalmente escalável
- **Critérios**:
  - Múltiplos workers consumindo da mesma fila (Redis Streams ou RabbitMQ)
  - Configurável: `WORKERS=4`
  - Dead letter queue para eventos que falham repetidamente
- **Skills**: sistemas distribuídos, message queues

#### F-SIEM-09 — Storage de logs `[MVP]`
- **O quê**: Persistência de longo prazo
- **Critérios**:
  - Backend padrão: Loki (mais leve)
  - Backend opcional: OpenSearch (mais features de busca)
  - Retenção configurável (default 30 dias quente, 90 frio)
  - Compressão automática (gzip ou zstd)
- **Skills**: storage de time-series, trade-offs custo/performance

---

### 🎯 Detecção e correlação

#### F-SIEM-10 — Engine de regras Sigma `[MVP]`
- **O quê**: Suporte ao padrão Sigma (formato YAML aberto, usado pela indústria)
- **Critérios**:
  - Carregar regras de `~/.sentinelbr/rules/`
  - Hot-reload (sem reiniciar o servidor)
  - Conversão Sigma → query Loki/OpenSearch
  - Catálogo inicial com 50+ regras (brute force, port scan, privilege escalation)
- **Skills**: parsers, design de DSL, threat detection

#### F-SIEM-11 — Detecção de anomalias com ML `[v1]`
- **O quê**: Detecta desvios sem regra explícita
- **Algoritmos**:
  - Isolation Forest para outliers em features (hora, geo, frequência)
  - DBSCAN para clusters de comportamento
  - Análise de série temporal (Prophet) para baselines
- **Critérios**:
  - Treinamento automático nos primeiros 7 dias (período de baseline)
  - Re-treinamento semanal (job Celery)
  - Score de anomalia 0-100 + explicabilidade (SHAP)
- **Skills**: ML aplicado, scikit-learn, feature engineering, explicabilidade

#### F-SIEM-12 — Correlação multi-evento `[v1]`
- **O quê**: Detectar padrões que envolvem múltiplos eventos relacionados
- **Exemplo**: "login bem-sucedido seguido de criação de usuário privilegiado em 5min" = ataque
- **Critérios**:
  - DSL para regras de correlação (extensão das regras Sigma)
  - Janelas deslizantes em Redis sorted sets
  - Cap de memória para evitar explosão
- **Skills**: stream processing, complex event processing

#### F-SIEM-13 — Threat intelligence feeds `[v1]`
- **O quê**: Consumir IOCs (Indicators of Compromise) de fontes públicas
- **Fontes**:
  - AbuseIPDB (IPs maliciosos)
  - AlienVault OTX
  - Feodo Tracker (botnets)
  - URLhaus (URLs maliciosas)
- **Critérios**:
  - Atualização automática (cron diário)
  - Cache local
  - Match em tempo real durante ingestão
- **Skills**: integração com APIs, threat intel

---

### 🔔 Alertas e investigação

#### F-SIEM-14 — Geração de alertas `[MVP]`
- **O quê**: Quando regra dispara, gera alerta estruturado
- **Critérios**:
  - Severidade: info, low, medium, high, critical
  - Deduplicação inteligente (mesmo alerta repetido = agrupado)
  - Auto-fechamento se situação resolveu (configurável)
- **Skills**: design de UX para operação 24/7

#### F-SIEM-15 — Notificações multi-canal `[MVP]`
- **Canais**:
  - E-mail (SMTP configurável)
  - Telegram (bot)
  - Slack (webhook)
  - Discord (webhook)
  - Webhook genérico
- **Critérios**:
  - Roteamento por severidade e tag
  - Não notificar de madrugada para alertas baixos (silent hours)
  - Throttling para evitar alert fatigue
- **Skills**: design de notificações, integração de plataformas

#### F-SIEM-16 — Busca avançada `[MVP]`
- **O quê**: Procurar em todos os logos com filtros e queries
- **Critérios**:
  - Linguagem de query intuitiva (similar a Lucene)
  - Filtros visuais: período, host, severidade, tag
  - Salvar buscas favoritas
  - Exportar resultado em CSV/JSON
- **Skills**: UX de busca, integração com Loki/OpenSearch

#### F-SIEM-17 — Timeline de incidente `[v1]`
- **O quê**: Visualização cronológica de eventos relacionados
- **Critérios**:
  - Linha do tempo interativa
  - Filtro por entidade (host, IP, usuário)
  - Anotações manuais ("aqui o atacante fez X")
- **Skills**: data viz, design de ferramentas forenses

---

## Módulo 2 — Firewall (Funcionalidades)

#### F-FW-01 — Detecção automática de backend `[MVP]`
- **O quê**: Identificar se o host usa nftables, iptables ou firewalld
- **Critérios**: Sem configuração manual; agente reporta backend
- **Skills**: abstração sobre ferramentas similares

#### F-FW-02 — Listagem de regras ativas `[MVP]`
- **O quê**: UI mostra todas as regras configuradas em cada host
- **Critérios**:
  - Visualização em tabela e em "fluxo" (qual chain → qual ação)
  - Busca/filtro por porta, IP, ação
  - Identificação visual de regras "perigosas" (aceita tudo, sem source)
- **Skills**: parsing de output de iptables/nft, data viz

#### F-FW-03 — CRUD de regras `[MVP]`
- **O quê**: Criar, editar, remover regras via interface
- **Critérios**:
  - Formulário com validação (porta entre 1-65535, IP válido)
  - Pré-visualização do comando que será executado
  - Confirmação obrigatória para regras de DROP em chains críticas
- **Skills**: UX defensiva, validação robusta

#### F-FW-04 — Templates declarativos `[MVP]`
- **O quê**: Conjuntos de regras prontas para casos comuns
- **Templates iniciais**:
  - Servidor Web (HTTP/HTTPS público, SSH restrito)
  - Servidor de Banco de Dados (DB porta apenas para rede interna)
  - Bastion Host (SSH público, restante interno)
  - Workstation (sem serviços expostos)
- **Critérios**:
  - YAML editável
  - Aplicar template = cria regras + tag identificando origem
  - Atualizar template propaga (com confirmação)
- **Skills**: design de configuração declarativa, IaC

#### F-FW-05 — Histórico e rollback `[MVP]`
- **O quê**: Toda mudança versionada, retornar a estado anterior em 1 clique
- **Critérios**:
  - Diff visual entre versões
  - Snapshots automáticos antes de cada mudança
  - Rollback testado (aplica + verifica + reverte se falhar)
- **Skills**: versionamento de configuração, controle transacional

#### F-FW-06 — Bloqueio dinâmico (integração com SIEM) `[MVP]`
- **O quê**: SIEM detecta ataque → firewall bloqueia automaticamente
- **Critérios**:
  - Backend `ipset` para performance (regra única em nft)
  - TTL configurável por tipo de ameaça
  - Lista de IPs bloqueados visível e gerenciável
  - Allowlist (jamais bloquear esses IPs)
- **Skills**: integração entre módulos, performance de filtros

#### F-FW-07 — Geo-blocking `[v1]`
- **O quê**: Bloquear/permitir por país de origem
- **Critérios**:
  - Base GeoLite2 atualizada semanalmente
  - UI com mapa-múndi clicável
  - Performance: usar ipset com nft set
- **Skills**: integração com GeoIP, visualização geo

#### F-FW-08 — Detecção de regras conflitantes `[v1]`
- **O quê**: Avisar quando uma regra é "morta" (nunca dispara) ou conflita com outra
- **Skills**: análise estática de configuração

#### F-FW-09 — Modo de simulação `[v1]`
- **O quê**: Aplicar mudança em modo "log only" antes de tornar efetiva
- **Critérios**: Por X horas, regra apenas registra o que faria, sem bloquear de fato
- **Skills**: feature flags em segurança, deployment safe

---

## Módulo 3 — SELinux (Funcionalidades)

#### F-SE-01 — Status agregado `[v1]`
- **O quê**: Dashboard mostrando modo do SELinux em cada host
- **Critérios**:
  - Visual: enforcing (verde), permissive (amarelo), disabled (vermelho)
  - Alerta quando host crítico está em permissive ou disabled
- **Skills**: monitoramento de configuração

#### F-SE-02 — Coleta de AVC denials `[v1]`
- **O quê**: Capturar e estruturar bloqueios do SELinux
- **Critérios**:
  - Parser robusto de `/var/log/audit/audit.log`
  - Deduplicação (mesmo denial X vezes = 1 entrada com count)
  - Enriquecimento: descrição amigável do contexto
- **Skills**: parsing de formato denso, troubleshooting Linux profundo

#### F-SE-03 — Tradução para linguagem humana `[v1]`
- **O quê**: AVC bruto → mensagem em português entendível
- **Critérios**:
  - Base de conhecimento mapeando contextos comuns (httpd_t, mysqld_t, etc.)
  - Sugestão de causa provável
  - Sugestão de ação corretiva
- **Skills**: design de UX para área hostil, tech writing

#### F-SE-04 — Geração assistida de policies `[v1]`
- **O quê**: Wizard que cria policies SELinux customizadas
- **Critérios**:
  - Coleta denials relacionados a um app
  - Wrapper sobre `audit2allow`
  - Mostra `.te` gerado para revisão
  - Aplicação requer aprovação explícita (segurança!)
  - Histórico de policies aplicadas
- **Skills**: automação de tarefa especializada, segurança de change management

#### F-SE-05 — Gestão de booleanos `[v1]`
- **O quê**: Interface para os "switches" do SELinux
- **Critérios**:
  - Lista todos os booleanos com descrição em PT-BR
  - Toggle persistente (`-P` flag)
  - Categorias (rede, banco, web, etc.)
  - Indicação de risco (médio/alto)
- **Skills**: tradução de configuração técnica para UX

#### F-SE-06 — Gestão de file contexts `[v1]`
- **O quê**: UI para `semanage fcontext`
- **Critérios**:
  - Wizard: aponta diretório → sugere contexto baseado em similares
  - `restorecon` automático após mudança
  - Diff antes/depois
- **Skills**: automação inteligente

#### F-SE-07 — Modo de troubleshooting `[v2]`
- **O quê**: Diagnosticar "por que isso não funciona?"
- **Fluxo**:
  1. Usuário descreve sintoma
  2. Plataforma correlaciona com AVCs recentes
  3. Sugere causa e fix
- **Skills**: diagnóstico assistido

---

## Módulo 4 — Resposta a Incidentes (Funcionalidades)

#### F-IR-01 — Engine de playbooks `[v1]`
- **O quê**: Executor de fluxos declarativos em YAML
- **Critérios**:
  - DSL clara: triggers, steps, conditions, loops
  - Variáveis e templating (`{{ event.source.ip }}`)
  - Execução isolada (timeout, sandbox de erros)
  - Logs de cada step
- **Skills**: design de DSL, executor de workflows

#### F-IR-02 — Catálogo de actions plugáveis `[v1]`
- **O quê**: Biblioteca de "blocos de Lego" para os playbooks
- **Actions iniciais**:
  - `firewall.block_ip(ip, duration)`
  - `firewall.unblock_ip(ip)`
  - `host.kill_process(host, pid)`
  - `host.isolate(host)` (corta rede exceto management)
  - `forensics.collect(host, types[])`
  - `notify.telegram(message, channel)`
  - `notify.slack(message, channel)`
  - `notify.email(to, subject, body)`
  - `webhook.send(url, payload)`
  - `siem.create_case(title, severity, evidence)`
- **Critérios**:
  - Cada action é plugin Python com schema validado
  - Documentação auto-gerada
- **Skills**: arquitetura plugável, extensibilidade

#### F-IR-03 — Aprovação humana inline `[v1]`
- **O quê**: Step do playbook pode pausar e exigir aprovação
- **Critérios**:
  - Notificação via Telegram com botões inline (Aprovar/Negar)
  - Timeout configurável (se ninguém aprovar em X min, escala ou cancela)
  - Razão obrigatória ao negar
- **Skills**: human-in-the-loop, design de aprovação

#### F-IR-04 — Coleta forense automática `[v1]`
- **O quê**: Snapshot do host no momento do incidente
- **Coleta**:
  - Lista de processos (`ps auxf`)
  - Conexões de rede (`ss -tunap`)
  - Usuários logados (`who`, `last`)
  - Hashes de binários relevantes
  - Memória de processo suspeito (gcore opcional)
  - Logs dos últimos 30 min
- **Critérios**:
  - Empacotado em tar.gz com hash de integridade
  - Upload para storage central (S3/MinIO)
  - Retenção mínima por compliance
- **Skills**: forense digital, chain of custody

#### F-IR-05 — Editor visual de playbook `[v2]`
- **O quê**: Drag-and-drop de steps (estilo n8n simplificado)
- **Skills**: frontend avançado, UX para automação

#### F-IR-06 — Biblioteca de playbooks prontos `[v1]`
- **Cenários iniciais**:
  - Brute force SSH detectado
  - Tentativa de privilege escalation
  - Conexão para C2 conhecido
  - Suspeita de ransomware (alteração massiva de arquivos)
  - Vazamento de credenciais
- **Skills**: conhecimento operacional, threat response

#### F-IR-07 — Métricas de resposta `[v1]`
- **MTTD** (Mean Time To Detect): tempo entre evento e detecção
- **MTTR** (Mean Time To Respond): tempo entre detecção e ação
- **Skills**: KPIs de SOC

---

## Módulo 5 — Compliance LGPD (Funcionalidades)

#### F-LGPD-01 — Cadastro de ativos sensíveis `[v2]`
- **O quê**: Inventário de onde estão os dados pessoais
- **Tipos**:
  - Arquivos/diretórios em hosts
  - Tabelas de banco
  - Endpoints de API
  - Buckets de storage
- **Atributos**:
  - Categoria LGPD (pessoal / sensível / criança e adolescente)
  - Base legal aplicada (consentimento, legítimo interesse, etc.)
  - Finalidade
  - DPO/responsável
  - Período de retenção
- **Skills**: modelagem de domínio LGPD, gestão de privacidade

#### F-LGPD-02 — Auditoria automática via auditd `[v2]`
- **O quê**: Configurar regras auditd para vigiar ativos cadastrados
- **Critérios**:
  - Quando admin cadastra `/srv/dados`, plataforma adiciona watch automaticamente
  - Eventos taggeados como `lgpd_*` no SIEM
  - Cobertura: read, write, attribute change, delete
- **Skills**: integração profunda com Linux audit subsystem

#### F-LGPD-03 — Relatório de operações de tratamento `[v2]`
- **O quê**: Exigência da LGPD (art. 37): manter registro
- **Conteúdo do relatório**:
  - Quais dados são tratados
  - Para quê
  - Por quanto tempo
  - Quem acessa
  - Com quem é compartilhado
- **Saída**: PDF assinável, CSV para integração
- **Skills**: tech writing legal, compliance documentation

#### F-LGPD-04 — RIPD (Relatório de Impacto) `[v2]`
- **O quê**: Wizard que ajuda DPO a montar RIPD
- **Critérios**: Templates pré-prontos para casos comuns
- **Skills**: especialização em privacidade

#### F-LGPD-05 — Gestão de incidentes de privacidade `[v2]`
- **O quê**: Workflow específico para vazamentos
- **Critérios**:
  - Cronograma das obrigações (notificação em prazo razoável à ANPD)
  - Template de comunicação aos titulares
  - Registro probatório
- **Skills**: incident response com viés legal

#### F-LGPD-06 — Atendimento a direitos do titular `[v2]`
- **O quê**: Apoiar respostas a pedidos (acesso, retificação, eliminação, portabilidade)
- **Critérios**:
  - Fluxo de tickets dedicado
  - Busca cross-system para localizar dados do titular
  - Geração de pacote de portabilidade
- **Skills**: data discovery, integração horizontal

#### F-LGPD-07 — Detecção de vazamento `[v2]`
- **Regras Sigma específicas**:
  - SELECT em massa em tabela cadastrada como sensível
  - Cópia de arquivo sensível para `/tmp` ou destino externo
  - Acesso fora de horário comercial
  - Acesso por usuário não autorizado
- **Skills**: especialização em DLP

#### F-LGPD-08 — Dashboard de conformidade `[v2]`
- **Indicadores**:
  - % de ativos com base legal definida
  - % de ativos com retenção configurada
  - Incidentes abertos/fechados
  - Pedidos de titulares respondidos no prazo
- **Skills**: KPIs de privacidade, dashboards executivos

---

## Frontend (Funcionalidades)

### 🎨 Princípios de UX
- **Mobile-friendly** (não mobile-first, mas responsivo)
- **Tema escuro por padrão** (operadores SOC trabalham à noite)
- **Atalhos de teclado** (`Cmd+K` para busca global, navegação por teclado)
- **PT-BR como idioma padrão**, com chave para EN-US

### Funcionalidades

#### F-FE-01 — Dashboard principal `[MVP]`
- **Widgets**:
  - Eventos por minuto (gráfico de área)
  - Top 10 IPs ativos
  - Alertas abertos por severidade
  - Saúde dos agentes (% online)
  - Mapa-múndi com origem de eventos
- **Skills**: data viz, design responsivo

#### F-FE-02 — Lista de hosts `[MVP]`
- **O quê**: Inventário visual dos servidores monitorados
- **Por host**:
  - Status (online/offline)
  - Última comunicação
  - Eventos nas últimas 24h
  - Alertas abertos
  - Ações rápidas (bloquear IP atacante, isolar host)

#### F-FE-03 — Tela de busca de eventos `[MVP]`
- **Componentes**:
  - Barra de query
  - Filtros laterais
  - Tabela paginada com infinite scroll
  - Detalhe expandível por evento
- **Skills**: UX de ferramenta de power user

#### F-FE-04 — Tela de configuração de regras `[MVP]`
- **Skills**: editor estruturado, validação em tempo real

#### F-FE-05 — Wizard de onboarding `[v1]`
- **O quê**: Primeiros 10 minutos de quem instala
- **Passos**:
  1. Criar admin
  2. Adicionar primeiro host (gera comando `curl ... | sudo bash`)
  3. Aplicar template de firewall
  4. Configurar canal de notificação
  5. Pronto!
- **Skills**: design de onboarding, redução de fricção

#### F-FE-06 — Tema escuro/claro `[MVP]`
- **Skills**: design system, theming

#### F-FE-07 — Internacionalização `[v1]`
- **Skills**: i18n, design para múltiplos idiomas

---

## DevOps & Deploy

### F-OPS-01 — Docker Compose para desenvolvimento `[MVP]`
- **O quê**: `docker compose up` sobe ambiente completo
- **Serviços**: API, frontend, PostgreSQL, Redis, Loki, agente de exemplo
- **Critérios**: Pronto em < 2 minutos no primeiro `up`
- **Skills**: Docker, orquestração local

### F-OPS-02 — Imagens Docker oficiais `[MVP]`
- **O quê**: Imagens publicadas no GitHub Container Registry
- **Critérios**:
  - Multi-stage builds (imagem final < 100MB)
  - Imagens minimal (distroless ou alpine)
  - Multi-arch (amd64 e arm64)
  - SBOM e assinatura (cosign)
- **Skills**: Docker avançado, supply chain security

### F-OPS-03 — CI/CD com GitHub Actions `[MVP]`
- **Pipelines**:
  - Lint (ruff, eslint, hadolint)
  - Testes unitários e de integração
  - Build e push de imagens
  - Geração de release notes
  - Deploy automatizado para ambiente de demo
- **Skills**: CI/CD, GitOps

### F-OPS-04 — Helm chart para Kubernetes `[v2]`
- **O quê**: Deploy em K8s com 1 comando
- **Recursos**:
  - Values.yaml bem documentado
  - Suporte a HPA (autoscaling)
  - PodDisruptionBudgets
  - NetworkPolicies
- **Skills**: Kubernetes, Helm

### F-OPS-05 — Terraform module `[v2]`
- **O quê**: Provisiona infra completa em provedores cloud
- **Suporte inicial**: DigitalOcean, Hetzner (focando custo-benefício)
- **Skills**: IaC, multi-cloud

### F-OPS-06 — Backup e disaster recovery `[v1]`
- **O quê**: Estratégia de backup do estado da plataforma
- **Critérios**:
  - Dump diário do PostgreSQL para S3/MinIO
  - Snapshot do Loki
  - Documentação de recovery testada
- **Skills**: BCP/DR

### F-OPS-07 — Documentação de instalação `[MVP]`
- **Cenários documentados**:
  - VPS standalone (Ubuntu 22.04)
  - Docker Compose em servidor próprio
  - Kubernetes via Helm
- **Skills**: technical writing

### F-OPS-08 — Demo pública online `[v1]`
- **O quê**: Instância de exemplo rodando em VPS, acesso read-only com credenciais públicas
- **Skills**: hosting, segurança de demo

---

## Mapa de habilidades demonstradas

> Esta seção é o "cardápio" para o LinkedIn — o que cada parte do projeto prova que você sabe fazer.

### 🔧 Backend
- **Python avançado**: FastAPI, async/await, type hints, Pydantic
- **(Opcional) Go**: para o agente, demonstra polivalência
- **Mensageria**: Redis Streams, RabbitMQ
- **Bancos**: PostgreSQL (modelagem, índices, queries complexas)
- **Caching estratégico**: Redis
- **API design**: REST, OpenAPI, versionamento
- **Background jobs**: Celery

### 🎨 Frontend
- **React + TypeScript**: hooks, context, suspense
- **Tailwind + shadcn/ui**: design system moderno
- **Data viz**: Recharts ou ECharts
- **State management**: TanStack Query (server state)
- **Acessibilidade**: ARIA, navegação por teclado

### 🛡️ Segurança
- **Criptografia aplicada**: Argon2, JWT, mTLS
- **PKI**: gestão de certificados
- **Threat detection**: regras Sigma, IOC matching
- **DFIR**: forense digital, chain of custody
- **Hardening Linux**: SELinux, auditd, iptables/nftables
- **LGPD**: implementação prática de privacy by design

### 🤖 Machine Learning (sem dependência de APIs externas)
- **scikit-learn**: Isolation Forest, DBSCAN
- **Feature engineering**: extração de sinais de logs
- **Time series**: detecção de baseline e anomalias
- **Explicabilidade**: SHAP

### 🚀 DevOps / SRE
- **Containers**: Docker multi-stage, supply chain
- **Orquestração**: Kubernetes, Helm
- **IaC**: Terraform
- **CI/CD**: GitHub Actions
- **Observabilidade**: Prometheus, Grafana, OpenTelemetry
- **GitOps**: ambientes versionados

### 🏗️ Arquitetura
- **Sistemas distribuídos**: comunicação assíncrona, idempotência
- **Event-driven**: produção e consumo de eventos
- **Plugin systems**: arquitetura extensível
- **Multi-tenant**: isolamento entre clientes
- **Design for failure**: circuit breakers, retries, fallbacks

### 📝 Soft skills demonstradas
- **Documentação**: README, docs técnicos, comentários inteligentes
- **Comunicação**: explicar conceitos complexos para públicos diferentes
- **Product thinking**: priorização (MVP vs nice-to-have)
- **Empatia com o usuário**: UX defensiva, mensagens de erro úteis

---

## Roadmap por fases

### 🟢 Fase 1 — MVP (Mês 1 e 2)

**Objetivo**: ter um ciclo completo funcionando: log gerado → coletado → analisado → alerta → ação.

- F-AUTH-01, 03, 04 (auth básica + RBAC + audit)
- F-API-01, 02 (API documentada + rate limit)
- F-OBS-01, 02 (métricas + health)
- F-SIEM-01, 02, 04, 05, 06, 08, 09, 10, 14, 15, 16 (pipeline completo + Sigma)
- F-FW-01, 02, 03, 04, 05, 06 (firewall completo + integração com SIEM)
- F-FE-01, 02, 03, 04, 06 (frontend essencial)
- F-OPS-01, 02, 03, 07 (Docker + CI + docs)

**Marco**: deploy em VPS, instalação documentada, vídeo demo de 3 min.

### 🔵 Fase 2 — v1.0 (Mês 3 e 4)

**Objetivo**: features de "operação real" — SELinux, resposta automatizada, ML.

- F-AUTH-02 (2FA)
- F-API-03, 04 (webhooks + tokens)
- F-OBS-03 (tracing)
- F-SIEM-03, 07, 11, 12, 13, 17 (enriquecimento + ML + correlação + threat intel)
- F-FW-07, 08, 09 (geo-blocking + análise estática + simulação)
- F-SE-01 a F-SE-06 (módulo SELinux completo)
- F-IR-01 a F-IR-04, F-IR-06, F-IR-07 (resposta a incidentes)
- F-FE-05, F-FE-07 (onboarding + i18n)
- F-OPS-06, F-OPS-08 (backup + demo pública)

**Marco**: post no Dev.to / LinkedIn / Medium contando arquitetura.

### 🟣 Fase 3 — v2.0 (Mês 5 e 6)

**Objetivo**: enterprise-readiness e o módulo de privacidade.

- F-AUTH-05 (SSO)
- F-LGPD-01 a F-LGPD-08 (módulo LGPD completo)
- F-SE-07 (troubleshooting)
- F-IR-05 (editor visual)
- F-OPS-04, F-OPS-05 (Helm + Terraform)
- Multi-tenant

**Marco**: case completo no LinkedIn, talk em meetup local sobre o projeto.

### 🟡 Fase 4 — Contínuo

- Integrações (Wazuh, Suricata, MISP)
- Plugins da comunidade
- Documentação avançada
- Otimizações e polimento

---

## Como esse documento ajuda no LinkedIn

Cada vez que você publicar um post sobre o projeto, pode referenciar funcionalidades específicas:

- *"Implementei autenticação mTLS entre os agentes e o servidor — aqui o motivo de não usar API key (link)"* → demonstra **F-SIEM-05**
- *"Criei um pipeline de detecção de anomalias com Isolation Forest e explicabilidade via SHAP"* → demonstra **F-SIEM-11**
- *"Como evitar quebrar produção ao mexer no firewall: implementei rollback transacional"* → demonstra **F-FW-05**
- *"Por que a LGPD é mais sobre engenharia que sobre jurídico"* → demonstra **Módulo 5**

Esse documento é seu **arsenal de conteúdo**: cada funcionalidade vira um post potencial.

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
