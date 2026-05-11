//go:build linux

package firewall

import (
	"fmt"
	"net"
	"os/exec"
	"strings"
	"time"
)

// nftablesReal usa o comando `nft` pra manipular um set proprio em uma table
// nossa (inet sentinelbr). Vantagens: nao mexe nas regras existentes do user,
// remover IP eh atomico via element delete.
//
// Bootstrap (rodado idempotentemente em Init):
//   nft add table inet sentinelbr
//   nft add set inet sentinelbr blocked_ips { type ipv4_addr; flags interval; }
//   nft add chain inet sentinelbr input { type filter hook input priority -100; }
//   nft add rule  inet sentinelbr input ip saddr @blocked_ips drop
type nftablesReal struct {
	initialized bool
}

func newNftablesReal() FirewallExecutor { return &nftablesReal{} }

func (n *nftablesReal) Backend() string { return "nftables" }

func (n *nftablesReal) init() error {
	if n.initialized {
		return nil
	}
	steps := [][]string{
		{"nft", "add", "table", "inet", "sentinelbr"},
		{"nft", "add", "set", "inet", "sentinelbr", "blocked_ips", "{ type ipv4_addr; flags interval; }"},
		{"nft", "add", "chain", "inet", "sentinelbr", "input", "{ type filter hook input priority -100 ; policy accept ; }"},
		{"nft", "add", "rule", "inet", "sentinelbr", "input", "ip", "saddr", "@blocked_ips", "drop"},
	}
	for _, s := range steps {
		// nft retorna nao-zero se ja existe — silenciamos esses casos via prefix do stderr.
		out, err := exec.Command(s[0], s[1:]...).CombinedOutput() // #nosec G204 — args sao constantes
		if err != nil && !strings.Contains(string(out), "exists") {
			return fmt.Errorf("nft bootstrap %v: %w (%s)", s[1:], err, strings.TrimSpace(string(out)))
		}
	}
	n.initialized = true
	return nil
}

func (n *nftablesReal) BlockIP(ip net.IP, _ time.Duration) error {
	if err := n.init(); err != nil {
		return err
	}
	out, err := exec.Command("nft", "add", "element", "inet", "sentinelbr", "blocked_ips", "{ "+ip.String()+" }").CombinedOutput() // #nosec G204
	if err != nil && !strings.Contains(string(out), "exists") {
		return fmt.Errorf("nft add element %s: %w (%s)", ip, err, strings.TrimSpace(string(out)))
	}
	return nil
}

func (n *nftablesReal) UnblockIP(ip net.IP) error {
	if err := n.init(); err != nil {
		return err
	}
	out, err := exec.Command("nft", "delete", "element", "inet", "sentinelbr", "blocked_ips", "{ "+ip.String()+" }").CombinedOutput() // #nosec G204
	if err != nil && !strings.Contains(string(out), "No such") {
		return fmt.Errorf("nft delete element %s: %w (%s)", ip, err, strings.TrimSpace(string(out)))
	}
	return nil
}

func (n *nftablesReal) ListRules() ([]Rule, error)     { return nil, ErrNotImplemented }
func (n *nftablesReal) Snapshot() (*Snapshot, error)   { return nil, ErrNotImplemented }
