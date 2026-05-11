// Package cmddispatcher recebe pb.Command vindos do server (no HeartbeatResponse)
// e despacha pra implementacao apropriada (firewall, yara, quarentena, clamav),
// produzindo pb.CommandResult que vao no proximo HeartbeatRequest.
package cmddispatcher

import (
	"bufio"
	"bytes"
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/sentinelbr/agent/internal/events"
	"github.com/sentinelbr/agent/internal/firewall"
	pb "github.com/sentinelbr/agent/internal/grpc/pb"
	"github.com/sentinelbr/agent/internal/quarantine"
	"github.com/sentinelbr/agent/internal/yarascanner"
)

type Dispatcher struct {
	Firewall    firewall.FirewallExecutor
	DryRun      bool
	Log         *slog.Logger
	HostID      string
	YaraRulesPath string // se vazio, scans YARA sao reportados como UNSUPPORTED
	EventBus    chan<- *events.Event // canal pra emitir matches YARA. nil = nao emite.
	Quarantiner *quarantine.Quarantiner // se nil, quarantine eh UNSUPPORTED
	ScanTimeout time.Duration // default 5min
}

// Execute roda 1 comando e devolve o resultado a ser reportado.
func (d *Dispatcher) Execute(cmd *pb.Command) *pb.CommandResult {
	res := &pb.CommandResult{
		CommandId:  cmd.Id,
		ExecutedAt: timestamppb.New(time.Now().UTC()),
	}

	switch p := cmd.Payload.(type) {
	case *pb.Command_BlockIp:
		res.Status, res.ErrorMessage = d.handleBlockIP(p.BlockIp)
	case *pb.Command_UnblockIp:
		res.Status, res.ErrorMessage = d.handleUnblockIP(p.UnblockIp)
	case *pb.Command_RunYaraScan:
		res.Status, res.ErrorMessage = d.handleYaraScan(p.RunYaraScan)
	case *pb.Command_QuarantineFile:
		res.Status, res.ErrorMessage = d.handleQuarantine(p.QuarantineFile)
	case *pb.Command_RunClamavScan:
		res.Status, res.ErrorMessage = d.handleClamavScan(p.RunClamavScan)
	case *pb.Command_Fail2BanUnban:
		res.Status, res.ErrorMessage = d.handleFail2banSet(p.Fail2BanUnban.Jail, p.Fail2BanUnban.Ip, "unbanip", p.Fail2BanUnban.Reason)
	case *pb.Command_Fail2BanBan:
		res.Status, res.ErrorMessage = d.handleFail2banSet(p.Fail2BanBan.Jail, p.Fail2BanBan.Ip, "banip", p.Fail2BanBan.Reason)
	case *pb.Command_RunRkhunterScan:
		res.Status, res.ErrorMessage = d.handleRkhunterScan(p.RunRkhunterScan)
	case *pb.Command_RunLynisAudit:
		res.Status, res.ErrorMessage = d.handleLynisAudit(p.RunLynisAudit)
	case *pb.Command_RunChkrootkitScan:
		res.Status, res.ErrorMessage = d.handleChkrootkitScan(p.RunChkrootkitScan)
	case *pb.Command_RunAideCheck:
		res.Status, res.ErrorMessage = d.handleAideCheck(p.RunAideCheck)
	case *pb.Command_AddFirewallRule:
		res.Status, res.ErrorMessage = d.handleAddFirewallRule(p.AddFirewallRule)
	case *pb.Command_RemoveFirewallRule:
		res.Status, res.ErrorMessage = d.handleRemoveFirewallRule(p.RemoveFirewallRule)
	default:
		res.Status = pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED
		res.ErrorMessage = "tipo de comando nao suportado pelo agente"
	}
	return res
}

// clamavMatch eh uma linha "FOUND" do clamscan.
type clamavMatch struct {
	FilePath  string
	Signature string
}

