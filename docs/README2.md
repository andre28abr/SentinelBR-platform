# SentinelBR — Documentos Extras

> Pasta complementar ao zip principal `sentinelbr-docs`. Contém 3 documentos extras que ajudam **especialmente na hora de começar a codar**.

## 📚 Documentos

| # | Documento | Descrição |
|---|-----------|-----------|
| 10 | [Diagramas visuais](docs-extras/10-diagramas-visuais.md) | Diagramas em Mermaid (renderizam no GitHub) |
| 11 | [Glossário](docs-extras/11-glossario.md) | 100+ termos técnicos explicados |
| 12 | [Fixtures de eventos](docs-extras/12-fixtures-eventos.md) | Exemplos reais de logs para testes |

## 🎯 Para que servem

### 10 — Diagramas visuais
Substituem os diagramas ASCII dos documentos principais por versões em Mermaid, que renderizam visualmente no GitHub. Inclui:
- Visão de contexto C4
- Containers e componentes
- Fluxos de evento e bloqueio automático
- Modelo de dados (ER diagram)
- Estados de alerta e agente
- Pipeline de processamento
- Arquitetura de rede
- Camadas de segurança
- Roadmap em Gantt

### 11 — Glossário
Consulta rápida para todos os termos técnicos do projeto. Cada termo:
- Tem nível de complexidade (🟢🟡🔴)
- Linguagem simples
- Relações com outros termos (→)
- Exemplos práticos

### 12 — Fixtures de eventos
Exemplos reais de logs (SSH, auditd, sudo, nginx, postgres, kernel, SELinux) com:
- Log cru (como aparece no servidor)
- Versão normalizada em ECS (como deve ficar após parsing)
- Padrões de ataque (brute force, path traversal, SQL injection, etc.)
- Como usar nos testes do projeto

## 📁 Onde colocar no projeto

Sugestão: descompactar e mover os 3 arquivos para a mesma pasta `docs/` do zip principal. A numeração (10, 11, 12) já está pensada para continuar a sequência:

```
sentinelbr/
└── docs/
    ├── 01-visao-geral-modulos.md
    ├── 02-funcionalidades-detalhadas.md
    ├── 03-interface-grafica.md
    ├── 04-arquitetura-dados.md
    ├── 05-arquitetura-tecnica.md
    ├── 06-api-reference.md
    ├── 07-roadmap-detalhado.md
    ├── 08-stack-decisions.md
    ├── 09-deployment.md
    ├── 10-diagramas-visuais.md   ← NOVO
    ├── 11-glossario.md           ← NOVO
    └── 12-fixtures-eventos.md    ← NOVO
```

---

*Construído com ❤️ no Brasil.*
