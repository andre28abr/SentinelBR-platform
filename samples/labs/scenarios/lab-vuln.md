# lab-vuln — Buffet de ataques (estilo Metasploitable)

**Distro**: Debian 11 (turbinado) · **Pacote**: apt · **Foco do cenário**: VM **propositalmente exposta** com múltiplos vetores ao mesmo tempo. Inspirada na clássica [Metasploitable](https://docs.rapid7.com/metasploit/metasploitable-2/) — máquina de prática de pentest da Rapid7.

⚠️ **Esta VM é INTENCIONALMENTE vulnerável**. Nunca exponha à rede pública. Container OrbStack isolado garante que ataques não vazam pra fora.

## O que está plantado nesta VM

Cobre **TODOS** os cenários das outras VMs juntos + extras agressivos:

| Vetor | Onde | Severity esperada |
|---|---|---|
| **Webshell PHP** | `/var/www/upload/shell.php` | critical (yara_critical_match → quarantine) |
| **Cryptominer** | `/tmp/lab-bait/xmrig.json` + binário falso `/opt/.hidden/xmrig` | high |
| **Brute-force SSH** | 12 tentativas de `198.51.100.166` | high (block_ip auto) |
| **Cron backdoor** | `/etc/cron.d/.evil-cron` chamando reverse shell | warn (rkhunter pega — se rodar manual) |
| **SUID misconfig** | `find` com SUID em `/usr/local/bin/.malicious-find` | warn |
| **Permissões 666 em /etc** | Arquivos sensíveis world-writable | lynis warning |
| **Pacotes vulneráveis** | OpenSSL antigo, sudo antigo | CVEs aparecem em /vulnerabilities |
| **Suite hardening** | Instalada mas com configs **frouxas** propositalmente | Mostra que ferramenta sozinha não basta — config importa |

## O que esperar na UI

1. **Aba Hosts** → Lab Vulneravel com badge `active` (~30s)
2. **Aba Alertas** → **6+ alertas simultâneos**:
   - 1 webshell crítico (auto-quarantined)
   - 1 SSH brute-force (auto-block_ip)
   - 1 cryptominer (warn)
   - Vulnerabilidades CVEs (vários)
3. **Aba Ações** → 2-3 ações automáticas executadas em ~30s (block_ip + quarantine_file)
4. **Aba Vulnerabilidades** → Risk Score elevado (60-80)
5. **Aba Eventos** → Centenas de events em ~1 min
6. **Compliance/MTTR** → demonstra Mean Time To Respond curto (segundos do alerta à ação)

## Como reproduzir do zero

```bash
make lab-attack  # re-planta tudo
# Pra ver "do nada" novo (limpa alertas):
# UI → Login → "Resetar demo" (futuro)
```

## Por que essa VM existe

A "vitrine de ataque". Quando você quer demonstrar **a velocidade da plataforma** ("alerta → resposta automática em 30s"), essa é a VM pra ligar. Tudo acontece ao mesmo tempo, dashboard fica colorido, gráficos se mexem.

Também serve pra **purple team exercises** — analista usa essa VM pra praticar identificar diferentes tipos de ataque na mesma máquina, comparar com a base MITRE ATT&CK PT-BR (`/kb`).

## Caveat de segurança

Os arquivos plantados são **iscas inofensivas** (texto puro que parece código malicioso). Não há binários executáveis maliciosos reais. EICAR é o único "vírus de teste" oficial — também 100% inofensivo, projetado pra testar antivírus sem risco.
