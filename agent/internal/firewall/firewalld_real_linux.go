//go:build linux

package firewall

import (
	"context"
	"fmt"
	"net"
	"os/exec"
	"strings"
	"time"
)

const firewallCmdTimeout = 15 * time.Second

func runFirewallCmd(args ...string) ([]byte, error) {
	ctx, cancel := context.WithTimeout(context.Background(), firewallCmdTimeout)
	defer cancel()
	return exec.CommandContext(ctx, "firewall-cmd", args...).CombinedOutput() // #nosec G204
}

// firewalldReal usa `firewall-cmd` (presente em Rocky/Alma/RHEL/Fedora).
// Adiciona/remove rich rule que dropa todo trafego do IP. --permanent + --reload
// sobrevive a reboot do daemon.
type firewalldReal struct{}

func newFirewalldReal() FirewallExecutor { return &firewalldReal{} }

func (firewalldReal) Backend() string { return "firewalld" }

func (firewalldReal) BlockIP(ip net.IP, _ time.Duration) error {
	rich := fmt.Sprintf("rule family=ipv4 source address=%s drop", ip)
	out, err := runFirewallCmd("--permanent", "--add-rich-rule", rich)
	if err != nil && !strings.Contains(string(out), "ALREADY_ENABLED") {
		return fmt.Errorf("firewall-cmd add-rich-rule %s: %w (%s)", ip, err, strings.TrimSpace(string(out)))
	}
	if out2, err := runFirewallCmd("--reload"); err != nil {
		return fmt.Errorf("firewall-cmd reload: %w (%s)", err, strings.TrimSpace(string(out2)))
	}
	return nil
}

func (firewalldReal) UnblockIP(ip net.IP) error {
	rich := fmt.Sprintf("rule family=ipv4 source address=%s drop", ip)
	out, err := runFirewallCmd("--permanent", "--remove-rich-rule", rich)
	if err != nil && !strings.Contains(string(out), "NOT_ENABLED") {
		return fmt.Errorf("firewall-cmd remove-rich-rule %s: %w (%s)", ip, err, strings.TrimSpace(string(out)))
	}
	if out2, err := runFirewallCmd("--reload"); err != nil {
		return fmt.Errorf("firewall-cmd reload: %w (%s)", err, strings.TrimSpace(string(out2)))
	}
	return nil
}

func (firewalldReal) ListRules() ([]Rule, error)   { return nil, ErrNotImplemented }
func (firewalldReal) Snapshot() (*Snapshot, error) { return nil, ErrNotImplemented }
