// Package eventstream gerencia o canal bidirecional gRPC StreamEvents:
// agente envia *events.Event, server confirma com EventAck.
//
// Lifecycle: Run abre o stream, le do channel `in`, envia, le acks em paralelo.
// Sai quando ctx cancela ou o channel `in` fecha.
package eventstream

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"

	"google.golang.org/protobuf/types/known/timestamppb"

	"github.com/sentinelbr/agent/internal/events"
	pb "github.com/sentinelbr/agent/internal/grpc/pb"
)

type Sender struct {
	Client pb.AgentServiceClient
	Log    *slog.Logger
}

// Run abre o stream e relinca eventos do channel `in` ate ele fechar ou ctx cancelar.
// Acks sao lidos em background — falhas no ack viram log warn, nao matam o stream.
func (s *Sender) Run(ctx context.Context, in <-chan *events.Event) error {
	stream, err := s.Client.StreamEvents(ctx)
	if err != nil {
		return fmt.Errorf("abrir StreamEvents: %w", err)
	}

	ackErr := make(chan error, 1)
	go func() {
		ackErr <- s.readAcks(stream)
	}()

	count := 0
	for {
		select {
		case <-ctx.Done():
			_ = stream.CloseSend()
			<-ackErr
			return nil
		case ev, ok := <-in:
			if !ok {
				if err := stream.CloseSend(); err != nil {
					return fmt.Errorf("close send: %w", err)
				}
				if err := <-ackErr; err != nil && !errors.Is(err, io.EOF) {
					return err
				}
				s.Log.Info("stream encerrado", "events_sent", count)
				return nil
			}
			if err := stream.Send(toProto(ev)); err != nil {
				return fmt.Errorf("send event: %w", err)
			}
			count++
			if count%50 == 0 {
				s.Log.Debug("stream progress", "events_sent", count)
			}
		}
	}
}

func (s *Sender) readAcks(stream pb.AgentService_StreamEventsClient) error {
	for {
		ack, err := stream.Recv()
		if err != nil {
			return err
		}
		if !ack.Stored {
			s.Log.Warn("server reportou evento nao armazenado", "event_id", ack.EventId)
		}
	}
}

func toProto(e *events.Event) *pb.Event {
	return &pb.Event{
		EventId:  e.ID,
		HostId:   e.HostID,
		Ts:       timestamppb.New(e.Timestamp),
		Source:   e.Source,
		Severity: string(e.Severity),
		Raw:      e.Raw,
		Fields:   e.Fields,
	}
}
