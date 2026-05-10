//go:build darwin

package firewall

func newPF() FirewallExecutor { return NoopFirewall{name: "pf-stub"} }
