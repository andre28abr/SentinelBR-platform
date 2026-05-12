# SentinelBR — Visão Geral dos Módulos

> Documentação de alto nível da plataforma. Esta versão é a "explicação fácil", pensada para qualquer pessoa entender — incluindo recrutadores não-técnicos, gestores e stakeholders. As versões técnicas vêm em arquivos separados.

---

## 📖 Sumário

1. [O que é o SentinelBR](#o-que-é-o-sentinelbr)
2. [Por que ele existe (problema que resolve)](#por-que-ele-existe)
3. [Os 5 módulos da plataforma](#os-5-módulos)
   - [Módulo 1 — SIEM](#módulo-1--siem)
   - [Módulo 2 — Firewall](#módulo-2--firewall)
   - [Módulo 3 — SELinux](#módulo-3--selinux)
   - [Módulo 4 — Resposta a Incidentes](#módulo-4--resposta-a-incidentes)
   - [Módulo 5 — Compliance / LGPD](#módulo-5--compliance--lgpd)
4. [Como os módulos conversam entre si](#como-os-módulos-conversam)
5. [Glossário rápido](#glossário-rápido)

---

## O que é o SentinelBR

O **SentinelBR** é uma plataforma de segurança para servidores Linux. Pense nela como um **sistema de monitoramento e proteção 24h** para a infraestrutura de uma empresa — algo parecido com a central de monitoramento de um shopping ou condomínio, só que voltada para servidores e dados.

Ela faz cinco coisas principais:

1. **Vigia** tudo que acontece nos servidores (quem entrou, o que fez, o que tentou)
2. **Controla** o que pode entrar ou sair (firewall amigável)
3. **Protege** os programas dentro dos servidores (SELinux humanizado)
4. **Reage automaticamente** a ataques (resposta a incidentes)
5. **Documenta** tudo para a LGPD (compliance)

Tudo numa interface única, em português, pensada para a realidade brasileira.

---

## Por que ele existe

Hoje, uma pequena ou média empresa que quer ter um nível decente de segurança precisa:

- Pagar caro por ferramentas estrangeiras (Splunk, Elastic, Wazuh Cloud)
- Contratar especialista em cada uma delas
- Lidar com tudo em inglês e com termos técnicos
- Montar relatórios da LGPD no braço

Resultado: muita empresa **desliga** o que protege porque é difícil de configurar (clássico SELinux desabilitado, firewall liberado pra tudo, logs ninguém olha) e fica torcendo pra não acontecer nada.

O SentinelBR resolve isso oferecendo uma plataforma **única, em português, gratuita/open-source, com foco na realidade brasileira (LGPD, fusos, idioma)** e **fácil de usar** mesmo para quem não é especialista.

---

## Os 5 módulos

---

### Módulo 1 — SIEM

> **SIEM** (Security Information and Event Management) é o cérebro central que coleta e analisa os eventos.

#### A analogia

Imagine que cada servidor da empresa é uma loja num shopping. Cada loja tem câmeras, sensores de porta, alarme de incêndio e detector de fumaça — tudo gerando registros do que acontece o tempo todo. O problema é que **ninguém consegue ficar olhando 50 lojas ao mesmo tempo**, e ainda por cima cada loja tem um sistema diferente.

O SIEM é a **central de segurança do shopping**:

- Recebe as imagens e alarmes de **todas as lojas ao mesmo tempo**
- Tem **um painel grande** mostrando o status de tudo
- Tem um **segurança experiente** (na verdade, um motor de regras) que sabe ler os sinais: "olha, alguém tentou abrir essa porta 30 vezes em 1 minuto — isso não é normal, dispara o alarme"
- **Guarda gravações** caso precise rever depois
- **Avisa o gerente** (você) quando encontra algo suspeito

#### O que ele faz na prática

- **Coleta logs**: pega os registros de tudo que acontece (logins, acessos a arquivos, conexões de rede, erros)
- **Padroniza**: como cada programa escreve de um jeito diferente, ele traduz tudo para um formato único e fácil de pesquisar
- **Armazena**: guarda tudo organizado por dias, semanas, meses (você escolhe quanto tempo)
- **Analisa em tempo real**: aplica centenas de regras para procurar padrões suspeitos (tipo "tentativa de invasão de SSH", "acesso a arquivo sensível", "conexão com IP malicioso conhecido")
- **Detecta anomalias**: aprende o comportamento normal e avisa quando algo foge do padrão (login no domingo às 3h da manhã, por exemplo)
- **Alerta**: dispara notificação no Telegram, Slack, e-mail ou painel quando algo grave acontece
- **Permite investigar**: tem busca rápida ("me mostre tudo que esse IP fez nos últimos 7 dias")

#### Para quem isso é útil

- Time de TI/segurança para **detectar ataques cedo**
- Auditor para **investigar incidentes** com calma depois
- Gestor para **provar que a empresa monitora** os ambientes (LGPD, ISO 27001)

---

### Módulo 2 — Firewall

> **Firewall** é a parede que controla o que entra e sai do servidor pela rede.

#### A analogia

Pense no firewall como o **porteiro do prédio**. Ele tem uma lista do que pode entrar e sair: "moradores entram, entregadores só com autorização do morador, vendedores ambulantes não entram nunca, ex-namorado da Dona Maria está bloqueado".

O problema é que essa lista, no Linux, é escrita num formato **bem chato** (`iptables` ou `nftables`) — cheio de comandos, símbolos e parâmetros que parecem hieróglifos. Um administrador erra uma vírgula e:

- Ou trava a empresa toda (todo mundo fica sem acesso)
- Ou abre tudo (firewall vira queijo suíço)

Nosso módulo é uma **interface visual amigável** para o porteiro:

- Mostra todas as regras numa **tabela bonita**, em português
- Permite criar regra clicando em botão ("bloquear esse IP", "liberar essa porta")
- Tem **modelos prontos** ("servidor web", "servidor de banco de dados", "máquina de desenvolvedor")
- Se você errar, dá para **voltar para a versão anterior** (tipo Ctrl+Z, com histórico completo)
- **Conversa com o SIEM**: se o SIEM detectar ataque, o firewall **bloqueia automaticamente** sem você precisar fazer nada

#### O que ele faz na prática

- **Visualiza regras ativas**: mostra tudo que está configurado, com cores e ícones (verde = permite, vermelho = bloqueia)
- **Cria/edita/remove** regras com formulário simples: "bloquear conexões da porta X vindas do IP Y"
- **Templates prontos**: aplique configurações testadas com um clique
- **Histórico e rollback**: toda mudança fica registrada, dá para voltar a qualquer ponto
- **Bloqueio automático**: integrado com o SIEM, bloqueia atacantes sozinho
- **Bloqueio por país (geo-blocking)**: "só aceitar conexões do Brasil" com um toggle
- **Listas dinâmicas**: IPs bloqueados por tempo determinado (1 hora, 1 dia, permanente)
- **Auditoria**: quem mudou o quê, quando, e por quê

#### Para quem isso é útil

- Administrador para **gerenciar acessos** sem decorar comandos
- Time de segurança para **responder a ataques** rapidamente
- Auditor para **provar controles de acesso de rede**

---

### Módulo 3 — SELinux

> **SELinux** é uma camada extra de segurança que controla o que cada programa pode fazer dentro do servidor.

#### A analogia

Se o firewall é o porteiro do prédio (cuida de quem entra de fora), o SELinux é tipo um **segurança paranoico que fica vigiando dentro do escritório**. Enquanto o firewall pergunta "você pode entrar?", o SELinux pergunta:

> "Tá, você entrou. Mas você é o estagiário do marketing — o que você está fazendo no andar do RH mexendo na sala dos contratos? Sai daí."

Ele observa cada programa rodando e diz coisas como:

- "Ô Apache, você é um servidor web. Você não tem **nada** que abrir o arquivo `/etc/shadow` (senhas). **Bloqueado**."
- "Ô MySQL, você cuida do banco de dados. **Por que** está tentando enviar e-mails? Suspeito. **Bloqueado**."

Isso é uma proteção poderosíssima: mesmo se um hacker invadir o Apache, ele não consegue acessar o resto do servidor — porque o SELinux não deixa o Apache passar do lugar dele.

**O problema**: o SELinux é **muito chato de configurar**. Quando algo não funciona no Linux, 70% das vezes é o SELinux bloqueando alguma coisa, e a mensagem de erro é um inferno de decifrar — algo tipo:

```
type=AVC msg=audit(1234567890.123:456): avc: denied { read } for pid=1234 
comm="httpd" name="config.json" dev="dm-0" ino=789 
scontext=system_u:system_r:httpd_t:s0 
tcontext=system_u:object_r:default_t:s0 tclass=file
```

Por causa disso, **muita gente simplesmente desabilita o SELinux** e fica vulnerável. Triste.

#### O que nosso módulo faz

Nosso módulo é o **tradutor amigável do SELinux**:

- **Mostra em português** o que ele bloqueou e por quê: "O Apache tentou ler o arquivo `/srv/site/config.json`, mas o contexto do arquivo não permite. Isso geralmente acontece quando você move o arquivo para um diretório novo."
- **Sugere a correção**: "Para resolver, basta aplicar o contexto correto. Quer que eu faça isso pra você? [Sim] [Não]"
- **Permite ligar/desligar funcionalidades** com botão amigável: "Permitir que o Apache faça conexões de rede para fora? [Sim/Não]"
- **Cria permissões customizadas automaticamente** quando seu app precisa de algo específico
- **Mostra o status** de cada servidor (ligado, modo permissivo, desabilitado) num dashboard
- **Histórico de mudanças**: o que foi alterado, quando, por quem

#### Para quem isso é útil

- Administrador que **odeia mexer com SELinux** e por isso o desabilitava
- Time de segurança que quer **manter o SELinux ligado** sem virar inimigo dos desenvolvedores
- Auditor que precisa **provar isolamento entre processos**

---

### Módulo 4 — Resposta a Incidentes

> **Resposta a Incidentes** automatiza as primeiras ações quando um ataque é detectado.

#### A analogia

Imagine um **plano de evacuação de incêndio** num prédio. Quando soa o alarme, ninguém fica pensando "hmm, o que faço agora?". Já existe um procedimento testado:

1. Fechar as portas corta-fogo
2. Acionar os bombeiros
3. Conduzir as pessoas pelas escadas
4. Contar todo mundo no ponto de encontro

Em segurança digital é a mesma coisa. Quando um ataque é detectado, **cada segundo conta**. Mas em muitas empresas, quando o alarme toca, o time de TI fica:

- Procurando o telefone de quem responde
- Lendo manual para lembrar o que fazer
- Discutindo no chat sobre quem faz o quê
- Enquanto isso, o atacante está roubando dados

Nosso módulo é o **plano de evacuação automatizado**. Você define **uma vez** o que fazer em cada tipo de incidente, e a plataforma executa **sozinha** quando aquele tipo de evento acontecer.

Exemplos de "playbooks" prontos:

- **Detectou tentativa de invasão SSH** → bloqueia o IP por 1 hora + avisa no Telegram
- **Detectou possível ransomware** → isola o servidor da rede + tira snapshot de evidências + chama o time
- **Detectou acesso suspeito a dados pessoais** → registra evidência + notifica o DPO

#### Como funciona com aprovação humana

Para ações **leves e seguras** (bloquear um IP, mandar mensagem), a plataforma age sozinha — não precisa esperar humano.

Para ações **drásticas** (desligar um servidor de produção, apagar um processo), ela **pede aprovação primeiro**: manda uma mensagem no Telegram com botões "Aprovar" / "Negar". Você decide com 1 toque, e a plataforma continua dali.

Isso evita o problema clássico de automação: **causar mais estrago que o ataque** original.

#### O que ele faz na prática

- **Playbooks prontos** para cenários comuns (brute force, ransomware, vazamento)
- **Editor visual** de playbooks (parecido com um fluxograma)
- **Catálogo de ações disponíveis**: bloquear IP, isolar host, matar processo, coletar evidências, notificar
- **Aprovação humana** opcional para ações críticas
- **Coleta forense automática**: tira "fotografia" do estado do servidor no momento do ataque (processos rodando, conexões abertas, arquivos modificados)
- **Notificações** integradas: Telegram, Slack, e-mail, webhook
- **Linha do tempo** dos incidentes: o que foi detectado, o que foi feito, qual o resultado

#### Para quem isso é útil

- Time pequeno de TI que **não tem plantão 24h** (a plataforma age durante a madrugada)
- Empresas que precisam **responder rápido** por exigência regulatória
- Análise pós-incidente: **timeline completa** para entender o que aconteceu

---

### Módulo 5 — Compliance / LGPD

> **Compliance** é provar para auditor/regulador que a empresa cumpre as regras.

#### A analogia

Imagine que você tem uma **lanchonete** e a Vigilância Sanitária pode aparecer a qualquer momento. O fiscal não vai acreditar na sua palavra ("juro que limpo a cozinha todo dia, moço") — ele vai querer **ver o livro de registro**: que dia foi limpa, quem limpou, com qual produto.

A LGPD funciona igual. A lei diz que sua empresa precisa **provar** que cuida bem dos dados pessoais. Se acontecer um vazamento, a ANPD (a "Vigilância Sanitária dos dados") vai aparecer e perguntar:

- "Quem teve acesso aos dados que vazaram?"
- "Quando acessaram?"
- "Tinham permissão para acessar?"
- "Vocês foram avisados que estava acontecendo?"
- "Em quanto tempo reagiram?"

Sem ferramenta, descobrir tudo isso é um **pesadelo** — o pessoal de TI vai vasculhar logs no braço por dias para montar o relatório, geralmente já tarde demais.

#### O que nosso módulo faz

Esse módulo **automatiza a auditoria de dados pessoais**. Você marca uma vez quais arquivos, pastas, tabelas e sistemas têm dados pessoais, e a plataforma **fica vigiando 24/7**.

- **Cadastro dos ativos sensíveis**: você diz "esses arquivos aqui têm dados de cliente, essa tabela tem CPFs, esse endpoint da API expõe e-mails"
- **Vigilância automática**: toda vez que alguém acessa, modifica ou copia esses dados, fica registrado
- **Relatórios prontos para a ANPD**: PDF com tudo organizado, em formato de auditoria oficial
- **Mapa de dados**: diagrama mostrando por onde os dados pessoais transitam na empresa (útil para o DPO)
- **Detecção de vazamento**: regras especiais que disparam quando o comportamento parece suspeito (download em massa de tabela de clientes, cópia de arquivo sensível para pasta temporária, etc.)
- **Registro do consentimento**: integra com o sistema da empresa para registrar quando cada titular consentiu o quê
- **Atendimento a direitos do titular**: facilita responder pedidos de "quero saber o que vocês têm sobre mim", "apaguem meus dados", etc.

#### Por que isso vale ouro

A LGPD pode aplicar multas de até **2% do faturamento** (limitado a R$ 50 milhões por infração). Mais do que isso: o **dano de imagem** de um vazamento mal-tratado destrói marcas em semanas.

Empresas pequenas e médias **não têm** time dedicado de privacidade. O DPO geralmente é alguém da TI ou jurídico fazendo "nas horas vagas". Esse módulo dá a esse profissional **superpoderes**: o que levaria dias agora leva minutos.

#### Para quem isso é útil

- DPO (Encarregado de Dados) que precisa **operacionalizar a LGPD**
- Time jurídico que precisa **responder rápido** a solicitações de titulares
- Diretoria que quer **dormir tranquila** sabendo que está em conformidade
- Empresas em **processo de certificação** (ISO 27701, por exemplo)

---

## Como os módulos conversam

Os 5 módulos não são caixinhas isoladas — eles **trabalham juntos** como um time. Veja a história de um ataque:

1. **2h da manhã**: alguém na Romênia começa a tentar adivinhar a senha do SSH de um servidor.
2. **SIEM detecta**: identifica o padrão "muitas tentativas falhas em pouco tempo = brute force".
3. **Playbook é acionado**: o módulo de Resposta a Incidentes recebe o evento e dispara o playbook "Brute Force SSH".
4. **Firewall age**: bloqueia o IP do atacante por 1 hora automaticamente.
5. **SELinux protege**: caso o atacante tivesse conseguido entrar, o SELinux teria bloqueado ele de acessar arquivos fora do permitido — então mesmo se passasse, dano seria mínimo.
6. **Compliance registra**: o módulo de LGPD registra que houve uma tentativa de acesso a um servidor que tem dados pessoais, gerando entrada no relatório de incidentes.
7. **Notificação**: você recebe uma mensagem no Telegram às 7h: "Tentativa de invasão bloqueada às 02:14, IP 203.0.113.42, nenhum dado comprometido."

**Tudo isso aconteceu sozinho enquanto você dormia.**

Diagrama simplificado da comunicação:

```
┌─────────────┐
│   Agente    │ ── coleta logs ──┐
│ (nos hosts) │                  ▼
└─────────────┘            ┌──────────┐
       ▲                   │   SIEM   │
       │ executa           │ (cérebro)│
       │ ações             └─────┬────┘
       │                         │ detecta ameaça
       │                         ▼
┌──────┴───────┐         ┌──────────────┐
│   Firewall   │◄────────┤   Playbook   │
│   SELinux    │ aciona  │  (resposta)  │
└──────────────┘         └──────┬───────┘
                                │ registra
                                ▼
                         ┌──────────────┐
                         │  Compliance  │
                         │    (LGPD)    │
                         └──────────────┘
```

---

## Glossário rápido

- **Log**: registro escrito do que um programa fez (tipo um diário). Servidores geram milhões por dia.
- **SIEM**: ferramenta que junta e analisa logs de várias fontes para detectar problemas.
- **Firewall**: filtro de rede que decide o que pode entrar ou sair de um computador.
- **SELinux**: mecanismo do Linux que limita o que cada programa pode fazer dentro do sistema.
- **Brute force**: ataque que tenta milhares de senhas até acertar.
- **Playbook**: receita pronta de "se acontecer X, faça Y, Z e W".
- **DPO**: Encarregado de Proteção de Dados, responsável legal pela LGPD na empresa.
- **ANPD**: Autoridade Nacional de Proteção de Dados, órgão que fiscaliza a LGPD.
- **RIPD**: Relatório de Impacto à Proteção de Dados, documento exigido pela LGPD em alguns casos.
- **Forense (digital)**: coleta de evidências para entender como um ataque aconteceu.
- **Compliance**: conformidade — provar que a empresa segue as regras (leis, normas, padrões).

---

## Próximos documentos

Esta é a documentação de **visão geral**. Os documentos técnicos virão em arquivos separados:

- `02-arquitetura-tecnica.md` — Stack, deploys, comunicação entre componentes
- `03-modulo-siem-tecnico.md` — Parsers, regras Sigma, schema de eventos
- `04-modulo-firewall-tecnico.md` — Backends, modelo de regras, integração
- `05-modulo-selinux-tecnico.md` — Parsing de AVC, geração de policies
- `06-modulo-resposta-tecnico.md` — Engine de playbooks, catálogo de actions
- `07-modulo-compliance-tecnico.md` — Auditing, relatórios LGPD
- `08-roadmap.md` — Fases de desenvolvimento, MVP, releases
- `09-stack-decisions.md` — Escolhas técnicas e justificativas

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Licença da documentação: CC BY-SA 4.0*
