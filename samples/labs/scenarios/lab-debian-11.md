# lab-debian-11 — Brute-force SSH + auto-block

**Distro**: Debian 11 (Bullseye) · **Pacote**: apt · **Foco do cenário**: detecção de força bruta SSH com resposta automática (block_ip)

## O que está plantado nesta VM

| Tipo | Onde | O que demonstra |
|---|---|---|
| **12 tentativas falhas SSH** em `/var/log/auth.log` | IP `198.51.100.124` (RFC 5737 — IP de documentação, não real) | Detector `ssh_brute_force_ip` (regra Sigma-style) cria alerta `high` |
| **Suite hardening completa** | Todos os pacotes Tier 1+2 instalados | Aba Ferramentas mostra todos os 9 cards verdes |
| **AppArmor** ativo | LSM padrão do Debian/Ubuntu | Card "AppArmor: enabled" + comandos pra editar profiles |

## O que esperar na UI após esta VM ficar ativa

1. **Aba Hosts** → `Lab Debian 11` aparece com badge `active` (verde) em ~30s
2. **Aba Eventos** (filtro `source=sshd`) → 12 linhas tipo `Failed password for root from 198.51.100.124`
3. **Aba Alertas** → 1 alerta novo: `ssh_brute_force_ip`, severity `high`, host `Lab Debian 11`
4. **Aba Ações** → 1 ação `block_ip` automaticamente criada pra `198.51.100.124`, status `executed` em ~30s
5. **Botão "ver detalhes"** no alerta → modal com explicação leiga (T1110.001 MITRE ATT&CK em PT-BR), passos de mitigação, links pras docs oficiais

## Como reproduzir do zero

```bash
make lab-attack  # re-planta tudo nas 4 VMs (idempotente)
```

Ou limpe alertas pra demonstrar de novo: aba Login → botão "Resetar demo" (futuro).

## Por que essa VM existe

Demonstra o **fluxo completo do SIEM**:
- Coleta (agente lê `/var/log/auth.log`)
- Detecção (regra Sigma roda em ciclo Celery 30s)
- Resposta (policy.py cria `block_ip`)
- Execução (agente roda `nft add element` no firewall)
- Auditoria (audit_log entry pra cada passo)

É o **caso mais comum de ataque a servidor Linux exposto na internet**.
