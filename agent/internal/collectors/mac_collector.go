package collectors

import (
	"context"
	"fmt"
	"time"

	"github.com/sentinelbr/agent/internal/events"
	"github.com/sentinelbr/agent/internal/parsers/apparmor"
	"github.com/sentinelbr/agent/internal/parsers/selinux"
)

// MACKind indica qual parser usar no MACCollector.
type MACKind string

const (
	MACKindSELinux  MACKind = "selinux"
	MACKindAppArmor MACKind = "apparmor"
)

// MACCollector le linhas de auditd/dmesg e emite eventos de denial conforme
// o MAC system detectado. Mesmo padrao do SSHDCollector: Source + parser + canal de saida.
type MACCollector struct {
	Kind   MACKind
	HostID string
	Source Source
	Out    chan *events.Event
}

func NewMACCollector(kind MACKind, hostID string, source Source) *MACCollector {
	return &MACCollector{
		Kind:   kind,
		HostID: hostID,
		Source: source,
		Out:    make(chan *events.Event, 64),
	}
}

func (c *MACCollector) Name() string                 { return string(c.Kind) + ":" + c.Source.Name() }
func (c *MACCollector) Events() <-chan *events.Event { return c.Out }

func (c *MACCollector) Run(ctx context.Context) error {
	defer close(c.Out)

	srcDone := make(chan error, 1)
	go func() {
		defer func() {
			if r := recover(); r != nil {
				srcDone <- fmt.Errorf("source panic: %v", r)
			}
		}()
		srcDone <- c.Source.Run(ctx)
	}()

	parse := c.pickParser()

	for line := range c.Source.Lines() {
		select {
		case <-ctx.Done():
			return nil
		default:
		}
		ev := parse(c.HostID, line.Timestamp, line.Text)
		if ev == nil {
			continue
		}
		select {
		case <-ctx.Done():
			return nil
		case c.Out <- ev:
		}
	}

	if err := <-srcDone; err != nil {
		return fmt.Errorf("source: %w", err)
	}
	return nil
}

// pickParser retorna o parser apropriado pro kind.
func (c *MACCollector) pickParser() func(hostID string, ts time.Time, line string) *events.Event {
	switch c.Kind {
	case MACKindSELinux:
		return selinux.Parse
	case MACKindAppArmor:
		return apparmor.Parse
	default:
		return func(string, time.Time, string) *events.Event { return nil }
	}
}