// handleClamavScan roda `clamscan -r --no-summary --infected <path>` e emite
// events pra cada arquivo infectado. Format esperado:
//
//	/path/to/file: Signature.Name FOUND
func (d *Dispatcher) handleClamavScan(c *pb.RunClamavScanCommand) (pb.CommandStatus, string) {
	if c.Path == "" {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "path vazio"
	}
	if _, err := exec.LookPath("clamscan"); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "clamscan nao instalado"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN clamav_scan", "path", c.Path, "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}

	timeout := d.ScanTimeout
	if timeout == 0 {
		timeout = 10 * time.Minute // ClamAV eh mais lento que YARA
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	d.Log.Info("clamav_scan iniciado", "path", c.Path, "reason", c.Reason)
	matches, err := runClamavScan(ctx, c.Path)
	if err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}

	// Emite event pra cada infected file
	if d.EventBus != nil {
		for _, m := range matches {
			ev := events.New(d.HostID, "clamav", time.Now().UTC(),
				"infected: "+m.FilePath+" ("+m.Signature+")")
			ev.Severity = events.SeverityCritical
			ev.Fields["event.category"] = "malware"
			ev.Fields["event.action"] = "clamav_match"
			ev.Fields["event.outcome"] = "alert"
			ev.Fields["clamav.signature"] = m.Signature
			ev.Fields["file.path"] = m.FilePath
			ev.Fields["clamav.scan_reason"] = c.Reason
			select {
			case d.EventBus <- ev:
			default:
			}
		}
	}
	d.Log.Info("clamav_scan completo", "path", c.Path, "matches", len(matches))
	return pb.CommandStatus_COMMAND_STATUS_OK, fmt.Sprintf("matches=%d", len(matches))
}

// runClamavScan executa clamscan recursivo e parseia "FOUND" lines.
// ClamAV exit codes: 0 = clean, 1 = malware found, 2+ = error.
// Em exit=1 ainda parsemos stdout (matches).
func runClamavScan(ctx context.Context, path string) ([]clamavMatch, error) {
	cmd := exec.CommandContext(ctx, "clamscan", "-r", "--no-summary", "--infected", path)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	runErr := cmd.Run()
	// exit 1 = found malware (esperado), 0 = clean, 2+ = error.
	if runErr != nil {
		if exitErr, ok := runErr.(*exec.ExitError); ok {
			code := exitErr.ExitCode()
			if code != 0 && code != 1 {
				return nil, fmt.Errorf("clamscan exit=%d: %s", code,
					strings.TrimSpace(stderr.String()))
			}
		} else {
			return nil, fmt.Errorf("clamscan: %w", runErr)
		}
	}
	return parseClamavOutput(stdout.String()), nil
}

func parseClamavOutput(output string) []clamavMatch {
	var out []clamavMatch
	sc := bufio.NewScanner(strings.NewReader(output))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		// Format: "/path/file: Signature.Name FOUND"
		idx := strings.LastIndex(line, " FOUND")
		if idx < 0 {
			continue
		}
		head := line[:idx]
		// head = "/path/file: Signature.Name"
		colon := strings.LastIndex(head, ": ")
		if colon < 0 {
			continue
		}
		out = append(out, clamavMatch{
			FilePath:  strings.TrimSpace(head[:colon]),
			Signature: strings.TrimSpace(head[colon+2:]),
		})
	}
	return out
}

func (d *Dispatcher) handleBlockIP(c *pb.BlockIPCommand) (pb.CommandStatus, string) {
	ip := net.ParseIP(c.Ip)
	if ip == nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "IP invalido: " + c.Ip
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN block_ip", "ip", c.Ip, "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	if d.Firewall == nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "firewall nao configurado"
	}
	dur := time.Duration(c.DurationSeconds) * time.Second
	if err := d.Firewall.BlockIP(ip, dur); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}
	d.Log.Info("block_ip aplicado", "ip", c.Ip, "backend", d.Firewall.Backend())
	return pb.CommandStatus_COMMAND_STATUS_OK, ""
}

