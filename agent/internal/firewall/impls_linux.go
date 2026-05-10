//go:build linux

package firewall

func newNftables() FirewallExecutor  { return NoopFirewall{name: "nftables-stub"} }
func newIptables() FirewallExecutor  { return NoopFirewall{name: "iptables-stub"} }
func newFirewalld() FirewallExecutor { return NoopFirewall{name: "firewalld-stub"} }
func newUfw() FirewallExecutor       { return NoopFirewall{name: "ufw-stub"} }
