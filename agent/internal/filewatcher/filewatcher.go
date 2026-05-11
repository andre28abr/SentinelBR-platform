// Package filewatcher monitora diretorios via fsnotify e dispara YARA scans
// quando arquivos sao criados ou modificados.
//
// Cada match alimenta o EventBus do agente (mesma rota do scan manual).
// Debounce: agrupa eventos do mesmo arquivo dentro de DebounceWindow pra
// evitar scan repetido em writes parciais (editor salvando em multiplos passos).
package filewatcher

import (
	"context"
	"fmt"
	"log/slog"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/fsnotify/fsnotify"

	"github.com/sentinelbr/agent/internal/events"
	"github.com/sentinelbr/agent/internal/yarascanner"
)

const (
	DefaultDebounce  = 2 * time.Second
	DefaultScanTimeout = 30 * time.Second
)

type Watcher struct {
	HostID         string
	Dirs           []string         // diretorios a monitorar (recursivo)
	RulesPath      string           // arquivo .yar ou diretorio
	EventBus       chan<- *events.Event
	Log            *slog.Logger
	DebounceWindow time.Duration    // default 2s
	ScanTimeout    time.Duration    // default 30s
	IgnoreSuffixes []string         // ".swp", ".tmp", "~", etc — nao scaneia
}

// Run abre o watcher, registra os diretorios e bloqueia ate ctx ser cancelado.
// Erros nao-fatais sao logados; retorna apenas se ctx encerrar ou se o setup
// inicial falhar.
func (w *Watcher) Run(ctx context.Context) error {
	if len(w.Dirs) == 0 {
		w.Log.Info("filewatcher: nenhum diretorio configurado, desabilitado")
		return nil
	}
	if w.RulesPath == "" {
		return fmt.Errorf("filewatcher: RulesPath obrigatorio")
	}
	scanner, err := yarascanner.NewScanner(w.HostID, w.RulesPath)
	if err != nil {
		return fmt.Errorf("filewatcher: yarascanner: %w", err)
	}

	fsw, err := fsnotify.NewWatcher()
	if err != nil {
		return fmt.Errorf("filewatcher: fsnotify.NewWatcher: %w", err)
	}
	defer fsw.Close()

	for _, d := range w.Dirs {
		if err := fsw.Add(d); err != nil {
			w.Log.Warn("filewatcher: falha ao adicionar dir", "dir", d, "err", err)
			continue
		}
		w.Log.Info("filewatcher: monitorando", "dir", d)
	}

	debounce := w.DebounceWindow
	if debounce == 0 {
		debounce = DefaultDebounce
	}
	timeout := w.ScanTimeout
	if timeout == 0 {
		timeout = DefaultScanTimeout
	}

	var (
		mu      sync.Mutex
		pending = map[string]*time.Timer{}
	)

	scheduleScan := func(path string) {
		mu.Lock()
		defer mu.Unlock()
		if t, ok := pending[path]; ok {
			t.Stop()
		}
		pending[path] = time.AfterFunc(debounce, func() {
			mu.Lock()
			delete(pending, path)
			mu.Unlock()
			w.scanAndEmit(ctx, scanner, path, timeout)
		})
	}

	for {
		select {
		case <-ctx.Done():
			return nil
		case ev, ok := <-fsw.Events:
			if !ok {
				return nil
			}
			if !shouldScan(ev, w.IgnoreSuffixes) {
				continue
			}
			scheduleScan(ev.Name)
		case err, ok := <-fsw.Errors:
			if !ok {
				return nil
			}
			w.Log.Warn("filewatcher: erro fsnotify", "err", err)
		}
	}
}

func shouldScan(ev fsnotify.Event, ignoreSuffixes []string) bool {
	// CREATE ou WRITE — outros eventos (CHMOD, RENAME, REMOVE) nao precisam scan.
	if ev.Op&(fsnotify.Create|fsnotify.Write) == 0 {
		return false
	}
	base := filepath.Base(ev.Name)
	if strings.HasPrefix(base, ".") {
		return false // arquivos ocultos / metadata
	}
	for _, suf := range ignoreSuffixes {
		if strings.HasSuffix(base, suf) {
			return false
		}
	}
	return true
}

func (w *Watcher) scanAndEmit(parentCtx context.Context, scanner *yarascanner.Scanner, path string, timeout time.Duration) {
	ctx, cancel := context.WithTimeout(parentCtx, timeout)
	defer cancel()

	evs, err := scanner.ScanToEvents(ctx, path)
	if err != nil {
		// stat-error eh esperado se o arquivo foi deletado entre fsnotify e o scan.
		w.Log.Debug("filewatcher: scan falhou", "path", path, "err", err)
		return
	}
	if len(evs) == 0 {
		return
	}
	w.Log.Info("filewatcher: matches encontrados", "path", path, "n", len(evs))
	for _, ev := range evs {
		ev.Fields["yara.scan_reason"] = "filewatcher"
		select {
		case <-parentCtx.Done():
			return
		case w.EventBus <- ev:
		}
	}
}
