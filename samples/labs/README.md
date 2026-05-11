# Lab — VMs vulneráveis pra testar SentinelBR end-to-end

Este lab sobe 4 VMs Linux no OrbStack, cada uma com vulnerabilidades **plantadas
de propósito**, pra você ver o SentinelBR detectar e responder de verdade.

## Pré-requisitos

| Item | Como instalar |
|------|---------------|
| OrbStack | https://orbstack.dev (instalado no seu sistema se você seguiu este projeto) |
| `jq` | `brew install jq` |
| Docker rodando + stack do SentinelBR | `make dev && make server & make grpc & make worker & make beat` |
| Admin seedado | `cd server && uv run python -m app.scripts.seed` (default: admin@sentinelbr.io / admin1234) |

## Comandos

```bash
make lab-up          # cross-compila agente + cria 4 VMs + planta vulns (~5min total)
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

| VM | Distro | Plantação | Detecções esperadas |
|----|--------|-----------|---------------------|
| **lab-debian-11** | Debian 11 (bullseye) | webshell + miner + brute-force + pkgs vulneráveis | YARA matches, alerta brute-force, vulns OSV |
| **lab-ubuntu-22** | Ubuntu 22.04 LTS | mesmo da Debian | mesmo |
| **lab-fedora** | Fedora (latest) | mesmo da Debian (testa ecosystem RPM) | mesmo + cobertura RPM no scan OSV |
| **lab-vuln** | Debian 11 + extras | tudo do acima + backdoor cron + miner em /opt/.hidden + perms erradas + webshell extra | YARA crítico (auto-quarantine dispara) |

Detalhes do que está plantado e como verificar: [EXPECTED.md](EXPECTED.md).

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

- **Disco**: ~1.5GB por VM. 4 VMs ≈ 6GB.
- **RAM**: ~300MB por VM enquanto rodando.
- **CPU**: zero quando idle. Subir as 4 leva ~5min na primeira vez.

`make lab-down` libera tudo. As VMs ficam isoladas — não afetam o Mac.

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
