package firewall

import (
	"net"
	"time"

	"github.com/sentinelbr/agent/internal/osdetect"
)

func New(info *osdetect.OSInfo) FirewallExecutor {
	switch info.FirewallTool {
	case "nftables":
		return newNftables()
	case "iptables":
		return newIptables()
	case "firewalld":
		return newFirewalld()
	case "ufw":
		return newUfw()
	case "windows-firewall":
		return newWindowsFirewall()
	case "pf":
		return newPF()
	default:
		return NoopFirewall{name: info.FirewallTool}
	}
}

type NoopFirewall struct{ name string }

func (n NoopFirewall) Backend() string                                 { return "noop:" + n.name }
func (NoopFirewall) ListRules() ([]Rule, error)                        { return nil, ErrNotImplemented }
func (NoopFirewall) BlockIP(_ net.IP, _ time.Duration) error           { return ErrNotImplemented }
func (NoopFirewall) UnblockIP(_ net.IP) error                          { return ErrNotImplemented }
func (NoopFirewall) Snapshot() (*Snapshot, error)                      { return nil, ErrNotImplemented }
