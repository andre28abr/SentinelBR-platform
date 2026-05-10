# SentinelBR — Threat Knowledge Base e Prevenção

> Especificação da base de conhecimento sobre técnicas de ataque, prevenção e remediação. Cobre catálogo MITRE ATT&CK navegável em PT-BR, recomendações de hardening por host, biblioteca de threat hunting queries, IOC matching retroativo, simulação de ataques (purple team) e modo aprendizado para usuários novatos.

---

## 📋 Sumário

1. [Filosofia: educar para defender](#filosofia-educar-para-defender)
2. [Catálogo MITRE ATT&CK em PT-BR](#catálogo-mitre-attck-em-pt-br)
3. [Recomendações de hardening por host](#recomendações-de-hardening-por-host)
4. [Threat hunting queries](#threat-hunting-queries)
5. [IOC matching retroativo](#ioc-matching-retroativo)
6. [Knowledge base de remediação](#knowledge-base-de-remediação)
7. [Simulação de ataques (purple team)](#simulação-de-ataques-purple-team)
8. [Modo aprendizado](#modo-aprendizado)
9. [Schema de dados](#schema-de-dados)
10. [Endpoints da API](#endpoints-da-api)

---

## Filosofia: educar para defender

### O problema do mercado

A maioria das ferramentas de segurança trata o usuário como **observador passivo de alertas**: mostra que aconteceu algo, diz "é grave", mas não explica O QUÊ aconteceu, POR QUÊ é grave, ou COMO prevenir.

Resultado: empresas com ferramentas caras, mas que não conseguem agir sobre o que elas mostram.

### A abordagem do SentinelBR

Cada alerta, vulnerabilidade e detecção vem com:

1. **O que aconteceu** (em português claro)
2. **Por que é importante** (contexto de negócio)
3. **O que fazer agora** (passos imediatos)
4. **Como prevenir no futuro** (orientação estratégica)
5. **Referências** (para quem quer aprender mais)

Isso transforma a plataforma em **ferramenta + tutor**.

### Para quem é útil

- PMEs sem time de segurança experiente: aprendem fazendo
- Profissionais novatos: ferramenta vira mentor
- Profissionais experientes: economizam tempo
- DPOs/jurídico: entendem o técnico
- Diretoria: vê o "porquê" do investimento

---

## Catálogo MITRE ATT&CK em PT-BR

### O que é MITRE ATT&CK

Framework mantido pela MITRE Corporation que cataloga **táticas, técnicas e procedimentos** (TTPs) usados por atacantes. Padrão da indústria.

Estrutura:
- **14 táticas** (objetivos do atacante)
- **~200 técnicas** (formas de atingir táticas)
- **~600 sub-técnicas** (variações específicas)

### Por que adaptar para PT-BR

- Documentação oficial é em inglês
- Profissionais BR de meio-de-carreira lutam com termos
- Contexto cultural (exemplos brasileiros) ajuda
- Diferencial competitivo

### As 14 táticas traduzidas

| ID | Original | PT-BR |
|----|----------|-------|
| TA0043 | Reconnaissance | Reconhecimento |
| TA0042 | Resource Development | Desenvolvimento de recursos |
| TA0001 | Initial Access | Acesso inicial |
| TA0002 | Execution | Execução |
| TA0003 | Persistence | Persistência |
| TA0004 | Privilege Escalation | Escalada de privilégio |
| TA0005 | Defense Evasion | Evasão de defesa |
| TA0006 | Credential Access | Acesso a credenciais |
| TA0007 | Discovery | Descoberta |
| TA0008 | Lateral Movement | Movimentação lateral |
| TA0009 | Collection | Coleta de dados |
| TA0011 | Command and Control | Comando e controle |
| TA0010 | Exfiltration | Exfiltração de dados |
| TA0040 | Impact | Impacto |

### Estrutura de uma página de técnica

Cada técnica tem página dedicada com seções:

#### 1. O que é (linguagem simples)

Explicação em português acessível, com analogia quando possível.

Exemplo (T1110 — Brute Force):
> Atacante tenta adivinhar senhas testando muitas combinações. É como ladrão testando vários chaveiros até achar a chave certa, mas computador faz isso milhões de vezes por segundo.

#### 2. Sub-técnicas

Lista variações específicas:
- T1110.001: Password Guessing — chuta senhas comuns
- T1110.002: Password Cracking — quebra hashes vazados
- T1110.003: Password Spraying — testa 1 senha em N usuários
- T1110.004: Credential Stuffing — usa credenciais vazadas

#### 3. Como acontece na prática

Exemplo realista, com log capturado:

```
Failed password for root from 203.0.113.42 port 38241
Failed password for admin from 203.0.113.42 port 38242
Failed password for ubuntu from 203.0.113.42 port 38243
```

#### 4. Como prevenir

Por nível de maturidade:

**NÍVEL 1 (todos deveriam fazer):**
- Desabilitar login como root via SSH
- Senhas fortes (16+ chars)
- Habilitar fail2ban

**NÍVEL 2 (intermediário):**
- Migrar de senha para chave SSH
- Mudar porta padrão
- 2FA no SSH

**NÍVEL 3 (avançado):**
- SSH apenas atrás de VPN/bastion
- Whitelist de IPs no firewall
- Certificados SSH

#### 5. Como detectar (status no SentinelBR)

```
Status: ✅ COBERTO

Regras Sigma ativas:
- ssh_brute_force_v2 (5+ falhas em 60s)
- ssh_password_spray
- ssh_login_anomaly

Playbooks ativos:
- brute_force_response → bloqueia IP automaticamente
```

#### 6. Grupos que usam (threat actors)

- APT28 (Fancy Bear) — frequentemente
- APT41 — em campanhas seletivas
- Lapsus$ — credentials stuffing
- Maioria dos botnets — diariamente

#### 7. Referências

- Link para MITRE oficial
- OWASP Authentication Cheat Sheet
- NIST 800-63B

### Status de cobertura

```
✅ COBERTO         Plataforma detecta confiavelmente
🟡 PARCIAL         Detecta variantes comuns, não todas
🔴 SEM COBERTURA   Plataforma não detecta
⚪ NÃO APLICÁVEL   Técnica não aplica ao escopo
```

### Dashboard de cobertura

Visualização tipo "matriz ATT&CK" que mostra cobertura geral:

```
┌──────────────────────────────────────────────┐
│ COBERTURA MITRE ATT&CK                       │
│                                              │
│ Total: 156 técnicas relevantes               │
│ ✅ Cobertas:        89 (57%)                 │
│ 🟡 Parciais:        34 (22%)                 │
│ 🔴 Sem cobertura:   33 (21%)                 │
│                                              │
│ Por tática:                                  │
│   Initial Access:        ████████░░ 80%      │
│   Execution:             ███████░░░ 70%      │
│   Persistence:           █████████░ 90%      │
│   Privilege Escalation:  ████████░░ 80%      │
│                                              │
└──────────────────────────────────────────────┘
```

### Atualização periódica

Catálogo atualizado via cron mensal:
1. Busca enterprise-attack.json do MITRE
2. Detecta novas técnicas/sub-técnicas
3. Cria entries em "needs translation"
4. Admin recebe notificação para traduzir/revisar

---

## Recomendações de hardening por host

Plataforma analisa cada host e gera **lista personalizada** de melhorias.

### Como funciona

```
1. Agente coleta configurações do host
2. Compara com baseline de boas práticas
3. Gera lista priorizada de melhorias
4. Cada item tem: comando para aplicar + impacto no score
5. Admin pode aplicar manualmente ou via wizard
```

### Estrutura de uma recomendação

```yaml
id: ssh-disable-root
title: "Desabilitar login como root via SSH"
severity: high
category: ssh
score_impact: 5

description: |
  Permitir login direto como root pelo SSH é uma das maiores
  superfícies de ataque. Atacantes sabem que "root" sempre existe.

why: |
  - Facilita brute force
  - Sem rastreabilidade (vários admins usando "root")
  - Compromisso = total

solution:
  manual: |
    Edite /etc/ssh/sshd_config:
      PermitRootLogin no
    Reinicie SSH:
      sudo systemctl reload sshd
  
  rollback: |
    sudo sed -i 's/^PermitRootLogin no/PermitRootLogin yes/' \
      /etc/ssh/sshd_config

verification:
  command: "sudo grep '^PermitRootLogin' /etc/ssh/sshd_config"
  expected: "PermitRootLogin no"

mitre_techniques: [T1078, T1110]
```

### Catálogo inicial (~80-100 recomendações)

Cobrindo:

**SSH (15 recomendações):**
- Desabilitar root login
- Desabilitar password auth
- Configurar MaxAuthTries
- Mudar porta padrão (opcional)
- Habilitar 2FA
- Configurar AllowUsers/AllowGroups
- Idle timeout
- Banner de aviso legal

**Firewall (10 recomendações):**
- Habilitar firewall
- Default policy DROP
- Limitar SSH a redes específicas
- Geo-blocking

**SELinux/AppArmor (8 recomendações):**
- Mudar para enforcing
- Reabilitar (se disabled)
- Auditar denials
- Aplicar profiles em apps

**Auditing (12 recomendações):**
- Instalar auditd
- Configurar regras LGPD
- Configurar retenção
- Centralizar logs

**Kernel hardening via sysctl (15 recomendações):**
- ASLR ativo
- Restricted dmesg
- Kernel pointer hiding
- IPv4/IPv6 hardening

**Mounts (5 recomendações):**
- /tmp com nodev, nosuid, noexec
- /var/tmp idem
- /home com nodev

**Updates (5 recomendações):**
- unattended-upgrades configurado
- Reboot agendado se kernel update

**Cron / agendamento, contas, logs, etc.**

### Aplicação em 1 clique (com salvaguardas)

UI mostra recomendação com botão "Aplicar":

```
┌──────────────────────────────────────────────────────────┐
│ 🔴 Desabilitar login como root via SSH                   │
│                                                          │
│ Em web-01.prod                                           │
│ Impacto no score: +5 pontos (78 → 83)                    │
│                                                          │
│ ⚠️ ATENÇÃO                                               │
│ Antes de aplicar, certifique-se de ter outro usuário     │
│ com sudo configurado e testado.                          │
│                                                          │
│ MUDANÇA QUE SERÁ APLICADA                                │
│ - PermitRootLogin yes                                    │
│ + PermitRootLogin no                                     │
│                                                          │
│ ☑ Fazer backup do sshd_config antes                      │
│ ☑ Validar que nova config funciona                       │
│ ☑ Permitir rollback em 5 min se algo quebrar             │
│                                                          │
│ Confirmação extra (digite "APLICAR"):                    │
│ ┌──────────────────────────────────────────────────┐     │
│ │                                                  │     │
│ └──────────────────────────────────────────────────┘     │
│                                                          │
│   [Cancelar]                       [Aplicar mudança]     │
└──────────────────────────────────────────────────────────┘
```

### Aplicação em massa

Aplicar mesma recomendação em vários hosts:
- Selecionar hosts (filtro por tag, OS, etc.)
- Selecionar recomendações
- Janela de manutenção
- Auto-rollback se SSH ficar inacessível

---

## Threat hunting queries

Biblioteca de "perguntas que threat hunters fazem". Diferencial: SIEM tradicional entrega **alertas**, threat hunting é o oposto — caçador formula hipóteses e procura evidências.

### Estrutura de uma query

```yaml
id: hunt-001
title: "Usuários criados fora do provisionamento"
description: |
  Procura criação de usuários do sistema que não foram criados
  via Ansible/Puppet/Terraform da empresa.

category: persistence
mitre_techniques: [T1136]
severity_if_found: high

query: |
  source="auditd"
  event.action="user_created"
  user.name NOT IN [pattern_corporativo]
  | last 30 days

interpretation: |
  ✅ FALSO POSITIVO COMUM:
    - Usuários criados por instalação de pacote
    - Migrações temporárias durante manutenção
  
  🔴 INVESTIGAR:
    - Nome aleatório (sjkdh3, x1, etc.)
    - Criado fora do horário comercial
    - Criado em produção sem ticket associado

next_actions:
  - "Verificar como usuário foi criado (cmdline)"
  - "Verificar se tem chave SSH ativa"
  - "Verificar histórico de comandos"
```

### Categorias do catálogo (~94 queries)

| Categoria | Quantidade |
|-----------|------------|
| Initial Access | 8 |
| Execution | 12 |
| Persistence | 15 |
| Privilege Escalation | 10 |
| Defense Evasion | 8 |
| Credential Access | 7 |
| Discovery | 6 |
| Lateral Movement | 5 |
| Collection | 6 |
| Command & Control | 8 |
| Exfiltration | 5 |
| Impact | 4 |

### Exemplos práticos

#### Procurar webshells

```yaml
title: "Webshells PHP em diretórios de upload"
agent_command: |
  find /var/www -name "*.php" -mtime -30 \
    -exec grep -l -E "eval\(|base64_decode|system\(|exec\(" {} \;
interpretation: |
  Investigar cada arquivo:
  - É da aplicação legítima? (compare com git)
  - Foi adicionado recentemente sem deploy?
  - Tem nome estranho (img.php em /uploads)?
```

#### Detectar beaconing C2

```yaml
title: "Possível comunicação C2 (beaconing)"
description: |
  Atacantes usam C2 que se comunica em intervalos regulares
  (ex: a cada 60 segundos).
query: |
  Conexões de saída do mesmo host para o mesmo destino externo,
  em intervalos regulares (variação < 10%), por mais de 1 hora.
```

#### Travel impossível

```yaml
title: "Travel impossível (login de 2 países em curto período)"
query: |
  Para cada usuário, comparar logins em países diferentes.
  Se distância requer voo de 5+ horas em 1h, é impossível.
interpretation: |
  ✅ VPN sendo usada
  🔴 Conta comprometida (uma das sessões é atacante)
```

### Execução

Admin clica "Executar hunt":
1. Gera query LogQL/SQL
2. Roda contra Loki + PostgreSQL
3. Retorna resultados em tabela
4. Permite drill-down em cada item
5. Permite "transformar em alerta permanente"

### Hunts agendados

Hunts importantes podem rodar regularmente:

```yaml
schedule:
  - id: hunt-c2-beacon
    cron: "0 */6 * * *"
  - id: hunt-impossible-travel
    cron: "0 8 * * *"
```

Resultados viram alertas se houver hits.

---

## IOC matching retroativo

Quando recebemos novo IOC (Indicator of Compromise), buscamos no histórico **completo**.

### Cenário motivador

```
1. Recebemos via threat intel: IP 198.51.100.99 é C2 do APT-X
2. Search retroativo em TODOS os logs históricos
3. Descobrimos: web-01 conectou para esse IP 47x em fevereiro
4. ALERTA: possível comprometimento já em fevereiro
```

Sem isso, IOC novo só protege FUTURO. Com isso, protege também passado.

### Tipos de IOCs

| Tipo | Exemplo | Fonte |
|------|---------|-------|
| IP malicioso | 198.51.100.42 | AbuseIPDB, OTX |
| Domínio C2 | evil-domain.com | ThreatFox |
| URL malicioso | http://bad.com/payload.exe | URLhaus |
| Hash de malware | abc123... (sha256) | MalwareBazaar |
| JA3 fingerprint | tls fingerprint | CAPE |
| ASN | AS12345 | AbuseIPDB |

### Processo

```python
async def retroactive_ioc_match(ioc):
    # 1. Determine queries por tipo
    queries = build_queries_for_ioc(ioc)
    
    # 2. Execute no Loki (logs)
    loki_matches = await loki.search_all(queries)
    
    # 3. Execute no PostgreSQL (eventos)
    pg_matches = await db.search_events_by_ioc(ioc)
    
    all_matches = loki_matches + pg_matches
    
    if not all_matches:
        return  # tudo limpo
    
    # 4. Cria alerta de "IOC histórico encontrado"
    await create_alert(
        title=f"IOC retroativo: {ioc.value}",
        severity="high",
        related_events=[m.id for m in all_matches],
    )
```

### UI de resultado

```
┌──────────────────────────────────────────────────────────────┐
│ 🚨 IOC Retroativo Encontrado                                 │
│                                                              │
│ IP 198.51.100.42 foi adicionado como malicioso há 2h.       │
│ Buscando histórico (90 dias):                                │
│                                                              │
│ ⚠️ ENCONTRADO 47 vezes                                       │
│                                                              │
│ Primeira ocorrência: 12/02/2026 03:45                        │
│ Última ocorrência:   28/04/2026 19:23                        │
│                                                              │
│ Hosts afetados:                                              │
│ • web-01.prod (45 conexões)                                  │
│ • db-01.prod (2 conexões — investigar URGENTE!)              │
│                                                              │
│ POSSÍVEL CENÁRIO                                             │
│ Comprometimento de fevereiro não detectado até agora.        │
│                                                              │
│ AÇÕES RECOMENDADAS                                           │
│ 1. ⚠️ Isolar db-01 IMEDIATAMENTE                             │
│ 2. Coletar forense completa de db-01                         │
│ 3. [LGPD] Verificar exfiltração de dados pessoais            │
│                                                              │
│ [Iniciar playbook IR] [Ver eventos] [Marcar investigado]    │
└──────────────────────────────────────────────────────────────┘
```

---

## Knowledge base de remediação

Cada tipo de alerta tem playbook de remediação manual estruturado.

### Estrutura

```yaml
alert_type: ssh_brute_force
title: "Brute force SSH detectado"

immediate_actions:
  - title: "Confirmar que é ataque (não pentest)"
    steps:
      - "Verificar se há pentest agendado"
      - "Confirmar com time de segurança"
  
  - title: "Bloquear o IP atacante"
    automated: true  # já feito pelo playbook
  
  - title: "Verificar se atacante teve sucesso"
    steps:
      - "Buscar logins bem-sucedidos do mesmo IP"
      - "Query: source.ip:X AND event.outcome:success"
      - "Se houver: usuário comprometido, mude senha"

investigation:
  - title: "Verificar reincidência"
  - title: "Avaliar exposição"

prevention:
  short_term:
    - "Aplicar fail2ban"
    - "Reduzir MaxAuthTries"
  long_term:
    - "Migrar para chave SSH"
    - "SSH atrás de bastion/VPN"
    - "Implementar 2FA"

lessons_learned:
  - "Quantos hosts ainda têm SSH com password?"
  - "Time foi alertado em tempo razoável?"
```

UI mostra como wizard interativo, marcando o que já foi feito.

---

## Simulação de ataques (purple team)

Feature avançada (fase 3+) — testa se as detecções funcionam de verdade.

### Conceito

- **Red team**: ataca
- **Blue team**: defende
- **Purple team**: ambos juntos, com objetivo de melhorar detecção

Plataforma simula ataques **controlados** e verifica se SentinelBR detectou.

### Cenários disponíveis

| Cenário | O que faz | Risco |
|---------|-----------|-------|
| SSH Brute Force | 50 senhas falhas de IP controlado | 🟢 zero |
| Privilege Escalation | sudo com senha errada | 🟢 zero |
| Suspicious File | Cria arquivo "malicioso" em /tmp | 🟢 zero |
| Webshell Drop | .php com pattern suspeito em /var/www | 🟡 baixo |
| Persistence Cron | Cronjob suspeito por 5min | 🟡 baixo |
| Lateral Movement | SSH entre hosts gerenciados | 🟡 baixo |
| Mimikatz pattern | Padrões de log típicos | 🟢 zero |
| Living off the Land | curl baixando binário fake | 🟢 zero |

### Como funciona

```yaml
simulation: ssh_brute_force_test

phase_1_setup:
  - "Identifica host alvo"
  - "Confirma com admin (manual approval)"

phase_2_attack:
  - "De IP controlado"
  - "50 tentativas SSH com senhas erradas"
  - "Velocidade: 1 tentativa/segundo"

phase_3_verify:
  - "Aguarda 60s"
  - "Verifica se alerta foi criado"
  - "Verifica se IP foi bloqueado"
  - "Verifica notificação enviada"

phase_4_report:
  - "✅ Detection: alerta criado em 12s"
  - "✅ Response: IP bloqueado em 15s"
  - "✅ Notification: enviada em 18s"
  - "Score: 100/100"

phase_5_cleanup:
  - "Remove IP do bloqueio"
  - "Marca alerta como 'simulação'"
```

### Salvaguardas obrigatórias

- Aprovação obrigatória do admin antes de cada simulação
- Janela de manutenção configurável
- Tag clara nos eventos: "purple_team_simulation"
- Limite: 1 simulação/host/dia
- Logging completo
- Rollback automático

### Coverage Test integrado com MITRE

```
┌──────────────────────────────────────────────────────────────┐
│ TESTE DE COBERTURA — MITRE ATT&CK                            │
│                                                              │
│ Executou 47 simulações nas últimas 24h.                      │
│                                                              │
│ ✅ 38 técnicas detectadas (81%)                              │
│ 🟡 5 detectadas com delay > 60s                              │
│ 🔴 4 NÃO DETECTADAS — corrigir!                              │
│                                                              │
│ TÉCNICAS NÃO DETECTADAS                                      │
│ • T1059.004 (Bash command obfuscation)                       │
│ • T1027 (Obfuscated files)                                   │
│ • T1055 (Process injection)                                  │
│ • T1574 (Hijack execution flow)                              │
│                                                              │
│ Para cada uma, sugere:                                       │
│ • Regra Sigma faltando                                       │
│ • Coleta de log adicional necessária                         │
│                                                              │
│ [Ver detalhes de cada gap]                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Modo aprendizado

Toggle para usuários novatos: explicações educativas em cada alerta.

### Como funciona

Em configurações do usuário:

```
☑ Modo aprendizado (explicações em cada alerta)
```

Quando ativo, cada alerta vem com bloco extra:

```
┌──────────────────────────────────────────────────────────────────┐
│ 🚨 Brute force SSH em web-01.prod                                │
│                                                                  │
│ ┌─ 📚 EXPLICAÇÃO PARA APRENDER ─────────────────────────────────┐ │
│ │                                                                │ │
│ │ O QUE É BRUTE FORCE?                                           │ │
│ │ Imagine alguém testando vários chaveiros pra entrar na sua    │ │
│ │ casa. É exatamente isso, mas com senhas. Computadores são     │ │
│ │ rápidos — testam milhões de senhas por segundo.                │ │
│ │                                                                │ │
│ │ POR QUE FOI DETECTADO?                                         │ │
│ │ 47 tentativas seguidas com senhas erradas em 60s. Não é       │ │
│ │ humano — é máquina atacando.                                   │ │
│ │                                                                │ │
│ │ O QUE A PLATAFORMA FEZ?                                        │ │
│ │ Bloqueou o atacante automaticamente por 1h.                    │ │
│ │                                                                │ │
│ │ O QUE VOCÊ PRECISA FAZER?                                      │ │
│ │ Provavelmente nada agora. Mas considere:                       │ │
│ │ 1. Migrar para chaves SSH                                      │ │
│ │ 2. Esconder SSH atrás de VPN                                   │ │
│ │                                                                │ │
│ │ APRENDER MAIS                                                  │ │
│ │ → Ver técnica MITRE T1110 explicada                            │ │
│ │ → Tutorial: configurar chaves SSH                              │ │
│ │                                                                │ │
│ └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Para quem é

- Estudantes começando em segurança
- DPOs vindos do jurídico
- Diretoria que quer entender
- Times pequenos que aprendem fazendo

Power users desligam o toggle.

### Glossário inline

Termos técnicos têm tooltip:

```
"Detectamos brute force [T1110](explicar)..."
                              ↑
                         Hover mostra explicação rápida
```

---

## Schema de dados

```sql
-- Schema knowledge base

CREATE TABLE kb.mitre_techniques (
    id              VARCHAR(16) PRIMARY KEY,  -- 'T1110.001'
    parent_id       VARCHAR(16),
    name            VARCHAR(255) NOT NULL,
    name_ptbr       VARCHAR(255),
    description     TEXT,
    description_ptbr TEXT,
    tactics         TEXT[] NOT NULL,
    platforms       TEXT[],
    coverage_status VARCHAR(16) DEFAULT 'unknown',
    coverage_notes  TEXT,
    detection_rules UUID[],
    references      TEXT[],
    last_updated_mitre TIMESTAMPTZ
);


CREATE TABLE kb.hardening_recommendations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(64) NOT NULL UNIQUE,
    title           VARCHAR(255) NOT NULL,
    title_ptbr      VARCHAR(255),
    category        VARCHAR(64),
    severity        VARCHAR(16) NOT NULL,
    score_impact    INTEGER NOT NULL DEFAULT 1,
    description     TEXT,
    why             TEXT,
    solution_manual TEXT NOT NULL,
    solution_automated TEXT,
    rollback        TEXT,
    verification_command TEXT,
    expected_output TEXT,
    prerequisites   TEXT[],
    references      TEXT[],
    mitre_techniques VARCHAR(16)[],
    applicable_to   JSONB
);


CREATE TABLE kb.host_recommendations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host_id         UUID NOT NULL REFERENCES inventory.hosts(id),
    recommendation_id UUID NOT NULL REFERENCES kb.hardening_recommendations(id),
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applied_at      TIMESTAMPTZ,
    applied_by      UUID REFERENCES auth.users(id),
    UNIQUE(host_id, recommendation_id)
);


CREATE TABLE kb.threat_hunting_queries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code            VARCHAR(64) NOT NULL UNIQUE,
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(64),
    mitre_techniques VARCHAR(16)[],
    query_logql     TEXT,
    query_sql       TEXT,
    interpretation  TEXT,
    next_actions    TEXT[],
    schedule_cron   VARCHAR(64)
);


CREATE TABLE kb.hunting_executions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id        UUID NOT NULL REFERENCES kb.threat_hunting_queries(id),
    executed_by     UUID REFERENCES auth.users(id),
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    results_count   INTEGER,
    results         JSONB,
    triggered_alerts UUID[]
);


CREATE TABLE kb.iocs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            VARCHAR(32) NOT NULL,    -- 'ip', 'domain', 'hash', 'url', 'ja3'
    value           VARCHAR(512) NOT NULL,
    source          VARCHAR(64),             -- 'abuseipdb', 'otx', 'manual'
    confidence      INTEGER,                 -- 0-100
    threat_actor    VARCHAR(120),
    description     TEXT,
    first_seen      TIMESTAMPTZ,
    last_seen       TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(type, value)
);

CREATE INDEX idx_iocs_type_value ON kb.iocs(type, value);
CREATE INDEX idx_iocs_active ON kb.iocs(expires_at) WHERE expires_at > NOW();


CREATE TABLE kb.ioc_retroactive_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ioc_id          UUID NOT NULL REFERENCES kb.iocs(id),
    host_id         UUID REFERENCES inventory.hosts(id),
    matched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    occurrences     INTEGER NOT NULL,
    first_occurrence_at TIMESTAMPTZ,
    last_occurrence_at TIMESTAMPTZ,
    related_events  TEXT[],
    alert_id        UUID REFERENCES alerts.alerts(id)
);


CREATE TABLE kb.simulations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario        VARCHAR(64) NOT NULL,
    target_host_id  UUID REFERENCES inventory.hosts(id),
    requested_by    UUID REFERENCES auth.users(id),
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    status          VARCHAR(16) NOT NULL DEFAULT 'pending',
                    -- 'pending', 'running', 'completed', 'failed'
    detection_score INTEGER,                 -- 0-100
    detection_time_seconds INTEGER,
    response_time_seconds INTEGER,
    report          JSONB
);
```

---

## Endpoints da API

```
══════════════════════════════════════════════════════════════════
ENDPOINTS DE KNOWLEDGE BASE
══════════════════════════════════════════════════════════════════

# MITRE ATT&CK
GET    /api/v1/kb/mitre/tactics
GET    /api/v1/kb/mitre/techniques
GET    /api/v1/kb/mitre/techniques/{id}
GET    /api/v1/kb/mitre/coverage-matrix
PATCH  /api/v1/kb/mitre/techniques/{id}/coverage-status

# Hardening
GET    /api/v1/kb/hardening/recommendations
GET    /api/v1/kb/hardening/hosts/{host_id}/recommendations
POST   /api/v1/kb/hardening/hosts/{host_id}/apply
POST   /api/v1/kb/hardening/bulk-apply
POST   /api/v1/kb/hardening/recommendations/{id}/dismiss

# Threat Hunting
GET    /api/v1/kb/hunting/queries
POST   /api/v1/kb/hunting/queries
POST   /api/v1/kb/hunting/queries/{id}/execute
GET    /api/v1/kb/hunting/executions
GET    /api/v1/kb/hunting/executions/{id}
POST   /api/v1/kb/hunting/queries/{id}/promote-to-rule

# IOCs
GET    /api/v1/kb/iocs
POST   /api/v1/kb/iocs                # adiciona manual
DELETE /api/v1/kb/iocs/{id}
POST   /api/v1/kb/iocs/{id}/retroactive-search
GET    /api/v1/kb/iocs/feeds
POST   /api/v1/kb/iocs/feeds/refresh

# Simulação
GET    /api/v1/kb/simulations/scenarios
POST   /api/v1/kb/simulations
GET    /api/v1/kb/simulations/{id}
POST   /api/v1/kb/simulations/{id}/approve
GET    /api/v1/kb/simulations/coverage-test
```

---

## Por que esse módulo impressiona

- **Educação como feature**: raríssimo em ferramentas de segurança
- **Cobertura MITRE em PT-BR**: diferencial competitivo único
- **Threat hunting acessível**: democratiza prática avançada
- **IOC retroativo**: detecta comprometimentos passados
- **Purple team**: valida que detecções funcionam (não só fé)
- **Modo aprendizado**: democratiza segurança

Posts potenciais no LinkedIn:

- "Como traduzi MITRE ATT&CK para o português brasileiro"
- "Threat hunting acessível: 94 queries que sua empresa pode usar HOJE"
- "IOC retroativo: encontrei comprometimento de 2 meses atrás (e o que aprendi)"
- "Purple team automatizado: testando se suas detecções realmente funcionam"
- "Hardening Linux em 1 clique: 100 recomendações catalogadas"
- "Modo aprendizado: como minha plataforma educa enquanto protege"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
