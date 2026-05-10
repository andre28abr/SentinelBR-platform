//go:build !windows

package firewall

func newWindowsFirewall() FirewallExecutor { return NoopFirewall{name: "winfw-unavailable"} }
