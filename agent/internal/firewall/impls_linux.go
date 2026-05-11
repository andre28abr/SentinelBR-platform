//go:build linux

package firewall

func newNftables() FirewallExecutor  { return newNftablesReal() }
func newIptables() FirewallExecutor  { return NoopFirewall{name: "iptables-stub"} }
func newFirewalld() FirewallExecutor { return newFirewalldReal() }
func newUfw() FirewallExecutor       { return NoopFirewall{name: "ufw-stub"} }
