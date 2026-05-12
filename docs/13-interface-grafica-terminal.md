# SentinelBR — Interface Gráfica Estilo Terminal

> Especificação completa da interface visual da plataforma. Combina a estética de terminal/hacker (fundo escuro, cores neon semânticas, mini-terminais embarcados) com padrões modernos de UX (acessibilidade, responsividade, atalhos de teclado). Substitui o documento `03-interface-grafica.md` anterior por uma versão alinhada à estética escolhida.

---

## 📋 Sumário

1. [Filosofia visual](#filosofia-visual)
2. [Inspirações de mercado](#inspirações-de-mercado)
3. [Paleta de cores completa](#paleta-de-cores-completa)
4. [Tipografia](#tipografia)
5. [Layout master](#layout-master)
6. [Componentes da topbar](#componentes-da-topbar)
7. [Componentes da sidebar](#componentes-da-sidebar)
8. [Área de conteúdo](#área-de-conteúdo)
9. [Mini-terminais embarcados](#mini-terminais-embarcados)
10. [Sistema de componentes](#sistema-de-componentes)
11. [Telas detalhadas](#telas-detalhadas)
12. [Estados e feedback](#estados-e-feedback)
13. [Microinterações e animações](#microinterações-e-animações)
14. [Atalhos de teclado](#atalhos-de-teclado)
15. [Responsividade](#responsividade)
16. [Acessibilidade](#acessibilidade)
17. [Stack técnica do frontend](#stack-técnica-do-frontend)
18. [Identidade sonora opcional](#identidade-sonora-opcional)

---

## Filosofia visual

A interface do SentinelBR carrega DNA de **terminal/cyber security tooling**, mas com **modernidade e usabilidade** de produtos contemporâneos como Linear, Vercel e Tailscale.

### Os 7 princípios visuais

#### 1. 🌑 Fundo escuro como ambiente padrão

Profissionais de segurança trabalham por horas, frequentemente à noite. Tela escura é **regra de saúde ocular**, não escolha estética. Modo claro existe como opção de acessibilidade, mas nunca é o default.

Importante: usamos **quase-preto com leve tom azul** (`#0A0E1A`), não preto puro (`#000000`). Em monitores LCD/IPS comuns, preto puro vira "buraco negro" desconfortável. O quase-preto mantém a estética terminal sem cansar.

#### 2. ⌨️ Estética terminal, mas legibilidade moderna

Tipografia híbrida:
- **Inter** (sans-serif moderna, otimizada para tela) para UI geral, formulários, botões, textos longos
- **JetBrains Mono** (monospaced com ligaduras) para logs, IPs, hashes, comandos, código, mini-terminais

Isso é o segredo: você **mantém a sensação terminal** nos elementos certos (logs, dados técnicos) e **garante legibilidade** nos elementos de UI tradicional. Tipografia mono em tudo cansa.

#### 3. 🎨 Cores semânticas com luminosidade controlada

Cores brilhantes (#FF0000) em fundo escuro causam halação (texto parece "sangrar"). Por isso, nossa paleta usa **versões dessaturadas e levemente mais escuras** das cores semânticas tradicionais.

#### 4. 🟢 Cinza claro como cor de texto principal

Texto principal em **`#C9D1D9`** (cinza claro com leve tom azul) em vez de branco puro. Diferença sutil mas crítica para conforto visual em sessões longas.

#### 5. 💻 Mini-terminais como elementos vivos

Quadros embarcados que mostram atividade em tempo real — sensação de ferramenta poderosa. Estética inspirada em htop, fzf, k9s. Não são REPLs completos (escopo), mas aceitam comandos curados via auto-complete.

#### 6. ⚡ Densidade informativa de power user

Operadores de SOC trabalham com muita informação simultânea. A interface prioriza **densidade** sobre espaço em branco generoso (estilo Notion). Mais perto de cockpit de avião do que de Pinterest.

#### 7. 🔒 Sem decoração inútil

Cada elemento existe por motivo funcional. Nada de animações decorativas, ícones desnecessários, gradientes "porque sim". Estética limpa, séria, profissional.

---

## Inspirações de mercado

Para alinhar expectativas, estes são produtos cuja estética e UX nos inspiram:

| Produto | O que pegamos | Link |
|---------|---------------|------|
| **Linear** | Sidebar elegante, command palette, cinza escuro polido | linear.app |
| **Wazuh Dashboard** | Densidade informativa de SIEM, cards de KPI | wazuh.com |
| **Vercel Dashboard** | Tipografia, espaçamento, sutileza visual | vercel.com |
| **Greynoise** | Tabelas densas, dados técnicos legíveis | greynoise.io |
| **Tailscale Admin** | Fundo escuro premium, terminais embarcados | tailscale.com |
| **GitHub Dark** | Paleta de cinzas, contraste para código | github.com |
| **k9s (CLI)** | Estética terminal como referência espiritual | k9scli.io |
| **htop / btop** | Visualização densa em "blocos terminal" | htop.dev |

### O que NÃO somos

- ❌ Bootstrap genérico
- ❌ Material Design padrão
- ❌ Excel-com-tema-escuro
- ❌ Hacker movie clichê (chuva de Matrix, fontes "GLITCH")
- ❌ Skeumorfismo (botões com sombra 3D, etc.)

---

## Paleta de cores completa

### Cores de fundo (backgrounds)

```
══════════════════════════════════════════════════════════════════
NÍVEL                  HEX        USO
══════════════════════════════════════════════════════════════════
bg-base              #0A0E1A     Fundo geral da aplicação
bg-surface           #131826     Cards, modais, painéis
bg-elevated          #1B2235     Hover de cards, dropdowns
bg-overlay           #0A0E1ACC   Overlay de modal (com blur 12px)
bg-terminal          #050810     Mini-terminais (mais escuro)
bg-input             #0F1421     Inputs, selects, textareas
bg-input-focus       #1A2138     Input focado
bg-active            #1F2942     Linha de tabela ativa/selecionada
```

### Texto

```
══════════════════════════════════════════════════════════════════
NÍVEL                  HEX        CONTRASTE       USO
══════════════════════════════════════════════════════════════════
text-primary         #C9D1D9     11.2:1 ✓ AAA   Texto principal (cinza claro)
text-secondary       #8B949E     6.8:1  ✓ AA    Labels, info menos importante
text-tertiary        #6E7681     4.7:1  ✓ AA    Placeholder, info terciária
text-muted           #484F58     2.8:1  borderline  Comentários, dicas
text-disabled        #30363D     1.6:1           Estados desabilitados
text-inverse         #0A0E1A                     Sobre fundos claros (botão primary)
```

### Bordas

```
══════════════════════════════════════════════════════════════════
border-subtle        #1F2638     Divisões sutis
border-default       #2A3349     Bordas padrão de cards/inputs
border-strong        #3D4865     Hover/focus em bordas
border-terminal      #00FF85     Borda de mini-terminal (verde neon sutil)
```

### Cores semânticas (status)

Versões dessaturadas para fundo escuro — não causam halação.

```
══════════════════════════════════════════════════════════════════
SEMÂNTICA            HEX         RGB                USO
══════════════════════════════════════════════════════════════════
critical             #F85149     248,81,73          Crítica (vermelho-tomate)
critical-bg          #F8514920   transparente 12%   Fundo de badge crítica
critical-border      #F85149     border             

danger               #FF6B6B     255,107,107        Alerta de perigo
warning              #F0B72F     240,183,47         Atenção (âmbar)
warning-bg           #F0B72F20

success              #3FB950     63,185,80          OK, online (verde)
success-bg           #3FB95020

info                 #58A6FF     88,166,255         Informativo (azul céu)
info-bg              #58A6FF20

medium               #FF9F43     amarelo alaranjado  Severidade média

low                  #6C757D     cinza azulado       Severidade baixa
```

### Cor da marca (brand)

```
══════════════════════════════════════════════════════════════════
brand-50             #E6FFF7     Tons muito claros (raros, em modo claro)
brand-100            #B3F5DC
brand-300            #4DDEAD
brand-500            #00D9A3     COR PRIMÁRIA (verde-água SentinelBR)
brand-600            #00B388     Hover de botão primary
brand-700            #008C6B     Active de botão primary
brand-900            #003D2E     Backgrounds com brand
```

### Cores especiais para terminal

Inspiradas em syntax highlighting e cores de terminal modernos.

```
══════════════════════════════════════════════════════════════════
PROPÓSITO            HEX         USO
══════════════════════════════════════════════════════════════════
terminal-prompt      #00FF85     Caractere de prompt ($, >)
terminal-command     #C9D1D9     Comando digitado
terminal-output      #8B949E     Saída padrão
terminal-string      #A5D6FF     Strings em logs ("ssh", "/var/log")
terminal-number      #79C0FF     Números (PIDs, portas, IPs)
terminal-keyword     #FF7B72     Keywords (Failed, Accepted, Error)
terminal-comment     #6E7681     Comentários
terminal-cursor      #00D9A3     Cursor piscando

selection-bg         #1F6FEB66   Texto selecionado (azul translúcido)
```

### Cor de severidade em logs (highlight automático)

```
log-info             #58A6FF
log-warning          #F0B72F
log-error            #F85149
log-critical         #FF6B6B (com background sutil)
log-success          #3FB950
log-debug            #6E7681
```

---

## Tipografia

### Famílias de fonte

```
══════════════════════════════════════════════════════════════════
NOME                 USO
══════════════════════════════════════════════════════════════════
Inter                UI geral (botões, formulários, parágrafos)
JetBrains Mono       Logs, IPs, hashes, comandos, código
SF Pro Display       Fallback macOS
Segoe UI             Fallback Windows
```

**Stack CSS completa:**

```css
--font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", 
             Roboto, Helvetica, Arial, sans-serif;
--font-mono: "JetBrains Mono", "Fira Code", "Consolas", 
             "Monaco", "Courier New", monospace;
```

### Por que essas fontes?

**Inter:**
- Otimizada para telas (não para impressão)
- Dígitos tabulares por default (números alinham em colunas — crítico para tabelas)
- Suporte completo a português brasileiro
- Excelente em pesos variados (300 a 900)
- Open-source, performática

**JetBrains Mono:**
- Ligaduras opcionais (`!=`, `=>`, `->`, `<=`)
- Distingue claramente: `0` (zero) vs `O`, `1` vs `l` vs `I`
- Altura de linha confortável
- Excelente para logs e código

### Escala tipográfica

```
══════════════════════════════════════════════════════════════════
NOME       SIZE      LINE-HEIGHT  WEIGHT  USO
══════════════════════════════════════════════════════════════════
display-1   48px      56px         700     Hero (raro)
display-2   36px      44px         700     Page title em tela cheia
h1          28px      36px         700     Título principal de tela
h2          22px      30px         600     Seção dentro de tela
h3          18px      26px         600     Subseção, card title
h4          16px      24px         600     Title de tabela, dialog
body        14px      22px         400     Texto padrão
body-sm     13px      20px         400     Texto secundário
caption     12px      18px         500     Labels, badges
mono-md     14px      22px         400     Logs, código inline (mono)
mono-sm     12px      18px         400     Métricas, IDs (mono)
mono-lg     16px      24px         400     Mini-terminais (mono, mais espaçado)
overline    11px      14px         600     Uppercase (CRÍTICO, ABERTO)
                                           letter-spacing: 0.08em
```

### Pesos tipográficos

```
300 - Light       (raro, decorativo)
400 - Regular     (texto padrão)
500 - Medium      (botões, links destacados)
600 - SemiBold    (headings menores)
700 - Bold        (headings grandes)
800 - ExtraBold   (display)
```

### Regras de uso

✅ **FAZER:**
- Inter para 90% da UI
- Mono para qualquer coisa que represente "dado de máquina" (IPs, IDs, hashes, paths, comandos)
- Manter escala (não criar tamanhos arbitrários)
- Letter-spacing levemente positivo em texto pequeno
- Uppercase apenas em overlines e badges

❌ **NÃO FAZER:**
- Mono para tudo (cansa em sessão longa)
- Tamanho menor que 12px em qualquer texto importante
- Negrito em texto secundário (perde hierarquia)
- Cursiva (raríssimo, só em citações literais)

---

## Layout master

Toda a aplicação compartilha esta estrutura macro:

```
┌──────────────────────────────────────────────────────────────────────┐
│ [≡] 🛡️ SentinelBR                              [⌘K]  [🔔3] [👤 ▼]    │ ← Topbar 56px
├──────────┬───────────────────────────────────────────────────────────┤
│          │                                                           │
│  📊 Dash │   ┌─────────────────────────────────────────────────────┐ │
│  🖥️ Hosts │   │ Page header                                         │ │
│          │   │ Breadcrumb · Title · Actions                        │ │
│  ─────   │   └─────────────────────────────────────────────────────┘ │
│  Monit.  │                                                           │
│  📊 Evnt │   ┌─────────────────────────────────────────────────────┐ │
│  🚨 Alrt │   │                                                     │ │
│  📜 Rules│   │              CONTENT AREA                           │ │
│          │   │              (rolável)                              │ │
│  ─────   │   │                                                     │ │
│  Proteç. │   │                                                     │ │
│  🛡️ FW   │   │                                                     │ │
│  🔒 SLnx │   │                                                     │ │
│          │   │                                                     │ │
│  ─────   │   └─────────────────────────────────────────────────────┘ │
│  ...     │                                                           │
│          │                                                           │
│  📡 [⏸️]  │ ← Mini-terminal de status (opcional, fixo no rodapé)      │
│          │   "events processed: 1.2k/min · agents online: 12/12"    │
└──────────┴───────────────────────────────────────────────────────────┘
   240px                          flexível
```

### Dimensões e medidas

```
══════════════════════════════════════════════════════════════════
ELEMENTO              SIZE                   COMPORTAMENTO
══════════════════════════════════════════════════════════════════
Topbar height         56px                   Fixa, sempre visível
Sidebar width         240px (expandida)      Colapsável a 64px
                      64px (colapsada)       
Sidebar mobile        100% (drawer)          Esconde por padrão
Content padding       24px 32px              Diminui em mobile
Status bar height     40px (opcional)        Toggle pelo usuário
Z-index modal         9999                   
Z-index dropdown      8000
Z-index toast         7000
Z-index tooltip       6000
```

---

## Componentes da topbar

A topbar tem altura fixa de 56px e fundo `bg-surface` (`#131826`) com border-bottom de 1px em `border-subtle`.

### Elementos (esquerda → direita)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [☰] [Logo] / Hosts / web-01           [🔍 Buscar...]  [🔔3] [👤▼]    │
└──────────────────────────────────────────────────────────────────────┘
  1     2          3                          4         5      6
```

**1. Botão hambúrguer (toggle sidebar)**
- 32x32px, ícone 18px, hover `bg-elevated`
- Atalho: `Cmd+B` ou `Ctrl+B`
- Ícone: `Menu` (lucide-react)

**2. Logo**
- Escudo SentinelBR (24x24) + texto "SentinelBR"
- Texto some quando sidebar está colapsada (mantém só escudo)
- Clicar: navega pra dashboard
- Cor: `brand-500` no escudo, `text-primary` no texto

**3. Breadcrumb**
- Mostra contexto da navegação atual
- Separador: ` / ` em `text-tertiary`
- Último item em `text-primary`, anteriores em `text-secondary`
- Clicáveis (navegação)
- Em mobile: oculto

**4. Barra de busca global (Command Palette trigger)**
- Largura: 320px, altura 32px, border-radius 6px
- Background `bg-input`, border `border-default`
- Placeholder: `🔍 Buscar... ⌘K`
- Click ou Cmd+K abre o command palette modal
- Fonte: Inter 14px

**5. Indicador de saúde + notificações**
- Bolinha colorida (8px) com pulsação sutil
  - Verde: tudo OK
  - Amarelo: degradado (algum agent offline, etc.)
  - Vermelho: incidente ativo
- Hover: tooltip com detalhes
- Sino com badge numerado: alertas não lidos

**6. Avatar + dropdown de usuário**
- Avatar circular 32x32, com inicial ou foto
- Dropdown ao clicar:
  - Nome completo + email
  - Linha separadora
  - Meu perfil
  - Preferências
  - Atalhos de teclado
  - Documentação
  - Linha separadora
  - Sair (em vermelho)

### Estados da topbar

- **Default**: como descrito acima
- **Em página de erro**: ainda mostra topbar (usuário precisa navegar)
- **Em login**: topbar não aparece (apenas logo central)
- **Modo apresentação (F11)**: topbar oculta, modo telão de SOC

---

## Componentes da sidebar

A sidebar é o **principal mecanismo de navegação**. Tem fundo `bg-surface`, border-right de 1px em `border-subtle`.

### Estados

```
═══════════════════════════════════════════════════════════════
EXPANDIDA (240px)              COLAPSADA (64px)              MOBILE
═══════════════════════════════════════════════════════════════
[ícone] Label                  [ícone]  (tooltip ao hover)   Drawer overlay
───────────────────            ──────                        ───
Tem labels visíveis            Apenas ícones                 Slide da esquerda
                                                              Esconde ao tocar fora
```

### Estrutura completa (expandida)

```
╔═══════════════════════════════╗
║                               ║
║  📊 Dashboard               ◄ ← Item ativo (barra esquerda em brand-500)
║  🖥️  Hosts                    ║
║                               ║
║  ────  MONITORAMENTO  ────    ║ ← Section header (caption uppercase)
║  📊 Eventos                   ║
║  🚨 Alertas              [3] ║ ← Badge numerado em critical
║  📜 Regras                    ║
║  🔍 Investigação              ║
║                               ║
║  ────  PROTEÇÃO  ────         ║
║  🛡️  Firewall                 ║
║  🔒 SELinux                   ║
║                               ║
║  ────  AUTOMAÇÃO  ────        ║
║  ⚡ Playbooks                 ║
║  📋 Incidentes           [1] ║
║                               ║
║  ────  PRIVACIDADE  ────      ║
║  ⚖️  LGPD                      ║
║  📁 Ativos sensíveis          ║
║  📑 Relatórios                ║
║                               ║
║  ────  ADMIN  ────            ║
║  ⚙️  Configurações            ║
║  👥 Usuários                  ║
║  🔌 Integrações               ║
║  📚 Auditoria                 ║
║                               ║
║                               ║
║─────────────────────────────  ║
║  📡 Status do sistema         ║ ← Status mini, fundo bg-terminal
║  events: 1.2k/min ●           ║
║  agents: 12/12 ●              ║
╚═══════════════════════════════╝
```

### Especificações

**Item de menu:**
- Altura: 36px
- Padding lateral: 12px
- Ícone: 18px à esquerda
- Texto: Inter 14px / 500 weight
- Hover: `bg-elevated`, transição 150ms
- Ativo: barra esquerda 3px em `brand-500` + `bg-active`

**Section header:**
- Altura: 32px
- Texto uppercase: Inter 11px / 600 / `text-tertiary`
- Letter-spacing: 0.1em
- Padding: 12px 16px 4px

**Badges:**
- Posição: à direita do item
- Background: cor semântica (`critical-bg`, `warning-bg`)
- Border-radius: 10px (pill)
- Texto: 11px mono, cor semântica forte

**Status bar (rodapé da sidebar):**
- Altura: 60px
- Background: `bg-terminal` (#050810)
- Texto: JetBrains Mono 11px
- Mostra: eventos/min, agentes online, latência API
- Bolinhas de status pulsando suavemente

### Comportamento

- **Cmd+B**: toggle expandir/colapsar
- **Cmd+1, Cmd+2, ...**: ir direto pra primeiro, segundo item
- Estado salvo em `localStorage`
- Tooltips aparecem em modo colapsado (delay 500ms)
- Section headers somem no modo colapsado (apenas separador `─`)

---

## Área de conteúdo

A área principal onde o conteúdo de cada tela aparece.

### Estrutura típica

```
┌─────────────────────────────────────────────────────────┐
│ Hosts                              [+ Novo host]        │ ← Page header (h1)
│ Inventário de servidores monitorados                    │ ← Subtitle (text-secondary)
├─────────────────────────────────────────────────────────┤
│                                                         │
│ [Filtros] [Status ▼] [Tags ▼]      [⚙️ Customizar]     │ ← Toolbar
│                                                         │
│ ┌─────────────────────────────────────────────────────┐ │
│ │                                                     │ │
│ │              CONTEÚDO PRINCIPAL                     │ │
│ │              (tabela, cards, gráficos)              │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                         │
│ Mostrando 1-50 de 234       [‹] 1 2 3 ... [›]         │ ← Footer paginação
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Padrões

- Padding lateral: 32px (24px em tablet, 16px em mobile)
- Padding vertical: 24px
- Largura máxima: 1600px (centraliza em telas muito grandes)
- Scroll: vertical apenas (horizontal apenas em tabelas via overflow)

---

## Mini-terminais embarcados

**O elemento de identidade visual mais forte** da plataforma. Trazem a sensação de "estou olhando o que o sistema tá fazendo de verdade".

### Anatomia

```
┌─ web-01 · sshd ─────────────────────────────────── [⏸️] [🗑️] [⛶] ┐ ← Header
│                                                                  │
│  $ tail -f /var/log/auth.log | grep ssh                          │ ← Comando (opcional)
│                                                                  │
│  May 09 14:23:45 web-01 sshd[12345]: Failed password for         │ ← Logs em tempo real
│  ┊                root from 203.0.113.42 port 38241 ssh2         │   (cinza claro)
│                                                                  │
│  May 09 14:23:47 web-01 sshd[12346]: Failed password for         │
│  ┊                root from 203.0.113.42 port 38241 ssh2         │
│                                                                  │
│  ▌ ← cursor piscando                                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                                          1.2k events/min ●
```

### Especificações detalhadas

**Container:**
- Background: `bg-terminal` (#050810) — mais escuro que o resto
- Border: 1px `border-default`
- Border-radius: 8px
- Padding: 0 (header tem padding próprio)
- Box-shadow: leve sombra interna no topo (efeito "tela CRT sutil")

**Header do terminal:**
- Altura: 32px
- Background: levemente mais claro que o body (`bg-surface`)
- Border-bottom: 1px `border-subtle`
- Padding: 0 12px
- Conteúdo:
  - Esquerda: nome (em mono, `text-secondary`)
  - Direita: ícones de ação
    - ⏸️ Pause/play stream
    - 🗑️ Limpar buffer
    - ⛶ Expandir fullscreen
    - ⊕ Filtrar (modal de filtro)

**Body:**
- Padding: 12px 16px
- Font: JetBrains Mono 13px
- Line-height: 20px (1.54)
- Cor base: `text-primary` (#C9D1D9)
- Scroll: virtualizado (suporta milhões de linhas)
- Auto-scroll: por padrão ON, pausa ao usuário scrollar pra cima
- Indicação visual: badge "PAUSADO" se usuário rolou

**Coloração automática (syntax highlighting):**

```
══════════════════════════════════════════════════════════════════
ELEMENTO            COR                    REGEX/REGRA
══════════════════════════════════════════════════════════════════
Timestamps          terminal-comment       \d{4}-\d{2}-\d{2} ou similar
IPs                 terminal-number        \d+\.\d+\.\d+\.\d+
Portas              terminal-number        port \d+
PIDs                terminal-number        \[\d+\]
Strings com aspas   terminal-string        "..." ou '...'
Paths /var/log/...  terminal-string        /[\w/.\-_]+
Keywords positivas  success                Accepted, OK, success
Keywords negativas  critical               Failed, denied, ERROR, FATAL
Keywords atenção    warning                WARNING, retry
Hostnames           text-primary           palavra após timestamp
Comentários #...    terminal-comment       linhas começando com #
```

**Cursor (quando interativo):**
- Bloco de 8x16px em `terminal-cursor` (#00D9A3)
- Pisca a cada 1.06s (regra clássica de terminal)
- Some quando perde foco

### Modo de input (comandos curados)

Mini-terminais podem aceitar comandos do usuário, mas **NÃO são REPLs livres** (escopo + segurança). Em vez disso:

```
┌─ Console SentinelBR ───────────────────────────────── [help: ?] ┐
│                                                                 │
│  > block ip 203.0.113.42 --duration=1h                          │
│  ✓ IP bloqueado em todos os hosts (TTL: 1h)                    │
│                                                                 │
│  > show alerts --severity=high --status=open                    │
│  3 alertas encontrados:                                         │
│    ALR-2945  ssh_brute_force  web-01     há 12min               │
│    ALR-2944  privilege_esc    db-01      há 23min               │
│    ALR-2940  port_scan        bastion    há 1h                  │
│                                                                 │
│  > _                                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Comandos suportados (catálogo):**

```
SISTEMA
?, help                 Lista comandos
clear, cls              Limpa terminal
exit                    Fecha terminal

HOSTS
hosts list              Lista todos os hosts
host <name>             Detalhes do host

ALERTAS
alerts                  Lista alertas abertos
alerts --severity=high
alert <id>              Detalhes
ack <id>                Reconhece
resolve <id> "nota"     Resolve

FIREWALL
block ip <ip>           Bloqueia IP
block ip <ip> --duration=1h
unblock ip <ip>
allowlist add <ip>

EVENTOS
search <query>          Busca eventos
tail <host>             Mostra eventos em tempo real do host

SISTEMA
status                  Status da plataforma
agents                  Lista agentes
```

**Auto-complete:**
- Tab completa comandos parciais
- Mostra dropdown com sugestões enquanto digita
- Setas pra navegar nas sugestões, Enter executa

**Histórico:**
- ↑/↓ navega histórico
- `Cmd+R` busca histórico (estilo bash reverse-i-search)

### Onde aparecem mini-terminais

1. **Dashboard**: 1 mini-terminal grande mostrando "live tail" de eventos
2. **Tela de host**: 1 mini-terminal mostrando logs em tempo real do host
3. **Tela de alerta**: 1 mini-terminal mostrando eventos relacionados
4. **Investigação**: múltiplos mini-terminais lado a lado (cada um filtrado)
5. **Modal de console** (`Ctrl+~`): console flutuante invocável de qualquer tela
6. **Sidebar status**: mini-status no rodapé (limitado, só status)

### Modo apresentação (telão SOC)

Para telões de SOC: tela cheia com 4-6 mini-terminais lado a lado, sem sidebar/topbar. Atalho: `F11` ou `Cmd+Shift+P`.

```
┌────────────────────────────┬────────────────────────────┐
│ alerts:high                │ events:rate                │
│ 🔴 ssh_brute_force web-01  │ ▁▂▃▅▇▆▅▃▂▁▂▃▄▅▆▇▆▅        │
│ 🔴 privilege_esc   db-01   │ now: 1.2k/min              │
├────────────────────────────┼────────────────────────────┤
│ firewall:blocks            │ system:status              │
│ 23 IPs blocked (last 24h)  │ ✓ all systems operational  │
│ 🇨🇳45 🇷🇺22 🇰🇵12 🇮🇷8     │ agents: 12/12 online       │
├────────────────────────────┼────────────────────────────┤
│ live:tail                  │ map:origins                │
│ [logs scrolling...]        │ [world map dots]           │
└────────────────────────────┴────────────────────────────┘
```

---

## Sistema de componentes

### Botões

```
══════════════════════════════════════════════════════════════════
VARIANTE              VISUAL                              USO
══════════════════════════════════════════════════════════════════
primary               brand-500 bg, text inverse          CTA principal
secondary             bg-surface, border-default          Ação secundária
ghost                 transparente, hover bg-elevated     Ação terciária
danger                critical bg, white text             Destrutivo
success               success bg, dark text               Confirmar
icon                  apenas ícone, hover bg-elevated     Toolbar, ações em linha
```

**Tamanhos:** xs (24px), sm (28px), md (36px default), lg (44px)
**Border-radius:** 6px (sm), 8px (md/lg)
**Loading state:** spinner substituindo conteúdo, mantém largura

### Inputs

```
┌─────────────────────────────────────┐
│ Email                          ← label (text-secondary, 12px)
│ ┌─────────────────────────────────┐ │
│ │ user@example.com                │ │ ← bg-input, border-default
│ └─────────────────────────────────┘ │   altura 36px, padding 12px
│ Insira seu email cadastrado          ← helper text (text-tertiary, 12px)
└─────────────────────────────────────┘
```

**Estados:**
- Default: border `border-default`
- Hover: border `border-strong`
- Focus: border `brand-500`, ring 2px `brand-500/20`
- Error: border `critical`, helper text `critical`
- Disabled: bg mais escuro, text-muted

### Tabelas

A tabela é o componente mais usado. **Densa por padrão**, com:

```
┌────────────────────────────────────────────────────────────────┐
│ ☐ │ Hostname  │ IP         │ Status │ Last seen   │ Tags    [⋮] │ ← Header
├───┼───────────┼────────────┼────────┼─────────────┼─────────────┤
│ ☐ │ web-01    │ 10.0.1.5   │ ●online│ 23s ago     │ [prod]      │ ← Row (32px)
│ ☐ │ db-01     │ 10.0.1.10  │ ●online│ 1m ago      │ [prod][db]  │
│ ☐ │ ...                                                          │
└────────────────────────────────────────────────────────────────┘
```

**Características:**
- Altura de linha: 32px (densa) / 40px (confortável) / 24px (compacta)
- Hover na linha: `bg-elevated`
- Selected: `bg-active` + `brand-500` na borda esquerda
- Sort indicators (▲▼) ao lado da coluna ativa
- Filtro inline ou painel lateral
- Virtualização para listas grandes (TanStack Virtual)
- Texto técnico (IPs, hashes) em mono
- Texto narrativo em sans

### Badges

```
🟢 ONLINE        success-bg, success border, success text, mono 11px
🔴 CRÍTICO       critical-bg, critical text, mono 11px uppercase
🟡 MÉDIA         warning-bg, warning text
🔵 INFO          info-bg, info text
⚫ FECHADO       text-secondary on bg-elevated
```

Border-radius: 4px (não pill — combina mais com estética terminal)

### Cards

```
┌─────────────────────────────────────┐
│ EVENTOS NAS ÚLTIMAS 24H             │ ← Caption (overline)
│                                     │
│  12.483             ↑ 8% vs ontem  │ ← display-1 + comparação
│                                     │
│  ▁▂▃▅▇▆▅▃▂▁▂▃▄▅                    │ ← sparkline (terminal-prompt color)
│                                     │
│  Detalhes →                         │ ← link
└─────────────────────────────────────┘
```

- Background: `bg-surface`
- Border: 1px `border-default`
- Border-radius: 8px
- Padding: 20px
- Hover: border `border-strong` (sutil)

### Modals e drawers

**Modal central:**
- Background: `bg-surface`
- Border: 1px `border-default`
- Border-radius: 12px
- Box-shadow: forte (modal "flutua")
- Overlay: `bg-overlay` com backdrop-blur 8px
- Animação: fade overlay + scale 0.95→1 conteúdo (200ms)

**Drawer lateral:**
- Slide da direita
- Largura: 480px (desktop), 100% (mobile)
- Mesmo styling de modal

---

## Telas detalhadas

### 1. Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│ Dashboard                                  [Últimas 24h ▼]  [⟳]    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│ │ EVENTOS      │ │ ALERTAS      │ │ HOSTS        │ │ ATAQUES      ││
│ │              │ │ ABERTOS      │ │ ONLINE       │ │ BLOQUEADOS   ││
│ │ 12.483       │ │ 7            │ │ 12 / 12      │ │ 243          ││
│ │ ↑ 8%         │ │ 🔴2 🟡5      │ │ ● 100%       │ │ ↑ 12%        ││
│ │ ▁▂▃▅▇▆▅▃▂   │ │              │ │              │ │ 🇨🇳45 🇷🇺22  ││
│ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘│
│                                                                     │
│ ┌─────────────────────────────────┐ ┌────────────────────────────┐ │
│ │ EVENTS RATE (last 24h)          │ │ live:events                │ │
│ │                                 │ │ ┌────────────────────────┐ │ │
│ │     ▁▂▃▅▇▆▅▃▂▁▂▃▄▅▆▇▆▅▄        │ │ │ 14:23:45 web-01 sshd:  │ │ │
│ │  00              12       24    │ │ │ Failed password for... │ │ │
│ │                                 │ │ │ 14:23:47 db-01: ...    │ │ │
│ │  ──ssh ──http ──audit           │ │ │ ▌                       │ │ │
│ └─────────────────────────────────┘ │ └────────────────────────┘ │ │
│                                     │ events: 1.2k/min ●         │ │
│                                     └────────────────────────────┘ │
│                                                                     │
│ ┌─────────────────────────────────┐ ┌────────────────────────────┐ │
│ │ TOP IPS (24h)                   │ │ MAP                        │ │
│ │ 203.0.113.42  823 events  🔴   │ │   [world map with dots]    │ │
│ │ 198.51.100.7  455 events  🟡   │ │                            │ │
│ │ 192.0.2.155   312 events  🟢   │ │   ● BR  8234               │ │
│ └─────────────────────────────────┘ └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Lista de hosts

```
┌─────────────────────────────────────────────────────────────────────┐
│ Hosts                                              [+ Adicionar]    │
│ 12 servidores monitorados · 12 online                               │
├─────────────────────────────────────────────────────────────────────┤
│ [🔍 Buscar...]  [Status ▼]  [Tags ▼]    [⚙️]                       │
├─────────────────────────────────────────────────────────────────────┤
│ ☐ │ Hostname    │ IP         │ Status  │ Eventos 24h │ Alertas │⋮ │
├───┼─────────────┼────────────┼─────────┼─────────────┼─────────┼──┤
│ ☐ │ web-01.prod │ 10.0.1.5   │ ●online │ 1.234       │ 🔴 2    │› │
│ ☐ │ db-01.prod  │ 10.0.1.10  │ ●online │ 567         │ 🟡 1    │› │
│ ☐ │ bastion     │ 10.0.1.1   │ ●online │ 89          │ —       │› │
└─────────────────────────────────────────────────────────────────────┘
```

### 3. Detalhe de host (drawer lateral)

```
┌────────────────────────────────────────┐
│ ✕                       web-01.prod  ☆ │
├────────────────────────────────────────┤
│                                        │
│ STATUS                                 │
│ ● online · last seen 23s ago           │
│                                        │
│ INFO                                   │
│ IP:        10.0.1.5                    │
│ OS:        Ubuntu 22.04 LTS            │
│ Kernel:    5.15.0-91-generic           │
│ Agent:     v1.0.3 ✓ atualizado         │
│ Tags:      [prod] [web] [critical]     │
│                                        │
│ MÉTRICAS (60min)                       │
│ CPU:    45%  ▁▂▃▅▆▅▃▂▁                │
│ MEM:    67%  ▃▄▅▆▆▆▅▄▃                │
│ DISK /: 78%  [████████░░]              │
│                                        │
│ ┌─ live:tail ──────────────[⏸️]──── ┐  │
│ │ 14:23:45 sshd: Accepted password  │  │
│ │ 14:23:47 sshd: Failed password    │  │
│ │ 14:23:49 nginx: 200 GET /api      │  │
│ │ ▌                                  │  │
│ └────────────────────────────────────┘  │
│                                        │
│ AÇÕES                                  │
│ [Ver eventos] [Coletar forense]        │
│ [Isolar host ⚠️]                       │
└────────────────────────────────────────┘
```

### 4. Tela de eventos com mini-terminal

```
┌─────────────────────────────────────────────────────────────────────┐
│ Eventos                                          [Salvar busca ▼]   │
├─────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────┐        │
│ │ 🔍 host:"web-01" AND severity:high                       │        │
│ └──────────────────────────────────────────────────────────┘        │
│ Filtros: [✕ severity:high] [✕ host:web-01]   + Adicionar filtro   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ ┌─ live:events ─────────────────── [⏸️] [⛶] [filtros] ─┐           │
│ │                                                       │           │
│ │ 14:23:45.123 web-01 sshd[12345]: Failed password for  │           │
│ │              root from 203.0.113.42 port 38241 ssh2   │           │
│ │                                                       │           │
│ │ 14:23:47.502 web-01 sshd[12346]: Failed password for  │           │
│ │              root from 203.0.113.42 port 38242 ssh2   │           │
│ │                                                       │           │
│ │ 14:23:49.001 web-01 sshd[12347]: Failed password for  │           │
│ │              root from 203.0.113.42 port 38243 ssh2   │           │
│ │                                                       │           │
│ │ 🔴 ALERTA DISPARADO: ssh_brute_force                  │           │
│ │                                                       │           │
│ │ 14:23:50.123 system: IP 203.0.113.42 blocked (1h)     │           │
│ │                                                       │           │
│ │ ▌                                                     │           │
│ │                                                       │           │
│ └───────────────────────────────────────────────────────┘           │
│                                                                     │
│ [Ver detalhes] [Exportar CSV] [Criar regra]                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 5. Tela de alerta com console embutido

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← Voltar     Alerta · ALR-2945                          🔴 ALTA    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│ Brute force SSH detectado em web-01.prod                            │
│ Aberto há 12 minutos · Atribuído a: você                            │
│                                                                     │
│ ┌─ DETALHES ──────────────────────────────────────────────────────┐ │
│ │ Origem:    203.0.113.42 (🇨🇳 China · ChinaNet AS4134)          │ │
│ │ Alvos:     root, admin, ubuntu                                  │ │
│ │ Tentativas: 47 em 60s                                           │ │
│ │ Regra:     ssh_brute_force_v2                                   │ │
│ │ MITRE:     T1110.001                                            │ │
│ │ Threat:    AbuseIPDB score 95/100                               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ AÇÕES TOMADAS ─────────────────────────────────────────────────┐ │
│ │ ✓ 14:23:50  IP bloqueado no firewall (TTL: 1h)                 │ │
│ │ ✓ 14:23:51  Notificação enviada ao Telegram                    │ │
│ │ ⏸️ 14:23:52  Aguardando aprovação: coleta forense              │ │
│ │             [Aprovar] [Rejeitar]                                │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ ┌─ live:related ────────────────────────────── [⏸️] ─┐              │
│ │                                                   │              │
│ │ 14:23:45 sshd: Failed password from 203.0.113.42  │              │
│ │ 14:23:47 sshd: Failed password from 203.0.113.42  │              │
│ │ ...                                               │              │
│ │ 14:24:50 firewall: blocked 203.0.113.42 (1h)      │              │
│ │ ▌                                                 │              │
│ │                                                   │              │
│ └───────────────────────────────────────────────────┘              │
│                                                                     │
│ COMENTÁRIOS                                                         │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ Adicionar nota...                                               │ │
│ └─────────────────────────────────────────────────────────────────┘ │
│                                                                     │
│ [Investigar] [Resolver] [Falso positivo] [Bloquear permanente]     │
└─────────────────────────────────────────────────────────────────────┘
```

### 6. Console flutuante (Ctrl+~)

Invocável de qualquer tela:

```
                  ┌─ console ─────────────────────[?] [⛶] [✕]─┐
                  │                                            │
                  │ Bem-vindo ao SentinelBR Console            │
                  │ Digite 'help' para ver comandos            │
                  │                                            │
                  │ > status                                   │
                  │ ✓ all systems operational                  │
                  │   agents: 12/12 online                     │
                  │   events: 1.2k/min                         │
                  │   queue: 0 pending                         │
                  │                                            │
                  │ > block ip 203.0.113.42 --duration=24h     │
                  │ ✓ IP bloqueado em 12 hosts (TTL: 24h)     │
                  │                                            │
                  │ > _                                        │
                  │                                            │
                  └────────────────────────────────────────────┘
```

---

## Estados e feedback

### Loading

**Skeleton screens** (não spinners) para cards e tabelas:

```
┌────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓        │  ← Linha "fantasma" cinza animada
│                    │
│ ▓▓▓▓▓▓▓▓ ▓▓▓▓     │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓     │
│ ▓▓▓▓▓▓             │
└────────────────────┘
```

Animação shimmer horizontal sutil de 1.5s.

### Empty states

```
┌─────────────────────────────────────────┐
│                                         │
│              ┌─────┐                    │
│              │ 🛡️  │                   │
│              └─────┘                    │
│                                         │
│       Nenhum host monitorado            │
│                                         │
│   Para começar, instale o agente em     │
│   pelo menos um servidor.               │
│                                         │
│      [+ Adicionar primeiro host]        │
│                                         │
│      Ver guia →                         │
│                                         │
└─────────────────────────────────────────┘
```

### Error states

```
┌─────────────────────────────────────────┐
│  ⚠️                                     │
│  Não foi possível carregar os eventos   │
│                                         │
│  O servidor de logs (Loki) não está    │
│  respondendo. Tente novamente em alguns │
│  instantes.                             │
│                                         │
│  > debug: connection timeout 30s        │  ← em mono, text-tertiary
│  > request_id: req_abc123def            │
│                                         │
│  [Tentar novamente] [Reportar]          │
└─────────────────────────────────────────┘
```

### Toasts

Aparecem no canto inferior direito, slide-in:

```
                          ┌──────────────────────────────┐
                          │ ✓ IP bloqueado com sucesso   │ ← success
                          │   203.0.113.42 (TTL: 1h)     │
                          │                       [✕]    │
                          └──────────────────────────────┘
```

- Auto-dismiss em 4s
- Hover pausa
- Stack vertical (mais recente em cima)
- Cores: success / warning / critical / info

### Confirmações destrutivas

```
┌──────────────────────────────────────────┐
│ ⚠️  Confirmar ação destrutiva            │
├──────────────────────────────────────────┤
│ Você está prestes a remover a regra      │
│ "ssh_brute_force". Esta ação não pode    │
│ ser desfeita.                            │
│                                          │
│ A regra disparou 234 vezes nos últimos   │
│ 30 dias.                                 │
│                                          │
│ Para confirmar, digite o nome da regra:  │
│ ┌──────────────────────────────────────┐ │
│ │                                      │ │
│ └──────────────────────────────────────┘ │
│                                          │
│ [Cancelar]              [Remover ⚠️]    │
└──────────────────────────────────────────┘
```

---

## Microinterações e animações

### Princípios

- **Curtas**: 150-250ms é ideal
- **Easing natural**: `cubic-bezier(0.4, 0, 0.2, 1)` para entrada
- **Sempre funcionais**: comunicam mudança de estado
- **Reduzíveis**: respeitam `prefers-reduced-motion`

### Catálogo de animações

```
══════════════════════════════════════════════════════════════════
ELEMENTO              ANIMAÇÃO                       DURAÇÃO
══════════════════════════════════════════════════════════════════
Hover em card         translateY(-2px) + shadow     150ms
Click em botão        scale(0.98)                    100ms
Toast aparecendo      slide-in-right + fade          250ms
Modal abrindo         fade overlay + scale 0.95→1    200ms
Lista atualizando     fade in verde sutil            300ms
Status mudando        cor transition                 400ms
Sidebar colapsando    width transition               200ms
Drawer abrindo        slide-in-right                 250ms
Page transition       fade out + fade in             100ms cada
Cursor terminal       blink a cada 1.06s             ∞
Status pulse          opacity 0.5→1                  2s loop
Sparkline drawing     stroke-dasharray animation     800ms
```

### Anti-padrões a evitar

❌ Animações longas (>500ms)
❌ Bounce/spring em ferramenta séria
❌ Auto-play de som ou vídeo
❌ Parallax (atrapalha em tela densa)
❌ Hover-dependent para ações críticas
❌ "Fancy" loading screens com mascote

---

## Atalhos de teclado

```
═══════════════════════════════════════════════════════════════
NAVEGAÇÃO
═══════════════════════════════════════════════════════════════
⌘K        Busca global / command palette
⌘B        Toggle sidebar
⌘\        Toggle status bar (rodapé)
⌘~        Toggle console flutuante
?         Mostrar todos os atalhos
Esc       Fechar modal / drawer / autocomplete

═══════════════════════════════════════════════════════════════
NAVEGAÇÃO RÁPIDA
═══════════════════════════════════════════════════════════════
G + D     Ir para Dashboard
G + H     Ir para Hosts
G + E     Ir para Eventos
G + A     Ir para Alertas
G + R     Ir para Regras
G + F     Ir para Firewall
G + S     Ir para SELinux
G + P     Ir para Playbooks
G + L     Ir para LGPD
G + ,     Ir para Configurações

═══════════════════════════════════════════════════════════════
LISTAS E TABELAS
═══════════════════════════════════════════════════════════════
J / K     Próxima / anterior linha (vim-style)
↑ / ↓     Idem
Enter     Abrir item
X         Selecionar/desselecionar
⌘A        Selecionar todos
/         Focar busca local
Esc       Limpar seleção / busca

═══════════════════════════════════════════════════════════════
AÇÕES EM ALERTAS
═══════════════════════════════════════════════════════════════
A         Acknowledge
R         Resolver
F         Marcar falso positivo
B         Bloquear IP relacionado
C         Adicionar comentário
⌘⏎        Submeter comentário

═══════════════════════════════════════════════════════════════
TERMINAL/CONSOLE
═══════════════════════════════════════════════════════════════
Tab           Auto-complete
↑ / ↓         Histórico
⌘R            Reverse search histórico
⌘L            Clear terminal
Ctrl+C        Cancelar comando atual
```

Modal de atalhos (`?`) mostra tudo isso categorizado.

---

## Responsividade

### Breakpoints

```
mobile      < 640px
tablet      640 - 1024
laptop      1024 - 1280
desktop     1280 - 1920
soc-screen  > 1920    (modo telão SOC)
```

### Adaptações

**Mobile (<640px):**
- Sidebar vira drawer overlay
- Tabelas viram cards empilhados
- Topbar simplificada
- Modais viram bottom sheets
- Mini-terminais com altura reduzida
- Console flutuante é fullscreen
- Não suportado: editor visual de playbooks, edição YAML longa

**Tablet (640-1024):**
- Sidebar colapsada por padrão (apenas ícones)
- Tabelas com colunas críticas apenas
- Layout de 2 colunas no dashboard

**Desktop+ (>1024):**
- Layout completo
- Sidebar expandida
- Todas as features

**SOC mode (>1920 ou F11):**
- Modo telão sem sidebar/topbar
- Cards maiores
- Auto-refresh agressivo (5s)
- Múltiplos mini-terminais visíveis

---

## Acessibilidade

### Critérios obrigatórios

WCAG 2.1 nível **AA** mínimo, alvo AAA onde possível:

- ✅ Contraste de texto: mínimo 4.5:1 (text-primary atinge 11.2:1)
- ✅ Navegação por teclado: 100% das ações
- ✅ Foco visível: ring 2px brand-500
- ✅ Skip links: "Pular para conteúdo principal"
- ✅ ARIA labels em ícones-botões
- ✅ Live regions para atualizações em tempo real
- ✅ Sem dependência apenas de cor (status sempre tem ícone + cor)
- ✅ Touch targets ≥44px em mobile
- ✅ Respeita `prefers-reduced-motion`
- ✅ Suporta zoom até 200% sem quebrar layout

### Modo alto contraste

Tema dedicado com contrastes ainda maiores para usuários com baixa visão:
- Fundos pretos puros
- Texto branco puro
- Bordas mais visíveis
- Sem cinzas sutis

Toggle nas preferências do usuário.

---

## Stack técnica do frontend

### Core

```
React 18+
TypeScript 5+ strict mode
Vite (build tool)
TanStack Router (routing tipado)
```

### UI

```
Tailwind CSS 4
shadcn/ui (Radix + Tailwind components)
Lucide React (ícones)
Framer Motion (animações)
```

### Estado e dados

```
TanStack Query (server state)
Zustand (client state)
React Hook Form + Zod (forms)
```

### Visualização e terminal

```
xterm.js (motor dos mini-terminais — battle-tested)
Recharts (gráficos padrão)
ECharts (mapa-múndi, heatmaps)
TanStack Table + Virtual (tabelas grandes)
react-flow (editor visual de playbooks)
```

**Por que xterm.js para mini-terminais?** É o mesmo motor usado pelo VS Code Terminal, Hyper, ttyd. Performance imbatível, suporte completo a ANSI escape codes, virtualização nativa para milhões de linhas.

### Realtime

```
WebSocket nativo (com reconexão exponencial)
EventSource (SSE) como fallback
```

### Qualidade

```
Vitest (unit tests)
Playwright (e2e)
Storybook (catálogo de componentes)
ESLint + Prettier
```

### Bundle

- Code splitting por rota
- Lazy load de módulos pesados
- Target: <200KB gzipped no first load
- xterm.js carregado sob demanda (apenas em telas com terminal)

---

## Identidade sonora opcional

Sons sutis, opcionais (toggle nas preferências), para reforçar feedback:

```
══════════════════════════════════════════════════════════════════
EVENTO                          SOM
══════════════════════════════════════════════════════════════════
Alerta crítico                  Beep curto, baixo (200hz, 100ms)
Toast de sucesso                Click subtle (mecânico)
Erro                            Beep duplo
Comando executado no console    Click curto
Notificação chegando            Tom suave de 3 notas
```

**Princípios:**
- Sons sempre opt-in (default OFF)
- Volume ajustável
- Sons curtos (<300ms)
- Inspiração: terminal beeps, não jingles

Implementação: Web Audio API com sons gerados (não arquivos baixados).

---

## Por que essa interface impressiona no portfólio

A combinação **estética terminal + UX moderna + acessibilidade séria** é rara. Mostra:

- **Diferenciação visual**: não é mais um Material Design genérico
- **Conhecimento profundo de UX**: princípios visuais justificados
- **Pensamento em domínio**: ferramenta para profissional, não Pinterest
- **Tecnicalidade**: xterm.js, syntax highlighting, virtualização
- **Acessibilidade não-negociável**: WCAG AA mínimo, AAA onde dá
- **Detalhamento**: do hex específico a microinterações

Posts potenciais no LinkedIn:

- "Por que escolhi #0A0E1A em vez de #000000 (e o que aprendi sobre conforto visual)"
- "Mini-terminais embarcados com xterm.js: como fiz o SentinelBR parecer poderoso"
- "Tipografia híbrida (Inter + JetBrains Mono): o segredo da estética terminal moderna"
- "Densidade informativa: por que ferramentas de SOC NÃO devem parecer com Notion"
- "WCAG AAA em fundo escuro: o desafio do contraste"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 2.0 (substitui 03-interface-grafica.md)*
