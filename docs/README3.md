# SentinelBR — Extras V2 (Funcionalidades Avançadas)

> Pasta complementar com 4 documentos cobrindo funcionalidades extras discutidas: vulnerability management, suporte multi-OS, antivírus/malware e knowledge base de ameaças.

## 📚 Documentos

| # | Documento | Descrição | Tamanho |
|---|-----------|-----------|---------|
| 14 | [Vulnerability Management](14-vulnerability-management.md) | Scanner CVE não-invasivo, CIS Benchmark, FIM, Patch Mgmt | 56 KB |
| 15 | [Suporte Multi-OS](15-suporte-multi-os.md) | Cobertura Linux (todas as distros) + Windows roadmap | 25 KB |
| 16 | [Antivírus e Malware](16-antivirus-malware.md) | ClamAV, YARA, Defender, integrações comerciais | 42 KB |
| 17 | [Threat Knowledge Base](17-threat-knowledge-base.md) | MITRE ATT&CK PT-BR, hardening, hunting, purple team | 35 KB |

## 🎯 O que cada um traz

### 14 — Vulnerability Management
- Scanner de CVEs **não-invasivo** (apenas via inventário de pacotes)
- Sistema de **5 tags de status** (✅OK, 🟡needs-check, 🔴vulnerable, 🟠acknowledged, ⚪N/A)
- **CIS Benchmark scanner** (~250 checks por OS)
- **File Integrity Monitoring** (FIM) com inotify em tempo real
- **Patch Management** com janelas de manutenção
- Cross-reference com **CISA KEV** (vulnerabilidades em exploração ativa) e **EPSS** (probabilidade de exploração)
- Wizards de correção guiada
- Score de segurança 0-100 por host

### 15 — Suporte Multi-OS
- **Tier 1**: Ubuntu, Debian, Rocky, AlmaLinux (testado em CI)
- **Tier 2**: RHEL, Fedora, openSUSE, SUSE SLES
- **Tier 3**: Arch, Alpine, Oracle Linux, CentOS Stream
- **Tier 4 (futuro)**: Windows Server 2019/2022/2025
- Detecção automática de OS pelo agente
- Abstração via interfaces (Go) — adicionar OS = implementar interfaces
- CI matrix testando em todas as distros
- Documentação de instalação por OS

### 16 — Antivírus e Malware
- **ClamAV** integrado (open-source, padrão Linux)
- **YARA** (detecção avançada com regras customizáveis) — pacote starter com regras de APT, miners, webshells, ransomware
- **Microsoft Defender** for Linux + Windows
- Integração com AVs comerciais (CrowdStrike, SentinelOne, Sophos, Bitdefender, ESET)
- **Heurísticas próprias** (sem AV): processos suspeitos, modificações em /etc/, persistência, living off the land
- Quarentena automática com aprovação humana
- VirusTotal integration (privacy-friendly: só hash por padrão)
- Limitações honestas documentadas

### 17 — Threat Knowledge Base
- **Catálogo MITRE ATT&CK em PT-BR** com tradução cultural (não literal)
- Cada técnica explicada para 3 níveis (básico, intermediário, avançado)
- Status de cobertura visível (✅🟡🔴⚪)
- **Recomendações de hardening por host** (~80-100 recomendações catalogadas)
- **94 threat hunting queries** prontas (procurar webshells, beaconing, travel impossível, etc.)
- **IOC matching retroativo**: novo IOC busca em TODO histórico
- **Simulação de ataques (purple team)**: testa se detecções funcionam
- **Modo aprendizado**: explicações educativas em cada alerta para novatos

## 📁 Onde colocar no projeto

Sugestão: descompactar e mover os arquivos para a mesma pasta `docs/` dos outros documentos:

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
    ├── 10-diagramas-visuais.md
    ├── 11-glossario.md
    ├── 12-fixtures-eventos.md
    ├── 13-interface-grafica-terminal.md
    ├── 14-vulnerability-management.md      ← NOVO
    ├── 15-suporte-multi-os.md              ← NOVO
    ├── 16-antivirus-malware.md             ← NOVO
    └── 17-threat-knowledge-base.md         ← NOVO
```

Total: **17 documentos** cobrindo a plataforma completa.

## 🚀 Como esses documentos elevam o projeto

Antes desses 4 documentos, o SentinelBR era "mais um SIEM open-source com algumas features".

Com esses documentos, vira:

1. **Plataforma de gestão de vulnerabilidades** — concorre com Tenable, Qualys (versão simples)
2. **Hardening assistido** — concorre com Lynis, OpenSCAP (versão usável)
3. **Threat detection avançado** — concorre com Wazuh + extensões
4. **Educação em segurança** — diferencial absurdo no portfólio

## 💼 Para o portfólio

Cada documento é potencial post no LinkedIn:

- "Vulnerability scanning sem ser invasivo"
- "Por que Rocky Linux é tier 1 (e CentOS Stream não)"
- "ClamAV + YARA: defesa em profundidade open-source"
- "Como traduzi MITRE ATT&CK para o português"
- "Threat hunting acessível: 94 queries para começar hoje"
- "Hardening Linux em 1 clique"
- "Purple team automatizado"

Cada um pode gerar engajamento e vagas.

---

*Construído com ❤️ no Brasil.*
