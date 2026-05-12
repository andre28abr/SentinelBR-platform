package collectors

import (
	"context"
	"fmt"
	"strings"

	"github.com/sentinelbr/agent/internal/events"
	"github.com/sentinelbr/agent/internal/parsers/sshd"
)

// SSHDCollector eh uma Source de Linhas + parser sshd. Linhas que nao casam com
// nenhum padrao do parser sao descartadas silenciosamente (logs ssh tem muito ruido).
//
// Importante: as linhas que vem de auth.log tem prefixo de timestamp + hostname + processo:
//   "May 09 02:14:12 web-01 sshd[15234]: Failed password for ..."
// O parser quer so o miolo (depois de "sshd[NN]: "). SSHDCollector faz o trim.
type SSHDCollector struct {
	HostID string
	Source Source
	Out    chan *events.Event
}

func NewSSHDCollector(hostID string, source Source) *SSHDCollector {
	return &SSHDCollector{
		HostID: hostID,
		Source: source,
		Out:    make(chan *events.Event, 64),
	}
}

func (c *SSHDCollector) Name() string                       { return "sshd:" + c.Source.Name() }
func (c *SSHDCollector) Events() <-chan *events.Event       { return c.Out }

func (c *SSHDCollector) Run(ctx context.Context) error {
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

	// Drena a Source ate o channel fechar (Source.Run terminou e fechou Lines()).
	for line := range c.Source.Lines() {
		select {
		case <-ctx.Done():
			return nil
		default:
		}
		text := stripSyslogPrefix(line.Text)
		ev := sshd.Parse(c.HostID, line.Timestamp, text)
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

// stripSyslogPrefix tenta remover o prefixo "May 09 02:14:12 web-01 sshd[15234]: "
// e devolver so o miolo. Se nao casar, devolve a linha como veio (parser silencia).
func stripSyslogPrefix(line string) string {
	idx := strings.Index(line, "sshd[")
	if idx < 0 {
		// pode ter vindo so o miolo (ex: fixture sem prefixo)
		return line
	}
	colon := strings.Index(line[idx:], "]: ")
	if colon < 0 {
		return line
	}
	return line[idx+colon+3:]
}
