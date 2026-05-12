# lab-alpine-3 — Container/edge (Linux mínimo)

**Distro**: Alpine Linux 3.20 (musl libc) · **Pacote**: apk · **Foco do cenário**: agente roda em distros minimalistas usadas em **containers Docker** e **edge devices** (IoT, routers).

## Por que Alpine importa

Alpine é o Linux **mais usado dentro de containers Docker** (imagens base `alpine:*` somam bilhões de pulls/mês). Footprint mínimo (~5 MB) + `musl libc` (em vez de `glibc`) + `apk` (em vez de `apt`/`dnf`).

Pra cobrir esse caso, o agente Go **deve cross-compilar com `CGO_ENABLED=0`** (binário totalmente estático) — assim roda em qualquer libc.

## O que está plantado nesta VM

| Tipo | Disponível? | Notas |
|---|---|---|
| **YARA scan** | ✅ | `yara` está no Alpine community repo |
| **ClamAV** | ✅ | `clamav` + `freshclam` funcionam |
| **fail2ban** | ✅ | `apk add fail2ban`, ativado via OpenRC (não systemd) |
| **auditd** | ⚠️ | Depende do kernel host (em container OrbStack, sem kernel próprio = limitado) |
| **AIDE** | ✅ | Disponível |
| **rkhunter / chkrootkit / lynis** | ❌ | Não existem no Alpine main/community — cards mostram "não detectado" + hint |
| **firewall** | nftables | Sem ufw, sem firewalld — `nft` direto |

## O que esperar na UI

1. **Aba Hosts** → Lab Alpine aparece com badge `active` (~30s)
2. **Aba Ferramentas** → 5 cards verdes (yara, clamav, fail2ban, aide, firewall=nftables) + 4 cinzas (rkhunter, chkrootkit, lynis, AppArmor) — cada um explicando porque não está disponível
3. **Aba Vulnerabilidades** → inventory via `apk info -v` cruzado com OSV (ecosystem `Alpine:vX.Y`)

## Como reproduzir

```bash
make lab-attack
```

## Por que essa VM existe

**Portfólio do agente**: prova que cross-compila + roda em libc não-padrão + pacotes alternativos. Recrutador olhando o projeto vê "ah, o agente é portátil de verdade — não é só script bash que assume Ubuntu".

Também cobre o caso prático de **monitorar containers Docker** que rodam serviços (nginx, redis, postgres) — tudo Alpine na maioria das stacks.

## Limitação honesta

Alguns hardening tools (rkhunter, chkrootkit, lynis) não existem no Alpine — comunidade do Alpine prefere abordagens diferentes (musl + minimum surface). A UI mostra isso transparentemente, sem fingir que tem feature que não tem.