func (d *Dispatcher) handleUnblockIP(c *pb.UnblockIPCommand) (pb.CommandStatus, string) {
	ip := net.ParseIP(c.Ip)
	if ip == nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "IP invalido: " + c.Ip
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN unblock_ip", "ip", c.Ip)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	if d.Firewall == nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "firewall nao configurado"
	}
	if err := d.Firewall.UnblockIP(ip); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}
	d.Log.Info("unblock_ip aplicado", "ip", c.Ip, "backend", d.Firewall.Backend())
	return pb.CommandStatus_COMMAND_STATUS_OK, ""
}

func (d *Dispatcher) handleYaraScan(c *pb.RunYaraScanCommand) (pb.CommandStatus, string) {
	if c.Path == "" {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "path vazio"
	}
	if d.YaraRulesPath == "" {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "yara rules-path nao configurado"
	}
	scanner, err := yarascanner.NewScanner(d.HostID, d.YaraRulesPath)
	if err != nil {
		if errors.Is(err, yarascanner.ErrYaraMissing) {
			return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "yara binary nao instalado"
		}
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}

	timeout := d.ScanTimeout
	if timeout == 0 {
		timeout = 5 * time.Minute
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	if d.DryRun {
		d.Log.Info("DRY-RUN yara_scan", "path", c.Path, "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}

	d.Log.Info("yara_scan iniciado", "path", c.Path, "reason", c.Reason)
	evs, err := scanner.ScanToEvents(ctx, c.Path)
	if err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}
	if d.EventBus != nil {
		for _, ev := range evs {
			ev.Fields["yara.scan_reason"] = c.Reason
			select {
			case <-ctx.Done():
			case d.EventBus <- ev:
			}
		}
	}
	d.Log.Info("yara_scan completo", "path", c.Path, "matches", len(evs))
	return pb.CommandStatus_COMMAND_STATUS_OK, fmt.Sprintf("matches=%d", len(evs))
}

func (d *Dispatcher) handleQuarantine(c *pb.QuarantineFileCommand) (pb.CommandStatus, string) {
	if c.FilePath == "" {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "file_path vazio"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN quarantine", "file", c.FilePath, "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	if d.Quarantiner == nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "quarantine nao configurado"
	}
	side, err := d.Quarantiner.Quarantine(c.FilePath, c.Reason)
	if err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}
	d.Log.Info("quarantine aplicado", "file", c.FilePath, "sha256", side.SHA256, "dest", side.QuarantinePath)
	if d.EventBus != nil {
		ev := events.New(d.HostID, "quarantine", time.Now().UTC(),
			fmt.Sprintf("quarantined %s -> %s", side.OriginalPath, side.QuarantinePath))
		ev.Severity = events.SeverityCritical
		ev.Fields["event.category"] = "malware"
		ev.Fields["event.action"] = "file_quarantined"
		ev.Fields["event.outcome"] = "success"
		ev.Fields["file.path"] = side.OriginalPath
		ev.Fields["file.hash.sha256"] = side.SHA256
		ev.Fields["quarantine.path"] = side.QuarantinePath
		ev.Fields["quarantine.reason"] = strings.TrimSpace(c.Reason)
		select {
		case d.EventBus <- ev:
		default:
			// bus cheio — nao bloqueia o dispatcher
		}
	}
	return pb.CommandStatus_COMMAND_STATUS_OK, fmt.Sprintf("sha256=%s", side.SHA256[:16])
}

// handleFail2banSet roda `fail2ban-client set <jail> <action> <ip>`.
// action = "unbanip" | "banip". Valida jail/ip pra impedir shell injection.
func (d *Dispatcher) handleFail2banSet(jail, ip, action, reason string) (pb.CommandStatus, string) {
	if jail == "" || ip == "" {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "jail/ip vazio"
	}
	if net.ParseIP(ip) == nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "IP invalido: " + ip
	}
	// Permite so alfanumerico + dash/underscore no jail (espelha validador do server)
	for _, r := range jail {
		if !(r >= 'a' && r <= 'z') && !(r >= 'A' && r <= 'Z') &&
			!(r >= '0' && r <= '9') && r != '-' && r != '_' {
			return pb.CommandStatus_COMMAND_STATUS_FAILED, "jail invalido: " + jail
		}
	}
	if _, err := exec.LookPath("fail2ban-client"); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "fail2ban-client nao instalado"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN fail2ban", "action", action, "jail", jail, "ip", ip, "reason", reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	out, err := exec.CommandContext(ctx, "fail2ban-client", "set", jail, action, ip).CombinedOutput()
	if err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED,
			fmt.Sprintf("fail2ban-client: %s (%s)", strings.TrimSpace(string(out)), err.Error())
	}
	d.Log.Info("fail2ban_set aplicado", "action", action, "jail", jail, "ip", ip)
	// Emite event pra registrar no log historico
	if d.EventBus != nil {
		evAction := "fail2ban_unban"
		if action == "banip" {
			evAction = "fail2ban_ban"
		}
		ev := events.New(d.HostID, "fail2ban", time.Now().UTC(),
			fmt.Sprintf("%s %s on jail %s", action, ip, jail))
		ev.Severity = events.SeverityInfo
		ev.Fields["event.category"] = "intrusion_detection"
		ev.Fields["event.action"] = evAction
		ev.Fields["event.outcome"] = "success"
		ev.Fields["fail2ban.jail"] = jail
		ev.Fields["fail2ban.ip"] = ip
		ev.Fields["fail2ban.reason"] = reason
		select {
		case d.EventBus <- ev:
		default:
		}
	}
	return pb.CommandStatus_COMMAND_STATUS_OK, ""
}

