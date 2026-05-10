//go:build !linux

package firewall

// Stubs para constructors que só existem em Linux real (impls_linux.go).
// Mantêm a factory compilando em macOS dev e Windows.

func newNftables() FirewallExecutor  { return NoopFirewall{name: "nftables-unavailable"} }
func newIptables() FirewallExecutor  { return NoopFirewall{name: "iptables-unavailable"} }
func newFirewalld() FirewallExecutor { return NoopFirewall{name: "firewalld-unavailable"} }
func newUfw() FirewallExecutor       { return NoopFirewall{name: "ufw-unavailable"} }
