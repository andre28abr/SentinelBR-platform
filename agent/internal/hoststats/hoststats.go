// Package hoststats coleta snapshot de stats do host (CPU, memoria, disco, IP,
// uptime) pra incluir no HostStats do heartbeat. Cross-platform via gopsutil.
//
// Coletas que podem falhar (ex: load_avg no Windows) viram zero/empty — server
// trata fields ausentes graciosamente.
package hoststats

import (
	"net"
	"runtime"

	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/load"
	"github.com/shirou/gopsutil/v3/mem"

	"github.com/sentinelbr/agent/internal/clamavdetect"
	pb "github.com/sentinelbr/agent/internal/grpc/pb"
	"github.com/sentinelbr/agent/internal/sysadmin"
	"github.com/sentinelbr/agent/internal/toolsdetect"
)

// Collect retorna um snapshot atual. Erros sao silenciados (campo fica zero).
func Collect() *pb.HostStats {
	stats := &pb.HostStats{
		CpuCount: uint32(runtime.NumCPU()),
	}

	if vm, err := mem.VirtualMemory(); err == nil {
		stats.MemTotalBytes = vm.Total
		stats.MemUsedBytes = vm.Used
	}

	if du, err := disk.Usage("/"); err == nil {
		stats.DiskTotalBytes = du.Total
		stats.DiskUsedBytes = du.Used
	}

	if avg, err := load.Avg(); err == nil {
		stats.LoadAvg_1M = avg.Load1
	}

	if hi, err := host.Info(); err == nil {
		stats.UptimeSeconds = hi.Uptime
	}

	if ip := primaryIPv4(); ip != "" {
		stats.IpAddress = ip
	}

	// ClamAV detection (silent if not installed)
	clam := clamavdetect.Detect()
	stats.ClamavInstalled = clam.Installed
	stats.ClamavVersion = clam.Version
	stats.ClamavDbAgeDays = clam.DBAgeDays

	// Admin panel counts (Fase C) — best-effort, retornam 0 em macOS/erros.
	stats.ServicesRunning, stats.ServicesFailed = sysadmin.CountServices()
	stats.PackagesUpgradable = sysadmin.CountPackagesUpgradable()
	stats.ListeningPorts = sysadmin.CountListeningPorts()
	stats.CronJobs = sysadmin.CountCronJobs()

	// Security tools detection (Fases H1+H2+H4+H5+H7) — best-effort.
	tools := toolsdetect.Detect()
	stats.Fail2BanInstalled = tools.Fail2banInstalled
	stats.Fail2BanBannedIps = tools.Fail2banBannedIPs
	stats.Fail2BanJailsActive = tools.Fail2banJailsActive
	stats.Fail2BanStatusJson = tools.Fail2banStatusJSON
	stats.FirewallActive = tools.FirewallActive
	stats.FirewallStatusJson = tools.FirewallStatusJSON
	stats.AuditdActive = tools.AuditdActive
	stats.AuditdStatusJson = tools.AuditdStatusJSON
	stats.RkhunterInstalled = tools.RkhunterInstalled
	stats.LynisInstalled = tools.LynisInstalled
	stats.ChkrootkitInstalled = tools.ChkrootkitInstalled
	stats.AideInstalled = tools.AideInstalled
	stats.SelinuxMode = tools.SELinuxMode
	stats.ApparmorMode = tools.AppArmorMode

	return stats
}

// primaryIPv4 retorna o primeiro IP nao-loopback v4 que conseguir.
// Heuristica simples — pega o primeiro de interface up.
func primaryIPv4() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return ""
	}
	for _, a := range addrs {
		ipnet, ok := a.(*net.IPNet)
		if !ok || ipnet.IP.IsLoopback() {
			continue
		}
		ip := ipnet.IP.To4()
		if ip != nil {
			return ip.String()
		}
	}
	return ""
}
