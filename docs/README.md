# SentinelBR — Documentação

> Plataforma open-source de segurança para servidores Linux, com foco na realidade brasileira (LGPD, idioma português, SMBs).

Para visão executiva do projeto, veja o [README raiz](../README.md). Para roteiro de quickstart técnico, idem.

Esta pasta concentra a **documentação completa** — também renderizada in-app na aba `/docs` (com sidebar TOC) depois de logar.

## Índice (18 documentos)

| # | Documento | Para quem |
|---|-----------|-----------|
| 01 | [Visão geral dos módulos](01-visao-geral-modulos.md) | Recrutador / curioso |
| 02 | [Funcionalidades detalhadas](02-funcionalidades-detalhadas.md) | Avaliador técnico |
| 03 | [Interface gráfica](03-interface-grafica.md) | Designer / UX |
| 04 | [Arquitetura de dados](04-arquitetura-dados.md) | DBA / dev backend |
| 05 | [Arquitetura técnica](05-arquitetura-tecnica.md) | Tech lead / arquiteto |
| 06 | [API Reference](06-api-reference.md) | Quem vai integrar |
| 07 | [Roadmap detalhado](07-roadmap-detalhado.md) | Quem vai contribuir |
| 08 | [Stack decisions (ADRs)](08-stack-decisions.md) | Tech lead avaliando |
| 09 | [Deployment](09-deployment.md) | DevOps / SRE |
| 10 | [Diagramas visuais](10-diagramas-visuais.md) | Apresentação |
| 11 | [Glossário](11-glossario.md) | Quem está chegando agora |
| 12 | [Fixtures de eventos](12-fixtures-eventos.md) | QA / testador |
| 13 | [Interface gráfica terminal](13-interface-grafica-terminal.md) | Designer dark theme |
| 14 | [Vulnerability management](14-vulnerability-management.md) | Security analyst |
| 15 | [Suporte multi-OS](15-suporte-multi-os.md) | Multi-platform dev |
| 16 | [Antivírus / malware](16-antivirus-malware.md) | Detection engineer |
| 17 | [Threat knowledge base](17-threat-knowledge-base.md) | Threat hunter |
| 18 | [Demo Mode (lab)](18-demo-mode.md) | Pra rodar a demo localmente |

## Por onde começar?

- **Recrutador / curioso**: comece pelo [01-visao-geral](01-visao-geral-modulos.md)
- **Desenvolvedor avaliando**: leia [05-arquitetura-tecnica](05-arquitetura-tecnica.md) + [08-stack-decisions](08-stack-decisions.md)
- **Quem vai contribuir**: comece pelo [07-roadmap-detalhado](07-roadmap-detalhado.md)
- **Quem vai instalar**: vá direto pro [09-deployment](09-deployment.md)
- **Quem quer ver rodando**: [18-demo-mode](18-demo-mode.md) explica como ativar o lab

## Status do projeto

🟢 **Implementado.** Fases 1-11 fechadas. CI matriz multi-OS (Linux/macOS/Windows) verde, 149 testes server, agent Go suite verde, build web sem warnings.

Componentes prontos:

- **`server/`** — FastAPI + Pydantic v2 + SQLAlchemy 2 async + Celery + grpcio mTLS
- **`agent/`** — Go 1.25 cross-compilado, coletor SSH + YARA + inventory
- **`web/`** — React 19 + Vite 8 + Tailwind 4, lazy-loaded por rota
- **`proto/`** — Contratos gRPC compartilhados (mTLS)
- **`samples/labs/`** — 6 VMs OrbStack propositalmente vulneráveis pra demo

Ver [07-roadmap-detalhado](07-roadmap-detalhado.md) para o histórico completo.

## Licença

[AGPL-3.0](../LICENSE) — ver [ADR-018 em 08-stack-decisions](08-stack-decisions.md).
