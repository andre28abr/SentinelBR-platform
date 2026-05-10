// Package firewall abstrai o gerenciador de firewall do OS.
package firewall

import (
	"errors"
	"net"
	"time"
)

var ErrNotImplemented = errors.New("firewall: operação não implementada para este OS")

type Rule struct {
	ID        string
	Chain     string
	Action    string // accept | drop | reject
	Protocol  string // tcp | udp | icmp | any
	SrcIP     string
	DstIP     string
	DstPort   int
	Comment   string
}

type Snapshot struct {
	Backend   string
	Timestamp time.Time
	Rules     []Rule
	Raw       []byte // dump bruto (iptables-save / nft list ruleset / etc.)
}

type FirewallExecutor interface {
	// Backend retorna o backend ativo (nftables, iptables, firewalld, ufw, ...).
	Backend() string

	ListRules() ([]Rule, error)
	BlockIP(ip net.IP, duration time.Duration) error
	UnblockIP(ip net.IP) error

	Snapshot() (*Snapshot, error)
}
