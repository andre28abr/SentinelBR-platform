# Sobre o autor

## André Augusto Azarias De Souza

→ [LinkedIn](https://linkedin.com/in/adreaugusto-azariasdesouza) · [GitHub](https://github.com/andre28abr) · [Profile completo](https://github.com/andre28abr)

---

## Resumo

Profissional com mais de 18 anos de experiência em **gestão administrativa, compliance, governança da informação e proteção de dados pessoais**, com atuação integrada entre áreas administrativas, tecnologia da informação e conformidade regulatória.

Formação dupla em **Direito (Anhanguera)** e **Análise e Desenvolvimento de Sistemas (Mackenzie)**, complementada por especializações em LGPD, Direito Digital, Segurança Digital e Liderança Ágil.

Exerceu por quase duas décadas a função de **Gerente Administrativo e Encarregado de Dados (DPO)** em organização do setor de saúde suplementar, com atuação na organização da governança, adequação à LGPD, controle documental e apoio às áreas administrativas e tecnológicas.

Atualmente em transição de carreira, com **disponibilidade imediata**, busca posições em DPO (Encarregado de Dados), Compliance, Governança & GRC, Privacy Engineering ou Security Analyst com viés regulatório.

---

## Por que esse projeto existe

O **SentinelBR** nasceu como exercício pessoal de portfólio com três objetivos:

1. **Traduzir conceitos regulatórios em código.** A LGPD não é só sobre política — também é sobre como o sistema *implementa* audit log (Art. 37), retenção (Art. 16), PII masking, base legal pra tratamento. Esse projeto força essa tradução em decisões técnicas concretas.

2. **Demonstrar fluência técnica suficiente pra dialogar com times de engenharia e segurança.** Um DPO ou Compliance Officer que entende mTLS, multi-tenancy estrito, detection rules e threat hunting consegue conversar diretamente com a equipe técnica, sem precisar de intermediário que traduza requisitos.

3. **Exercitar orquestração de projeto técnico complexo com auxílio de IA generativa.** A skill emergente do mercado pós-2024 não é "decorar sintaxe" — é saber **definir requisitos, validar arquitetura, traduzir necessidades de negócio em especificações técnicas** e usar IA pra acelerar a entrega. O projeto cobre 11 fases com ~150 testes verdes e CI multi-OS, gerenciado nesse modelo.

---

## Atuação neste projeto

**Papel:** Product Owner técnico, com auxílio de assistentes de IA generativa para a etapa de codificação.

**Entregas pessoais (sem auxílio de IA):**
- Definição de **requisitos, escopo e roadmap** das 11 fases entregues
- **Validação da arquitetura**: cliente-servidor mTLS gRPC, multi-tenancy, isolamento cross-org, observabilidade, audit append-only
- **Tradução de exigências LGPD** para requisitos funcionais (Art. 37 audit log, Art. 16 retenção, PII masking)
- **Curadoria da Knowledge Base** MITRE ATT&CK PT-BR: 12 técnicas traduzidas com `summary_simple` em linguagem leiga (`what_happened`, `should_worry`, `what_to_do`, `jargon`), 6 hunting queries, 3 purple team playbooks
- **Especificação do laboratório**: 6 VMs Linux propositalmente vulneráveis (Debian, Ubuntu, Fedora, Rocky, Alpine, vuln-lab) com cenários de detecção e resposta
- **Redação de 18 documentos técnicos em português** (arquitetura, deployment, glossário, ADRs, roadmap, demo mode)
- **Review e decisões de trade-off** em cada fase (escolhas como Loki vs. Elasticsearch, AGPL vs. MIT, 404 vs. 403 em cross-org leakage, Celery vs. asyncio puro)

**Etapa de codificação:** orquestrada com auxílio de IA generativa, sob direção e revisão do autor. A stack do projeto (Python/FastAPI, Go, React, gRPC mTLS, etc.) foi escolhida pela exposição prévia em estudos e pela aderência ao caso de uso, não por domínio prático prévio em escrita de código de produção.

---

## Formação relevante para o domínio

### Formação acadêmica

- **Bacharelado em Direito** — Anhanguera Educacional
- **Análise e Desenvolvimento de Sistemas** — Universidade Presbiteriana Mackenzie

### Pós-graduações ligadas a Privacy / Security / Tech

- **Privacidade e Proteção de Dados Pessoais (LGPD)** — Faculdade Focus
- **Direito, Inovação e Tecnologia** — Faculdade CERS
- **Direito Digital** — Legale Educacional
- **Segurança Digital, Governança e Gestão de Dados** — PUCRS

### Certificações ligadas ao tema deste projeto

- **DPO – Data Protection Officer (LGPD)** — CERS (2020)
- **Cybersecurity Essentials** — Cisco (2022)
- **Cibersegurança – Ameaças e Táticas de Prevenção** — FGV (2023)
- **Crise Cibernética e Continuidade de Negócios** — FGV (2023)
- **Fundamentos na Lei Geral de Proteção de Dados** — Certiprof Summit (2023)
- **Data Mapping: da Teoria à Prática** — IbiJus (2023)
- **AI for Leaders** — StartSe University (2024)
- **Visual Law** — Legale Educacional (2023)

---

## Outros projetos

**SC Platform** *(privado, sob NDA — disponível para apresentação em entrevistas mediante solicitação)*

Plataforma SaaS multi-tenant para gestão de licitações públicas brasileiras (PNCP em tempo real, simulador FSM da Lei 14.133, robô de lances em 3 modos, extração de PDF com IA local via ChromaDB + Sentence-Transformers, gerador de propostas, CRM, Telegram em tempo real). Stack: **Python 3.14 + Flask 3 + SQLAlchemy 2 + PostgreSQL 15 + Redis + Playwright + ReportLab + Docling + Manifest V3 Chrome Extension**. ~75.000 linhas, 420 testes, 30 modelos, 245 rotas, 29 migrations.

---

## Vagas em foco

- **DPO / Encarregado de Dados** (LGPD)
- **Compliance & Governança (GRC)** — políticas, controles, mapeamento de dados
- **Privacy Engineering** — bridge entre legal e técnico
- **Security Analyst** com viés regulatório
- **Consultoria em LGPD / Privacy**

**Modalidades aceitas:** remoto, híbrido, presencial — Brasil.

---

## Contato

Para apresentação técnica de projetos privados (SC Platform), entrevistas, ou propostas de oportunidade, o canal de contato é o **[LinkedIn](https://linkedin.com/in/adreaugusto-azariasdesouza)**.

Dados de contato direto (email, telefone) são fornecidos sob demanda durante processo seletivo, via canais formais do RH.
