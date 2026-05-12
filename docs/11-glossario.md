# SentinelBR — Glossário de Termos

> Glossário com todos os termos técnicos usados no projeto, em ordem alfabética. Consulta rápida quando aparecer uma sigla ou conceito desconhecido. Pensado para servir tanto a iniciantes quanto a desenvolvedores experientes que precisam relembrar significados específicos do domínio.

---

## 📋 Como usar

- Consulta rápida: Cmd+F (ou Ctrl+F) para buscar o termo
- Termos relacionados estão marcados com → (seta)
- Exemplos práticos quando o termo é abstrato
- Cada termo tem nível: 🟢 básico, 🟡 intermediário, 🔴 avançado

---

## A

### ACID 🟡
Sigla para **A**tomicity, **C**onsistency, **I**solation, **D**urability — propriedades garantidas por bancos de dados relacionais (como → PostgreSQL). Significam que transações ou completam totalmente ou não completam (atomicidade), mantêm regras (consistência), não interferem entre si (isolamento), e persistem após confirmação (durabilidade).

### ADR (Architecture Decision Record) 🟡
Documento curto e estruturado que registra uma decisão arquitetural importante: contexto, alternativas consideradas, decisão tomada e consequências. Útil como memória institucional. Ver doc 08.

### Agente 🟢
No SentinelBR, é o programa instalado em cada servidor monitorado. Coleta logs, executa comandos remotos do servidor central, mantém comunicação contínua. Escrito em → Go.

### AGPL-3.0 🟡
**Affero General Public License v3** — licença open-source com → copyleft forte. Quem oferece software com AGPL como serviço web (SaaS) também precisa abrir código das modificações. Protege contra "AWS effect" (provedores fechando forks de projetos open-source).

### Alembic 🟡
Ferramenta de → migrations para → SQLAlchemy/Python. Permite versionar mudanças no schema do banco (igual ao git para código).

### Allowlist 🟢
Lista de IPs/redes que **nunca** devem ser bloqueados, mesmo que regras de segurança disparem. Oposto de → blacklist. Usado para garantir que IPs de gerenciamento ou parceiros confiáveis não sejam acidentalmente bloqueados.

### ANPD 🟢
**Autoridade Nacional de Proteção de Dados** — órgão brasileiro que fiscaliza a → LGPD. Aplica multas em caso de violações.

### Argon2id 🔴
Algoritmo de hash de senhas, vencedor da Password Hashing Competition (2015). Usado no SentinelBR em vez de bcrypt por ser mais resistente a ataques GPU/ASIC. "id" é a variante recomendada (combina Argon2i + Argon2d).

### ASGI 🟡
**Async Server Gateway Interface** — padrão para servidores web Python assíncronos. Sucessor do WSGI. → FastAPI usa ASGI. Servidor recomendado: → Uvicorn.

### audit2allow 🔴
Ferramenta do → SELinux que analisa → AVC denials e gera automaticamente uma → policy que permitiria aquela ação. Usado quando você precisa permitir algo bloqueado.

### auditd 🟡
Subsistema de auditoria do kernel Linux. Registra chamadas de sistema (acesso a arquivos, execução de binários, etc.) em `/var/log/audit/audit.log`. Fonte primária de eventos de segurança coletados pelo → agente.

### AVC denial 🔴
**Access Vector Cache denial** — registro do → SELinux indicando que uma ação foi bloqueada. Aparece em formato cifrado em `/var/log/audit/audit.log`. O módulo SELinux do SentinelBR traduz para linguagem humana.

---

## B

### Backoff exponencial 🟡
Estratégia de retry: ao falhar, espera tempos crescentes antes de tentar novamente (1s, 2s, 4s, 8s, 16s...). Evita martelar serviço já em problema.

### Backpressure 🔴
Em sistemas assíncronos, mecanismo que sinaliza ao produtor "estou lento, me mande menos coisas" para evitar acúmulo. No SentinelBR, → buffer do agente fica cheio quando servidor central está sobrecarregado, e o agente passa a descartar eventos antigos.

### BCP (Business Continuity Planning) 🟡
Plano para manter operações funcionando durante incidentes. Inclui → DR (Disaster Recovery).

