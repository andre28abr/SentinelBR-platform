# Modo Laboratório (Demo Mode)

> **Não é pra produção.** O modo lab existe pra portfólio, demos pra
> recrutadores, e treino de purple team. Toda VM é propositalmente
> vulnerável; o controle de start/stop expõe `orb` shell pro backend.

## O que é

O Modo Laboratório (Lab Mode) habilita uma área `/lab` na UI que:

- Lista as VMs OrbStack do demo (`lab-debian-11`, `lab-fedora`, etc.)
- Permite iniciar / parar VMs com 1 clique
- Permite re-rodar o `attack.sh` numa VM específica (refresca alertas)
- Tem um botão **"Resetar demo"** que apaga alertas + ações da org atual
  para começar a gravação do zero

A LoginPage também ganha um banner amarelo avisando que a instância
está em modo demo — útil pra deixar claro que dados não são reais.

## Como ligar

Defina a env var antes de subir o servidor:

```bash
export SENTINELBR_LAB_MODE=true
make server   # backend lê o flag no startup
```

No script `start-dev.command` (Mac), o flag já vem ligado por padrão —
comente a linha `export SENTINELBR_LAB_MODE=true` se quiser simular
produção localmente.

Após o backend subir com `lab_mode=true`:

1. A aba **"Lab"** (com ícone de tubo de ensaio) aparece no header da UI
2. A LoginPage mostra o banner amarelo
3. O endpoint `GET /api/v1/lab/status` retorna `{"enabled": true}`

## Como verificar que está funcionando

```bash
# Sem auth (endpoint /status é público):
curl http://localhost:8000/api/v1/lab/status
# {"enabled":true}

# Com auth (admin):
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/lab/vms
# [{"name":"lab-debian-11","state":"running","distro":"debian:11","arch":"arm64"}, ...]
```

## Endpoints disponíveis (só quando lab_mode=true)

| Método | Path | Auth | Descrição |
|---|---|---|---|
| GET  | `/api/v1/lab/status`                | público | flag on/off |
| GET  | `/api/v1/lab/vms`                   | admin   | lista VMs lab-* |
| POST | `/api/v1/lab/vms/{name}/start`      | admin   | `orb start <name>` |
| POST | `/api/v1/lab/vms/{name}/stop`       | admin   | `orb stop <name>` |
| POST | `/api/v1/lab/vms/{name}/attack`     | admin   | `attack.sh <slug>` |
| POST | `/api/v1/lab/reset`                 | admin   | apaga alerts+actions |

Quando `lab_mode=false`, **todos exceto `/status`** retornam 404 — a
API se comporta como se a feature nem existisse.

## Modelo de segurança

Por que essa funcionalidade só existe em modo lab:

1. **Endpoints rodam comandos shell no host real.** `orb start` e `orb stop`
   afetam VMs do desenvolvedor. Em produção multi-tenant seria caos.
2. **`SENTINELBR_LAB_MODE` é opt-in explícito** via env var. Nunca por
   padrão; nunca via API; nunca persistido em DB.
3. **VM names validados** contra `^lab-[a-z0-9-]+$` — bloqueia
   `"; rm -rf /"` e similares. Defesa em profundidade junto com `argv`
   list (sem `shell=True`).
4. **Timeout em todo `orb` call** (30s normal, 5min para `attack.sh`).
   Evita handler hung se VM travada.
5. **Endpoints exigem `AdminUser`.** Operator/viewer não operam VMs.
6. **`/reset` NÃO apaga hosts nem audit logs.** Hosts precisariam
   re-enroll pra voltar (custoso); audit é obrigatório pela LGPD.

## O que cada VM demonstra

Veja [`samples/labs/EXPECTED.md`](../samples/labs/EXPECTED.md) para o
índice completo. Resumo:

| VM | Cenário principal | Severity esperada |
|---|---|---|
| `lab-debian-11` | Brute-force SSH + auto-block | high |
| `lab-ubuntu-22` | Webshell + quarantine + LGPD/PII | critical |
| `lab-fedora`    | SELinux + auditd + hardening showcase | warn (educacional) |
| `lab-rocky-9`   | Vulnerability management (CVEs OSV) | high |
| `lab-alpine-3`  | Container/edge (musl + OpenRC) | medium |
| `lab-vuln`      | Buffet de ataques (estilo Metasploitable) | critical |

## Workflow típico de demo (recrutador)

1. **Antes**: `make lab-up` (provisionamento ~5min, **só primeira vez**)
2. **Subir tudo**: dois cliques no `start-dev.command`
3. **Login**: `admin@sentinelbr.io` / `admin1234` (banner amarelo
   confirma que está em modo lab)
4. **Primeira gravação**: mostre Hosts → Alertas → Ações → LGPD
5. **Reset**: `/lab` → "Resetar demo" → confirma
6. **Re-atacar uma VM**: `/lab` → card da VM → "Re-atacar" (espera ~30s)
7. **Próxima gravação**: novos alertas aparecem em ~30s

## Variáveis de ambiente relacionadas

| Var | Default | Descrição |
|---|---|---|
| `SENTINELBR_LAB_MODE`         | `false` | Habilita endpoints `/lab/*` |
| `SENTINELBR_LAB_ORB_BINARY`   | `orb`   | Path do `orb` no PATH |
| `SENTINELBR_LAB_SCRIPTS_DIR`  | `<repo>/samples/labs` | Onde `attack.sh` mora |

## Limitações conhecidas

- **OrbStack apenas**. `orb` é específico do macOS — Linux/Windows
  precisariam adaptar pra Vagrant/multipass/WSL2.
- **`orb` no PATH**. O backend não tenta achar o binário em locais
  alternativos. Se você instalou o OrbStack via DMG e não tá no PATH,
  configure `SENTINELBR_LAB_ORB_BINARY=/Applications/OrbStack.app/...`.
- **Reset só na org atual**. Multi-tenant: `/reset` só apaga alerts e
  actions de hosts que pertencem à org do user logado.
- **VMs precisam ter prefixo `lab-`**. Filtro hardcoded pra não tocar
  VMs pessoais do desenvolvedor.

## Como desligar (modo produção)

Simplesmente não defina a env var:

```bash
unset SENTINELBR_LAB_MODE   # ou comente em start-dev.command
make server
```

A aba "Lab" some da UI, o banner some da LoginPage, e os endpoints
respondem 404. A feature deixa de existir do ponto de vista do usuário.
