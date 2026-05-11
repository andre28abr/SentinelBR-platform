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
	"encoding/json"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

const cmdTimeout = 5 * time.Second

// maxIPsPerJail limita o tamanho da lista enviada no heartbeat. Jails com
// muitos banidos truncam — UI ainda mostra o count total.
const maxIPsPerJail = 50

// Info eh o snapshot que o agente reporta no heartbeat.
type Info struct {
	Fail2banInstalled   bool
	Fail2banBannedIPs   uint32
	Fail2banJailsActive uint32
	Fail2banStatusJSON  string // detalhado, formato JSON {"jails":[{...}]}
	FirewallActive      string // "ufw" | "firewalld" | "nftables" | "iptables" | ""
	FirewallStatusJSON  string // detalhado, formato varia por backend
	AuditdActive        bool
	AuditdStatusJSON    string // {"rules":["-a always,exit ..."]}
	RkhunterInstalled   bool
	LynisInstalled      bool
	// Fase H7
	ChkrootkitInstalled bool
	AideInstalled       bool
	SELinuxMode         string // "Enforcing" | "Permissive" | "Disabled" | ""
	AppArmorMode        string // "enabled" | "disabled" | ""
}

// Fail2banJailDetail eh o detalhe completo de um jail (serializado em JSON).
type Fail2banJailDetail struct {
	Name        string   `json:"name"`
	BannedCount uint32   `json:"banned_count"`
	BannedIPs   []string `json:"banned_ips"` // truncado em maxIPsPerJail
}

type fail2banStatusPayload struct {
	Jails []Fail2banJailDetail `json:"jails"`
}

// Detect roda todos os detectores e retorna o resultado consolidado.
func Detect() Info {
	info := Info{
		RkhunterInstalled:   binaryExists("rkhunter"),
		LynisInstalled:      binaryExists("lynis"),
		ChkrootkitInstalled: binaryExists("chkrootkit"),
		AideInstalled:       binaryExists("aide"),
		AuditdActive:        detectAuditd(),
		FirewallActive:      detectFirewall(),
		SELinuxMode:         detectSELinuxMode(),
		AppArmorMode:        detectAppArmorMode(),
	}
	jails := detectFail2banDetailed()
	if jails != nil {
		info.Fail2banInstalled = true
		info.Fail2banJailsActive = uint32(len(jails))
		var total uint32
		for _, j := range jails {
			total += j.BannedCount
		}
		info.Fail2banBannedIPs = total
		if b, err := json.Marshal(fail2banStatusPayload{Jails: jails}); err == nil {
			info.Fail2banStatusJSON = string(b)
		}
	} else if binaryExists("fail2ban-client") {
		// Binario existe mas daemon nao respondeu — reporta instalado sem detalhes.
		info.Fail2banInstalled = true
	}
	info.FirewallStatusJSON = detectFirewallStatusJSON(info.FirewallActive)
	if info.AuditdActive {
		info.AuditdStatusJSON = detectAuditdStatusJSON()
	}
	return info
}

