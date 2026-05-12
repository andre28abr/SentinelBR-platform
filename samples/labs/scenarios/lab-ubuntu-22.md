# lab-ubuntu-22 — Webshell + auto-quarantine + LGPD/PII

**Distro**: Ubuntu 22.04 (Jammy) · **Pacote**: apt · **Foco do cenário**: detecção de malware em pasta web + ação automática de quarentena + mascaramento de dados pessoais (LGPD Art. 37)

## O que está plantado nesta VM

| Tipo | Onde | O que demonstra |
|---|---|---|
| **Webshell PHP** | `/var/www/upload/shell.php` (eval+base64) | Regra YARA `WebshellPHP` (severity `critical`) + auto-quarantine pela policy |
| **Mineiro de cripto** | `/tmp/lab-bait/xmrig.json` (config XMRig) | Regra YARA `CryptoMinerXMRig` (severity `high`) |
| **EICAR** | `/tmp/lab-bait/eicar.txt` (string padrão) | ClamAV detecta como `Eicar-Test-Signature` em scan manual |
| **Linhas com PII** | `/var/log/sentinelbr-test/access.log` (CPFs, emails, IPs) | Demonstra `mask_pii=true` no endpoint `/events` |
| **Suite hardening** | Todos pacotes Tier 1+2 + AppArmor | Aba Ferramentas com 9 cards verdes |
| **ClamAV ativo** | `clamscan` instalado + freshclam atualizado | Botão "Escanear pasta" funcional na aba Anti-malware |

## O que esperar na UI

1. **Aba Eventos** (`source=yara`) → 2 matches: webshell + miner
2. **Aba Alertas** → `yara_critical_match` (severity `critical`, do webshell)
3. **Aba Ações** → `quarantine_file` automaticamente criada pelo policy.py — arquivo movido pra `/var/sentinelbr/quarantine/<sha256>.bin`
4. **Aba Ferramentas → ClamAV** → clica "Escanear pasta /tmp" → ~10s depois aparece evento `clamav_match` no source=clamav
5. **Aba Eventos** com `mask_pii=true` (query param) → CPFs viram `***.***.***-XX`, emails viram `***@***.com`, IPs IPv4 viram `203.0.113.x`

## Como reproduzir

```bash
make lab-attack
# Pra disparar scan ClamAV manual:
# UI → Lab Ubuntu 22.04 → Anti-malware → ClamAV → "Escanear pasta..."
```

## Por que essa VM existe

Demonstra **3 capacidades juntas**:
1. **Anti-malware proativo** (YARA + ClamAV trabalhando juntos)
2. **Resposta autônoma** (auto-quarantine em alerta crítico)
3. **Compliance LGPD** (PII masking em events, audit log de cada ação)

É o caso típico de **servidor web com upload de usuário** (WordPress, e-commerce, painel admin) — vetor #1 de comprometimento em SMB BR.
