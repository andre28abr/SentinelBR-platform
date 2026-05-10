# sentinel-agent

Coletor Go que roda em cada host monitorado.

## Build

```bash
make agent          # OS host
make agent-cross    # linux/darwin/windows × amd64/arm64
```

## Estrutura

```
agent/
├── cmd/sentinel-agent/      # entry point (cobra)
├── internal/
│   ├── osdetect/            # detecta distro e popula OSInfo
│   ├── packagemgr/          # interface + apt/dnf/zypper/pacman/apk
│   ├── firewall/            # interface + nftables/iptables/firewalld/ufw
│   ├── mac/                 # interface + SELinux/AppArmor
│   ├── collectors/          # coleta de logs (journald, /var/log, EventLog)
│   ├── grpc/                # cliente gRPC + mTLS
│   ├── config/              # viper
│   └── logging/             # slog estruturado
└── bin/                     # binários compilados (gitignored)
```

## Padrão de portabilidade

Cada interface abstrai um aspecto OS-dependent. Implementações concretas usam **build tags** Go:

```go
//go:build linux
// +build linux
```

Para adicionar suporte a um OS novo:
1. Implementar `packagemgr.PackageManager`
2. Implementar `firewall.FirewallExecutor`
3. Implementar `mac.MACSystem` (ou usar `NoopMAC{}`)
4. Adicionar branch no `factory.New(osInfo)` de cada package

Nenhuma mudança no código de business logic é necessária — esse é o ponto.

## Comandos

```bash
sentinel-agent doctor   # diagnóstica o ambiente (detecta OS, lista capabilities)
sentinel-agent run      # roda o agente (loop principal)
sentinel-agent version  # versão
```
