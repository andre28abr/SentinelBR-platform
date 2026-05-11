// Package collectors implementa as fontes de eventos do agente. Uma `Source` produz
// linhas de log (com timestamp se conhecido); um `Collector` casa Source + Parser.
//
// Source sao cross-platform; Collectors juntam uma Source especifica com o parser do
// dominio (ex: SSHDCollector = FileSource em /var/log/auth.log + parser sshd).
package collectors

import (
	"context"
	"time"
)

// Line eh uma linha bruta vinda de algum arquivo/stream de log com seu timestamp.
type Line struct {
	Timestamp time.Time // se a fonte nao expoe, usa time.Now()
	Text      string
}

// Source produz linhas continuamente ate Run terminar (ctx cancelado ou erro fatal).
// Lines() entrega um channel que eh fechado quando Run sair.
type Source interface {
	Name() string
	Run(ctx context.Context) error
	Lines() <-chan Line
}
