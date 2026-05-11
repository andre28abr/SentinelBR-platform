# sentinel-agent

Coletor Go que roda em cada host monitorado. Cross-platform (Linux primário, macOS dev, Windows preview), 1 binário por target. mTLS gRPC com a API central.

## Build

```bash
# do root:
make agent              # OS host (geralmente macOS dev)
make agent-cross        # linux/darwin/windows × amd64/arm64
make lab-build-agent    # só linux/arm64 (pras VMs do OrbStack)

# direto:
cd agent && go build -o bin/sentinel-agent ./cmd/sentinel-agent
GOOS=linux GOARCH=arm64 go build -o bin/sentinel-agent-linux-arm64 ./cmd/sentinel-agent
```

## Subcommands

```bash
sentinel-agent doctor        # detecta OS + lista capabilities (package mgr, firewall, MAC)
sentinel-agent enroll \      # registra esse host no server (one-shot)
  --server=http://server:8000 \
  --grpc=server:9443 \
  --token=<token-gerado-no-UI>
sentinel-agent run           # loop principal: heartbeat (30s) + collectors + dispatcher
sentinel-agent inventory     # envia lista de pacotes pro server (cross-ref OSV)
sentinel-agent scan \        # roda YARA contra um path e manda eventos
  --path=/var/www \
  --rules-path=./yara-rules \
  --send-events=true
sentinel-agent version
```

Após `enroll`, os certs ficam em `~/.sentinelbr/` (mode 600 na key).

### Flags de `sentinel-agent run`

| Flag | O quê |
|------|-------|
| `--ssh-source-file=/var/log/auth.log` | habilita collector sshd (sem flag = desabilitado) |
| `--ssh-source-once` | lê até EOF e sai (modo replay com fixture) |
| `--mac-source-file=/var/log/audit/audit.log` | SELinux denials; ou syslog pra AppArmor |
| `--mac-source-once` | mesmo do SSH |
| `--firewall-dry-run` | loga `block_ip`/`unblock_ip` sem executar (Mac dev) |
| `--yara-rules-path=/etc/sentinelbr/yara-rules` | habilita `run_yara_scan` commands + filewatcher |
| `--yara-watch-dir=/var/www` | (repetível) dirs monitorados via fsnotify pra scan on-write |
| `--quarantine-dir=/var/sentinelbr/quarantine` | destino dos arquivos quarantinados (default) |
| `--quarantine-dry-run` | loga quarantine sem mover (dev/lab) |

## Estrutura

```
agent/
├── cmd/sentinel-agent/         # entry point (cobra)
├── internal/
│   ├── agentstate/             # leitura/escrita de ~/.sentinelbr/{state.json,client.crt,client.key,ca.crt}
│   ├── osdetect/               # detecta distro/version/arch/kernel/package_mgr/firewall_tool/mac_system
│   ├── packagemgr/             # interface + apt (dpkg-query), dnf (rpm -qa), zypper, pacman, apk, noop
│   ├── firewall/               # interface + nftables (set "blocked_ips"), firewalld (rich-rule), iptables, ufw, noop
│   ├── mac/                    # interface + SELinuxNoop / AppArmorNoop (real impl postponed)
│   ├── parsers/
│   │   ├── sshd/               # Failed/Accepted password, Invalid user
│   │   ├── selinux/            # type=AVC denied
│   │   └── apparmor/           # apparmor=DENIED
│   ├── collectors/             # FileSource (tail -F ou once) + SSHDCollector + MACCollector
│   ├── yarascanner/            # wrapper do binário `yara` (lookpath check), ScanToEvents → ECS-style
│   ├── filewatcher/            # fsnotify, debounce 2s, ignora .swp/.tmp/~/hidden
│   ├── quarantine/             # move arquivo pra <baseDir>/<sha256>.bin + sidecar JSON (0400)
│   ├── cmddispatcher/          # pb.Command → handler (block_ip, unblock_ip, run_yara_scan, quarantine_file)
│   ├── eventstream/            # cliente gRPC StreamEvents (bidi)
│   ├── grpcclient/             # Dial mTLS (ServerName="sentinelbr-server")
│   ├── grpc/pb/                # gerado de proto/agent.proto
│   ├── heartbeat/              # loop 30s + drain de command results
│   ├── enrollclient/           # POST /api/v1/agents/enroll (HTTP REST, sem mTLS)
│   ├── config/                 # viper (config.yaml opcional)
│   └── logging/                # slog estruturado
├── yara-rules/                 # 5 starter rules (Webshell, CryptoMiner, RansomNote, etc)
└── bin/                        # gitignored
```

## Padrão de portabilidade

Cada `interface` em `internal/{packagemgr,firewall,mac}` abstrai um aspecto OS-dependent. Implementações usam **build tags** Go:

```go
//go:build linux

package packagemgr

type aptManager struct{}
func (aptManager) ListInstalled() ([]Package, error) { ... }
```

Pra adicionar suporte a um OS novo:
1. Implementar `packagemgr.PackageManager`
2. Implementar `firewall.FirewallExecutor`
3. Implementar `mac.MACSystem` (ou usar `NoopMAC{}`)
4. Adicionar branch no `factory.New(osInfo)` de cada package

Nenhuma mudança no código de business logic — esse é o ponto.

## Implementações concretas (status)

| Aspecto | apt (Deb/Ubu) | dnf (Fedora/Rocky) | zypper | pacman | apk | macOS dev | Windows |
|---------|---------------|---------------------|--------|--------|-----|-----------|---------|
| packagemgr | ✅ dpkg-query | ✅ rpm -qa | ⚠️ stub | ⚠️ stub | ⚠️ stub | noop (brew futuro) | ⚠️ stub |
| firewall | ✅ nftables | ✅ firewalld | ⚠️ stub | ⚠️ stub | ⚠️ stub | dry-run | ⚠️ stub |
| mac | SELinux/AppArmor parser ✅ | parser ✅ | parser ✅ | n/a | n/a | n/a | n/a |
| yarascanner | ✅ binário `yara` | ✅ | ✅ | ✅ | ✅ | ✅ (`brew install yara`) | ⚠️ untested |

## Testes

```bash
go test ./...                          # full suite
go test -race ./internal/quarantine/   # subset
go vet ./...                           # lint
```

## CI

Builda em macOS-latest + Ubuntu-latest + Windows-latest. Tests rodam em todos. Veja `.github/workflows/ci.yml`.
