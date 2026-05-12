# Lab — VMs vulneráveis pra testar SentinelBR end-to-end

Este lab sobe 6 VMs Linux no OrbStack, cada uma com cenário diferente
e vulnerabilidades **plantadas de propósito**, pra você ver o SentinelBR
detectar e responder de verdade.

## Pré-requisitos

| Item | Como instalar |
|------|---------------|
| OrbStack | https://orbstack.dev (instalado no seu sistema se você seguiu este projeto) |
| `jq` | `brew install jq` |
| Docker rodando + stack do SentinelBR | `make dev && make server & make grpc & make worker & make beat` |
| Admin seedado | `cd server && uv run python -m app.scripts.seed` (default: admin@sentinelbr.io / admin1234) |

## Comandos

```bash
make lab-up          # cross-compila agente + cria 6 VMs + planta vulns (~10min primeira vez)
make lab-status      # mostra estado das VMs + status no DB
make lab-attack      # re-planta vulns (renova webshells, brute-force, etc)
make lab-down        # destrói todas as VMs (libera disco)
```

Pra trabalhar com **uma só** VM:

```bash
samples/labs/up.sh debian-11           # só Debian
samples/labs/down.sh ubuntu-22         # destruir só Ubuntu
samples/labs/attack.sh debian-11 vuln-lab
```

## O que cada VM tem

Cada VM ganha as iscas universais (webshell + brute-force SSH + EICAR + dropper bash + reverse shell Python + cron backdoor + pacotes congelados com CVEs reais via OSV) e, dependendo do `.env`, suite hardening completa.

| VM | Distro | Cenário focal | Detecções esperadas |
|----|--------|---------------|---------------------|
| **lab-debian-11** | Debian 11 (apt + systemd) | Brute-force SSH + auto-block IP | alerta `ssh_brute_force_ip`, action `block_ip` |
| **lab-ubuntu-22** | Ubuntu 22.04 (apt + systemd) | Webshell + auto-quarantine + LGPD/PII | YARA critical, action `quarantine_file`, audit log |
| **lab-fedora** | Fedora (dnf + systemd) | Hardening showcase (SELinux, auditd, rkhunter) | aba Ferramentas com 9 cards verdes |
| **lab-rocky-9** | Rocky 9 (dnf+EPEL + systemd) | CVE/vulnerability management | Risk score elevado, vulns na aba dedicada |
| **lab-alpine-3** | Alpine (apk + OpenRC) | Container/edge (musl libc) | testa cross-compile + footprint pequeno |
| **lab-vuln** | Debian 11 + extras agressivos | Buffet de ataques (estilo Metasploitable) | 6+ alertas simultâneos, auto-quarantine, block_ip |

Cada VM tem doc detalhado em [`scenarios/`](scenarios/) (plantio + UI esperado + repro + porquê).

Visão consolidada do que esperar na UI: [EXPECTED.md](EXPECTED.md).

## Arquitetura

```
Mac (host)                         OrbStack VMs (lab-*)
┌──────────────────────┐          ┌──────────────────────┐
│ FastAPI :8000        │◄─────────│ sentinel-agent       │
│ gRPC :9443 (mTLS)    │◄─────────│   (heartbeat 30s)    │
│ Postgres :5433       │          │   (events stream)    │
│ Loki :3100           │          │                      │
│ Vite :5173 (UI)      │          │ /var/log/auth.log    │
│                      │          │ /var/www (webshell)  │
│                      │          │ /tmp (miner config)  │
└──────────────────────┘          └──────────────────────┘
```

VMs alcançam o Mac via `host.orb.internal`. O Mac alcança as VMs via
`<vmname>.orb.local` (ex: `ssh sentinel@lab-debian-11.orb.local`).

## Custo de recursos

- **Disco**: 500MB-1.2GB por VM. 6 VMs ≈ 5-6GB total.
- **RAM**: ~300MB por VM enquanto rodando.
- **CPU**: zero quando idle. Subir as 6 leva ~10min na primeira vez (download das imagens + install hardening); reattach é ~10s.

`make lab-down` libera tudo. As VMs ficam isoladas — não afetam o Mac.

## Controle pela UI (Lab Mode)

Com `SENTINELBR_LAB_MODE=true` no backend, a aba **Lab** aparece no header do app (`/lab`) com:

- Lista das 6 VMs com estado (running/stopped)
- Botões Iniciar / Parar / Re-atacar por VM
- Botão **Resetar demo** que apaga alertas + ações pra recomeçar gravação do zero

Detalhes em [docs/18-demo-mode.md](../../docs/18-demo-mode.md).

## Troubleshooting

### "VM não consegue alcançar host.orb.internal:8000"

O `make server` original escutava só em 127.0.0.1. Foi mudado pra 0.0.0.0 nesse
mesmo PR. Confirme:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
# Tem que mostrar: *.8000 (não 127.0.0.1.8000)
```

Se ainda falhar, reinicie o `make server`.

### "Action fica em pending pra sempre"

Significa que o agente da VM não está fazendo heartbeat. Cheque:

```bash
make lab-status                                # status systemd em cada VM
orb -m lab-debian-11 -u root journalctl -u sentinelbr-agent --no-pager -n 30
```

Possíveis causas: enroll falhou, gRPC não acessível, cert do server inválido.

### "As VMs sobem mas a UI não mostra elas como ativas"

Aguarde 30s (intervalo do heartbeat). Se persistir, veja logs do server (`make
server`) procurando por erros de mTLS ou NOT_FOUND.

### "Quero recomeçar do zero"

```bash
make lab-down && make lab-up
```

Se quiser limpar também os hosts no banco: delete pelo botão da UI antes do
`lab-down`.

## Aviso

As VMs contêm artefatos **textuais** que parecem maliciosos (PHP webshell,
config de miner, scripts curl|bash, linhas falsas em auth.log). **Nada disso é
executado** — são strings que existem só para o YARA / parser SSH casarem. As
VMs estão isoladas pelo OrbStack e os artefatos somem com `make lab-down`.

Não exponha essas VMs pra rede externa. Não as use como base pra produção.
