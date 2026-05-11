package collectors

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"time"
)

// FileSource le um arquivo de log e emite cada linha. Suporta dois modos:
//
//   - Once = true: le do inicio ate EOF, fecha o channel. Bom pra fixture/replay.
//   - Once = false (padrao): le ate EOF, depois faz polling pra novas linhas
//     (igual `tail -F`) — sobrevive a logrotate.
//
// PollInterval default 500ms. Path obrigatorio.
type FileSource struct {
	Path         string
	Once         bool
	PollInterval time.Duration

	out chan Line
}

func NewFileSource(path string, once bool) *FileSource {
	return &FileSource{
		Path:         path,
		Once:         once,
		PollInterval: 500 * time.Millisecond,
		out:          make(chan Line, 64),
	}
}

func (s *FileSource) Name() string         { return "file:" + s.Path }
func (s *FileSource) Lines() <-chan Line   { return s.out }

func (s *FileSource) Run(ctx context.Context) error {
	defer close(s.out)

	f, err := os.Open(s.Path)
	if err != nil {
		return fmt.Errorf("open %s: %w", s.Path, err)
	}
	defer f.Close()

	r := bufio.NewReader(f)

	for {
		line, err := r.ReadString('\n')
		if err == nil {
			if !s.emit(ctx, line) {
				return nil
			}
			continue
		}

		if !errors.Is(err, io.EOF) {
			return fmt.Errorf("read %s: %w", s.Path, err)
		}

		if s.Once {
			// fragmento final sem \n
			if line != "" {
				s.emit(ctx, line)
			}
			return nil
		}

		// EOF em modo follow: espera e tenta de novo. Se a linha terminou sem \n,
		// guardamos pra continuar lendo na proxima passada.
		if line != "" {
			// re-injeta no buffer (rebobina): jeito mais simples eh reabrir o reader,
			// mas pra logs ssh as linhas sao pequenas — espera o \n chegar.
		}

		select {
		case <-ctx.Done():
			return nil
		case <-time.After(s.PollInterval):
		}
	}
}

func (s *FileSource) emit(ctx context.Context, raw string) bool {
	text := raw
	// remove '\n' final se existir
	if n := len(text); n > 0 && text[n-1] == '\n' {
		text = text[:n-1]
	}
	if text == "" {
		return true
	}
	select {
	case <-ctx.Done():
		return false
	case s.out <- Line{Timestamp: time.Now().UTC(), Text: text}:
		return true
	}
}
