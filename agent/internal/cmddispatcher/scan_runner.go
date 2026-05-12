// Package cmddispatcher: helper compartilhado pros handlers de scan.
//
// Motivo: scans como rkhunter/chkrootkit/clamav podem rodar 10-30min e emitir
// dezenas de MB de output. CombinedOutput() acumula tudo em memoria, podendo
// matar o agente em OOM. runScanBounded usa StdoutPipe + LimitReader pra
// truncar em maxBytes (default 10MB) — output excedente eh descartado, mas
// processo continua e completa normalmente.
//
// Tambem wrappa com `timeout` GNU coreutils pra matar travas em I/O bloqueante
// (vide chkrootkit issue com /dev/console).
package cmddispatcher

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os/exec"
	"time"
)

const defaultScanMaxBytes int64 = 10 * 1024 * 1024 // 10MB

// runScanBounded executa cmd com timeout coreutils + bound de output.
// Retorna stdout (truncated em maxBytes), stderr (truncated tb), e erro.
//
// timeout: enviado ao binario `timeout` se disponivel; do contrario eh so
// passado ao ctx do Go. ctx pai (do dispatcher) eh propagado.
func runScanBounded(
	parentCtx context.Context,
	timeout time.Duration,
	binary string,
	args ...string,
) ([]byte, []byte, error) {
	// Margem extra de 30s no ctx Go pra dar tempo do `timeout` coreutils
	// matar o processo gracefully antes do ctx do Go.
	ctx, cancel := context.WithTimeout(parentCtx, timeout+30*time.Second)
	defer cancel()

	var cmd *exec.Cmd
	if _, err := exec.LookPath("timeout"); err == nil {
		// Wrap com `timeout --kill-after=30s <N>s <bin> <args>`
		fullArgs := append(
			[]string{"--kill-after=30s", fmt.Sprintf("%ds", int(timeout.Seconds())), binary},
			args...,
		)
		cmd = exec.CommandContext(ctx, "timeout", fullArgs...)
	} else {
		cmd = exec.CommandContext(ctx, binary, args...)
	}

	stdoutPipe, err := cmd.StdoutPipe()
	if err != nil {
		return nil, nil, fmt.Errorf("stdoutpipe: %w", err)
	}
	stderrPipe, err := cmd.StderrPipe()
	if err != nil {
		return nil, nil, fmt.Errorf("stderrpipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return nil, nil, fmt.Errorf("start: %w", err)
	}

	// LimitReader trunca em maxBytes — qualquer overflow eh descartado mas
	// nao bloqueia o processo (ele continua escrevendo no pipe, ate fechar).
	stdoutBuf := &bytes.Buffer{}
	stderrBuf := &bytes.Buffer{}

	// Drena ambos pipes em paralelo pra evitar deadlock (kernel buffer cheia).
	stdoutDone := make(chan error, 1)
	stderrDone := make(chan error, 1)
	go func() {
		_, e := io.Copy(stdoutBuf, io.LimitReader(stdoutPipe, defaultScanMaxBytes))
		// Continua drenando o que sobrou pra nao bloquear o pipe (descarta).
		_, _ = io.Copy(io.Discard, stdoutPipe)
		stdoutDone <- e
	}()
	go func() {
		_, e := io.Copy(stderrBuf, io.LimitReader(stderrPipe, defaultScanMaxBytes/10))
		_, _ = io.Copy(io.Discard, stderrPipe)
		stderrDone <- e
	}()

	<-stdoutDone
	<-stderrDone
	waitErr := cmd.Wait()
	return stdoutBuf.Bytes(), stderrBuf.Bytes(), waitErr
}
