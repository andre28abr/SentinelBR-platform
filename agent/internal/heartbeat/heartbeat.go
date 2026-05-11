// Package heartbeat roda o loop de heartbeat do agente: a cada N segundos,
// chama AgentService.Heartbeat via gRPC mTLS e processa comandos pendentes.
package heartbeat

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"

	pb "github.com/sentinelbr/agent/internal/grpc/pb"
)

type Loop struct {
	Client   pb.AgentServiceClient
	HostID   string
	Interval time.Duration
	Log      *slog.Logger
}

func (l *Loop) Run(ctx context.Context) error {
	ticker := time.NewTicker(l.Interval)
	defer ticker.Stop()

	if err := l.tick(ctx); err != nil {
		l.Log.Warn("heartbeat inicial falhou", "err", err)
	}

	for {
		select {
		case <-ctx.Done():
			return nil
		case <-ticker.C:
			if err := l.tick(ctx); err != nil {
				l.Log.Warn("heartbeat falhou", "err", err)
			}
		}
	}
}

func (l *Loop) tick(ctx context.Context) error {
	cctx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	req := &pb.HeartbeatRequest{
		HostId: l.HostID,
		Ts:     timestamppb.Now(),
	}
	resp, err := l.Client.Heartbeat(cctx, req)
	if err != nil {
		return fmt.Errorf("Heartbeat RPC: %w", err)
	}

	if pending := len(resp.PendingCommands); pending > 0 {
		l.Log.Info("comandos pendentes recebidos (handler em fase futura)", "count", pending)
	}
	l.Log.Debug("heartbeat ok", "server_ts", resp.ServerTs.AsTime().Format(time.RFC3339))
	return nil
}
