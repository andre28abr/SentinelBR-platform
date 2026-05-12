# SentinelBR

> Plataforma open-source de segurança para servidores Linux, com foco na realidade brasileira (LGPD, idioma português, SMBs).

## ✨ O que é

Uma plataforma única que reúne SIEM, gestão de Firewall, gestão de SELinux, resposta automatizada a incidentes e compliance LGPD — tudo em português, com interface amigável e sem depender de ferramentas pagas.

## 🎯 Para quem é

- Pequenas e médias empresas brasileiras que precisam de segurança séria sem orçamento de multinacional
- DPOs e times de TI que querem operacionalizar a LGPD
- Profissionais de segurança que querem uma stack open-source nacional

## 🧩 Módulos

1. **SIEM** — coleta e correlaciona logs, detecta ameaças
2. **Firewall** — interface amigável para iptables/nftables
3. **SELinux** — tradutor humano para o SELinux
4. **Resposta a Incidentes** — playbooks automáticos de reação
5. **Compliance LGPD** — auditoria contínua e relatórios para a ANPD

## 📚 Documentação

A documentação está organizada em 9 documentos progressivos:

| # | Documento | Descrição |
|---|-----------|-----------|
| 01 | [Visão geral dos módulos](docs/01-visao-geral-modulos.md) | Explicação leiga dos 5 módulos |
| 02 | [Funcionalidades detalhadas](docs/02-funcionalidades-detalhadas.md) | 50+ features catalogadas com prioridade |
| 03 | [Interface gráfica](docs/03-interface-grafica.md) | Design system, telas, UX |
| 04 | [Arquitetura de dados](docs/04-arquitetura-dados.md) | Bancos, schemas, retenção |
| 05 | [Arquitetura técnica](docs/05-arquitetura-tecnica.md) | Componentes, padrões, comunicação |
| 06 | [API Reference](docs/06-api-reference.md) | Endpoints REST completos |
| 07 | [Roadmap detalhado](docs/07-roadmap-detalhado.md) | Fases, sprints, marcos |
| 08 | [Stack decisions (ADRs)](docs/08-stack-decisions.md) | 20 decisões arquiteturais |
| 09 | [Deployment](docs/09-deployment.md) | Instalação em todos os cenários |

### Por onde começar?

- **Recrutador / curioso**: leia o [01-visao-geral](docs/01-visao-geral-modulos.md) (visão executiva)
- **Desenvolvedor avaliando**: leia [05-arquitetura](docs/05-arquitetura-tecnica.md) e [08-stack-decisions](docs/08-stack-decisions.md)
- **Quem vai contribuir**: comece pelo [07-roadmap](docs/07-roadmap-detalhado.md)
- **Quem vai instalar**: vá direto pro [09-deployment](docs/09-deployment.md)

## 📁 Estrutura do repositório

```
sentinelbr/
├── README.md                    ← você está aqui
├── docs/                        ← documentação do projeto (9 arquivos)
├── server/                      ← API e backend Python (em breve)
├── agent/                       ← coletor Go (em breve)
├── web/                         ← interface React (em breve)
├── proto/                       ← schemas Protobuf compartilhados
└── deploy/                      ← Docker Compose, Helm, Terraform
```

## 🚧 Status

Projeto em fase de **planejamento e documentação**. Próximo passo: começar o MVP (ver roadmap).

## 📜 Licença

A definir (provavelmente AGPL-3.0). Ver ADR-018.

---

*Construído com ❤️ no Brasil.*