// detectSELinuxMode roda `getenforce` (Linux com SELinux). Retorna vazio em
// sistemas sem SELinux (macOS, Linux sem getenforce).
func detectSELinuxMode() string {
	if !binaryExists("getenforce") {
		return ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "getenforce").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

// detectAppArmorMode usa `aa-status --enabled` (exit 0 = enabled).
func detectAppArmorMode() string {
	if !binaryExists("aa-status") {
		return ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	if err := exec.CommandContext(ctx, "aa-status", "--enabled").Run(); err == nil {
		return "enabled"
	}
	return "disabled"
}

// detectAuditdStatusJSON roda `auditctl -l` e empacota regras.
func detectAuditdStatusJSON() string {
	if !binaryExists("auditctl") {
		return ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "auditctl", "-l").Output()
	if err != nil {
		return ""
	}
	rules := make([]string, 0, 16)
	sc := bufio.NewScanner(strings.NewReader(string(out)))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "No rules") {
			continue
		}
		rules = append(rules, line)
	}
	type auditdPayload struct {
		Rules []string `json:"rules"`
	}
	b, err := json.Marshal(auditdPayload{Rules: rules})
	if err != nil {
		return ""
	}
	return string(b)
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

// detectFail2banDetailed roda fail2ban-client status, parseia lista de jails,
// e pra cada jail busca lista de banidos. Retorna nil se binario ausente OU
// daemon nao respondeu (Detect trata os 2 casos diferentes).
func detectFail2banDetailed() []Fail2banJailDetail {
	if !binaryExists("fail2ban-client") {
		return nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "fail2ban-client", "status").Output()
	if err != nil {
		return nil
	}
	jailNames := parseFail2banJails(string(out))
	details := make([]Fail2banJailDetail, 0, len(jailNames))
	for _, name := range jailNames {
		count, ips := fail2banJailStatus(name)
		details = append(details, Fail2banJailDetail{
			Name:        name,
			BannedCount: count,
			BannedIPs:   ips,
		})
	}
	return details
}

// fail2banJailStatus roda `fail2ban-client status <jail>` e extrai
// "Currently banned: N" + lista de IPs. IPs vem truncados a maxIPsPerJail.
func fail2banJailStatus(jail string) (uint32, []string) {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "fail2ban-client", "status", jail).Output()
	if err != nil {
		return 0, nil
	}
	var count uint32
	var ips []string
	for _, line := range strings.Split(string(out), "\n") {
		switch {
		case strings.Contains(line, "Currently banned"):
			if v := parseFail2banKVValue(line); v != "" {
				if n, err := strconv.ParseUint(v, 10, 32); err == nil {
					count = uint32(n)
				}
			}
		case strings.Contains(line, "Banned IP list"):
			raw := parseFail2banKVValue(line)
			if raw == "" {
				continue
			}
			for _, ip := range strings.Fields(raw) {
				if len(ips) >= maxIPsPerJail {
					break
				}
				ips = append(ips, ip)
			}
		}
	}
	return count, ips
}

// parseFail2banKVValue extrai o valor a direita do ":" numa linha do output do
// fail2ban-client (formato tree art com pipes/backticks).
func parseFail2banKVValue(line string) string {
	idx := strings.Index(line, ":")
	if idx < 0 {
		return ""
	}
	return strings.TrimSpace(line[idx+1:])
}

// detectFirewallStatusJSON retorna snapshot textual das regras ativas do
// firewall detectado. Formato: {"backend":"<nome>","raw":"<output>"} —
// frontend renderiza como bloco mono.
func detectFirewallStatusJSON(backend string) string {
	if backend == "" {
		return ""
	}
	type firewallPayload struct {
		Backend string `json:"backend"`
		Raw     string `json:"raw"`
	}
	raw := firewallRawStatus(backend)
	if raw == "" {
		return ""
	}
	b, err := json.Marshal(firewallPayload{Backend: backend, Raw: raw})
	if err != nil {
		return ""
	}
	return string(b)
}

func firewallRawStatus(backend string) string {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	var out []byte
	var err error
	switch backend {
	case "ufw":
		out, err = exec.CommandContext(ctx, "ufw", "status", "numbered").Output()
	case "firewalld":
		out, err = exec.CommandContext(ctx, "firewall-cmd", "--list-all").Output()
	case "nftables":
		out, err = exec.CommandContext(ctx, "nft", "list", "ruleset").Output()
	case "iptables":
		out, err = exec.CommandContext(ctx, "iptables", "-L", "-n", "-v").Output()
	default:
		return ""
	}
	if err != nil {
		return ""
	}
	// Limita tamanho do snapshot pra nao inflar heartbeat (ruleset gigante).
	const maxBytes = 16 * 1024
	s := string(out)
	if len(s) > maxBytes {
		s = s[:maxBytes] + "\n... (truncated)"
	}
	return s
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

