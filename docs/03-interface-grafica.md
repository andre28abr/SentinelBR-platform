# SentinelBR — Especificação Detalhada da Interface Gráfica

> Documento de design da interface (GUI). Cobre identidade visual, estrutura de navegação, layout de cada tela, componentes, estados, fluxos de usuário e diretrizes de acessibilidade. Pensado para servir tanto como **guia de implementação para desenvolvedores frontend** quanto como **referência de UX para apresentação no portfólio**.

---

## 📋 Sumário

1. [Filosofia de design](#filosofia-de-design)
2. [Identidade visual](#identidade-visual)
3. [Estrutura geral da aplicação](#estrutura-geral-da-aplicação)
4. [Sistema de componentes (design system)](#sistema-de-componentes)
5. [Telas detalhadas](#telas-detalhadas)
6. [Estados e feedback](#estados-e-feedback)
7. [Acessibilidade](#acessibilidade)
8. [Responsividade](#responsividade)
9. [Microinterações e animações](#microinterações-e-animações)
10. [Fluxos de usuário](#fluxos-de-usuário)
11. [Stack técnica do frontend](#stack-técnica-do-frontend)

---

## Filosofia de design

A interface do SentinelBR é construída sobre **5 princípios** que guiam toda decisão visual e de UX:

### 1. 🎯 Densidade informativa sem caos

Operadores de segurança trabalham com muita informação ao mesmo tempo. A interface precisa mostrar **muito dado num espaço pequeno**, mas com hierarquia visual clara. Não é Pinterest (espaço em branco generoso) — é mais perto de um cockpit de avião: tudo importante está à vista, mas organizado por importância.

### 2. 🚨 Cores com significado (não decorativas)

Vermelho **só** para alerta crítico. Verde **só** para "tudo OK". Amarelo **só** para atenção. Cores nunca são usadas por estética — são sempre semânticas. Isso cria leitura instantânea: o operador olha e em 0.5s sabe o estado do sistema.

### 3. ⌨️ Velocidade primeiro (power user friendly)

Todo fluxo crítico precisa ter atalho de teclado. `Cmd+K` abre busca global. `?` mostra atalhos. `Esc` fecha modais. `J/K` navega listas. Operadores experientes nunca tocam o mouse — a interface respeita isso.

### 4. 🌙 Dark mode como padrão

SOC opera 24/7. Telão escuro no horário noturno é regra de saúde ocular. O modo claro existe para contextos de auditoria/relatórios, mas o default é escuro.

### 5. 💬 Comunicação em português, sem jargão desnecessário

Mensagens de erro úteis: "Não foi possível conectar ao agente em web-01. Verifique se ele está rodando: `systemctl status sentinelbr-agent`". Não: "Error 500 - Connection refused".

---

## Identidade visual

### 🎨 Paleta de cores

#### Tema escuro (padrão)

```
═══════════════════════════════════════════════════════════════
BACKGROUNDS
═══════════════════════════════════════════════════════════════
bg-base       #0A0E1A   ← fundo geral (azul-quase-preto)
bg-surface    #131826   ← cards, modais
bg-elevated   #1B2235   ← hover de cards
bg-overlay    #0A0E1ACC ← overlay de modal (com blur)

═══════════════════════════════════════════════════════════════
TEXTOS
═══════════════════════════════════════════════════════════════
text-primary    #E6EDF7   ← texto principal
text-secondary  #9AA5B8   ← texto secundário
text-muted      #5C6577   ← labels, placeholders
text-inverse    #0A0E1A   ← texto sobre fundo claro

═══════════════════════════════════════════════════════════════
BORDAS
═══════════════════════════════════════════════════════════════
border-subtle   #1F2638
border-default  #2A3349
border-strong   #3D4865

═══════════════════════════════════════════════════════════════
CORES SEMÂNTICAS (usadas para STATUS)
═══════════════════════════════════════════════════════════════
success    #10B981 (verde)    ← OK, online, permitido
warning    #F59E0B (âmbar)    ← atenção, degradado
danger     #EF4444 (vermelho) ← crítico, bloqueado
info       #3B82F6 (azul)     ← informativo
purple     #8B5CF6 (roxo)     ← LGPD/compliance

═══════════════════════════════════════════════════════════════
ACCENT (cor da marca)
═══════════════════════════════════════════════════════════════
brand-500    #00D9A3 (verde-água, cor principal)
brand-600    #00B388
brand-400    #33E0B5
```

#### Tema claro

Mesma estrutura, mas inverte os fundos (#FFFFFF base, #F8FAFC surface) e ajusta semânticas para contraste em fundo claro.

### 🔤 Tipografia

```
═══════════════════════════════════════════════════════════════
FONTES
═══════════════════════════════════════════════════════════════
Sans-serif   "Inter"            ← UI geral
Monospace    "JetBrains Mono"   ← logs, código, IDs

═══════════════════════════════════════════════════════════════
ESCALA TIPOGRÁFICA
═══════════════════════════════════════════════════════════════
display    32px / 40px line-height / 700 weight
h1         24px / 32px / 700
h2         20px / 28px / 600
h3         16px / 24px / 600
body       14px / 20px / 400
small      12px / 16px / 400
tiny       11px / 14px / 500 (uppercase, letterspaced)
```

**Por que Inter?** Otimizada para telas, dígitos tabulares (números alinham em colunas — crítico para tabelas), suporte amplo a português.

**Por que JetBrains Mono?** Ligaduras desligáveis, ótima legibilidade, distingue claramente `0` de `O` e `1` de `l` (importante para hashes, IPs, comandos).

### 🖼️ Logo e marca

**Conceito**: escudo estilizado formado por 5 segmentos (representando os 5 módulos), com um circuito interno sugerindo tecnologia. Cor principal verde-água `#00D9A3` sobre fundo escuro.

**Variações necessárias**:
- Logo completo (escudo + "SentinelBR")
- Marca d'água (apenas escudo) para favicon, app móvel, sidebar colapsada
- Versão monocromática (preto e branco) para impressão de relatórios

### 📐 Sistema de espaçamento

Baseado em múltiplos de **4px**:

```
0.5  →  2px
1    →  4px
2    →  8px
3    →  12px
4    →  16px   ← padding padrão
6    →  24px   ← gap entre seções
8    →  32px
12   →  48px   ← margem de seção principal
16   →  64px
```

### 🔘 Border radius

```
sm    4px    ← inputs, botões pequenos
md    6px    ← botões, cards pequenos
lg    8px    ← cards, modais
xl    12px   ← cards grandes
full  9999px ← badges, avatares
```

---

## Estrutura geral da aplicação

### 🏗️ Layout master

Toda a aplicação (após login) compartilha esta estrutura:

```
┌──────────────────────────────────────────────────────────────┐
│  TOPBAR (altura fixa: 56px)                                  │
│  [☰] [Logo] ──────────── [Busca Cmd+K] [🔔] [👤 Usuário ▼]  │
├────────┬─────────────────────────────────────────────────────┤
│        │                                                     │
│  SIDE  │                                                     │
│  BAR   │              ÁREA DE CONTEÚDO PRINCIPAL             │
│        │              (altura: viewport - 56px)              │
│  240px │                                                     │
│        │              padding: 24px 32px                     │
│        │                                                     │
│        │                                                     │
│        │                                                     │
└────────┴─────────────────────────────────────────────────────┘
```

### 🧭 Topbar (cabeçalho)

**Componentes da esquerda para direita:**

1. **Botão hambúrguer** (mobile e desktop): colapsa/expande sidebar
2. **Logo SentinelBR**: clicável, leva ao dashboard
3. **Breadcrumb** (opcional, em telas profundas): `SIEM › Regras › Brute Force SSH`
4. **Espaço flexível**
5. **Barra de busca global** com placeholder `Buscar (Cmd+K)`
6. **Indicador de saúde do sistema**: bolinha verde/amarela/vermelha que detalha em hover
7. **Botão de notificações** com badge de contagem
8. **Avatar do usuário** com dropdown:
   - Meu perfil
   - Preferências
   - Atalhos de teclado
   - Documentação
   - Sair

**Comportamento**: a topbar permanece fixa no scroll. Em mobile, o logo é substituído pelo nome da tela atual.

### 📚 Sidebar (navegação principal)

```
┌─────────────────────┐
│ ──────────────────  │
│ NAVEGAÇÃO PRINCIPAL │
│ ──────────────────  │
│ 🏠 Dashboard        │
│ 🖥️  Hosts            │
│                     │
│ ──────────────────  │
│ MONITORAMENTO       │
│ ──────────────────  │
│ 📊 Eventos          │
│ 🚨 Alertas      [3] │  ← badge com count
│ 📜 Regras           │
│ 🔍 Investigação     │
│                     │
│ ──────────────────  │
│ PROTEÇÃO            │
│ ──────────────────  │
│ 🛡️  Firewall         │
│ 🔒 SELinux          │
│                     │
│ ──────────────────  │
│ AUTOMAÇÃO           │
│ ──────────────────  │
│ ⚡ Playbooks        │
│ 📋 Incidentes   [1] │
│                     │
│ ──────────────────  │
│ PRIVACIDADE         │
│ ──────────────────  │
│ ⚖️  LGPD            │
│ 📁 Ativos sensíveis │
│ 📑 Relatórios       │
│                     │
│ ──────────────────  │
│ ADMINISTRAÇÃO       │
│ ──────────────────  │
│ ⚙️  Configurações    │
│ 👥 Usuários          │
│ 🔌 Integrações       │
│ 📚 Auditoria         │
└─────────────────────┘
```

**Estados da sidebar:**

- **Expandida** (240px): texto + ícone visíveis
- **Colapsada** (64px): apenas ícones, label aparece em tooltip
- **Mobile** (drawer): sobrepõe conteúdo, fecha ao clicar fora

**Comportamento:**

- Item ativo tem barra lateral verde-água (`brand-500`) à esquerda + fundo `bg-elevated`
- Hover muda cor de fundo sutilmente
- Atalho `Cmd+B` colapsa/expande
- Persistência: estado salvo em localStorage

### 🔍 Busca global (Command Palette)

Aberta com `Cmd+K` (ou `Ctrl+K`), é um modal central que faz **busca universal**:

```
┌──────────────────────────────────────────────────────────┐
│  🔍 Buscar...                                       [Esc]│
├──────────────────────────────────────────────────────────┤
│  AÇÕES RÁPIDAS                                           │
│    ▶ Bloquear IP...                                      │
│    ▶ Adicionar host                                      │
│    ▶ Criar regra de firewall                             │
│                                                          │
│  HOSTS (3)                                               │
│    🖥️  web-01.prod (online)                              │
│    🖥️  db-01.prod (online)                               │
│    🖥️  bastion.prod (offline desde 14:23)                │
│                                                          │
│  ALERTAS RECENTES (2)                                    │
│    🚨 Brute force SSH em web-01                          │
│    ⚠️  Disco em 85% em db-01                             │
│                                                          │
│  IR PARA                                                 │
│    → Configurações › Notificações                        │
│    → Documentação                                        │
└──────────────────────────────────────────────────────────┘
```

Navegação por setas, `Enter` executa, `Tab` muda contexto. Faz **fuzzy search** em hosts, alertas, regras, configurações e ações disponíveis.

---

## Sistema de componentes

### 🔘 Botões

Quatro variantes principais:

```
PRIMARY      [████ Salvar ████]    bg-brand-500, hover bg-brand-600
SECONDARY    [████ Cancelar ████]  bg-surface, border, hover bg-elevated
DANGER       [████ Deletar ████]   bg-danger, hover variante mais escura
GHOST        [   Editar   ]       sem fundo, apenas hover
```

Tamanhos: `sm` (28px), `md` (36px, padrão), `lg` (44px).

Estados: default, hover, active, disabled, loading (com spinner).

### 📋 Tabelas

A tabela é **o componente mais importante** da interface (operadores passam horas lidando com listas).

**Anatomia:**

```
┌─────────────────────────────────────────────────────────────┐
│ TABELA DE EVENTOS                              [Filtros] [⋮]│
├─────────────────────────────────────────────────────────────┤
│ □ │ Hora ▼   │ Host        │ Severidade │ Mensagem          │
├───┼──────────┼─────────────┼────────────┼───────────────────┤
│ □ │ 14:23:45 │ web-01      │ 🔴 alta    │ Brute force SSH   │
│ □ │ 14:22:11 │ web-01      │ 🟡 média   │ Login fora hor... │
│ □ │ 14:20:03 │ db-01       │ 🟢 info    │ Backup concluído  │
├─────────────────────────────────────────────────────────────┤
│ Mostrando 1-50 de 1.234        [‹] 1 2 3 ... 25 [›]        │
└─────────────────────────────────────────────────────────────┘
```

**Funcionalidades obrigatórias:**

- **Ordenação**: clique no header alterna asc/desc, ícone indica direção
- **Filtros**: dropdown por coluna ou painel lateral expansível
- **Seleção múltipla**: checkbox para ações em lote
- **Densidade configurável**: confortável (40px) / compacta (32px) / muito compacta (24px)
- **Colunas customizáveis**: usuário escolhe quais aparecem, ordem, e larguras (persistido)
- **Linhas expansíveis**: clique no chevron expande detalhes inline
- **Atualização em tempo real**: novas linhas aparecem com fade-in verde
- **Exportação**: CSV, JSON, Excel (do estado atual com filtros aplicados)
- **Densidade infinita**: virtualização para listas com 10k+ itens (lib `@tanstack/react-virtual`)

### 🃏 Cards de estatística (KPI cards)

```
┌─────────────────────────────────────┐
│  EVENTOS NAS ÚLTIMAS 24H            │
│                                     │
│  12.483        ↑ 8% vs ontem        │
│  ▁▂▃▅▇▆▅▃▂▁▂▃▄▅                    │  ← sparkline
│                                     │
│  Detalhes →                         │
└─────────────────────────────────────┘
```

Sempre incluem: rótulo, valor principal, comparação histórica, micro-gráfico (sparkline) e link de ação.

### 🚨 Alertas e badges

**Badges de severidade** (sempre nesta ordem):

```
🔴 CRÍTICA    bg-danger, texto branco
🟠 ALTA       bg-orange-500
🟡 MÉDIA      bg-warning
🟢 BAIXA      bg-success
🔵 INFO       bg-info
```

Formato: `texto + cor de fundo + ícone à esquerda`. Sempre `uppercase` e tipografia `tiny`.

**Banners de alerta** (no topo de telas):

```
┌──────────────────────────────────────────────────────┐
│ ⚠️  3 hosts estão offline há mais de 1h        [Ver] │
└──────────────────────────────────────────────────────┘
```

### 📝 Formulários

Princípios:

- **Labels acima dos inputs** (sempre, nunca placeholder como label)
- **Helper text** abaixo do input em `text-secondary`
- **Validação inline** (não esperar submit) — borda vermelha + mensagem de erro abaixo
- **Botão primário à direita**, secundário à esquerda
- **Loading state** desabilita o form inteiro com overlay sutil

```
┌─────────────────────────────────────┐
│ Nome do host *                      │
│ ┌─────────────────────────────────┐ │
│ │ web-01.prod                     │ │
│ └─────────────────────────────────┘ │
│ Hostname único, sem espaços         │
│                                     │
│ Endereço IP *                       │
│ ┌─────────────────────────────────┐ │
│ │ 10.0.1.5_                       │ │
│ └─────────────────────────────────┘ │
│ ✗ Formato de IP inválido            │
│                                     │
│ Tags                                │
│ ┌─────────────────────────────────┐ │
│ │ [prod ✕] [web ✕] +              │ │
│ └─────────────────────────────────┘ │
│                                     │
│        [ Cancelar ]   [ Salvar ]    │
└─────────────────────────────────────┘
```

### 🪟 Modais e drawers

**Modal central**: para confirmações, formulários curtos, detalhes expandidos.

**Drawer lateral** (slide da direita, 480px de largura): para edição de itens em listas, sem perder contexto da lista.

**Bottom sheet** (mobile): substitui modais em telas pequenas.

Sempre incluem botão de fechar, fecham com `Esc`, e travam scroll do fundo quando abertos.

### 📊 Gráficos

Tipos usados na plataforma:

1. **Linha temporal**: eventos por minuto/hora/dia
2. **Área empilhada**: eventos por severidade ao longo do tempo
3. **Heatmap**: atividade por hora do dia × dia da semana
4. **Treemap**: distribuição de eventos por host
5. **Mapa-múndi**: origem geográfica de IPs
6. **Donut**: proporção de status (online/offline)
7. **Sparkline**: tendência inline em cards
8. **Gauge**: utilização de recursos (CPU, disco)

**Lib**: Recharts para a maioria, ECharts para mapa e heatmaps complexos.

**Cores em gráficos**: paleta extendida pensada para ser **distinguível por daltônicos** (usar [Color Brewer](https://colorbrewer2.org) palettes seguras).

### 🏷️ Tags e chips

Pequenas pílulas para representar categorias, status, filtros aplicados. Removíveis com `[x]`.

```
[prod ✕]  [web-server ✕]  [crítico ✕]
```

---

## Telas detalhadas

### 1. 🔐 Tela de Login

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                                                          │
│                                                          │
│                       🛡️                                 │
│                  SentinelBR                              │
│         Plataforma de segurança open-source              │
│                                                          │
│         ┌──────────────────────────────┐                 │
│         │ E-mail ou usuário            │                 │
│         │ ┌──────────────────────────┐ │                 │
│         │ │                          │ │                 │
│         │ └──────────────────────────┘ │                 │
│         │                              │                 │
│         │ Senha                        │                 │
│         │ ┌──────────────────────────┐ │                 │
│         │ │ ●●●●●●●●           👁️    │ │                 │
│         │ └──────────────────────────┘ │                 │
│         │                              │                 │
│         │ ☐ Lembrar deste dispositivo │                 │
│         │                              │                 │
│         │ [████████ Entrar ████████]   │                 │
│         │                              │                 │
│         │ ─────── ou ───────           │                 │
│         │                              │                 │
│         │ [ Entrar com SSO ]           │                 │
│         │                              │                 │
│         │ Esqueci minha senha          │                 │
│         └──────────────────────────────┘                 │
│                                                          │
│              v1.0.0 · docs · github                      │
└──────────────────────────────────────────────────────────┘
```

**Detalhes:**

- Background: gradiente sutil radial do centro (`bg-base` → ligeiramente mais escuro nas bordas)
- Logo animado (pulso lento na cor brand)
- Form com validação em tempo real
- Após enviar, mostra spinner + mensagem "Verificando credenciais..."
- Se 2FA habilitado, segunda tela pede código TOTP (com timer visual de validade)
- Erros não revelam se usuário existe (mensagem genérica "Credenciais inválidas")
- Footer mostra versão (link para changelog), docs e GitHub

### 2. 🏠 Dashboard Principal

A tela mais importante: visão consolidada da segurança.

```
┌──────────────────────────────────────────────────────────────┐
│ Dashboard                                  [Últimas 24h ▼]   │
├──────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐             │
│ │EVENTOS  │ │ALERTAS  │ │HOSTS    │ │ATAQUES  │             │
│ │         │ │ABERTOS  │ │ONLINE   │ │BLOQUEAD │             │
│ │ 12.483  │ │   7     │ │ 12 / 12 │ │  243    │             │
│ │ ▁▂▃▅▇   │ │ 2 alta  │ │ 100%    │ │ 🇨🇳45 🇷🇺22│            │
│ │ ↑ 8%    │ │ 5 média │ │  ✓ OK   │ │ ↑ 12%   │             │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘             │
│                                                              │
│ ┌──────────────────────────────────┐ ┌─────────────────────┐│
│ │ EVENTOS POR HORA                 │ │ TOP 10 IPs          ││
│ │                                  │ │                     ││
│ │     ▁▂▃▅▇▆▅▃▂▁▂▃▄▅▆▇▆▅▄▃▂▁    │ │ 203.0.113.42  823  ⨯││
│ │     ▁▂▃▄▅▆▇▆▅▄▃▂▁▂▃▄▅▆▇▆▅▄    │ │ 198.51.100.7  455  ⨯││
│ │  00:00              12:00       │ │ 192.0.2.155   312  ⨯││
│ │  ──── ssh ──── http ──── audit  │ │ ...                 ││
│ └──────────────────────────────────┘ └─────────────────────┘│
│                                                              │
│ ┌──────────────────────────────────┐ ┌─────────────────────┐│
│ │ MAPA-MÚNDI DE ORIGEM             │ │ ALERTAS RECENTES    ││
│ │                                  │ │                     ││
│ │       🌍 [mapa interativo]       │ │ 🔴 Brute force SSH  ││
│ │                                  │ │    web-01 · 14:23   ││
│ │  ● Brasil    8.234              │ │                     ││
│ │  ● EUA       1.122              │ │ 🟡 Disco 85%        ││
│ │  ● China       823              │ │    db-01 · 13:45    ││
│ │  ● Rússia      455              │ │                     ││
│ │                                  │ │ Ver todos →         ││
│ └──────────────────────────────────┘ └─────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

**Detalhes:**

- **Período configurável** no canto superior direito: 1h, 24h, 7d, 30d, custom
- **Auto-refresh** a cada 30s (configurável; ou desligável com toggle "pausar")
- **Cards clicáveis** levam à tela detalhada do indicador
- **Mapa interativo**: zoom, hover mostra país + contagem, clique filtra
- **Alertas recentes**: clique abre drawer com detalhes
- **Customização**: usuário pode reordenar widgets via drag-and-drop (estado salvo)
- **Modo apresentação** (`F11`): tela cheia, sem distrações, ideal para telão de SOC

### 3. 🖥️ Lista de Hosts

```
┌──────────────────────────────────────────────────────────────┐
│ Hosts                              [+ Adicionar host]        │
│ Busca: [____________]   Status: [Todos ▼]   Tag: [Todas ▼]  │
├──────────────────────────────────────────────────────────────┤
│  Host           IP          Status   Últ. evento  Alertas  ⚙│
├──────────────────────────────────────────────────────────────┤
│ ●web-01.prod   10.0.1.5    ● online  agora       🔴 2     ›│
│ ●db-01.prod    10.0.1.10   ● online  3min        🟡 1     ›│
│ ●bastion.prod  10.0.1.1    ● online  agora       —        ›│
│ ●worker-01     10.0.2.5    ● online  1min        —        ›│
│ ●worker-02     10.0.2.6    ⚠ slow    15min       🟡 1     ›│
│ ●monitor-01    10.0.1.20   ✗ offline 1h          —        ›│
└──────────────────────────────────────────────────────────────┘

Detalhes ao clicar (drawer lateral):
┌────────────────────────────────────┐
│ ✕                       web-01.prod│
├────────────────────────────────────┤
│ INFORMAÇÕES                        │
│   Hostname: web-01.prod            │
│   IP: 10.0.1.5                     │
│   OS: Ubuntu 22.04 LTS             │
│   Agente: v1.0.3 (atualizado)      │
│   Tags: prod, web, critical        │
│   Localização: AWS sa-east-1       │
│                                    │
│ MÉTRICAS (últimos 60min)           │
│   Eventos: 1.234                   │
│   Alertas: 2 (1 crítico)           │
│   CPU: ▁▂▃▅ 45%                   │
│   Memória: ▃▄▅▆ 67%                │
│   Disco /: ███░ 78%               │
│                                    │
│ AÇÕES RÁPIDAS                      │
│   [ Ver eventos ]                  │
│   [ Ver alertas ]                  │
│   [ Coletar forense ]              │
│   [ Isolar host ⚠️ ]                │
└────────────────────────────────────┘
```

**Detalhes:**

- **Indicador de status** colorido (bolinha à esquerda) com tooltip
- **Tooltip de IP** mostra geolocalização e ASN
- **Coluna de alertas** com badges coloridos clicáveis
- **Menu de contexto** (3 pontinhos) com ações: editar, remover, isolar, etc.
- **Bulk actions**: selecionar múltiplos com checkboxes para aplicar tag, remover, etc.
- **Filtros avançados**: por tag, OS, versão de agente, status

### 4. 📊 Tela de Eventos (busca avançada)

```
┌──────────────────────────────────────────────────────────────┐
│ Eventos                                  [Salvar busca ▼]    │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 🔍 host:"web-01" AND severity:high AND tag:ssh          ││
│ │                                              [Buscar]    ││
│ └──────────────────────────────────────────────────────────┘│
│ Filtros: [✕ severity:high]  [✕ host:web-01]  + Adicionar    │
│                                                              │
├──────────┬───────────────────────────────────────────────────┤
│ FILTROS  │  EVENTOS (1.234 encontrados)         [Exportar ▼]│
│          │ ┌───────────────────────────────────────────────┐ │
│ ▾ Tempo  │ │ 14:23:45.123  web-01    🔴 high              │ │
│  [24h ▼] │ │ ssh: Failed password for root from           │ │
│          │ │ 203.0.113.42 port 38241 ssh2                 │ │
│ ▾ Host   │ │ ▶ Expandir detalhes                          │ │
│  ☑ web-01│ ├───────────────────────────────────────────────┤ │
│  ☐ db-01 │ │ 14:23:38.502  web-01    🔴 high              │ │
│  ☐ bast.. │ │ ssh: Failed password for root from           │ │
│          │ │ 203.0.113.42 port 38240 ssh2                 │ │
│ ▾ Sever. │ │ ...                                           │ │
│  ☑ alta  │ └───────────────────────────────────────────────┘ │
│  ☐ média │                                                   │
│  ☐ baixa │  [‹ Anterior] Página 1 de 25 [Próxima ›]         │
│          │                                                   │
│ ▾ Tag    │  [Auto-refresh: ●ON]    Mostrar: [50 ▼] por pág  │
│  ☑ ssh   │                                                   │
│  ☐ http  │                                                   │
│          │                                                   │
└──────────┴───────────────────────────────────────────────────┘
```

**Detalhes:**

- **Linguagem de query Lucene-like**: campos, operadores (AND, OR, NOT), wildcards, ranges
- **Autocomplete inteligente** sugere campos disponíveis enquanto digita
- **Histórico de buscas** acessível por seta para baixo
- **Buscas salvas** com nome (compartilháveis com a equipe)
- **Auto-refresh** controlável (ON/OFF, intervalo)
- **Expansão de evento** mostra JSON cru + campos extraídos + eventos relacionados
- **Linha expandida**:
  ```
  ┌───────────────────────────────────────────────────┐
  │ Detalhes do evento                                │
  │                                                   │
  │ Timestamp: 2026-05-09 14:23:45.123 BRT            │
  │ Host:      web-01.prod (10.0.1.5)                 │
  │ Source IP: 203.0.113.42 (🇨🇳 China · ChinaNet)    │
  │ User:      root                                   │
  │ Process:   sshd[12345]                            │
  │                                                   │
  │ Mensagem original:                                │
  │ ┌─────────────────────────────────────────────┐  │
  │ │ Failed password for root from 203.0.113.42  │  │
  │ │ port 38241 ssh2                             │  │
  │ └─────────────────────────────────────────────┘  │
  │                                                   │
  │ Regras que dispararam:                            │
  │   • Brute Force SSH (alta severidade)             │
  │                                                   │
  │ Eventos correlacionados (32 nas últimas 5min):    │
  │   [Ver timeline →]                                │
  │                                                   │
  │ AÇÕES                                             │
  │ [Bloquear IP] [Criar regra] [Marcar como falso]   │
  └───────────────────────────────────────────────────┘
  ```

### 5. 🚨 Tela de Alertas

```
┌──────────────────────────────────────────────────────────────┐
│ Alertas                                                      │
│ [Abertos (7)] [Investigando (2)] [Fechados] [Todos]         │
├──────────────────────────────────────────────────────────────┤
│ ☐ │ Severidade │ Título               │ Host    │ Idade  │ ⋯│
├───┼────────────┼──────────────────────┼─────────┼────────┼──┤
│ ☐ │ 🔴 alta    │ Brute force SSH      │ web-01  │ 12min  │ ⋯│
│ ☐ │ 🔴 alta    │ Possível ransomware  │ db-01   │ 23min  │ ⋯│
│ ☐ │ 🟡 média   │ Login fora horário   │ web-01  │ 1h     │ ⋯│
│ ☐ │ 🟡 média   │ Disco em 85%         │ db-01   │ 2h     │ ⋯│
│ ☐ │ 🟡 média   │ Falha conexão MySQL  │ web-01  │ 3h     │ ⋯│
│ ☐ │ 🟢 baixa   │ Cert expira em 14d   │ web-01  │ 6h     │ ⋯│
│ ☐ │ 🟢 baixa   │ Backup atrasado      │ db-01   │ 8h     │ ⋯│
└──────────────────────────────────────────────────────────────┘

Detalhe do alerta (clique abre drawer):
┌────────────────────────────────────────────┐
│ ✕                  Brute force SSH em web-01│
├────────────────────────────────────────────┤
│ 🔴 ALTA SEVERIDADE                         │
│ Aberto há 12 minutos                       │
│                                            │
│ DESCRIÇÃO                                  │
│ Detectadas 47 tentativas de login falhas   │
│ no SSH do host web-01.prod a partir do     │
│ IP 203.0.113.42 nos últimos 60 segundos.   │
│                                            │
│ DETALHES                                   │
│ • Origem: 203.0.113.42 (🇨🇳 China)        │
│ • Usuários alvo: root, admin, ubuntu       │
│ • Regra disparada: ssh_brute_force_v2      │
│ • MITRE ATT&CK: T1110.001                  │
│                                            │
│ AÇÕES TOMADAS AUTOMATICAMENTE              │
│ ✓ IP bloqueado no firewall (1h)            │
│ ✓ Notificação enviada ao Telegram          │
│ ⏳ Aguardando aprovação: coleta forense    │
│   [Aprovar] [Rejeitar]                     │
│                                            │
│ TIMELINE                                   │
│ 14:23 ⚠ Primeira tentativa detectada       │
│ 14:23 🔴 Limite excedido, regra disparada  │
│ 14:23 🛡️ IP bloqueado automaticamente       │
│ 14:24 📩 Notificação enviada               │
│                                            │
│ COMENTÁRIOS                                │
│ ┌────────────────────────────────────────┐ │
│ │ Adicionar nota...                      │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ AÇÕES                                      │
│ [Investigar] [Marcar resolvido] [Falso +] │
└────────────────────────────────────────────┘
```

### 6. 📜 Tela de Regras (Sigma)

Lista de regras de detecção carregadas, com possibilidade de criar/editar.

```
┌──────────────────────────────────────────────────────────────┐
│ Regras de Detecção                  [+ Nova regra] [Importar]│
│ Busca: [____]  Status: [Todas ▼]  Categoria: [Todas ▼]      │
├──────────────────────────────────────────────────────────────┤
│ ✓│ Nome                  │ Categoria  │ Disparos │ Última  │⋯│
├──┼───────────────────────┼────────────┼──────────┼─────────┼─┤
│ ●│ Brute Force SSH       │ Auth       │ 234      │ 2min    │⋯│
│ ●│ Privilege Escalation  │ Privilege  │ 12       │ 1h      │⋯│
│ ●│ Suspicious Outbound   │ Network    │ 5        │ 6h      │⋯│
│ ○│ DNS Tunneling         │ Network    │ 0        │ nunca   │⋯│
└──────────────────────────────────────────────────────────────┘

Editor de regra (página própria):
┌──────────────────────────────────────────────────────────────┐
│ Editor de Regra: Brute Force SSH         [Salvar] [Testar]   │
├─────────────────────────────────┬────────────────────────────┤
│ EDITOR YAML                     │ PRÉVIA                     │
│ ┌─────────────────────────────┐ │                            │
│ │ title: Brute Force SSH      │ │ Esta regra dispara quando: │
│ │ description: ...            │ │                            │
│ │ status: stable              │ │ • É um evento de SSH       │
│ │ logsource:                  │ │ • Tipo: falha de login     │
│ │   product: linux            │ │ • Mais de 5 ocorrências    │
│ │   service: sshd             │ │   em 60 segundos           │
│ │ detection:                  │ │ • Mesmo IP de origem       │
│ │   selection:                │ │                            │
│ │     event_type: failed_auth │ │ Severidade: ALTA           │
│ │   timeframe: 60s            │ │ MITRE: T1110.001           │
│ │   condition: count() > 5    │ │                            │
│ │ falsepositives:             │ │ TESTE COM DADOS REAIS      │
│ │   - Legitimate users        │ │ ┌────────────────────────┐ │
│ │ level: high                 │ │ │ Últimos 7 dias:        │ │
│ │ tags:                       │ │ │ • 47 disparos          │ │
│ │   - attack.t1110.001        │ │ │ • 0 marcados como FP   │ │
│ └─────────────────────────────┘ │ │ • Cobertura: 12 hosts  │ │
│                                 │ └────────────────────────┘ │
│ ✓ YAML válido                   │                            │
│ ✓ Sigma compatível              │ [Visualizar disparos →]    │
└─────────────────────────────────┴────────────────────────────┘
```

### 7. 🛡️ Tela do Firewall

```
┌──────────────────────────────────────────────────────────────┐
│ Firewall                                                     │
│ [Regras] [Templates] [IPs Bloqueados] [Geo] [Histórico]     │
├──────────────────────────────────────────────────────────────┤
│ Host: [web-01.prod ▼]   Backend: nftables   [Aplicar via ▼]│
│                                                              │
│        [ + Nova regra ]  [Importar template]  [Snapshot]    │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ INPUT (chain)                                           │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │  #│ Ação  │ Proto│ Origem      │ Porta │ Comentário  ⋮ │ │
│ │  1│ ✓ ACC │ tcp  │ qualquer    │ 443   │ HTTPS público│ │
│ │  2│ ✓ ACC │ tcp  │ qualquer    │ 80    │ HTTP público │ │
│ │  3│ ✓ ACC │ tcp  │ 10.0.0.0/8  │ 22    │ SSH interno  │ │
│ │  4│ ✗ DROP│ tcp  │ @blacklist  │ qual. │ Bloqueio din │ │
│ │  5│ ✗ DROP│ qual.│ qualquer    │ qual. │ Padrão       │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─ Resumo ────────────────────────────────────────────────┐ │
│ │ Total de regras: 5    Última mudança: há 2 dias         │ │
│ │ IPs em blacklist dinâmica: 23 (limite: 1.000)           │ │
│ │ [Ver histórico] [Exportar regras] [Validar configuração]│ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

Modal de criação/edição de regra:
┌──────────────────────────────────────────────────┐
│ ✕                                Nova regra      │
├──────────────────────────────────────────────────┤
│ Chain                                            │
│ ( ) INPUT  ( ) OUTPUT  ( ) FORWARD              │
│                                                  │
│ Ação                                             │
│ [✓ ACCEPT] [✗ DROP] [↩ REJECT]                  │
│                                                  │
│ Protocolo                                        │
│ [TCP ▼]                                          │
│                                                  │
│ Origem                                           │
│ ( ) Qualquer                                     │
│ ( ) IP específico  [_______________]             │
│ ( ) Rede CIDR      [10.0.0.0/8____]              │
│ ( ) Conjunto       [@trusted ▼]                  │
│                                                  │
│ Porta de destino                                 │
│ [22________________]                             │
│                                                  │
│ Comentário                                       │
│ [SSH para rede interna_______________________]   │
│                                                  │
│ ┌──── Pré-visualização do comando ────────────┐  │
│ │ nft add rule inet filter input \            │  │
│ │   ip saddr 10.0.0.0/8 tcp dport 22 \        │  │
│ │   accept comment "SSH para rede interna"    │  │
│ └─────────────────────────────────────────────┘  │
│                                                  │
│  [ Cancelar ]              [ Aplicar regra ]    │
└──────────────────────────────────────────────────┘
```

### 8. 🔒 Tela do SELinux

```
┌──────────────────────────────────────────────────────────────┐
│ SELinux                                                      │
│ [Status] [Denials] [Booleanos] [Contextos] [Policies]       │
├──────────────────────────────────────────────────────────────┤
│ STATUS GERAL                                                 │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ HOST          MODO         POLICY     DENIALS (24h)     │ │
│ ├─────────────────────────────────────────────────────────┤ │
│ │ web-01.prod   🟢 enforcing  targeted   3                │ │
│ │ db-01.prod    🟡 permissive targeted   12 ⚠            │ │
│ │ bastion.prod  🟢 enforcing  targeted   0                │ │
│ │ monitor-01    🔴 disabled   —          —  ⚠            │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ ┌─ Atenção ───────────────────────────────────────────────┐ │
│ │ ⚠ monitor-01 está com SELinux desabilitado.             │ │
│ │   Recomendação: ativar em modo permissive primeiro.     │ │
│ │   [Ativar permissive] [Ver guia]                        │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

Aba "Denials":
┌──────────────────────────────────────────────────────────────┐
│ Bloqueios SELinux nas últimas 24h                            │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🔴 Apache não consegue ler /srv/myapp/config.json    × 5│ │
│ │                                                         │ │
│ │ EXPLICAÇÃO                                              │ │
│ │ O servidor web Apache (httpd_t) tentou ler um arquivo   │ │
│ │ que está com contexto incorreto (default_t). Isso       │ │
│ │ geralmente acontece quando arquivos foram movidos ou    │ │
│ │ criados manualmente fora do diretório padrão.           │ │
│ │                                                         │ │
│ │ SUGESTÃO                                                │ │
│ │ Aplicar o contexto correto:                             │ │
│ │ ┌────────────────────────────────────────────────────┐  │ │
│ │ │ semanage fcontext -a -t httpd_sys_content_t \      │  │ │
│ │ │   "/srv/myapp(/.*)?"                               │  │ │
│ │ │ restorecon -Rv /srv/myapp                          │  │ │
│ │ └────────────────────────────────────────────────────┘  │ │
│ │                                                         │ │
│ │ [Aplicar correção] [Ignorar] [Criar policy customizada] │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

Aba "Booleanos":
┌──────────────────────────────────────────────────────────────┐
│ Booleanos SELinux                       Busca: [______]      │
│ Categoria: [Todos ▼]                                         │
├──────────────────────────────────────────────────────────────┤
│ Nome                          Estado    Risco   Descrição   │
├──────────────────────────────────────────────────────────────┤
│ httpd_can_network_connect    [ ●  ] ON  🟡 médio Permite que │
│                                                  Apache faça │
│                                                  conexões... │
│ httpd_enable_cgi             [ ○  ] OFF 🟢 baixo Habilita... │
│ httpd_unified                [ ●  ] ON  🟢 baixo ...         │
└──────────────────────────────────────────────────────────────┘
```

### 9. ⚡ Tela de Playbooks

```
┌──────────────────────────────────────────────────────────────┐
│ Playbooks                          [+ Novo playbook] [Galeria]│
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│ │🛡️ Brute Force│ │💀 Ransomware │ │📤 Vazamento │           │
│ │              │ │              │ │              │           │
│ │ 234 disparos │ │ 0 disparos   │ │ 2 disparos   │           │
│ │ MTTR: 8s     │ │ MTTR: —      │ │ MTTR: 45s    │           │
│ │              │ │              │ │              │           │
│ │ ●ATIVO       │ │ ●ATIVO       │ │ ⏸ PAUSADO   │           │
│ │              │ │              │ │              │           │
│ │ [Ver] [⋮]    │ │ [Ver] [⋮]    │ │ [Ver] [⋮]    │           │
│ └──────────────┘ └──────────────┘ └──────────────┘           │
└──────────────────────────────────────────────────────────────┘

Editor visual de playbook (drag-and-drop):
┌──────────────────────────────────────────────────────────────┐
│ Brute Force SSH                          [Salvar] [Testar]   │
├──────┬───────────────────────────────────────────────────────┤
│BLOCOS│   ┌─────────────────────────┐                         │
│      │   │ ⚡ TRIGGER              │                         │
│Trig  │   │ Regra: ssh_brute_force  │                         │
│●Regr │   └────────────┬────────────┘                         │
│●Manu │                │                                      │
│      │   ┌────────────▼────────────┐                         │
│Ações │   │ 🛡️ AÇÃO                 │                         │
│●Bloq │   │ firewall.block_ip       │                         │
│●Mata │   │ ip: {{ event.src.ip }}  │                         │
│●Isol │   │ duration: 3600          │                         │
│●Notif│   └────────────┬────────────┘                         │
│      │                │                                      │
│Lógica│   ┌────────────▼────────────┐                         │
│●If   │   │ 📩 NOTIFICAÇÃO          │                         │
│●Loop │   │ telegram                │                         │
│●Aprv │   │ msg: "IP {{ip}} blq..." │                         │
│      │   └────────────┬────────────┘                         │
│      │                │                                      │
│      │   ┌────────────▼────────────┐                         │
│      │   │ ⏸️ APROVAÇÃO HUMANA      │                         │
│      │   │ Coletar evidências?     │                         │
│      │   │ Timeout: 30min          │                         │
│      │   └────────────┬────────────┘                         │
│      │                │                                      │
│      │   ┌────────────▼────────────┐                         │
│      │   │ 📦 COLETA FORENSE       │                         │
│      │   │ host: {{ event.host }}  │                         │
│      │   └─────────────────────────┘                         │
└──────┴───────────────────────────────────────────────────────┘
```

### 10. ⚖️ Tela de LGPD

```
┌──────────────────────────────────────────────────────────────┐
│ LGPD - Privacidade e Conformidade                            │
│ [Dashboard] [Ativos] [Tratamentos] [Incidentes] [Titulares] │
├──────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐ ┌──────────────────┐ ┌────────────────┐ │
│ │ ATIVOS           │ │ COBERTURA        │ │ INCIDENTES     │ │
│ │ MAPEADOS         │ │ DE BASE LEGAL    │ │ ATIVOS         │ │
│ │     34           │ │     89%          │ │     0          │ │
│ │ +3 este mês      │ │ ↑ desde 75%      │ │ ✓ Tudo OK      │ │
│ └──────────────────┘ └──────────────────┘ └────────────────┘ │
│                                                              │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ MAPA DE FLUXO DE DADOS                                   │ │
│ │                                                          │ │
│ │  [Site] ──→ [API] ──→ [DB Clientes] ──→ [Backups S3]     │ │
│ │              │                                           │ │
│ │              ↓                                           │ │
│ │         [Email Mkt]                                      │ │
│ │                                                          │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ PRÓXIMAS AÇÕES                                               │
│ • [Pendente] Definir base legal de 4 ativos                  │
│ • [Pendente] Revisar retenção de "logs_acesso"               │
│ • [Vencendo] Atualizar RIPD em 15 dias                       │
└──────────────────────────────────────────────────────────────┘

Cadastro de ativo sensível:
┌──────────────────────────────────────────────────┐
│ Cadastrar ativo com dados pessoais               │
├──────────────────────────────────────────────────┤
│ Nome do ativo *                                  │
│ [Banco de dados de clientes_____________]        │
│                                                  │
│ Tipo *                                           │
│ ( ) Arquivo/diretório                            │
│ (●) Tabela de banco de dados                     │
│ ( ) Endpoint de API                              │
│ ( ) Bucket de storage                            │
│                                                  │
│ Localização *                                    │
│ Host: [db-01.prod ▼]                             │
│ Caminho: [postgres://prod_db.customers]          │
│                                                  │
│ Categoria de dados *                             │
│ ☑ Pessoal (nome, email, etc.)                   │
│ ☐ Sensível (saúde, religião, etc.)              │
│ ☐ Criança/adolescente                           │
│                                                  │
│ Base legal *                                     │
│ ( ) Consentimento                                │
│ (●) Execução de contrato                         │
│ ( ) Legítimo interesse                           │
│ ( ) Cumprimento de obrigação legal               │
│                                                  │
│ Finalidade *                                     │
│ [Cadastro de clientes para...___________]        │
│                                                  │
│ Período de retenção                              │
│ [5 anos____] após fim do contrato                │
│                                                  │
│ Responsável (DPO)                                │
│ [Maria Silva ▼]                                  │
│                                                  │
│ ☑ Ativar auditoria automática (auditd)          │
│                                                  │
│  [ Cancelar ]              [ Cadastrar ativo ]   │
└──────────────────────────────────────────────────┘
```

### 11. ⚙️ Configurações

Estrutura de abas verticais:

```
┌─────────────────────┬────────────────────────────────────────┐
│ Configurações       │ NOTIFICAÇÕES                           │
│                     │                                        │
│ ▸ Geral             │ Canais ativos:                         │
│ ▸ Notificações  ●   │                                        │
│ ▸ Integrações       │ ┌────────────────────────────────────┐ │
│ ▸ Coleta de logs    │ │ 📱 TELEGRAM                  ●ON │ │
│ ▸ Retenção          │ │ Bot: @sentinelbr_alert_bot         │ │
│ ▸ API Tokens        │ │ Canal: -1001234567890              │ │
│ ▸ Backup            │ │ [Editar] [Testar] [Remover]        │ │
│                     │ └────────────────────────────────────┘ │
│                     │                                        │
│                     │ ┌────────────────────────────────────┐ │
│                     │ │ 💬 SLACK                     ●ON │ │
│                     │ │ Workspace: empresa.slack.com       │ │
│                     │ │ Canal: #security-alerts            │ │
│                     │ └────────────────────────────────────┘ │
│                     │                                        │
│                     │ [+ Adicionar canal]                    │
│                     │                                        │
│                     │ Roteamento por severidade:             │
│                     │   🔴 Crítica → Telegram, Slack, Email  │
│                     │   🟠 Alta    → Telegram, Slack         │
│                     │   🟡 Média   → Slack                   │
│                     │   🟢 Baixa   → Email (digest diário)   │
│                     │                                        │
│                     │ Silent hours: [22:00 - 06:00]         │
│                     │ (não notifica baixas neste período)    │
└─────────────────────┴────────────────────────────────────────┘
```

### 12. 🚀 Wizard de Onboarding

Apresentado no primeiro login após instalação:

```
Passo 1 de 5
┌──────────────────────────────────────────────────────────────┐
│ ●━━━○━━━○━━━○━━━○                                            │
│                                                              │
│             Bem-vindo ao SentinelBR! 🛡️                     │
│                                                              │
│   Vamos configurar sua plataforma em 5 passos rápidos.       │
│   Tempo estimado: 5 minutos.                                 │
│                                                              │
│   Você vai:                                                  │
│   ✓ Criar sua conta de administrador                         │
│   ✓ Adicionar seu primeiro servidor                          │
│   ✓ Aplicar configurações de segurança                       │
│   ✓ Configurar onde receber alertas                          │
│                                                              │
│                                       [ Começar ]            │
└──────────────────────────────────────────────────────────────┘

Passo 2 de 5: Adicionar primeiro host
┌──────────────────────────────────────────────────────────────┐
│ ●━━━●━━━○━━━○━━━○                                            │
│                                                              │
│ Vamos adicionar o primeiro servidor para monitorar.          │
│                                                              │
│ Você precisa rodar este comando no servidor:                 │
│                                                              │
│ ┌────────────────────────────────────────────────────────┐   │
│ │ curl -fsSL https://sentinelbr.io/install.sh | \        │   │
│ │   sudo bash -s -- --token=abc123def456 \               │   │
│ │   --server=https://sua-instancia.exemplo.com           │   │
│ │                                                  [📋]  │   │
│ └────────────────────────────────────────────────────────┘   │
│                                                              │
│ Aguardando agente conectar... ⏳                             │
│                                                              │
│ Não tem servidor agora? [Pular esta etapa]                   │
│                                                              │
│ [ ‹ Voltar ]                              [ Próximo › ]      │
└──────────────────────────────────────────────────────────────┘
```

---

## Estados e feedback

### ⏳ Loading states

- **Skeleton screens** para listas e cards (não spinners)
- **Spinners pequenos** apenas em botões durante ação
- **Progress bar superior** para mudanças de rota
- **"Carregando..."** com texto explicativo após 3 segundos

### 📭 Empty states

Quando tela não tem dados, sempre incluem:

1. **Ilustração** (linha simples, na cor da marca)
2. **Título** explicando o estado
3. **Descrição** de por que está vazio
4. **CTA principal** para resolver

Exemplo:

```
┌────────────────────────────────────────────┐
│                                            │
│            🛡️                              │
│                                            │
│      Nenhum host monitorado ainda          │
│                                            │
│   Para começar, instale o agente em        │
│   pelo menos um servidor.                  │
│                                            │
│       [ + Adicionar primeiro host ]        │
│                                            │
│       Ver documentação →                   │
│                                            │
└────────────────────────────────────────────┘
```

### ❌ Error states

```
┌────────────────────────────────────────────┐
│            ⚠️                              │
│   Não foi possível carregar os eventos     │
│                                            │
│   O servidor de logs (Loki) não está       │
│   respondendo. Tente novamente em alguns   │
│   instantes.                               │
│                                            │
│   Detalhes técnicos: connection timeout    │
│   após 30s.                                │
│                                            │
│   [ Tentar novamente ] [ Reportar bug ]    │
└────────────────────────────────────────────┘
```

### ✅ Success feedback

- **Toast notifications** no canto inferior direito
- **Cor verde** (success) com ícone ✓
- **Auto-dismiss** em 4 segundos
- **Texto curto e específico**: "Regra 'Brute Force SSH' criada com sucesso"
- **Ação reversível** quando aplicável: "[Desfazer]"

### ⚠️ Confirmações destrutivas

Para ações irreversíveis (deletar, desabilitar SELinux, etc.):

```
┌──────────────────────────────────────────────┐
│ ⚠️  Confirmar ação destrutiva                │
├──────────────────────────────────────────────┤
│ Você está prestes a remover a regra          │
│ "Brute Force SSH". Esta ação não pode        │
│ ser desfeita.                                │
│                                              │
│ A regra disparou 234 vezes e bloqueou        │
│ ataques nos últimos 30 dias.                 │
│                                              │
│ Para confirmar, digite o nome da regra:      │
│ ┌────────────────────────────────────────┐   │
│ │ ____________________________________   │   │
│ └────────────────────────────────────────┘   │
│                                              │
│  [ Cancelar ]              [ Remover ⚠️ ]    │
└──────────────────────────────────────────────┘
```

---

## Acessibilidade

### Critérios obrigatórios (WCAG 2.1 AA)

- **Contraste**: mínimo 4.5:1 para texto normal, 3:1 para texto grande
- **Navegação por teclado**: 100% das ações acessíveis sem mouse
- **Foco visível**: ring sólido de 2px na cor brand em qualquer elemento focado
- **Skip links**: "Pular para conteúdo principal" (visível ao tabular)
- **ARIA labels**: em ícones que são botões, em elementos interativos sem texto
- **Live regions**: anúncios para leitores de tela quando dados atualizam
- **Sem dependência de cor**: status sempre tem ícone + cor (nunca só cor)
- **Tamanho mínimo de touch target**: 44x44px em mobile
- **Suporte a redução de movimento**: respeita `prefers-reduced-motion`
- **Suporte a alto contraste**: tema dedicado disponível

### Atalhos de teclado

```
═══════════════════════════════════════════════════
NAVEGAÇÃO
═══════════════════════════════════════════════════
Cmd+K           Busca global
Cmd+B           Toggle sidebar
G + D           Ir para Dashboard
G + H           Ir para Hosts
G + E           Ir para Eventos
G + A           Ir para Alertas
?               Mostrar atalhos

═══════════════════════════════════════════════════
LISTAS E TABELAS
═══════════════════════════════════════════════════
J / K           Próxima / anterior linha
Enter           Abrir item
X               Selecionar/desselecionar linha
Cmd+A           Selecionar todos
/               Focar busca
Esc             Limpar seleção / fechar

═══════════════════════════════════════════════════
EM ALERTAS/EVENTOS
═══════════════════════════════════════════════════
A               Ack (reconhecer)
R               Resolver
F               Marcar como falso positivo
B               Bloquear IP relacionado
C               Adicionar comentário
```

---

## Responsividade

### Breakpoints

```
mobile      < 640px   ← celular vertical
tablet      640-1024  ← tablet, celular horizontal
laptop      1024-1280 ← laptops e desktops menores
desktop     1280-1536 ← desktop padrão
wide        > 1536    ← monitores grandes / SOC
```

### Adaptações por tamanho

**Mobile (<640px):**
- Sidebar vira drawer (escondida por padrão)
- Tabelas viram **cards empilhados** (cada linha = 1 card)
- Topbar simplificada (apenas logo + menu hambúrguer)
- Modais viram bottom sheets
- Gráficos com altura reduzida e legendas abaixo
- Filtros laterais viram sheet de baixo
- **Não suportado**: editor visual de playbooks, edição YAML longa (UI sugere abrir no desktop)

**Tablet (640-1024px):**
- Sidebar colapsada por padrão (apenas ícones)
- Tabelas com colunas críticas apenas (resto em "ver mais")
- Layout de 2 colunas no dashboard

**Desktop+ (>1024px):**
- Layout completo conforme especificado
- Sidebar expandida por padrão
- Todas as features disponíveis

**SOC mode (>1920px ou tela cheia):**
- Modo apresentação para telão
- Cards maiores
- Auto-refresh mais agressivo
- Sem distrações (sidebar oculta)

---

## Microinterações e animações

### Princípios

- **Rápidas** (150-250ms para a maioria)
- **Com easing natural** (`cubic-bezier(0.4, 0, 0.2, 1)` para entrada, mais agressivo para saída)
- **Funcionais** (sempre comunicam algo, nunca decoração)
- **Reduzíveis** via `prefers-reduced-motion`

### Catálogo

- **Hover em card**: leve elevação (translateY -2px) + sombra
- **Click em botão**: scale(0.98) por 100ms (feedback tátil)
- **Toast aparecendo**: slide da direita + fade in
- **Modal abrindo**: fade no overlay + scale 0.95→1 no conteúdo
- **Lista atualizando**: novo item entra com fade verde sutil
- **Loading skeleton**: shimmer horizontal lento
- **Status mudando**: cor transiciona suavemente (não pisca)
- **Sidebar colapsando**: largura anima 200ms
- **Drawer abrindo**: slide da direita 250ms
- **Página mudando**: fade out + fade in (100ms cada)

### Anti-padrões a evitar

- ❌ Animações longas (>500ms)
- ❌ Bouncing/spring em elementos sérios (ferramenta de segurança)
- ❌ Auto-play de vídeo/som
- ❌ Parallax (atrapalha em tela densa)
- ❌ Hover dependente para revelar ação crítica

---

## Fluxos de usuário

### Fluxo 1: Investigar um alerta

```
1. Notificação Telegram chega no celular do operador
2. Operador abre SentinelBR no navegador
3. Sidebar mostra badge "Alertas (1)"
4. Click em "Alertas" → lista com novo alerta no topo
5. Click no alerta → drawer com detalhes abre
6. Operador clica em "Ver eventos relacionados"
7. Tela de eventos abre com filtro pré-aplicado
8. Operador identifica padrão, volta ao alerta
9. Click em "Bloquear IP" → ação executada
10. Click em "Marcar resolvido" → adiciona nota
11. Toast confirma ação. Alerta sai da lista de "abertos"
```

### Fluxo 2: Adicionar host novo

```
1. Hosts → "+ Adicionar host"
2. Modal pede: nome, descrição, tags
3. Após confirmar, mostra comando de instalação
4. Comando é copiável com 1 clique
5. Tela exibe "Aguardando primeira conexão..."
6. Operador roda comando no servidor
7. Em ~10s, tela atualiza automaticamente:
   "✓ Agente conectado!"
8. Sugere aplicar template de firewall
9. Wizard guia configuração inicial
```

### Fluxo 3: Responder pedido de titular LGPD

```
1. LGPD → Titulares → "+ Novo pedido"
2. Formulário: nome do titular, e-mail, tipo de pedido
3. Plataforma faz busca cross-system pelos dados
4. Mostra mapa: "Encontrado em 3 sistemas: DB clientes, Email Mkt, Backup S3"
5. Operador revisa dados encontrados
6. Click em "Gerar pacote de portabilidade"
7. Plataforma gera ZIP com JSON estruturado
8. Operador envia ao titular via canal seguro
9. Ticket é fechado com timestamp e log de ação
```

---

## Stack técnica do frontend

### Core
- **React 18+** (com Suspense, Server Components opcional)
- **TypeScript estrito** (sem `any`, modo strict ativado)
- **Vite** (dev server e build)
- **TanStack Router** (file-based routing tipado)

### UI
- **Tailwind CSS** (estilização utilitária)
- **shadcn/ui** (componentes Radix + Tailwind, copiáveis e customizáveis)
- **Lucide React** (ícones)
- **Framer Motion** (animações complexas)

### Estado e dados
- **TanStack Query** (server state, cache, refetch)
- **Zustand** (client state simples — preferências, UI)
- **React Hook Form** + **Zod** (formulários com validação tipada)

### Visualização
- **Recharts** (gráficos padrão)
- **ECharts** (mapa-múndi, heatmaps)
- **TanStack Table** + **React Virtual** (tabelas grandes performáticas)
- **react-flow** (editor visual de playbooks)

### Realtime
- **WebSocket nativo** (com reconexão exponencial)
- **EventSource (SSE)** alternativa para alertas push

### Qualidade
- **Vitest** (unit tests)
- **Playwright** (e2e)
- **Storybook** (catálogo de componentes)
- **ESLint + Prettier** (lint e format)

### i18n
- **react-i18next** com PT-BR e EN-US

### Bundle
- **Code splitting** por rota
- **Lazy loading** de módulos pesados (mapas, editor de playbooks)
- **Bundle analyzer** no CI para evitar regressões
- **Target**: < 200KB gzipped no first load

---

## Por que essa interface impressiona no portfólio

A UI do SentinelBR é uma **vitrine de senioridade frontend**:

- **Não é mais um dashboard genérico**: é uma ferramenta especializada com decisões de domínio justificadas
- **Mostra design system real**: tokens, componentes, princípios — não Bootstrap colado
- **UX defensiva**: confirmações, undo, estados de erro úteis (recrutador percebe na hora)
- **Acessibilidade séria**: poucos projetos open-source levam a sério, isso destaca
- **Performance**: virtualização, code splitting, métricas — fala diretamente com sêniores
- **Pensamento em escala**: como a UI se comporta com 10k eventos? está respondido
- **Operação real em mente**: power user friendly (atalhos, busca global, modo apresentação)

Cada tela aqui é um **post de LinkedIn potencial**:

- "Como projetei uma tabela que escala para 10k+ linhas sem travar"
- "Por que dashboards de segurança devem ser dark-mode-first"
- "Acessibilidade em ferramentas técnicas: por que importa mesmo (e como faço)"
- "O command palette: como reduzi cliques médios em 60%"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
