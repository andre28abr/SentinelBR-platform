// Package cmddispatcher recebe pb.Command vindos do server (no HeartbeatResponse)
// e despacha pra implementacao apropriada (firewall, etc), produzindo pb.CommandResult
// que vao no proximo HeartbeatRequest.
package cmddispatcher

import (
	"fmt"
	"log/slog"
	"net"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/sentinelbr/agent/internal/firewall"
	pb "github.com/sentinelbr/agent/internal/grpc/pb"
)

type Dispatcher struct {
	Firewall firewall.FirewallExecutor
	DryRun   bool
	Log      *slog.Logger
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
