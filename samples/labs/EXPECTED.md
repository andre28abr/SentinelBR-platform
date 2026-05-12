# Lab — Cenários esperados

Cada VM do lab tem um **cenário focado** pra demonstrar uma capacidade específica do SentinelBR. Detalhes em `scenarios/<vm>.md`.

## Tabela rápida

| VM | Distro | Cenário | Documentação |
|---|---|---|---|
| `lab-debian-11` | Debian 11 | **Brute-force SSH + auto-block** | [→ scenarios/lab-debian-11.md](scenarios/lab-debian-11.md) |
| `lab-ubuntu-22` | Ubuntu 22.04 | **Webshell + auto-quarantine + LGPD/PII** | [→ scenarios/lab-ubuntu-22.md](scenarios/lab-ubuntu-22.md) |
| `lab-fedora` | Fedora 43 | **Showcase completo** (todas ferramentas + SELinux) | [→ scenarios/lab-fedora.md](scenarios/lab-fedora.md) |
| `lab-rocky-9` | Rocky Linux 9 | **CVEs em pacotes desatualizados** (OSV cross-ref) | [→ scenarios/lab-rocky-9.md](scenarios/lab-rocky-9.md) |
| `lab-alpine-3` | Alpine 3.20 | **Container/edge** (musl, footprint mínimo) | [→ scenarios/lab-alpine-3.md](scenarios/lab-alpine-3.md) |
| `lab-vuln` | Debian 11 | **Buffet de ataques** (multi-vetor, estilo Metasploitable) | [→ scenarios/lab-vuln.md](scenarios/lab-vuln.md) |

## Comandos úteis

```bash
# Sobe todo o lab (demora ~5min na primeira vez)
make lab-up

# Re-planta as iscas (sem destruir VMs)
make lab-attack

# Status atual das VMs + agentes
make lab-status

# Destrói tudo
make lab-down
```

## Ordem recomendada de demonstração

Pra um recrutador olhando o programa pela primeira vez:

1. **Comece com `lab-fedora`** — visual mais impressionante (9 cards verdes em Ferramentas)
2. **Mostre `lab-vuln`** — todas as detecções acontecendo ao mesmo tempo
3. **Aprofunde em `lab-ubuntu-22`** — fluxo completo de auto-quarantine + audit log + LGPD
4. **Toque em `lab-rocky-9`** pra mostrar Vulnerability Management
5. **Termine com `lab-alpine-3`** mostrando portabilidade do agente (cross-compile, musl)

`lab-debian-11` cobre o caso "default" — brute-force SSH é o ataque mais comum, vale mostrar quando quiser explicar o fluxo SIEM completo.

## Tempos esperados

| Evento | Quando acontece |
|---|---|
| Hosts viram `active` | ~30s após cada VM subir (1 ciclo heartbeat) |
| Eventos `sshd` aparecem | ~30s após heartbeat com agente lendo /var/log/auth.log |
| Alertas criados | ~30s após eventos chegarem (ciclo Celery beat de detect) |
| Ações automáticas (`block_ip`, `quarantine_file`) | ~30s após alerta criado (ciclo policy.maybe_create_action) |
| Vulnerabilidades CVE | ~10-30s após inventory enviado (Celery worker delay) |