// handleRkhunterScan roda `rkhunter --check --sk --rwo` (skip prompts, warnings
// only). Output line "Warning: ..." vira event individual.
func (d *Dispatcher) handleRkhunterScan(c *pb.RunRkhunterScanCommand) (pb.CommandStatus, string) {
	if _, err := exec.LookPath("rkhunter"); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "rkhunter nao instalado"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN rkhunter_scan", "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	timeout := d.ScanTimeout
	if timeout == 0 {
		timeout = 15 * time.Minute
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	d.Log.Info("rkhunter_scan iniciado", "reason", c.Reason)
	out, err := exec.CommandContext(ctx, "rkhunter", "--check", "--sk", "--rwo").CombinedOutput()
	// rkhunter exit codes: 0 = clean, 1 = warnings, 2 = error. Aceita 0 e 1.
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok && exitErr.ExitCode() == 1 {
			err = nil
		}
	}
	if err != nil {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}
	warnings := parseRkhunterWarnings(string(out))
	if d.EventBus != nil {
		for _, w := range warnings {
			ev := events.New(d.HostID, "rkhunter", time.Now().UTC(), w)
			ev.Severity = events.SeverityWarn
			ev.Fields["event.category"] = "intrusion_detection"
			ev.Fields["event.action"] = "rkhunter_warning"
			ev.Fields["event.outcome"] = "alert"
			ev.Fields["rkhunter.scan_reason"] = c.Reason
			select {
			case d.EventBus <- ev:
			default:
			}
		}
	}
	d.Log.Info("rkhunter_scan completo", "warnings", len(warnings))
	return pb.CommandStatus_COMMAND_STATUS_OK, fmt.Sprintf("warnings=%d", len(warnings))
}

func parseRkhunterWarnings(out string) []string {
	var ws []string
	sc := bufio.NewScanner(strings.NewReader(out))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if strings.HasPrefix(line, "Warning:") {
			ws = append(ws, strings.TrimSpace(strings.TrimPrefix(line, "Warning:")))
		}
	}
	return ws
}

