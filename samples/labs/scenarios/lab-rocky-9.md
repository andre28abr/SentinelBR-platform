# lab-rocky-9 — Vulnerability Management (CVEs em pacotes)

**Distro**: Rocky Linux 9 (família RHEL) · **Pacote**: dnf · **Foco do cenário**: gestão de vulnerabilidades — pacotes desatualizados com CVEs reais cruzados com a base [OSV.dev](https://osv.dev) (gratuita, sem auth).

## O que está plantado nesta VM

| Tipo | Onde | O que demonstra |
|---|---|---|
| **Pacotes congelados em versões antigas** | `dnf install -y openssl-1.1.1k-9.el9 sudo-1.9.5p2-1.el9` | Inventory cruza com OSV → encontra CVE-2022-3602, CVE-2023-22809, etc |
| **Suite hardening** | Mesma do Fedora | Aba Ferramentas com 9 cards verdes |
| **SELinux** | Família RHEL — pacotes nativos | Card SELinux tipo Fedora |

## O que esperar na UI

1. **Aba Vulnerabilidades** (do host Lab Rocky 9):
   - **Risk Score** colorido (0-100): tipicamente 40-70 dependendo do snapshot
   - **5 stat cards**: Critical / High / Medium / Low / Total
   - **Tabela de CVEs**: cada CVE com link pro NVD, severidade, pacote, versão instalada/fixed
   - **Botão "Re-scan"** força nova consulta ao OSV (Celery delay)

2. **Aba Ações** após o scan automático (Celery worker):
   - `run_inventory_scan` quando o agente envia inventory novo
   - Stats atualizados em ~10s

3. **ExplainPopover em cada CVE** (botão "ver"):
   - Descrição leiga ("essa vulnerabilidade no openssl permite ataque X")
   - Severity advice ("crítico = patch agora; medium = próximo ciclo")
   - Comandos pra atualizar (`dnf update openssl`)
   - Links pra NVD / OSV / vendor advisory

## Como reproduzir

```bash
make lab-attack
# Forçar re-scan de inventory:
# UI → Lab Rocky Linux 9 → Vulnerabilidades → "Re-scan"
```

## Por que essa VM existe

Demonstra a **integração com banco de vulnerabilidades global** sem precisar de licenças caras (OSV.dev é mantido pela Google + comunidade). É a feature **"o que está vulnerável no meu servidor agora?"** — pergunta crítica que SMB raramente sabe responder.

Família **RHEL/Rocky/Alma/CentOS** ainda é maioria em datacenters BR — importante mostrar que cobre.
