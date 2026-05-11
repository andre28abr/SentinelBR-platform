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

	pb "github.com/sentinelbr/agent/internal/grpc/pb"
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
