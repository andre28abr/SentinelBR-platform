# SentinelBR — Fixtures de Eventos Reais

> Coleção de exemplos reais de logs e eventos que servirão como **fixtures de teste** durante o desenvolvimento. Cada exemplo mostra o log cru (como aparece no servidor) e como deve ficar **após normalização ECS** pelo agente. Use estes exemplos para validar parsers, regras de detecção e transformações.

---

## 📋 Por que fixtures importam

Logs reais de produção têm peculiaridades que documentação geral não captura:

- Caracteres especiais inesperados
- Campos opcionais que aparecem só em alguns casos
- Formatos que mudam entre distribuições Linux
- Timestamps em fusos diferentes
- Mensagens fragmentadas

Testar com fixtures reais **previne 80% dos bugs** que apareceriam só em produção.

---

## 📋 Sumário

1. [SSH (sshd)](#ssh-sshd)
2. [auditd](#auditd)
3. [Sudo](#sudo)
4. [Nginx access log](#nginx-access-log)
5. [Nginx error log](#nginx-error-log)
6. [Apache access log](#apache-access-log)
7. [PostgreSQL](#postgresql)
8. [Systemd / journald](#systemd--journald)
9. [Kernel](#kernel)
10. [SELinux AVC](#selinux-avc)
11. [Como usar nos testes](#como-usar-nos-testes)

---

## SSH (sshd)

Origem: `/var/log/auth.log` (Ubuntu/Debian) ou `/var/log/secure` (RHEL/Rocky)

### 1.1 Login bem-sucedido com senha

**Log cru:**

```
May 09 14:23:45 web-01 sshd[12345]: Accepted password for ubuntu from 198.51.100.42 port 54321 ssh2
```

**ECS normalizado:**

```json
{
  "@timestamp": "2026-05-09T14:23:45.000Z",
  "host": {
    "name": "web-01",
    "hostname": "web-01"
  },
  "process": {
    "name": "sshd",
    "pid": 12345
  },
  "event": {
    "category": ["authentication"],
    "type": ["start"],
    "action": "ssh_login",
    "outcome": "success",
    "module": "sshd"
  },
  "user": {
    "name": "ubuntu"
  },
  "source": {
    "ip": "198.51.100.42",
    "port": 54321
  },
  "service": {
    "type": "ssh",
    "version": "2"
  },
  "auth": {
    "method": "password"
  },
  "raw": "Accepted password for ubuntu from 198.51.100.42 port 54321 ssh2"
}
```

### 1.2 Login bem-sucedido com chave pública

```
May 09 14:25:01 web-01 sshd[12389]: Accepted publickey for deploy from 10.0.1.50 port 41234 ssh2: RSA SHA256:abc123def456...
```

```json
{
  "@timestamp": "2026-05-09T14:25:01.000Z",
  "event": {
    "category": ["authentication"],
    "action": "ssh_login",
    "outcome": "success"
  },
  "user": {"name": "deploy"},
  "source": {"ip": "10.0.1.50", "port": 41234},
  "auth": {
    "method": "publickey",
    "key_type": "RSA",
    "key_fingerprint": "SHA256:abc123def456..."
  }
}
```

### 1.3 Falha de senha (TIPO MAIS IMPORTANTE — base do brute force)

```
May 09 02:14:12 web-01 sshd[15234]: Failed password for root from 203.0.113.42 port 38241 ssh2
```

```json
{
  "@timestamp": "2026-05-09T02:14:12.000Z",
  "event": {
    "category": ["authentication"],
    "type": ["denied"],
    "action": "ssh_login",
    "outcome": "failure",
    "reason": "wrong_password"
  },
  "user": {
    "name": "root",
    "target": true
  },
  "source": {"ip": "203.0.113.42", "port": 38241},
  "auth": {"method": "password"}
}
```

### 1.4 Falha de senha para usuário inexistente

```
May 09 02:14:15 web-01 sshd[15238]: Failed password for invalid user admin from 203.0.113.42 port 38242 ssh2
```

```json
{
  "@timestamp": "2026-05-09T02:14:15.000Z",
  "event": {
    "category": ["authentication"],
    "outcome": "failure",
    "reason": "invalid_user"
  },
  "user": {"name": "admin", "target": true, "valid": false},
  "source": {"ip": "203.0.113.42", "port": 38242}
}
```

### 1.5 Conexão fechada antes de autenticar (típico de scanners)

```
May 09 03:01:23 web-01 sshd[16001]: Connection closed by authenticating user root 192.0.2.99 port 50001 [preauth]
```

```json
{
  "@timestamp": "2026-05-09T03:01:23.000Z",
  "event": {
    "category": ["network"],
    "action": "connection_closed",
    "outcome": "unknown"
  },
  "user": {"name": "root", "target": true},
  "source": {"ip": "192.0.2.99", "port": 50001},
  "ssh": {"phase": "preauth"}
}
```

### 1.6 Logout

```
May 09 14:45:00 web-01 sshd[12345]: pam_unix(sshd:session): session closed for user ubuntu
```

```json
{
  "@timestamp": "2026-05-09T14:45:00.000Z",
  "event": {
    "category": ["authentication"],
    "type": ["end"],
    "action": "ssh_logout"
  },
  "user": {"name": "ubuntu"},
  "process": {"name": "sshd", "pid": 12345}
}
```

### 1.7 Múltiplas falhas (brute force pattern)

```
May 09 02:14:12 web-01 sshd[15234]: Failed password for root from 203.0.113.42 port 38241 ssh2
May 09 02:14:14 web-01 sshd[15235]: Failed password for root from 203.0.113.42 port 38241 ssh2
May 09 02:14:16 web-01 sshd[15236]: Failed password for root from 203.0.113.42 port 38241 ssh2
May 09 02:14:18 web-01 sshd[15237]: Failed password for root from 203.0.113.42 port 38241 ssh2
May 09 02:14:20 web-01 sshd[15238]: Failed password for root from 203.0.113.42 port 38241 ssh2
May 09 02:14:22 web-01 sshd[15239]: Failed password for root from 203.0.113.42 port 38241 ssh2
```

→ 6 falhas em 10s do mesmo IP = regra `ssh_brute_force` deve disparar.

---

## auditd

Origem: `/var/log/audit/audit.log`

### 2.1 Execução de comando privilegiado

**Log cru:**

```
type=EXECVE msg=audit(1715269425.123:567): argc=3 a0="sudo" a1="apt" a2="update"
type=SYSCALL msg=audit(1715269425.123:567): arch=c000003e syscall=59 success=yes exit=0 a0=7ffe6a4b8c00 a1=7ffe6a4b8a00 a2=7ffe6a4b8b00 a3=0 items=2 ppid=1234 pid=1235 auid=1000 uid=0 gid=0 euid=0 suid=0 fsuid=0 egid=0 sgid=0 fsgid=0 tty=pts0 ses=12 comm="sudo" exe="/usr/bin/sudo"
```

**ECS normalizado:**

```json
{
  "@timestamp": "2026-05-09T14:23:45.123Z",
  "event": {
    "category": ["process"],
    "type": ["start"],
    "action": "executed",
    "module": "auditd"
  },
  "process": {
    "pid": 1235,
    "ppid": 1234,
    "name": "sudo",
    "executable": "/usr/bin/sudo",
    "args": ["sudo", "apt", "update"],
    "tty": "pts0"
  },
  "user": {
    "id": "0",
    "audit_id": "1000",
    "effective_id": "0"
  },
  "auditd": {
    "session": "12",
    "audit_id": "567"
  }
}
```

### 2.2 Acesso a arquivo sensível (LGPD watch)

```
type=PATH msg=audit(1715269500.000:890): item=0 name="/srv/dados-clientes/customers.db" inode=12345 dev=fc:01 mode=0640 ouid=1000 ogid=1000 rdev=00:00 nametype=NORMAL
type=SYSCALL msg=audit(1715269500.000:890): arch=c000003e syscall=2 success=yes exit=3 a0=7ffe6a4b8c00 items=1 ppid=2000 pid=2001 auid=1001 uid=1001 gid=1001 comm="cat" exe="/usr/bin/cat" key="lgpd_clientes"
```

```json
{
  "@timestamp": "2026-05-09T14:30:00.000Z",
  "event": {
    "category": ["file"],
    "action": "file_access",
    "outcome": "success"
  },
  "file": {
    "path": "/srv/dados-clientes/customers.db",
    "inode": "12345",
    "mode": "0640",
    "owner_id": "1000"
  },
  "process": {
    "name": "cat",
    "pid": 2001,
    "executable": "/usr/bin/cat"
  },
  "user": {"id": "1001", "audit_id": "1001"},
  "tags": ["lgpd_clientes"]
}
```

### 2.3 Modificação de arquivo crítico

```
type=PATH msg=audit(1715269600.000:901): item=0 name="/etc/passwd" inode=98765 dev=fc:01 mode=0644 ouid=0 ogid=0 nametype=NORMAL
type=SYSCALL msg=audit(1715269600.000:901): arch=c000003e syscall=257 success=yes exit=4 ppid=3000 pid=3001 auid=0 uid=0 gid=0 comm="vim" exe="/usr/bin/vim" key="passwd_changes"
```

```json
{
  "@timestamp": "2026-05-09T14:33:20.000Z",
  "event": {
    "category": ["file"],
    "action": "file_modified",
    "outcome": "success"
  },
  "file": {"path": "/etc/passwd", "mode": "0644"},
  "process": {"name": "vim", "pid": 3001},
  "user": {"id": "0", "audit_id": "0", "name": "root"},
  "tags": ["passwd_changes"]
}
```

### 2.4 Tentativa de privilege escalation (typical attack)

```
type=USER_AUTH msg=audit(1715269700.000:912): pid=4001 uid=1500 auid=1500 ses=20 msg='op=PAM:authentication acct="root" exe="/usr/bin/su" hostname=? addr=? terminal=pts/2 res=failed'
```

```json
{
  "@timestamp": "2026-05-09T14:35:00.000Z",
  "event": {
    "category": ["authentication", "privilege_escalation"],
    "action": "privilege_escalation_attempt",
    "outcome": "failure"
  },
  "user": {"id": "1500", "name": "ubuntu", "target": "root"},
  "process": {"name": "su", "pid": 4001, "executable": "/usr/bin/su"},
  "auth": {"method": "PAM", "result": "failed"}
}
```

---

## Sudo

Origem: `/var/log/auth.log` ou journald

### 3.1 Sudo bem-sucedido

```
May 09 14:50:00 web-01 sudo:    deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/bin/systemctl restart nginx
```

```json
{
  "@timestamp": "2026-05-09T14:50:00.000Z",
  "event": {
    "category": ["authentication", "process"],
    "action": "sudo_executed",
    "outcome": "success"
  },
  "user": {"name": "deploy", "target": "root"},
  "process": {
    "command_line": "/bin/systemctl restart nginx",
    "tty": "pts/0",
    "working_directory": "/home/deploy"
  }
}
```

### 3.2 Sudo negado

```
May 09 14:51:00 web-01 sudo:    intern : 3 incorrect password attempts ; TTY=pts/1 ; PWD=/home/intern ; USER=root ; COMMAND=/bin/cat /etc/shadow
```

```json
{
  "@timestamp": "2026-05-09T14:51:00.000Z",
  "event": {
    "category": ["authentication"],
    "action": "sudo_denied",
    "outcome": "failure",
    "reason": "incorrect_password",
    "severity": "high"
  },
  "user": {"name": "intern", "target": "root"},
  "process": {"command_line": "/bin/cat /etc/shadow"},
  "sudo": {"failed_attempts": 3}
}
```

→ Tentativa de ler `/etc/shadow` por usuário não-privilegiado = **alerta de alta severidade**.

---

## Nginx access log

Formato comum (combined):

```
192.168.1.100 - alice [09/May/2026:14:00:00 +0000] "GET /api/users HTTP/1.1" 200 1234 "https://app.example.com/" "Mozilla/5.0..."
```

### 4.1 Request normal

```json
{
  "@timestamp": "2026-05-09T14:00:00.000Z",
  "event": {
    "category": ["web"],
    "action": "http_request",
    "outcome": "success"
  },
  "source": {"ip": "192.168.1.100"},
  "user": {"name": "alice"},
  "http": {
    "request": {
      "method": "GET",
      "referrer": "https://app.example.com/"
    },
    "response": {
      "status_code": 200,
      "body": {"bytes": 1234}
    },
    "version": "1.1"
  },
  "url": {"path": "/api/users"},
  "user_agent": {"original": "Mozilla/5.0..."}
}
```

### 4.2 Tentativa de path traversal

```
203.0.113.50 - - [09/May/2026:14:05:00 +0000] "GET /../../etc/passwd HTTP/1.1" 400 162 "-" "curl/7.81.0"
```

```json
{
  "@timestamp": "2026-05-09T14:05:00.000Z",
  "event": {
    "category": ["web", "intrusion_detection"],
    "action": "path_traversal_attempt",
    "outcome": "blocked",
    "severity": "high"
  },
  "source": {"ip": "203.0.113.50"},
  "http": {
    "request": {"method": "GET"},
    "response": {"status_code": 400}
  },
  "url": {"path": "/../../etc/passwd"},
  "user_agent": {"original": "curl/7.81.0"},
  "tags": ["suspicious", "path_traversal"]
}
```

### 4.3 SQL injection attempt

```
203.0.113.51 - - [09/May/2026:14:06:00 +0000] "GET /search?q=' OR '1'='1 HTTP/1.1" 200 5432 "-" "sqlmap/1.7"
```

```json
{
  "@timestamp": "2026-05-09T14:06:00.000Z",
  "event": {
    "category": ["web", "intrusion_detection"],
    "action": "sqli_attempt",
    "severity": "high"
  },
  "source": {"ip": "203.0.113.51"},
  "url": {
    "path": "/search",
    "query": "q=' OR '1'='1"
  },
  "user_agent": {"original": "sqlmap/1.7"},
  "tags": ["suspicious", "sqli", "scanner"]
}
```

### 4.4 Scan automatizado por vulnerabilidades

```
198.51.100.55 - - [09/May/2026:14:10:00 +0000] "GET /.env HTTP/1.1" 404 153 "-" "Mozilla/5.0 (compatible; Nuclei)"
198.51.100.55 - - [09/May/2026:14:10:01 +0000] "GET /.git/config HTTP/1.1" 404 153 "-" "Mozilla/5.0 (compatible; Nuclei)"
198.51.100.55 - - [09/May/2026:14:10:02 +0000] "GET /wp-admin HTTP/1.1" 404 153 "-" "Mozilla/5.0 (compatible; Nuclei)"
198.51.100.55 - - [09/May/2026:14:10:03 +0000] "GET /admin.php HTTP/1.1" 404 153 "-" "Mozilla/5.0 (compatible; Nuclei)"
```

→ 404 múltiplos rapidamente do mesmo IP em paths sensíveis = scan de vulnerabilidade.

---

## Nginx error log

```
2026/05/09 14:15:00 [error] 12345#0: *678 open() "/var/www/html/wp-login.php" failed (2: No such file or directory), client: 203.0.113.60, server: example.com, request: "GET /wp-login.php HTTP/1.1"
```

```json
{
  "@timestamp": "2026-05-09T14:15:00.000Z",
  "event": {
    "category": ["web"],
    "action": "file_not_found",
    "outcome": "failure"
  },
  "source": {"ip": "203.0.113.60"},
  "http": {"request": {"method": "GET"}},
  "url": {"path": "/wp-login.php"},
  "log": {"level": "error"},
  "tags": ["scanner_signature"]
}
```

---

## Apache access log

Mesmo formato combined do nginx, parser similar.

```
10.0.1.5 - - [09/May/2026:14:20:00 +0000] "POST /admin/login HTTP/1.1" 401 89 "-" "Apache-HttpClient/4.5.13"
```

→ POST com 401 = falha de autenticação web. Múltiplos seguidos = brute force web.

---

## PostgreSQL

Origem: `/var/log/postgresql/postgresql-16-main.log`

### 7.1 Conexão estabelecida

```
2026-05-09 14:30:00.123 BRT [12345] LOG:  connection authorized: user=app_user database=production host=10.0.1.20 port=54321
```

```json
{
  "@timestamp": "2026-05-09T17:30:00.123Z",
  "event": {
    "category": ["database"],
    "action": "db_connection",
    "outcome": "success"
  },
  "user": {"name": "app_user"},
  "source": {"ip": "10.0.1.20", "port": 54321},
  "destination": {"database": "production"},
  "process": {"pid": 12345}
}
```

### 7.2 Falha de autenticação

```
2026-05-09 14:31:00.456 BRT [12346] FATAL:  password authentication failed for user "admin"
```

```json
{
  "@timestamp": "2026-05-09T17:31:00.456Z",
  "event": {
    "category": ["authentication"],
    "action": "db_login_failed",
    "outcome": "failure"
  },
  "user": {"name": "admin"},
  "log": {"level": "fatal"}
}
```

### 7.3 Query lenta (auditoria de performance e LGPD)

```
2026-05-09 14:35:00.789 BRT [12347] LOG:  duration: 5234.567 ms  statement: SELECT * FROM customers WHERE created_at > '2024-01-01'
```

```json
{
  "@timestamp": "2026-05-09T17:35:00.789Z",
  "event": {"action": "slow_query"},
  "database": {
    "query": "SELECT * FROM customers WHERE created_at > '2024-01-01'",
    "duration_ms": 5234.567
  },
  "tags": ["performance", "potentially_lgpd"]
}
```

### 7.4 pgaudit log de acesso a tabela LGPD-tagged

```
2026-05-09 14:36:00.000 BRT [12348] LOG:  AUDIT: SESSION,1,1,READ,SELECT,TABLE,public.customers,SELECT cpf FROM customers WHERE id = 12345,<not logged>
```

```json
{
  "@timestamp": "2026-05-09T17:36:00.000Z",
  "event": {
    "category": ["database"],
    "action": "lgpd_data_accessed"
  },
  "database": {
    "operation": "SELECT",
    "table": "public.customers",
    "query": "SELECT cpf FROM customers WHERE id = 12345"
  },
  "user": {"name": "app_user"},
  "tags": ["lgpd", "pii_access"]
}
```

---

## Systemd / journald

### 8.1 Serviço falhou

```
May 09 14:40:00 web-01 systemd[1]: nginx.service: Main process exited, code=exited, status=1/FAILURE
May 09 14:40:00 web-01 systemd[1]: nginx.service: Failed with result 'exit-code'.
```

```json
{
  "@timestamp": "2026-05-09T14:40:00.000Z",
  "event": {
    "category": ["process"],
    "action": "service_failed",
    "outcome": "failure"
  },
  "service": {"name": "nginx"},
  "process": {"exit_code": 1},
  "log": {"level": "error"}
}
```

### 8.2 Serviço reiniciado

```
May 09 14:41:00 web-01 systemd[1]: nginx.service: Scheduled restart job, restart counter is at 3.
May 09 14:41:01 web-01 systemd[1]: Started A high performance web server and a reverse proxy server.
```

→ 3+ restarts em pouco tempo = serviço instável (alerta).

---

## Kernel

### 9.1 OOM Killer ativado

```
May 09 14:50:00 web-01 kernel: [12345.678] Out of memory: Killed process 9999 (java) total-vm:8388608kB, anon-rss:7340032kB
```

```json
{
  "@timestamp": "2026-05-09T14:50:00.000Z",
  "event": {
    "category": ["host"],
    "action": "oom_killed",
    "severity": "high"
  },
  "process": {
    "name": "java",
    "pid": 9999,
    "memory": {
      "virtual_kb": 8388608,
      "resident_kb": 7340032
    }
  }
}
```

### 9.2 Possível port scan detectado por iptables

```
May 09 14:55:00 web-01 kernel: [13000.000] IPTables-Dropped: IN=eth0 OUT= MAC=... SRC=203.0.113.99 DST=10.0.1.5 LEN=60 PROTO=TCP SPT=44444 DPT=22
```

```json
{
  "@timestamp": "2026-05-09T14:55:00.000Z",
  "event": {
    "category": ["network"],
    "action": "firewall_dropped"
  },
  "source": {"ip": "203.0.113.99", "port": 44444},
  "destination": {"ip": "10.0.1.5", "port": 22},
  "network": {"protocol": "tcp"}
}
```

→ Múltiplos drops do mesmo IP em portas diferentes = port scan.

---

## SELinux AVC

Origem: `/var/log/audit/audit.log` filtrando `type=AVC`

### 10.1 Apache tentando ler arquivo fora do contexto

```
type=AVC msg=audit(1715270000.000:1234): avc: denied { read } for pid=5000 comm="httpd" name="config.json" dev="dm-0" ino=78901 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:default_t:s0 tclass=file permissive=0
```

**ECS normalizado:**

```json
{
  "@timestamp": "2026-05-09T15:00:00.000Z",
  "event": {
    "category": ["host"],
    "type": ["denied"],
    "action": "selinux_denied",
    "module": "selinux"
  },
  "process": {
    "name": "httpd",
    "pid": 5000
  },
  "selinux": {
    "scontext": "system_u:system_r:httpd_t:s0",
    "tcontext": "system_u:object_r:default_t:s0",
    "tclass": "file",
    "permission": "read",
    "permissive": false,
    "source_type": "httpd_t",
    "target_type": "default_t"
  },
  "file": {
    "name": "config.json",
    "inode": "78901"
  },
  "human_readable": {
    "summary": "Apache (httpd) tentou ler 'config.json' mas o arquivo tem contexto 'default_t' incorreto",
    "suggestion": "Aplicar contexto 'httpd_sys_content_t' com: semanage fcontext -a -t httpd_sys_content_t '/path/to/file' && restorecon -v /path/to/file"
  }
}
```

### 10.2 MySQL tentando fazer conexão de rede

```
type=AVC msg=audit(1715270100.000:1235): avc: denied { name_connect } for pid=6000 comm="mysqld" dest=80 scontext=system_u:system_r:mysqld_t:s0 tcontext=system_u:object_r:http_port_t:s0 tclass=tcp_socket permissive=0
```

```json
{
  "@timestamp": "2026-05-09T15:01:40.000Z",
  "event": {
    "category": ["network"],
    "action": "selinux_denied",
    "severity": "medium"
  },
  "process": {"name": "mysqld", "pid": 6000},
  "selinux": {
    "permission": "name_connect",
    "tclass": "tcp_socket"
  },
  "network": {"destination_port": 80},
  "human_readable": {
    "summary": "MySQL tentando conectar a porta HTTP — comportamento incomum, possivelmente comprometido"
  },
  "tags": ["suspicious"]
}
```

---

## Como usar nos testes

### Estrutura sugerida no projeto

```
tests/
├── fixtures/
│   ├── raw_logs/
│   │   ├── ssh_brute_force.log     ← múltiplas linhas, simula ataque
│   │   ├── ssh_normal_login.log
│   │   ├── auditd_lgpd_access.log
│   │   ├── nginx_path_traversal.log
│   │   ├── selinux_denial.log
│   │   └── ...
│   └── expected_ecs/
│       ├── ssh_brute_force.json    ← resultado esperado após parsing
│       ├── ssh_normal_login.json
│       └── ...
├── unit/
│   └── parsers/
│       ├── test_ssh_parser.py
│       ├── test_auditd_parser.py
│       └── ...
└── integration/
    └── test_correlation_engine.py
```

### Exemplo de teste de parser

```python
# tests/unit/parsers/test_ssh_parser.py
import json
from pathlib import Path
from sentinelbr.agent.parsers import SSHParser

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"

def test_parse_failed_password():
    raw = (FIXTURES_DIR / "raw_logs/ssh_failed_password.log").read_text().strip()
    expected = json.loads(
        (FIXTURES_DIR / "expected_ecs/ssh_failed_password.json").read_text()
    )
    
    parser = SSHParser()
    result = parser.parse(raw)
    
    # Compara campos importantes (timestamp pode variar)
    assert result["event"]["action"] == expected["event"]["action"]
    assert result["event"]["outcome"] == expected["event"]["outcome"]
    assert result["source"]["ip"] == expected["source"]["ip"]
    assert result["user"]["name"] == expected["user"]["name"]


def test_parse_brute_force_pattern():
    raw_lines = (FIXTURES_DIR / "raw_logs/ssh_brute_force.log").read_text().splitlines()
    parser = SSHParser()
    
    events = [parser.parse(line) for line in raw_lines]
    
    # Todas falhas
    assert all(e["event"]["outcome"] == "failure" for e in events)
    # Mesmo IP atacante
    ips = {e["source"]["ip"] for e in events}
    assert len(ips) == 1
    # >5 eventos = trigger condition
    assert len(events) >= 5
```

### Teste de regra Sigma

```python
# tests/integration/test_correlation_engine.py
def test_ssh_brute_force_rule_triggers(redis_client, alerts_repo):
    rule = load_sigma_rule("ssh_brute_force.yml")
    engine = CorrelationEngine(redis_client, alerts_repo)
    
    # Carrega fixture com 6 falhas em 10s
    events = load_fixture_events("ssh_brute_force.log")
    
    for event in events:
        engine.evaluate(event, rule)
    
    # Deve ter criado alerta
    alerts = alerts_repo.list_by_rule(rule.id)
    assert len(alerts) == 1
    assert alerts[0].event_count == 6
    assert alerts[0].severity == "high"
```

### Validação manual durante desenvolvimento

Comando útil para validar parser visualmente:

```bash
cat tests/fixtures/raw_logs/ssh_brute_force.log | \
  python -m sentinelbr.agent.parsers.cli ssh | \
  jq .
```

---

## Onde conseguir mais fixtures reais

Quando precisar de mais exemplos:

1. **Honeypots públicos**: t-pot, cowrie têm datasets de ataques reais
2. **Datasets de pesquisa**: 
   - SecRepo.com (vários datasets de logs)
   - LANL Cybersecurity Dataset
   - DARPA datasets
3. **Logs próprios**: rodar honeypot por algumas horas em VPS pública
4. **GitHub**: buscar `auditd-rules`, `sigma-rules`, etc. — projetos têm exemplos
5. **Sigma repository**: github.com/SigmaHQ/sigma — regras vêm com exemplos

⚠️ **Cuidado**: ao usar logs reais, **sempre anonimize** IPs/hostnames antes de comitar no repositório (mesmo que sejam atacantes — boa prática).

---

## Como expandir esta lista

Quando encontrar log de tipo novo:

1. Capture o log cru (anonimize se necessário)
2. Defina como deve ficar em ECS
3. Adicione aqui com seção apropriada
4. Crie fixture file e teste
5. Garanta que parser cobre o caso

A lista cresce organicamente com o desenvolvimento.

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
