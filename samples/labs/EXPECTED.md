# EXPECTED — o que aparece no UI depois de `make lab-up`

Aguarde ~1min após o `lab-up` terminar (precisa de 1 ciclo de heartbeat de 30s
pro agente reportar + 1 ciclo de detection de 30s pra avaliar regras).

## 1. Hosts ativos (página `/hosts`)

Você deve ver **4 novos hosts** com badge verde "active":

- Lab Debian 11
- Lab Ubuntu 22.04
- Lab Fedora
- Lab Vulneravel (estilo Metasploitable)

Se algum estiver "pending" depois de 1 min, veja [README §Troubleshooting](README.md#troubleshooting).

## 2. Vulnerabilidades CVE (aba "Vulnerabilidades" em cada host)

Cada VM tem `openssl`, `sudo`, `bash` na versão que veio com a distro. O
inventário foi disparado no `lab-up`, então o scan OSV roda em background
(~30s) e popula CVEs reais.

| VM | CVEs esperados |
|----|----------------|
| Lab Debian 11 | dezenas de high/medium em openssl 1.1.1n e bash 5.1 |
| Lab Ubuntu 22.04 | medium/low (Ubuntu LTS faz mais backports) |
| Lab Fedora | low (RPMs têm patches mais frequentes) |
| Lab Vulnerável | igual Debian 11 + mais ruído |

**Risk score**: Debian 11 e Vuln devem ficar acima de 50 (laranja). Ubuntu/Fedora
costumam ficar 10-30 (verde/amarelo).

## 3. YARA (aba "Anti-malware (YARA)" em cada host)

### Manual

Clique "Escanear pasta…" e use `/var/www` ou `/tmp`. Em ~1 min:

- A Action vira `executed` em "Ações de resposta"
- Em "Eventos recentes" filtre por source=yara, vai aparecer:
  - `WebshellPHP` em `/var/www/html/admin.php`
  - `CryptoMinerXMRig` em `/tmp/lab-bait/xmrig.json`
  - `SuspiciousCurlBash` em `/tmp/lab-bait/install.sh`

### Automático (filewatcher)

O agente está rodando com `--yara-watch-dir=/var/www --yara-watch-dir=/tmp`.
Crie um arquivo dentro:

```bash
orb -m lab-debian-11 -u root bash -c 'echo "<?php eval(\$_GET[x]); ?>" > /var/www/test.php'
```

Em ~3s aparece um novo evento yara_match com `yara.scan_reason=filewatcher`.

### Auto-quarantine (vuln-lab)

A vuln-lab tem mais alvos críticos. Quando o YARA detectar `WebshellPHP` (severity
critical), a policy cria automaticamente uma Action `quarantine_file`.

> Nota: as VMs do lab estão com `--quarantine-dry-run` pra **não mover arquivos
> de verdade** (do contrário você teria que re-plantar tudo após cada detecção).
> Pra testar quarentena real, restart do agente sem essa flag.

## 4. Alertas SSH brute-force (página `/alerts`)

O `lab-up` injetou 12 linhas "Failed password for invalid user admin from
203.0.113.99" em `/var/log/auth.log` de cada VM. Em ~1 min você vê:

- `ssh_brute_force_ip` (high) — 12 tentativas do IP 203.0.113.99
- `ssh_user_enumeration` (medium) — múltiplos usuários inválidos do mesmo IP
- `ssh_root_login_failure` (medium) — 1 tentativa contra root

E na aba "Ações de resposta" aparece automaticamente:

- Action `block_ip` target=203.0.113.99 (criada pela policy)
- Status: pending → sent → executed (se firewall não estiver em dry-run)

> O `vm::install_systemd` configura o agente com `--firewall-dry-run` por
> padrão. O block é logado mas não executado de verdade na VM (pra não te
> deixar fora do SSH se você usar o IP do attacker do seu próprio range).

## 5. Re-atacar pra ver mais alertas

```bash
make lab-attack
```

Roda novos brute-force com IP randomizado, recria webshells, etc. Em 1 min novos
alertas aparecem. Útil pra demo/screenshot/vídeo.

## 6. Detecção cross-distro

A grande sacada do lab: você consegue ver a **mesma rule** disparando alertas
em distros diferentes (Debian/Ubuntu/Fedora) — prova que o agente é
cross-distro de verdade, não só código que compila.

Confira:

- `/alerts?rule_id=ssh_brute_force_ip` mostra um alerta por VM
- O scan OSV usou ecosystem diferente em cada (`Debian:11` vs `Ubuntu:22.04` vs `Fedora`)
- Os events YARA têm `host_id` diferente, mas mesma `yara.rule_name`
