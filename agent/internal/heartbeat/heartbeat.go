// Package heartbeat roda o loop de heartbeat do agente: a cada N segundos,
// chama AgentService.Heartbeat via gRPC mTLS, executa pending_commands recebidos
// e reporta resultados no proximo tick.
package heartbeat

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/sentinelbr/agent/internal/cmddispatcher"
	pb "github.com/sentinelbr/agent/internal/grpc/pb"
	"github.com/sentinelbr/agent/internal/hoststats"
)

type Loop struct {
	Client     pb.AgentServiceClient
	Dispatcher *cmddispatcher.Dispatcher
	HostID     string
	Interval   time.Duration
	Log        *slog.Logger

	mu             sync.Mutex
	pendingResults []*pb.CommandResult
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
	cctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	results := l.takePendingResults()

	req := &pb.HeartbeatRequest{
		HostId:         l.HostID,
		Ts:             timestamppb.Now(),
		Stats:          hoststats.Collect(),
		CommandResults: results,
	}
	resp, err := l.Client.Heartbeat(cctx, req)
	if err != nil {
		// devolve os resultados pra fila pra retry no proximo tick
		l.queuePendingResults(results)
		return fmt.Errorf("Heartbeat RPC: %w", err)
	}

	if n := len(resp.PendingCommands); n > 0 && l.Dispatcher != nil {
		l.Log.Info("processando comandos pendentes", "count", n)
		newResults := l.Dispatcher.ExecuteAll(resp.PendingCommands)
		l.queuePendingResults(newResults)
	}

	l.Log.Debug(
		"heartbeat ok",
		"server_ts", resp.ServerTs.AsTime().Format(time.RFC3339),
		"acked", len(results),
		"pending", len(resp.PendingCommands),
	)
	return nil
}

func (l *Loop) takePendingResults() []*pb.CommandResult {
	l.mu.Lock()
	defer l.mu.Unlock()
	out := l.pendingResults
	l.pendingResults = nil
	return out
}

func (l *Loop) queuePendingResults(results []*pb.CommandResult) {
	if len(results) == 0 {
		return
	}
	l.mu.Lock()
	l.pendingResults = append(l.pendingResults, results...)
	l.mu.Unlock()
}
