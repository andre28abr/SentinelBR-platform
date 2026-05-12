# SentinelBR — Suporte Multi-OS

> Especificação de cobertura de sistemas operacionais. Detalha quais distros Linux são suportadas, peculiaridades de cada uma, e roadmap de adição do Windows Server. Cada OS exige adaptações no agente (gerenciador de pacotes, formatos de log, ferramentas de firewall, etc.).

---

## 📋 Sumário

1. [Estratégia de cobertura](#estratégia-de-cobertura)
2. [Matriz de suporte](#matriz-de-suporte)
3. [Família Debian](#família-debian)
4. [Família Red Hat](#família-red-hat)
5. [Família SUSE](#família-suse)
6. [Outras distros Linux](#outras-distros-linux)
7. [Containers e imagens base](#containers-e-imagens-base)
8. [Windows Server (fase 4)](#windows-server-fase-4)
9. [Detecção automática de OS](#detecção-automática-de-os)
10. [Abstração no agente](#abstração-no-agente)
11. [Testes em cada OS](#testes-em-cada-os)

---

## Estratégia de cobertura

### Princípio: Linux primeiro, Linux bem feito

O mercado SMB brasileiro é majoritariamente Linux para servidores. Cobrir 5-6 distros principais com excelência é melhor que cobrir 20 distros mal.

**Ordem de prioridade:**

1. **Tier 1** (suportado oficialmente, testado em CI): Ubuntu, Debian, Rocky, AlmaLinux
2. **Tier 2** (suportado, testes manuais): RHEL, Fedora, openSUSE, SUSE Enterprise
3. **Tier 3** (best effort, comunidade): Arch, Alpine, Oracle Linux
4. **Tier 4** (futuro/roadmap): Windows Server, FreeBSD

### Por que essa ordem?

**Tier 1 (5 distros)** cobre ~85% dos servidores Linux do mercado:
- Ubuntu (mais popular em cloud e dev)
- Debian (servers tradicionais, preferida por SA/EU)
- Rocky (substituto natural do CentOS após mudança)
- AlmaLinux (alternativa ao Rocky, comunidade BR forte)

**Tier 2** adiciona empresas tradicionais e variantes:
- RHEL (com subscription paga)
- Fedora (workstations, servers de dev)
- SUSE Enterprise (corporate europeu)
- openSUSE (versão comunidade)

**Tier 3** atende casos específicos:
- Arch (servidores customizados, raro mas existe)
- Alpine (containers Docker, importante para K8s)
- Oracle Linux (clientes legacy do Oracle)

**Tier 4** entra quando MVP estiver maduro e precisarmos atender RFPs corporativas.

---

## Matriz de suporte

```
══════════════════════════════════════════════════════════════════════════════════════
DISTRO              VERSÕES         TIER  PKG MGR   LOG SYS    FIREWALL       SELINUX
══════════════════════════════════════════════════════════════════════════════════════
Ubuntu              20.04 LTS       T1    apt       journald   ufw/nftables   AppArmor
                    22.04 LTS                       /var/log
                    24.04 LTS

Debian              11 (Bullseye)   T1    apt       journald   nftables       opcional
                    12 (Bookworm)                   /var/log
                    13 (Trixie)

Rocky Linux         9.x             T1    dnf       journald   firewalld      SELinux
                    8.x                                                       enforcing

AlmaLinux           9.x             T1    dnf       journald   firewalld      SELinux
                    8.x                                                       enforcing

RHEL                9.x             T2    dnf       journald   firewalld      SELinux
                    8.x

Fedora              39, 40          T2    dnf       journald   firewalld      SELinux

openSUSE Leap       15.5, 15.6      T2    zypper    journald   firewalld      AppArmor
openSUSE Tumbleweed rolling                                                   ou SELinux

SUSE SLES           15 SP5, SP6     T2    zypper    journald   firewalld      AppArmor

CentOS Stream       9, 10           T3    dnf       journald   firewalld      SELinux

Oracle Linux        8.x, 9.x        T3    dnf       journald   firewalld      SELinux

Arch / Manjaro      rolling         T3    pacman    journald   nftables       opcional

Alpine              3.18, 3.19      T3    apk       syslog     iptables       n/a (small)

Windows Server      2019, 2022      T4    -         Event Log  netsh/PS       n/a
                    2025 (futuro)                              Win Defender
══════════════════════════════════════════════════════════════════════════════════════
```

---

## Família Debian

A família Debian (Debian + derivativos como Ubuntu) é a mais usada em servidores Linux modernos.

### Versões suportadas

#### Ubuntu

| Versão | Codename | Suporte | Notas |
|--------|----------|---------|-------|
| 20.04 LTS | Focal | até 2025 | Versão antiga ainda em uso |
| 22.04 LTS | Jammy | até 2027 | **Mais comum hoje** |
| 24.04 LTS | Noble | até 2029 | Recente, adoção crescendo |

Versões não-LTS (intermediárias) têm suporte best-effort.

#### Debian

| Versão | Codename | Suporte | Notas |
|--------|----------|---------|-------|
| 11 | Bullseye | até 2026 | Legacy mas comum |
| 12 | Bookworm | até 2028 | **Padrão atual** |
| 13 | Trixie | testing/futuro | |

### Peculiaridades técnicas

#### Gerenciador de pacotes (apt)

```bash
# Lista todos os pacotes instalados
dpkg-query -W -f='${Package}|${Version}|${Architecture}|${Status}\n'

# Updates disponíveis
apt list --upgradable 2>/dev/null

# Apenas security updates
apt-get -s upgrade | grep "^Inst" | grep -i securi

# Aplicar update específico
apt install --only-upgrade nginx

# Aplicar todos os security
unattended-upgrade --dry-run -d
```

#### Logs

```
/var/log/auth.log         autenticação SSH, sudo, su, PAM
/var/log/syslog           syslog geral
/var/log/kern.log         kernel
/var/log/dpkg.log         instalações apt
/var/log/apt/history.log  histórico apt
/var/log/audit/audit.log  auditd (se instalado)
/var/log/nginx/           se nginx instalado
/var/log/apache2/         se apache instalado
/var/log/postgresql/      se postgres instalado
```

Também via journald:
```bash
journalctl -u sshd -n 100
journalctl --since "1 hour ago"
```

#### Firewall

**Ubuntu** geralmente vem com `ufw` (frontend simples para iptables).
**Debian** tradicionalmente usa `nftables` direto.

Detecção:
```bash
# Verifica qual está ativo
systemctl is-active nftables
systemctl is-active ufw
which iptables-save
```

Suporte do agente:
- `nftables` (preferido se disponível)
- `iptables` (legado)
- `ufw` (manipulado via comandos `ufw`, não direto)

#### Mandatory Access Control

**Ubuntu**: AppArmor por padrão (mais simples que SELinux)
**Debian**: opcional, usuário escolhe

AppArmor fica em `/etc/apparmor.d/` com profiles por aplicação.

```bash
aa-status                # status geral
aa-complain /usr/bin/x   # modo permissive
aa-enforce /usr/bin/x    # modo enforcing
```

#### Updates não-atendidos (unattended-upgrades)

```bash
# Verifica configuração atual
cat /etc/apt/apt.conf.d/50unattended-upgrades

# Habilita updates de segurança automáticos
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Detecção pelo agente

```go
// Pseudocódigo Go
func detectDebianFamily() *OSInfo {
    // /etc/os-release é padrão LSB
    if data, err := os.ReadFile("/etc/os-release"); err == nil {
        info := parseOSRelease(data)
        if info.IDLike == "debian" || info.ID == "debian" || info.ID == "ubuntu" {
            return info
        }
    }
    return nil
}
```

### Casos especiais

**Ubuntu Pro / ESM**: usuários com subscription Ubuntu Pro têm acesso a updates estendidos. Agente deve detectar e ajustar busca de patches.

**Snap packages**: Ubuntu usa snaps para alguns pacotes. Cobertura inicial: apenas inventário (não vulnerability scanning de snaps na v1).

---

## Família Red Hat

Família baseada no Red Hat Enterprise Linux: RHEL, Rocky, AlmaLinux, Fedora, CentOS Stream, Oracle Linux.

### Versões suportadas

| Distro | Versões | Notas |
|--------|---------|-------|
| RHEL | 8.x, 9.x | Subscription paga, mas agente funciona |
| Rocky Linux | 8, 9 | **Substituto do CentOS clássico** |
| AlmaLinux | 8, 9 | Alternativa ao Rocky |
| Fedora | 39, 40 | Ciclo curto, ~13 meses por versão |
| CentOS Stream | 9, 10 | "Upstream" do RHEL agora |
| Oracle Linux | 8, 9 | Quase idêntico ao RHEL |

### Peculiaridades técnicas

#### Gerenciador de pacotes (dnf, antigamente yum)

```bash
# Lista pacotes instalados
rpm -qa --queryformat '%{NAME}|%{VERSION}-%{RELEASE}|%{ARCH}|%{EPOCH}\n'

# Updates disponíveis
dnf check-update

# Apenas security
dnf updateinfo list security

# Detalhes de um update
dnf updateinfo info CVE-2024-12345

# Aplicar update específico
dnf update nginx

# Aplicar apenas security updates
dnf update --security
```

#### Logs

```
/var/log/secure           autenticação (equivalente ao auth.log)
/var/log/messages         syslog geral
/var/log/dmesg            kernel
/var/log/dnf.log          dnf operations
/var/log/audit/audit.log  auditd (geralmente ativo)
/var/log/httpd/           apache padrão (não /var/log/apache2)
```

Também via journald (idêntico ao Debian).

#### Firewall

`firewalld` é padrão (com zonas).

```bash
# Listar zonas
firewall-cmd --list-all-zones

# Adicionar regra
firewall-cmd --zone=public --add-port=8080/tcp --permanent
firewall-cmd --reload
```

Por baixo, firewalld usa nftables (RHEL 8+) ou iptables (RHEL 7).

#### SELinux

Família Red Hat tem SELinux **enforcing por padrão**.

```bash
sestatus                  # status
getenforce                # modo atual
setenforce 1              # enforcing
setenforce 0              # permissive
```

Diferente do Ubuntu, aqui o módulo SELinux do SentinelBR vai ter mais trabalho (porque há mais denials).

#### Updates automáticos

```bash
# DNF Automatic
dnf install dnf-automatic
systemctl enable --now dnf-automatic-install.timer
```

### Diferenças entre RHEL, Rocky, AlmaLinux

Funcionalmente idênticos (Rocky e AlmaLinux são forks 1:1 do RHEL). Diferenças:
- Repos de pacotes apontam para domínios diferentes
- `/etc/os-release` tem ID e NAME diferentes
- Subscription Manager: apenas RHEL tem

Agente trata os 3 essencialmente iguais, com flag para identificar qual.

### CentOS Stream — atenção especial

CentOS clássico foi descontinuado em 2021. CentOS Stream agora é "rolling" (upstream do RHEL futuro), o que muda dinâmica:

- Updates mais frequentes
- Menos estável que Rocky/Alma
- Recomendado apenas para dev/test

Agente deve avisar usuários: "Detectado CentOS Stream — recomendamos migrar para Rocky/Alma para produção".

---

## Família SUSE

Mais comum em corporações europeias e ambientes SAP.

### Versões suportadas

| Distro | Versões | Notas |
|--------|---------|-------|
| SUSE SLES | 15 SP5, SP6 | Subscription paga |
| openSUSE Leap | 15.5, 15.6 | Comunidade, baseado em SLES |
| openSUSE Tumbleweed | rolling | Bleeding edge |

### Peculiaridades técnicas

#### Gerenciador de pacotes (zypper, RPM por baixo)

```bash
# Lista pacotes (mesmo formato RPM)
rpm -qa --queryformat '%{NAME}|%{VERSION}-%{RELEASE}|%{ARCH}\n'

# Updates disponíveis
zypper list-updates

# Apenas patches de segurança
zypper list-patches --category security

# Aplicar
zypper patch
```

#### Logs

```
/var/log/messages         syslog geral
/var/log/zypp/history     histórico zypper
/var/log/audit/audit.log  auditd
```

journald também disponível.

#### Firewall

`firewalld` por padrão (mesmo que Red Hat).

#### MAC

SUSE histórico usa **AppArmor** (não SELinux). Mas SUSE 15 SP3+ tem opção de SELinux.

Agente detecta qual está ativo e usa abordagem apropriada.

#### YaST

Ferramenta de configuração tradicional do SUSE. Não vamos integrar, mas mencionar na documentação.

---

## Outras distros Linux

### Arch / Manjaro

**Tier 3** — suporte best-effort.

```bash
# Pacotes
pacman -Q
pacman -Qi <pkg>           # detalhes

# Updates
pacman -Sy
pacman -Qu                 # disponíveis
pacman -Syu                # aplicar todos
```

Logs via journald (Arch usa systemd).

Firewall: `nftables` ou `iptables` (sem firewalld por padrão).

### Alpine Linux

**Tier 3** — importante por causa de containers.

```bash
# Pacotes
apk list -I                # instalados
apk list -u                # updates disponíveis
apk update                 # atualiza index
apk upgrade                # aplica updates
```

Diferenças importantes:
- Usa `musl libc` (não glibc) — algumas vulnerabilidades não aplicam
- Usa OpenRC (não systemd) por padrão
- Usa `syslog` simples (não journald)
- Footprint mínimo (~5 MB base)

Para Alpine, agente do SentinelBR deve ser **especialmente leve** (~10 MB OK).

### Oracle Linux

Quase idêntico ao RHEL/Rocky/Alma. Diferenças:
- "Unbreakable Enterprise Kernel" (UEK) opcional
- ULN (Unbreakable Linux Network) para subscription

Agente trata como família Red Hat.

---

## Containers e imagens base

### Imagens base mais comuns

```
══════════════════════════════════════════════════════════════════
IMAGEM             OS BASE         CASO DE USO        CVE COVERAGE
══════════════════════════════════════════════════════════════════
ubuntu:22.04       Ubuntu LTS      App genérico       ✅ completo
debian:12-slim     Debian          App leve           ✅ completo
alpine:3.19        Alpine          Microserviços      ✅ completo
python:3.12        Debian-based    Apps Python        ✅ completo
node:20            Debian-based    Apps Node          ✅ completo
nginx:alpine       Alpine          Reverse proxy      ✅ completo
postgres:16        Debian          Database           ✅ completo
redis:7-alpine     Alpine          Cache              ✅ completo
distroless         "scratch+"      Apps minimalistas  🟡 parcial
```

### Scan de imagens

Para hosts rodando Docker/Podman, o agente também pode escanear **imagens em uso**:

```bash
# Lista containers rodando
docker ps --format '{{.Image}}'

# Para cada imagem, extrai inventário de pacotes
docker run --rm <image> dpkg-query -W   # Debian-based
docker run --rm <image> rpm -qa          # RHEL-based
docker run --rm <image> apk list -I      # Alpine
```

Cross-reference com bases CVE (mesmo fluxo de hosts).

Integração opcional com **Trivy** (scanner de containers maduro):
- Trivy faz scan completo de imagem
- Resultado é importado para o SentinelBR
- Apresentado junto com vulns do host

### Distroless

Imagens "distroless" (sem shell, sem package manager) requerem abordagem diferente:
- Não dá pra rodar `dpkg -l`
- Solução: trivy faz scan da imagem em si (lê binários SBOM)

---

## Windows Server (fase 4)

Adicionado para o roadmap de longo prazo. Quando entrar:

### Versões suportadas

- Windows Server 2019
- Windows Server 2022
- Windows Server 2025 (quando lançar)

Não suportamos: Windows desktop (10/11), Windows Server 2016 e anteriores.

### Adaptações necessárias

#### Linguagem do agente

Go já compila pra Windows: `GOOS=windows GOARCH=amd64 go build`. Boa parte do código se mantém. Mudanças:
- Coleta de logs via Windows Event Log API (em vez de tail de arquivo)
- Comandos via PowerShell (em vez de bash)
- Service via Windows Service (em vez de systemd)

#### Coleta de logs

Windows Event Log tem 3 logs principais:
- **Security** (auditoria, autenticação)
- **System** (kernel, services)
- **Application** (apps)

Acesso via:
- API nativa Windows Event Log (mais eficiente)
- PowerShell `Get-WinEvent`
- WMI (legado, evitar)

Eventos importantes:
- 4624: Login bem-sucedido
- 4625: Login falhado
- 4720: Conta criada
- 4732: Membro adicionado a grupo de segurança
- 1102: Audit log foi limpo (sinal de ataque!)

#### Firewall

Windows Firewall via:
```powershell
# Lista regras
Get-NetFirewallRule

# Cria regra
New-NetFirewallRule -DisplayName "Block Bad IP" `
                    -Direction Inbound `
                    -Action Block `
                    -RemoteAddress 203.0.113.42

# netsh (legado)
netsh advfirewall firewall add rule ...
```

#### Inventário de software

```powershell
# Pacotes instalados
Get-WmiObject -Class Win32_Product

# Ou via registro (mais rápido)
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
  Select-Object DisplayName, DisplayVersion

# Updates
Get-HotFix
```

#### Patch management

WSUS (Windows Server Update Services) ou Windows Update API:

```powershell
# Updates pendentes
$Updates = Get-WindowsUpdate

# Aplicar
Install-WindowsUpdate -AcceptAll
```

#### Microsoft Defender (AV nativo)

```powershell
# Status
Get-MpComputerStatus

# Detectar ameaças
Get-MpThreatDetection

# Atualizar definições
Update-MpSignature

# Scan
Start-MpScan -ScanType QuickScan
```

Defender já vem ativo em Windows Server 2022+. Integração: SentinelBR consome alertas + status.

### Posição no roadmap

Windows Server entra na **fase 4** (após v2.0). Antes disso:
- v1.0: Linux Tier 1 funcionando perfeitamente
- v2.0: LGPD + multi-tenant
- v3.0: Linux Tier 2 + 3 cobertos
- **v4.0: Windows Server**

---

## Detecção automática de OS

Ao instalar, o agente **detecta sozinho** qual OS é e adapta o comportamento.

### Processo de detecção

```go
// Pseudocódigo Go
type OSInfo struct {
    Family       string  // "debian", "redhat", "suse", "arch", "alpine", "windows"
    Distro       string  // "ubuntu", "rocky", "opensuse-leap", etc.
    Version      string  // "22.04", "9.3"
    VersionID    string  // ID interno
    Codename     string  // "jammy", "bookworm"
    Arch         string  // "amd64", "arm64"
    Kernel       string  // versão do kernel
    PackageMgr   string  // "apt", "dnf", "zypper", "pacman", "apk"
    InitSystem   string  // "systemd", "openrc", "windows-service"
    FirewallTool string  // "nftables", "iptables", "firewalld", "ufw", "windows-firewall"
    MACSystem    string  // "selinux", "apparmor", "none"
}

func DetectOS() (*OSInfo, error) {
    // 1. /etc/os-release (padrão LSB)
    if info := parseOSRelease(); info != nil {
        return info, nil
    }
    
    // 2. /etc/redhat-release (legado)
    if data, err := os.ReadFile("/etc/redhat-release"); err == nil {
        return parseRedhatRelease(data), nil
    }
    
    // 3. /etc/debian_version
    if _, err := os.Stat("/etc/debian_version"); err == nil {
        return debianFallback(), nil
    }
    
    // 4. uname (last resort)
    return unameFallback()
}
```

### Resultado: dispatch correto

Com OS detectado, agente carrega módulos apropriados:

```go
func loadModules(os *OSInfo) []Module {
    modules := []Module{
        // Universais
        SyslogCollector{},
        SSHLogCollector{},
        
        // Específicos por OS
        switch os.PackageMgr {
        case "apt":
            return AptInventory{}, AptPatchManager{}
        case "dnf":
            return DnfInventory{}, DnfPatchManager{}
        case "zypper":
            return ZypperInventory{}, ZypperPatchManager{}
        // ...
        }
        
        switch os.FirewallTool {
        case "nftables":
            return NftablesExecutor{}
        case "firewalld":
            return FirewalldExecutor{}
        // ...
        }
        
        switch os.MACSystem {
        case "selinux":
            return SELinuxModule{}
        case "apparmor":
            return AppArmorModule{}
        }
    }
    return modules
}
```

### Reportagem ao servidor

OS info é enviado no enrollment e em cada heartbeat:

```json
{
  "host_id": "...",
  "os": {
    "family": "debian",
    "distro": "ubuntu",
    "version": "22.04",
    "codename": "jammy",
    "arch": "amd64",
    "kernel": "5.15.0-91-generic",
    "package_manager": "apt",
    "init_system": "systemd",
    "firewall_tool": "ufw",
    "mac_system": "apparmor"
  }
}
```

UI usa essas info para:
- Filtrar hosts por OS
- Mostrar comandos apropriados em wizards
- Estatísticas de cobertura ("temos 8 Ubuntu, 4 Rocky")

---

## Abstração no agente

Para suportar múltiplos OSes elegantemente, o agente usa **interfaces** (Go) que cada OS implementa.

### Interface PackageManager

```go
type PackageManager interface {
    Name() string
    ListInstalled() ([]Package, error)
    ListUpdatesAvailable() ([]Update, error)
    ListSecurityUpdates() ([]Update, error)
    Install(pkg string) error
    Update(pkg string) error
    UpdateAll(securityOnly bool) error
    Remove(pkg string) error
    Search(query string) ([]Package, error)
}

// Implementações:
type AptManager struct{ ... }     // Debian/Ubuntu
type DnfManager struct{ ... }     // RHEL family
type ZypperManager struct{ ... }  // SUSE
type PacmanManager struct{ ... }  // Arch
type ApkManager struct{ ... }     // Alpine
```

### Interface FirewallExecutor

```go
type FirewallExecutor interface {
    Backend() string
    ListRules() ([]Rule, error)
    AddRule(rule Rule) error
    RemoveRule(id string) error
    BlockIP(ip net.IP, duration time.Duration) error
    UnblockIP(ip net.IP) error
    Snapshot() (*Snapshot, error)
    Restore(snapshot *Snapshot) error
}

type NftablesExecutor struct{ ... }
type IptablesExecutor struct{ ... }
type FirewalldExecutor struct{ ... }
type UfwExecutor struct{ ... }
```

### Interface MACSystem

```go
type MACSystem interface {
    Name() string
    Status() (*Status, error)
    SetMode(mode Mode) error
    GetDenials(since time.Time) ([]Denial, error)
    GetBooleans() ([]Boolean, error)
    SetBoolean(name string, value bool, persistent bool) error
    GeneratePolicyFromDenials(denials []Denial) (string, error)
    ApplyPolicy(policy string) error
}

type SELinuxModule struct{ ... }
type AppArmorModule struct{ ... }
type NoMACModule struct{ ... }  // fallback
```

### Vantagens

- **Código de UI/lógica é o mesmo** em todos os OSes
- **Testes ficam isolados** (mockar interface)
- **Adicionar novo OS** é implementar interfaces (sem mudar lógica core)

---

## Testes em cada OS

### CI matrix

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    os:
      - {distro: ubuntu, version: "22.04"}
      - {distro: ubuntu, version: "24.04"}
      - {distro: debian, version: "12"}
      - {distro: rocky, version: "9"}
      - {distro: almalinux, version: "9"}
      - {distro: fedora, version: "40"}
      - {distro: opensuse-leap, version: "15.5"}
      - {distro: alpine, version: "3.19"}
```

Cada combinação roda:
- Testes unitários do agente
- Build do binário
- Smoke test (instala, conecta, envia heartbeat)

### Testes manuais

Tier 1 e Tier 2: testar a cada release em VMs reais.
Tier 3: testar a cada minor version.

### Containers para teste

Repositório tem Dockerfile para cada OS:

```
test/dockerfiles/
├── ubuntu-22.04.Dockerfile
├── debian-12.Dockerfile
├── rocky-9.Dockerfile
├── alma-9.Dockerfile
├── fedora-40.Dockerfile
├── opensuse-15.Dockerfile
└── alpine-3.19.Dockerfile
```

Permite testar localmente: `make test-on ubuntu-22.04`.

---

## Documentação por OS

Para cada OS suportado, doc específica de instalação:

```
docs/installation/
├── ubuntu.md
├── debian.md
├── rhel-rocky-alma.md
├── fedora.md
├── opensuse.md
├── alpine.md
├── arch.md
└── windows.md (futuro)
```

Cada doc cobre:
- Pré-requisitos do OS
- Comando de instalação
- Configurações específicas
- Troubleshooting comum
- Como atualizar
- Como remover

---

## Roadmap multi-OS

### v1.0 (MVP)
- Ubuntu 22.04
- Debian 12
- Rocky 9 / AlmaLinux 9

### v1.1
- Ubuntu 20.04, 24.04
- Debian 11
- Rocky 8 / AlmaLinux 8
- Fedora 39, 40
- RHEL 8, 9 (mesmo binário do Rocky/Alma)

### v2.0
- openSUSE Leap 15.5, 15.6
- SUSE SLES 15
- CentOS Stream 9, 10
- Oracle Linux 8, 9

### v3.0
- Arch / Manjaro
- Alpine Linux 3.19
- Containers (scan via Trivy integration)
- Kubernetes (DaemonSet do agente)

### v4.0
- Windows Server 2019, 2022
- Microsoft Defender integration
- Windows Event Log collector

### v5.0+
- macOS (talvez, mercado pequeno)
- FreeBSD (talvez, nichado)

---

## Por que esse capítulo impressiona

- **Cobertura realista**: tier 1, 2, 3 mostra priorização técnica
- **Detalhamento por distro**: peculiaridades reais (não copiar/colar genérico)
- **Abstração elegante**: interfaces + dispatch automático
- **Roadmap honesto**: Windows está documentado, mas na fase 4
- **Pragmatismo**: Tier 4 honesto sobre custos, não promete o que não entrega

Posts potenciais no LinkedIn:

- "Multi-OS no agente: 5 lições aprendidas suportando 8 distros"
- "Por que Rocky e AlmaLinux são tier 1 (e CentOS Stream não)"
- "Detecção automática de OS em Go: o código que escrevi"
- "AppArmor vs SELinux na prática: como meu projeto suporta os dois"

---

*Documento mantido por: [seu nome]  
Última atualização: 2026  
Versão: 1.0*
