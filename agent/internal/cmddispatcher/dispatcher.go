// Package cmddispatcher recebe pb.Command vindos do server (no HeartbeatResponse)
// e despacha pra implementacao apropriada (firewall, yara, quarentena),
// produzindo pb.CommandResult que vao no proximo HeartbeatRequest.
package cmddispatcher

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net"
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
	default:
		res.Status = pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED
		res.ErrorMessage = "tipo de comando nao suportado pelo agente"
	}
	return res
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