### Blacklist 🟢
Lista de IPs/redes bloqueados. No SentinelBR, há blacklist estática (manual) e dinâmica (gerada por → SIEM detectando ataques).

### Boolean (SELinux) 🔴
Configurações on/off no → SELinux que ativam/desativam comportamentos pré-definidos. Exemplo: `httpd_can_network_connect` permite que Apache faça conexões de saída.

### Brute force 🟢
Ataque que tenta milhares de combinações de senhas até acertar. Detecção comum: muitas tentativas falhas em curto período do mesmo IP.

### Bucket (storage) 🟢
"Pasta" no contexto de → object storage como → S3 ou → MinIO. Cada bucket tem políticas próprias de acesso, retenção e criptografia.

### Buffer 🟢
Área de memória/disco onde dados ficam temporariamente. No agente, → SQLite local serve como buffer caso o servidor central esteja inacessível.

---

## C

### C4 model 🟡
Técnica de documentar arquitetura em 4 níveis: Contexto (sistema + atores externos), Container (componentes deployáveis), Componente (módulos internos) e Código (classes). Criada por Simon Brown.

### CA (Certificate Authority) 🔴
Entidade que assina certificados digitais. No SentinelBR, geramos uma CA própria (não usamos Let's Encrypt) para certificar agentes via → mTLS.

### Caddy 🟢
Servidor web moderno alternativo ao → nginx. Pega certificados do Let's Encrypt automaticamente, configuração simples. Usado como → reverse proxy padrão no SentinelBR.

### Cardinalidade 🟡
Número de valores únicos possíveis. Em → Loki, labels com alta cardinalidade (como IP de origem, com milhões de valores) prejudicam performance. Por isso labels devem ser limitados (host, source, severity).

### Celery 🟡
Framework Python para tarefas assíncronas distribuídas. Permite jobs em background (geração de PDF, envio de email, ML). Usa → Redis como broker no SentinelBR.

### Cert-manager 🔴
Ferramenta para → Kubernetes que automatiza emissão e renovação de certificados TLS (Let's Encrypt, vault, etc.).

### CIDR 🟡
**Classless Inter-Domain Routing** — notação para faixas de IP. Ex: `10.0.0.0/8` = todos os IPs começando com 10.

### Circuit breaker 🔴
Padrão de design: se chamadas para serviço externo falham repetidamente, "abre o circuito" e retorna fallback por X segundos sem tentar novamente. Evita cascade failures.

### CISA KEV 🟡
**Catálogo Known Exploited Vulnerabilities** mantido pela CISA (agência americana). Lista CVEs sendo ativamente explorados. Útil para priorização de patches.

### Citext 🟡
Tipo de coluna do → PostgreSQL: string com comparação case-insensitive automática. Usado para emails (admin@x.com == ADMIN@X.com).

### CodeQL 🔴
Ferramenta de análise estática de código da GitHub. Detecta vulnerabilidades como SQL injection, XSS, etc. Integrada via GitHub Actions.

### Compliance 🟢
Conformidade — provar que a empresa segue as regras (leis, normas, padrões). LGPD compliance significa "estamos cumprindo a LGPD".

### Connection pooling 🟡
Técnica de reutilizar conexões com banco de dados em vez de abrir/fechar a cada query. → PgBouncer faz isso para PostgreSQL.

### Consumer group 🔴
Em → Redis Streams ou Kafka, grupo de consumidores que dividem o trabalho de processar mensagens (cada mensagem vai para um único consumer do grupo).

### Copyleft 🟡
Princípio de licenças open-source que exige que derivados também sejam open-source. → AGPL é copyleft forte (cobre uso em rede).

### Correlation 🟡
No contexto de → SIEM, processo de identificar relação entre múltiplos eventos para detectar ameaças complexas. Ex: "login bem-sucedido + criação de usuário privilegiado em 5min" = possível invasão.

### CQRS 🔴
**Command Query Responsibility Segregation** — separar operações que **mudam estado** (commands) das que **só leem** (queries). Permite otimizar cada uma independentemente. Usado de forma "leve" no SentinelBR.

### CSR (Certificate Signing Request) 🔴
Pedido de assinatura de certificado. Cliente gera CSR, envia para CA, recebe certificado assinado. Padrão do → mTLS.

### CVE 🟡
**Common Vulnerabilities and Exposures** — identificador único de vulnerabilidades de software. Ex: CVE-2024-12345.

---

## D

### DBSCAN 🔴
Algoritmo de clustering em → ML. Agrupa pontos densos e identifica outliers. Usado para detecção de anomalias.

### DSL 🟡
**Domain-Specific Language** — linguagem feita para um domínio específico. → Sigma rules e nossos → playbooks YAML são DSLs.

### Dependabot 🟢
Ferramenta da GitHub que abre pull requests automáticos para atualizar dependências com vulnerabilidades.

### DI (Dependency Injection) 🟡
Padrão onde dependências são "injetadas" em vez de criadas internamente. Facilita testes (mockar dependências) e configuração. → FastAPI tem DI nativo via `Depends()`.

### Disaster Recovery (DR) 🟡
Processo de restaurar serviços após falha catastrófica (perda de servidor, ataque ransomware, etc.).

### Docker 🟢
Plataforma para containers — empacota aplicações com suas dependências em "imagens" portáteis.

### Docker Compose 🟢
Ferramenta para orquestrar múltiplos containers Docker via arquivo YAML. Usado para → deploy MVP do SentinelBR.

### DPO 🟢
**Data Protection Officer** ou **Encarregado de Proteção de Dados** — pessoa responsável pela LGPD na empresa. Obrigatório por lei em algumas situações.

---

## E

### ECS (Elastic Common Schema) 🟡
Padrão de campos para eventos de segurança e logs criado pela Elastic. Define nomes consistentes (ex: `source.ip`, `event.action`). Adotado pela indústria mesmo fora do ecossistema Elastic.

### Endpoint 🟢
URL específica de uma API. Ex: `GET /api/v1/alerts` é um endpoint.

### Enrichment 🟡
Processo de adicionar contexto a um evento. Ex: pegar IP cru e adicionar GeoIP, reputação, reverse DNS.

### Enrollment 🟡
Processo de primeira autenticação de um → agente com o servidor central. Token único é trocado por certificado mTLS.

### EPSS 🔴
**Exploit Prediction Scoring System** — score que estima a probabilidade de uma → CVE ser explorada. Útil para priorização.

---

## F

### FastAPI 🟡
Framework web Python moderno e rápido. Type hints nativos, validação via → Pydantic, OpenAPI auto-gerado. Escolhido para a API do SentinelBR.

### Feature flag 🟡
Mecanismo para ativar/desativar funcionalidades sem deploy. Útil para roll-out gradual de features novas.

### Fingerprint 🟡
Hash que identifica unicamente algo. No SentinelBR, alertas têm fingerprint para → deduplicação (mesmo ataque detectado 100x = 1 alerta com count=100).

### Firewalld 🟢
Gerenciador de firewall padrão em RHEL/Rocky/Fedora. Abstração sobre → iptables ou → nftables.

### Forense (digital) 🟡
Coleta de evidências para entender como um ataque aconteceu. Inclui → snapshot de processos, conexões, arquivos modificados, dump de memória.

---

## G

### GeoIP 🟢
Tradução de IP para localização geográfica (país, cidade, ISP). Base usada no SentinelBR: → MaxMind GeoLite2.

### gRPC 🔴
Framework de RPC moderno baseado em → Protobuf e HTTP/2. Mais eficiente que REST para comunicação alta-frequência. Usado entre agente e servidor central.

### GIN index 🔴
Tipo de índice no PostgreSQL para busca em arrays e JSONB. Usado para queries em `tags[]` e `metadata jsonb`.

### Goroutine 🟡
Função em → Go que roda concorrentemente, gerenciada pelo runtime. Análoga a "thread leve". Usadas para coletas paralelas no agente.

---

## H

### HMAC 🔴
**Hash-based Message Authentication Code** — assinatura criptográfica para verificar autenticidade e integridade. Usado em webhooks (servidor assina, cliente verifica).

### HPA (Horizontal Pod Autoscaler) 🔴
Recurso do → Kubernetes que escala número de pods baseado em métricas (CPU, custom). Permite escalar workers automaticamente.

### Helm 🟡
Gerenciador de pacotes para → Kubernetes. SentinelBR oferecerá Helm chart oficial.

### Honeypot 🟡
Sistema deliberadamente vulnerável para atrair e estudar atacantes. Mencionado em projetos relacionados.

---

## I

### IaC (Infrastructure as Code) 🟡
Infraestrutura definida em código versionado (em vez de cliques no console). → Terraform e → Helm são IaC.

### Idempotência 🔴
Operação que produz mesmo resultado se executada uma ou múltiplas vezes. Crítico em sistemas distribuídos (retries não devem causar efeitos duplicados).

### Inode 🔴
Identificador interno de arquivo no Linux. Quando logrotate move log antigo, o novo arquivo tem inode diferente. → Agente usa isso para detectar rotação.

### IOC (Indicator of Compromise) 🟡
"Pegada" deixada por atacante: IPs maliciosos, hashes de malware, domínios de C2. Feeds de → threat intelligence fornecem listas de IOCs.

### Iptables 🟢
Firmware tradicional de firewall do Linux (em substituição por → nftables). Suportado no SentinelBR.

### ipset 🟡
Estrutura otimizada para o iptables/nftables armazenarem grandes conjuntos de IPs/redes com lookup O(1). Usado para → blacklist dinâmica.

### Isolation Forest 🔴
Algoritmo de → ML para detecção de outliers. Funciona "isolando" pontos: outliers são isolados em poucos passos, normais em muitos. Usado no módulo de detecção de anomalias.

---

## J

### JSONB 🟡
Tipo do PostgreSQL para JSON binário (otimizado e indexável). Usado para campos flexíveis (metadata, contexto de evento).

### JWT (JSON Web Token) 🟡
Token codificado em JSON usado para autenticação stateless. Carrega claims (user_id, roles, expires_at). Verificável sem consultar banco. Usado para auth de usuários no SentinelBR.

---

## K

### KEDA 🔴
**Kubernetes Event-driven Autoscaling** — escala pods baseado em eventos externos (profundidade de fila, mensagens em tópico, etc.). Usado para escalar workers Celery por tamanho da fila.

### Keycloak 🟡
Plataforma open-source de identidade. Suporte a → SSO via OIDC, SAML, etc. Mencionado como provider para o módulo SSO.

### Kubernetes (K8s) 🟡
Plataforma de orquestração de containers. Mais complexo que → Docker Compose, mas escala muito melhor. Suportado via → Helm chart.

---

## L

### Let's Encrypt 🟢
Autoridade certificadora gratuita e automatizada. Provê certificados HTTPS sem custo. Integrado via → Caddy ou → Cert-manager.

### LGPD 🟢
**Lei Geral de Proteção de Dados** — Lei 13.709/2018 brasileira. Regula tratamento de dados pessoais. Multas até 2% do faturamento. Equivalente brasileiro do GDPR europeu.

### Liveness probe 🔴
Em → Kubernetes, endpoint que K8s consulta para saber se container está vivo. Se falha, K8s reinicia. No SentinelBR: `/health/live`.

### Loki 🟡
Sistema de armazenamento de logs do Grafana. Otimizado para custo: indexa apenas → labels, não conteúdo. ~10x mais barato que → Elasticsearch para nosso caso de uso.

### LogQL 🟡
Linguagem de query do → Loki. Sintaxe similar a → PromQL. Ex: `{host="web-01", severity="high"}`.

---

## M

### Materialized view 🔴
View do banco com resultado pré-computado, refrescada periodicamente. Usado para dashboards (queries lentas viram lookups rápidos).

### MaxMind 🟡
Empresa que mantém base GeoIP. Versão gratuita: GeoLite2 (precisão menor que paga, mas suficiente).

### MFA 🟢
**Multi-Factor Authentication** — exigir mais de um fator de autenticação (senha + código TOTP, por exemplo). → 2FA é caso particular.

### Migration 🟡
Mudança versionada no schema do banco. → Alembic gerencia migrations no SentinelBR.

### MinIO 🟡
Object storage open-source compatível com → S3. Permite usar mesma API da AWS S3 em servidor próprio.

### MITRE ATT&CK 🟡
Framework que cataloga táticas, técnicas e procedimentos (TTPs) de atacantes. Cada técnica tem ID (ex: T1110.001 = Brute Force - Password Guessing). → Sigma rules referenciam ATT&CK.

### Monorepo 🟡
Repositório único com múltiplos componentes. Oposto: multi-repo. SentinelBR é monorepo.

### MTTD 🟡
**Mean Time To Detect** — tempo médio entre evento e detecção. Métrica chave de SOC.

### MTTR 🟡
**Mean Time To Respond** — tempo médio entre detecção e ação. Métrica chave de SOC.

### mTLS 🔴
**Mutual TLS** — TLS onde **ambos** lados (cliente e servidor) se autenticam com certificado. Usado entre → agente e servidor central.

---

## N

### NAT 🟡
**Network Address Translation** — tradução de IPs (privados ↔ públicos). Comum em redes corporativas.

### nftables 🟡
Sucessor moderno do → iptables no Linux. Sintaxe mais limpa, melhor performance. SentinelBR detecta e usa o que estiver disponível.

### nginx 🟢
Servidor web e reverse proxy popular. Alternativa ao → Caddy.

---

## O

### Object storage 🟡
Tipo de storage para arquivos via API HTTP (em vez de filesystem). → S3 e → MinIO são exemplos.

### OIDC 🔴
**OpenID Connect** — protocolo de autenticação sobre OAuth2. Padrão para → SSO moderno.

### OpenAPI 🟡
Especificação de API REST (antiga "Swagger"). → FastAPI gera automaticamente. Permite documentação interativa.

### OpenTelemetry 🔴
Padrão open-source para observabilidade (métricas, logs, traces). Permite trocar backend sem mudar instrumentação.

---

## P

### PAT 🟡
**Personal Access Token** — token longo para integração programática. No SentinelBR: prefixo `sbr_live_...`, com escopos limitados.

### Particionamento (banco) 🔴
Dividir tabela grande em partes menores por critério (ex: data). Queries em partição específica são rápidas; DROP de partição antiga é instantâneo. → pg_partman gerencia.

### Patroni 🔴
Ferramenta para alta disponibilidade do → PostgreSQL. Faz failover automático entre réplicas.

### pgaudit 🔴
Extensão do PostgreSQL para auditoria detalhada (quem leu/modificou o quê). Usado para → LGPD compliance.

### PgBouncer 🔴
→ Connection pooler para PostgreSQL. Permite milhares de clientes compartilharem poucas conexões reais ao DB.

### pgcrypto 🔴
Extensão do PostgreSQL para criptografia em coluna. Usado para criptografar CPFs/CNPJs e MFA secrets no SentinelBR.

### PII 🟡
**Personally Identifiable Information** — dados pessoais (nome, CPF, email). Categoria principal sob → LGPD.

### PITR 🔴
**Point-in-Time Recovery** — restaurar banco para qualquer momento específico (não só backup full). Requer → WAL archiving.

### Playbook 🟢
Receita pronta de "se acontecer X, faça Y, Z e W". No SentinelBR, escrito em YAML, executado pela engine de resposta.

### PKI 🔴
**Public Key Infrastructure** — infraestrutura de gestão de certificados (CA, emissão, revogação).

### Postgres / PostgreSQL 🟢
Banco de dados relacional open-source. Versão alvo: 16. Coração do estado da plataforma.

### Pre-commit 🟡
Hooks executados antes de cada commit (lint, format, etc.). Garantem qualidade básica.

### Promtail 🟡
Agente coletor de logs do ecossistema → Loki. Não usado no SentinelBR (temos nosso próprio agente), mas mencionado como alternativa.

### Protobuf 🔴
**Protocol Buffers** — formato binário compacto da Google para serialização. Usado por → gRPC. Schema versionado e cross-language.

### Pydantic 🟡
Biblioteca Python para validação de dados via type hints. v2 tem core em Rust (rápido). Usado em → FastAPI e Settings.

---

## Q

### Query (banco) 🟢
Consulta ao banco de dados. SQL: `SELECT * FROM users WHERE ...`.

### Queue (fila) 🟢
Estrutura FIFO usada para processamento assíncrono. → Celery + → Redis no SentinelBR.

---

## R

### Rate limiting 🟡
Limitar número de requisições por período (ex: 60/min por usuário). Defesa contra abuso. Implementado via → Redis.

### RBAC 🟡
**Role-Based Access Control** — controle de acesso baseado em papéis (roles). Usuários têm roles, roles têm permissions. Usado no SentinelBR.

### Readiness probe 🔴
Em → Kubernetes, endpoint que K8s consulta para saber se container está pronto a receber tráfego. No SentinelBR: `/health/ready` (verifica DB, Redis, etc.).

### Redis 🟡
Banco key-value em memória. Multi-purpose: cache, filas, pub/sub, sliding windows. Versão alvo: 7.2+.

### Repository pattern 🔴
Padrão de design: classe que encapsula acesso a dados. Services não escrevem SQL diretamente. Facilita testes e troca de DB.

### REST 🟡
**Representational State Transfer** — estilo arquitetural para APIs. Verbos HTTP (GET, POST, etc.) sobre recursos identificados por URL.

### RIPD 🟡
**Relatório de Impacto à Proteção de Dados** — documento exigido pela LGPD em alguns casos (tratamentos de alto risco). SentinelBR gera template.

### RPO 🔴
**Recovery Point Objective** — quanto de dados podemos perder em caso de desastre (medido em tempo). Ex: RPO de 1min = backup atualizado a cada minuto.

### RTO 🔴
**Recovery Time Objective** — quanto tempo aceitamos ficar fora do ar. Ex: RTO de 1h = volta a operar em até 1h após falha.

### Ruff 🟡
Linter + formatter Python escrito em Rust. ~100x mais rápido que flake8/black juntos.

---

## S

### S3 🟡
**Simple Storage Service** da AWS. Padrão de fato para → object storage. → MinIO é compatível com a API S3.

### Schema (banco) 🟡
Estrutura do banco: tabelas, colunas, tipos, relações. PostgreSQL também usa "schema" como namespace (`auth.users` vs `inventory.hosts`).

### SBOM 🔴
**Software Bill of Materials** — inventário de todas as dependências de um software. Importante para supply chain security.

### Secret 🟡
Credencial sensível (senha, API key, certificado). Não vai em código — vai em variáveis de ambiente, vault ou Kubernetes Secrets.

### SELinux 🟡
**Security-Enhanced Linux** — sistema de Mandatory Access Control. Restringe o que cada processo pode fazer dentro do servidor.

### semanage 🔴
Comando para gerenciar configuração do → SELinux (booleans, file contexts, ports, policies).

### Sentry 🟡
Plataforma de error tracking. Captura exceções em produção com contexto rico. Não obrigatório no SentinelBR mas recomendado.

### Serverless 🟡
Modelo onde você não gerencia servidores (AWS Lambda, Cloud Run). SentinelBR não usa por questões de custo + necessidade de stateful.

### Sigma 🟡
Padrão YAML para regras de detecção em SIEMs. Independente de vendor. → pysigma converte para → LogQL/etc.

### SIEM 🟢
**Security Information and Event Management** — sistema que coleta, correlaciona e analisa eventos de segurança. Módulo central do SentinelBR.

### Sliding window 🔴
Estrutura de dados que mantém eventos dos últimos N segundos/minutos. Usado para correlação ("5 falhas em 60s"). Implementado via → Redis sorted sets.

### SOAR 🔴
**Security Orchestration, Automation and Response** — categoria de produtos que automatizam resposta a incidentes. Módulo de Resposta do SentinelBR é SOAR simplificado.

### SOC 🟡
**Security Operations Center** — equipe que monitora segurança 24/7. SentinelBR é desenhado para ser usado em SOCs pequenos/médios.

### Soft delete 🟡
Marcar registro como deletado (`deleted_at`) sem realmente apagar. Importante para auditoria → LGPD.

### SQLAlchemy 🟡
ORM Python (Object-Relational Mapper). Versão 2.0+ tem suporte async excelente.

### SQLite 🟢
Banco embedded (single-file). Usado no → agente para → buffer offline.

### SRE 🟡
**Site Reliability Engineering** — disciplina que aplica engenharia de software à operação. Cuida de SLOs, observabilidade, automação.

### SSE 🟡
**Server-Side Encryption** — criptografia em repouso gerenciada pelo storage (S3, MinIO).

### SSO 🟡
**Single Sign-On** — login único que dá acesso a múltiplas aplicações. Implementado via → OIDC no SentinelBR.

### Streaming replication 🔴
PostgreSQL: réplica recebe alterações em tempo quase real do primary. Permite read replicas e failover.

### SVG 🟢
**Scalable Vector Graphics** — formato de imagem vetorial. Usado para ícones que escalam bem.

---

## T

### Tailwind CSS 🟡
Framework CSS utility-first. Em vez de classes semânticas (`btn-primary`), usa utilitárias (`bg-blue-500 text-white p-4`).

### TanStack Query 🟡
Biblioteca React para gerenciar server state (cache, refetch, optimistic updates). Antes era "React Query".

### Telegram Bot 🟢
Bot do Telegram para enviar/receber mensagens via API. Usado para → notificações e aprovações inline de playbooks.

### Temporal 🔴
Plataforma para orchestration de workflows complexos com state durável. Não usado no SentinelBR (Celery é suficiente).

### Terraform 🟡
Ferramenta → IaC para provisionar infraestrutura cloud. SentinelBR oferecerá modules para Hetzner e DigitalOcean.

### Threat intelligence (TI) 🟡
Informação sobre ameaças: IPs maliciosos, domínios C2, hashes de malware. Feeds: AbuseIPDB, OTX, Feodo Tracker.

### TLS 🟢
**Transport Layer Security** — protocolo que cifra comunicação na rede. Sucessor do SSL.

### TOTP 🟡
**Time-based One-Time Password** — código de 6 dígitos que muda a cada 30s. Usado por Google Authenticator, Authy. Padrão para → 2FA.

### TTL 🟡
**Time To Live** — tempo até expiração. Usado em cache, sessões, bloqueios temporários.

### Type hints 🟡
Anotações de tipo em Python (`def foo(x: int) -> str: ...`). Melhoram tooling, documentação. → Pydantic e → FastAPI usam intensivamente.

---

## U

### UFW 🟢
**Uncomplicated Firewall** — frontend simples para iptables. Comum em Ubuntu.

### UUID 🟡
**Universally Unique Identifier** — identificador de 128 bits. Padrão `550e8400-e29b-41d4-a716-446655440000`. Usado como ID em quase todas as tabelas do SentinelBR.

### Uvicorn 🟡
Servidor → ASGI rápido. Em produção, gerenciado por Gunicorn.

---

## V

### Vite 🟡
Build tool moderno para frontend. Dev server quase instantâneo, build production otimizado. Substitui Webpack.

### VPN 🟡
**Virtual Private Network** — rede privada sobre rede pública. Permite agentes em hosts externos acessarem servidor central interno.

---

## W

### WAL 🔴
**Write-Ahead Log** — log de transações do PostgreSQL antes de aplicar ao banco. Permite recuperação após crash e → PITR.

### WAL archiving 🔴
Arquivar segmentos de WAL para storage externo. Permite restore para qualquer ponto entre backups.

### WCAG 🟡
**Web Content Accessibility Guidelines** — diretrizes de acessibilidade web. Níveis A, AA, AAA. SentinelBR almeja AA.

### Webhook 🟡
HTTP callback: serviço A faz POST para URL de B quando evento acontece. Permite integração entre sistemas.

### WebSocket 🟡
Protocolo de comunicação bidirecional persistente sobre HTTP. Usado para realtime no frontend (alertas push).

### WireGuard 🟡
VPN moderna, simples e rápida. Mencionada como opção para conectar agentes externos.

---

## Y

### YAML 🟢
**YAML Ain't Markup Language** — formato de serialização legível por humanos. Usado em configurações, → Sigma rules, → playbooks.

---

## Z

### Zero-trust 🔴
Modelo de segurança: nunca confie, sempre verifique. Cada requisição autenticada e autorizada, mesmo dentro da rede. → mTLS implementa parcialmente isso.

### Zustand 🟡
Biblioteca de state management para React. Mais simples que Redux. Usada para client state (auth, preferências UI).

---

## Como contribuir com o glossário

Quando aparecer termo não listado:

1. Adicione com nível (🟢🟡🔴)
2. Use linguagem simples, **explicar como se fosse para alguém novo**
3. Marque relações com → para outros termos
4. Inclua exemplo prático quando o termo for abstrato
5. Mantenha ordem alfabética dentro de cada letra

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
