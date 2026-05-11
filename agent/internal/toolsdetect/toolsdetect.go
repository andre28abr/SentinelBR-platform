// Package toolsdetect verifica quais ferramentas de seguranca/hardening estao
// instaladas e ativas no host. Reportado no heartbeat — UI mostra painel de
// interacao so pra ferramentas presentes.
//
// Tier 1 atualmente:
//   - fail2ban (banimento de IPs por brute-force)
//   - firewall (ufw / firewalld / nftables / iptables — primeiro ativo)
//   - auditd (log de syscalls)
//   - rkhunter (rootkit hunter)
//   - lynis (auditoria de hardening)
//
// Todos os detectores silenciam erros — retornam zero/falso pra UI tratar
// como "nao detectado". cmdTimeout=5s pra nao travar heartbeat.
package toolsdetect

import (
	"bufio"
	"context"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

const cmdTimeout = 5 * time.Second

// Info eh o snapshot que o agente reporta no heartbeat.
type Info struct {
	Fail2banInstalled   bool
	Fail2banBannedIPs   uint32
	Fail2banJailsActive uint32
	FirewallActive      string // "ufw" | "firewalld" | "nftables" | "iptables" | ""
	AuditdActive        bool
	RkhunterInstalled   bool
	LynisInstalled      bool
}

// Detect roda todos os detectores e retorna o resultado consolidado.
func Detect() Info {
	info := Info{
		RkhunterInstalled: binaryExists("rkhunter"),
		LynisInstalled:    binaryExists("lynis"),
		AuditdActive:      detectAuditd(),
		FirewallActive:    detectFirewall(),
	}
	info.Fail2banInstalled, info.Fail2banJailsActive, info.Fail2banBannedIPs = detectFail2ban()
	return info
}

func binaryExists(name string) bool {
	_, err := exec.LookPath(name)
	return err == nil
}

// detectAuditd: ativo se systemctl reportar active OU se houver processo auditd.
func detectAuditd() bool {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "systemctl", "is-active", "auditd").Output()
	if err == nil && strings.TrimSpace(string(out)) == "active" {
		return true
	}
	// Fallback: pgrep
	ctx2, cancel2 := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel2()
	if err := exec.CommandContext(ctx2, "pgrep", "-x", "auditd").Run(); err == nil {
		return true
	}
	return false
}

// detectFirewall: retorna o nome do primeiro firewall detectado como ativo.
// Ordem de prioridade reflete o que normalmente ESTA configurado (ufw em
// Ubuntu, firewalld em Fedora/RHEL, nftables em distros modernas).
func detectFirewall() string {
	if firewallUFWActive() {
		return "ufw"
	}
	if firewallFirewalldActive() {
		return "firewalld"
	}
	if firewallNftablesActive() {
		return "nftables"
	}
	if firewallIptablesActive() {
		return "iptables"
	}
	return ""
}

func firewallUFWActive() bool {
	if !binaryExists("ufw") {
		return false
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, _ := exec.CommandContext(ctx, "ufw", "status").Output()
	return strings.Contains(string(out), "Status: active")
}

func firewallFirewalldActive() bool {
	if !binaryExists("firewall-cmd") {
		return false
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, _ := exec.CommandContext(ctx, "firewall-cmd", "--state").Output()
	return strings.TrimSpace(string(out)) == "running"
}

func firewallNftablesActive() bool {
	if !binaryExists("nft") {
		return false
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "nft", "list", "ruleset").Output()
	if err != nil {
		return false
	}
	return len(strings.TrimSpace(string(out))) > 0
}

func firewallIptablesActive() bool {
	if !binaryExists("iptables") {
		return false
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "iptables", "-L", "-n").Output()
	if err != nil {
		return false
	}
	// iptables sempre lista 3 chains default — so considera "ativo" se houver
	// alguma regra alem dos headers (heuristica: mais de 8 linhas).
	lines := 0
	sc := bufio.NewScanner(strings.NewReader(string(out)))
	for sc.Scan() {
		lines++
	}
	return lines > 8
}

// detectFail2ban: roda fail2ban-client status, parseia lista de jails, soma
// banidos. Precisa root (agente roda como root). Retorna (installed, jails, banidos).
func detectFail2ban() (bool, uint32, uint32) {
	if !binaryExists("fail2ban-client") {
		return false, 0, 0
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "fail2ban-client", "status").Output()
	if err != nil {
		// Binario existe mas nao executou (provavelmente daemon parado).
		// Considera instalado, sem jails ativos.
		return true, 0, 0
	}
	jails := parseFail2banJails(string(out))
	if len(jails) == 0 {
		return true, 0, 0
	}
	var totalBanned uint32
	for _, j := range jails {
		totalBanned += fail2banJailBanned(j)
	}
	return true, uint32(len(jails)), totalBanned
}

// parseFail2banJails extrai nomes de jails do `fail2ban-client status`.
// Output esperado contem linha "`- Jail list:	sshd, apache-auth".
func parseFail2banJails(out string) []string {
	for _, line := range strings.Split(out, "\n") {
		if !strings.Contains(line, "Jail list") {
			continue
		}
		idx := strings.Index(line, ":")
		if idx < 0 {
			continue
		}
		raw := strings.TrimSpace(line[idx+1:])
		if raw == "" {
			return nil
		}
		parts := strings.Split(raw, ",")
		jails := make([]string, 0, len(parts))
		for _, p := range parts {
			name := strings.TrimSpace(p)
			if name != "" {
				jails = append(jails, name)
			}
		}
		return jails
	}
	return nil
}

// fail2banJailBanned roda `fail2ban-client status <jail>` e extrai
// "Currently banned: N".
func fail2banJailBanned(jail string) uint32 {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "fail2ban-client", "status", jail).Output()
	if err != nil {
		return 0
	}
	for _, line := range strings.Split(string(out), "\n") {
		if !strings.Contains(line, "Currently banned") {
			continue
		}
		idx := strings.Index(line, ":")
		if idx < 0 {
			continue
		}
		raw := strings.TrimSpace(line[idx+1:])
		n, err := strconv.ParseUint(raw, 10, 32)
		if err != nil {
			return 0
		}
		return uint32(n)
	}
	return 0
}