// handleLynisAudit roda `lynis audit system --quick --no-colors`. Extrai
// "Hardening index" + warnings/suggestions.
func (d *Dispatcher) handleLynisAudit(c *pb.RunLynisAuditCommand) (pb.CommandStatus, string) {
	if _, err := exec.LookPath("lynis"); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "lynis nao instalado"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN lynis_audit", "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	timeout := d.ScanTimeout
	if timeout == 0 {
		timeout = 10 * time.Minute
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	d.Log.Info("lynis_audit iniciado", "reason", c.Reason)
	out, err := exec.CommandContext(ctx, "lynis", "audit", "system", "--quick", "--no-colors").CombinedOutput()
	// lynis exit codes: 0 success, 1+ varia. Aceita qualquer porque sempre gera output.
	score, findings := parseLynisOutput(string(out))
	if d.EventBus != nil {
		ev := events.New(d.HostID, "lynis", time.Now().UTC(),
			fmt.Sprintf("audit completo (score=%d, findings=%d)", score, len(findings)))
		ev.Severity = events.SeverityInfo
		ev.Fields["event.category"] = "configuration"
		ev.Fields["event.action"] = "lynis_audit"
		ev.Fields["event.outcome"] = "success"
		ev.Fields["lynis.score"] = fmt.Sprintf("%d", score)
		ev.Fields["lynis.findings"] = fmt.Sprintf("%d", len(findings))
		ev.Fields["lynis.reason"] = c.Reason
		select {
		case d.EventBus <- ev:
		default:
		}
	}
	if err != nil && score == 0 {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
	}
	return pb.CommandStatus_COMMAND_STATUS_OK, fmt.Sprintf("score=%d findings=%d", score, len(findings))
}

// parseLynisOutput extrai "Hardening index : N" e Suggestion/Warning lines.
func parseLynisOutput(out string) (int, []string) {
	var score int
	var findings []string
	sc := bufio.NewScanner(strings.NewReader(out))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if strings.HasPrefix(line, "Hardening index") {
			idx := strings.Index(line, ":")
			if idx >= 0 {
				tail := strings.TrimSpace(line[idx+1:])
				tail = strings.Split(tail, "[")[0]
				tail = strings.TrimSpace(tail)
				if n, err := strconv.Atoi(tail); err == nil {
					score = n
				}
			}
		}
		if strings.HasPrefix(line, "Suggestion:") || strings.HasPrefix(line, "Warning:") {
			findings = append(findings, line)
		}
	}
	return score, findings
}

// handleChkrootkitScan roda `chkrootkit -q` (quiet — so warnings).
func (d *Dispatcher) handleChkrootkitScan(c *pb.RunChkrootkitScanCommand) (pb.CommandStatus, string) {
	if _, err := exec.LookPath("chkrootkit"); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "chkrootkit nao instalado"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN chkrootkit_scan", "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	timeout := d.ScanTimeout
	if timeout == 0 {
		timeout = 10 * time.Minute
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	d.Log.Info("chkrootkit_scan iniciado", "reason", c.Reason)
	out, _ := exec.CommandContext(ctx, "chkrootkit", "-q").CombinedOutput()
	warnings := parseChkrootkitOutput(string(out))
	if d.EventBus != nil {
		for _, w := range warnings {
			ev := events.New(d.HostID, "chkrootkit", time.Now().UTC(), w)
			ev.Severity = events.SeverityWarn
			ev.Fields["event.category"] = "intrusion_detection"
			ev.Fields["event.action"] = "chkrootkit_warning"
			ev.Fields["event.outcome"] = "alert"
			ev.Fields["chkrootkit.scan_reason"] = c.Reason
			select {
			case d.EventBus <- ev:
			default:
			}
		}
	}
	d.Log.Info("chkrootkit_scan completo", "warnings", len(warnings))
	return pb.CommandStatus_COMMAND_STATUS_OK, fmt.Sprintf("warnings=%d", len(warnings))
}

func parseChkrootkitOutput(out string) []string {
	var ws []string
	sc := bufio.NewScanner(strings.NewReader(out))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		// chkrootkit -q so emite lines com "INFECTED" ou warnings sintaticos
		if line == "" {
			continue
		}
		if strings.Contains(line, "INFECTED") || strings.Contains(line, "Warning") {
			ws = append(ws, line)
		}
	}
	return ws
}

