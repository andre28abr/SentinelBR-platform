# lab-fedora — Showcase completo (todas as ferramentas + SELinux)

**Distro**: Fedora 43 · **Pacote**: dnf · **Foco do cenário**: showcase visual da aba "Ferramentas" com **todos os 9 cards verdes**, demonstra integração com SELinux + scans agendados Celery beat.

## O que está plantado nesta VM

| Tipo | Onde | O que demonstra |
|---|---|---|
| **Webshell + miner + brute-force** | Mesmas iscas das outras VMs | Detecções YARA + sshd funcionando |
| **fail2ban com 2 IPs banidos** | Jail `sshd` | Aba Ferramentas → fail2ban com lista de banidos + botão "desbanir" |
| **firewalld com rich rule** | Bloqueio de `198.51.100.0/24` | Aba Ferramentas → Firewall com snapshot real + botão "+ Adicionar regra" + "remover" |
| **auditd com 1 regra** | Monitora writes em `/etc/passwd` | Aba Ferramentas → auditd com 1 rule listada |
| **rkhunter, chkrootkit, lynis, AIDE** | Instalados, prontos pra rodar | Aba Ferramentas → cada um com botão "rodar agora" + warning de tempo |
| **SELinux** | Pacotes instalados (`getenforce`, `sestatus`) | Aba Ferramentas → SELinux com status `Disabled` (limitação container) + comandos pra ativar em VM real |
| **Scans agendados Celery beat** | rkhunter/chkrootkit/aide diários, lynis semanal | Aba Ações mostra entries `scheduled` periodicamente |

## O que esperar na UI

1. **Aba Ferramentas** (sub-aba "Visão geral") → **9 cards** todos com badge verde "ativo/instalado":
   - fail2ban (2 banidos · 1 jail)
   - Firewall (firewalld)
   - auditd (ativo)
   - rkhunter (instalado)
   - chkrootkit (instalado)
   - lynis (instalado)
   - AIDE (instalado)
   - SELinux (Disabled — esperado em container)
   - AppArmor (não detectado — esperado em Fedora)

2. **Sub-abas funcionais** acima do Visão Geral (clica e interage):
   - fail2ban: lista jails + botão "desbanir IP"
   - Firewall: regras + add/remove
   - auditd: lista regras `auditctl -l`
   - rkhunter/chkrootkit/lynis/AIDE: botão "rodar agora" + ScanProgressBadge
   - SELinux: status + comandos curados

3. **Após próximo ciclo do Celery beat** (~24h por padrão, ajustável via env):
   - Aba Ações ganha entries automáticas `run_rkhunter_scan reason=scheduled`

## Como reproduzir

```bash
make lab-attack
```

## Por que essa VM existe

A "vitrine" do projeto. Recrutador olha essa VM e vê **todo o ecossistema de hardening** que a plataforma cobre — não só "detector que avisa", mas também **interação real** (banir/desbanir, regras de firewall, scans on-demand).
