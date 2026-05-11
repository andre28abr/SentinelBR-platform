// Package events define o evento normalizado que o agente envia ao server via gRPC StreamEvents.
//
// Modelo proximo ao ECS (Elastic Common Schema): campos achatados em map pra facilitar
// a serializacao no proto (map<string,string> em fields). Tipagem forte no Go pra
// reduzir erros no agente, str-str na fronteira.
package events

import (
	"time"

	"github.com/google/uuid"
)

// Severity segue o padrao usual de syslog (debug < info < warn < error < critical).
type Severity string

const (
	SeverityDebug    Severity = "debug"
	SeverityInfo     Severity = "info"
	SeverityWarn     Severity = "warn"
	SeverityError    Severity = "error"
	SeverityCritical Severity = "critical"
)

// Event eh o registro normalizado que vai para o server.
// Raw eh o log original (preservar pra forensics + rerun de regras).
type Event struct {
	ID        string    // UUID v4 gerado no agente
	HostID    string    // UUID do host (vem do agentstate)
	Timestamp time.Time // quando o evento aconteceu (extraido do log, nao now())
	Source    string    // sshd | sudo | nginx | ...
	Severity  Severity
	Raw       string
	Fields    map[string]string // campos parseados (event.action, source.ip, user.name, etc)
}

// New cria um Event com ID gerado e Fields inicializado.
func New(hostID, source string, ts time.Time, raw string) *Event {
	return &Event{
		ID:        uuid.NewString(),
		HostID:    hostID,
		Timestamp: ts,
		Source:    source,
		Severity:  SeverityInfo,
		Raw:       raw,
		Fields:    map[string]string{},
	}
}