// handleAideCheck roda `aide --check`. Requer DB ja inicializado (admin
// precisou ter rodado `aide --init` antes — bem documentado pelo AIDE).
func (d *Dispatcher) handleAideCheck(c *pb.RunAideCheckCommand) (pb.CommandStatus, string) {
	if _, err := exec.LookPath("aide"); err != nil {
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "aide nao instalado"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN aide_check", "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	timeout := d.ScanTimeout
	if timeout == 0 {
		timeout = 30 * time.Minute
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	d.Log.Info("aide_check iniciado", "reason", c.Reason)
	out, err := exec.CommandContext(ctx, "aide", "--check").CombinedOutput()
	// AIDE exit codes: 0=ok, 1+ = differences found ou error.
	// Aceita exit 1-3 (diff types). 4+ ou err sem ExitError sao error real.
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			if code := exitErr.ExitCode(); code >= 4 {
				return pb.CommandStatus_COMMAND_STATUS_FAILED,
					fmt.Sprintf("aide exit=%d", code)
			}
		} else {
			return pb.CommandStatus_COMMAND_STATUS_FAILED, err.Error()
		}
	}
	added, changed, removed := parseAideSummary(string(out))
	if d.EventBus != nil {
		total := added + changed + removed
		ev := events.New(d.HostID, "aide", time.Now().UTC(),
			fmt.Sprintf("integrity check: +%d ~%d -%d", added, changed, removed))
		if total > 0 {
			ev.Severity = events.SeverityWarn
			ev.Fields["event.outcome"] = "alert"
		} else {
			ev.Severity = events.SeverityInfo
			ev.Fields["event.outcome"] = "success"
		}
		ev.Fields["event.category"] = "file"
		ev.Fields["event.action"] = "aide_check"
		ev.Fields["aide.added"] = fmt.Sprintf("%d", added)
		ev.Fields["aide.changed"] = fmt.Sprintf("%d", changed)
		ev.Fields["aide.removed"] = fmt.Sprintf("%d", removed)
		ev.Fields["aide.reason"] = c.Reason
		select {
		case d.EventBus <- ev:
		default:
		}
	}
	return pb.CommandStatus_COMMAND_STATUS_OK,
		fmt.Sprintf("added=%d changed=%d removed=%d", added, changed, removed)
}

// parseAideSummary extrai counts do bloco "Summary" do AIDE.
// Format: "  Total number of entries:  ..." e "Added entries: N", "Removed entries: N", etc.
func parseAideSummary(out string) (int, int, int) {
	var added, changed, removed int
	sc := bufio.NewScanner(strings.NewReader(out))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		switch {
		case strings.HasPrefix(line, "Added entries"):
			added = lastIntOnLine(line)
		case strings.HasPrefix(line, "Changed entries"):
			changed = lastIntOnLine(line)
		case strings.HasPrefix(line, "Removed entries"):
			removed = lastIntOnLine(line)
		}
	}
	return added, changed, removed
}

func lastIntOnLine(line string) int {
	idx := strings.LastIndex(line, ":")
	if idx < 0 {
		return 0
	}
	tail := strings.TrimSpace(line[idx+1:])
	n, _ := strconv.Atoi(tail)
	return n
}

// ExecuteAll roda todos os comandos e retorna a lista de resultados, na ordem.
func (d *Dispatcher) ExecuteAll(cmds []*pb.Command) []*pb.CommandResult {
	if len(cmds) == 0 {
		return nil
	}
	out := make([]*pb.CommandResult, 0, len(cmds))
	for _, c := range cmds {
		out = append(out, d.Execute(c))
	}
	return out
}

func StatusString(s pb.CommandStatus) string {
	switch s {
	case pb.CommandStatus_COMMAND_STATUS_OK:
		return "ok"
	case pb.CommandStatus_COMMAND_STATUS_FAILED:
		return "failed"
	case pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED:
		return "unsupported"
	default:
		return fmt.Sprintf("unknown(%d)", s)
	}
}
