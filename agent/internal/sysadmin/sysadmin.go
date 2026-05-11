// Package sysadmin coleta counts pra dashboard "estado do sistema":
//   - Numero de servicos systemd rodando vs failed
//   - Pacotes com updates disponiveis (apt/dnf)
//   - Portas em LISTEN
//   - Cron jobs cadastrados
//
// Todas as funcoes silenciam erros (retornam 0 ou 0,0) pq sao stats opcionais.
// Cross-platform: comandos tentam vias diferentes, em macOS dev falham gracioso.
package sysadmin

import (
	"bufio"
	"context"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const cmdTimeout = 5 * time.Second

// CountServices retorna (running, failed) de servicos systemd.
// Funciona em Linux com systemd. Em macOS retorna 0,0.
func CountServices() (uint32, uint32) {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "systemctl", "list-units", "--type=service",
		"--all", "--no-legend", "--no-pager", "--plain").Output()
	if err != nil {
		return 0, 0
	}
	var running, failed uint32
	sc := bufio.NewScanner(strings.NewReader(string(out)))
	for sc.Scan() {
		line := sc.Text()
		// Format: "service.service loaded active running ..."
		fields := strings.Fields(line)
		if len(fields) < 4 {
			continue
		}
		// fields[2] = active|inactive|failed
		// fields[3] = running|exited|dead|failed
		switch {
		case fields[2] == "failed" || (len(fields) > 3 && fields[3] == "failed"):
			failed++
		case len(fields) > 3 && fields[3] == "running":
			running++
		}
	}
	return running, failed
}

// CountPackagesUpgradable retorna numero de pacotes com update disponivel.
// Tenta apt primeiro, depois dnf. macOS retorna 0.
func CountPackagesUpgradable() uint32 {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	// apt: "apt list --upgradable" — 1 linha header + N pacotes
	if _, err := exec.LookPath("apt"); err == nil {
		out, err := exec.CommandContext(ctx, "apt", "list", "--upgradable").Output()
		if err == nil {
			lines := strings.Split(strings.TrimSpace(string(out)), "\n")
			// Primeira linha eh "Listing... Done" — ignora
			if len(lines) > 0 {
				return uint32(len(lines) - 1)
			}
		}
	}
	// dnf: "dnf check-update -q" — exit 100 se ha updates, lista impressa em stdout
	if _, err := exec.LookPath("dnf"); err == nil {
		out, _ := exec.CommandContext(ctx, "dnf", "check-update", "-q").Output()
		var count uint32
		sc := bufio.NewScanner(strings.NewReader(string(out)))
		for sc.Scan() {
			line := strings.TrimSpace(sc.Text())
			if line == "" || strings.HasPrefix(line, "Last metadata") {
				continue
			}
			// Linhas validas tem 3 colunas: nome.arch versao repo
			if len(strings.Fields(line)) >= 3 {
				count++
			}
		}
		return count
	}
	return 0
}

// CountListeningPorts retorna numero de portas em LISTEN (TCP).
// Usa `ss -tlnH` (Linux). macOS retorna 0.
func CountListeningPorts() uint32 {
	ctx, cancel := context.WithTimeout(context.Background(), cmdTimeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, "ss", "-tlnH").Output()
	if err != nil {
		return 0
	}
	var count uint32
	sc := bufio.NewScanner(strings.NewReader(string(out)))
	for sc.Scan() {
		if strings.TrimSpace(sc.Text()) != "" {
			count++
		}
	}
	return count
}

// CountCronJobs conta cron jobs ativos: /etc/cron.d/*, /etc/cron.{hourly,daily,
// weekly,monthly}/*, e crontabs de users (best-effort via /var/spool/cron/*).
// Retorna soma. macOS tem launchd nao implementado.
func CountCronJobs() uint32 {
	var count uint32

	// /etc/cron.d/*: cada file pode ter N linhas non-comment.
	count += countCronFiles("/etc/cron.d")

	// /etc/cron.{hourly,daily,weekly,monthly}: 1 arquivo = 1 job.
	for _, dir := range []string{"/etc/cron.hourly", "/etc/cron.daily", "/etc/cron.weekly", "/etc/cron.monthly"} {
		entries, err := os.ReadDir(dir)
		if err != nil {
			continue
		}
		for _, e := range entries {
			if !e.IsDir() {
				count++
			}
		}
	}

	// /var/spool/cron/{crontabs,}/* - crontabs de usuarios
	for _, dir := range []string{"/var/spool/cron/crontabs", "/var/spool/cron"} {
		count += countCronFiles(dir)
	}

	return count
}

func countCronFiles(dir string) uint32 {
	var count uint32
	_ = filepath.WalkDir(dir, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil // ignora erros (perm denied, etc)
		}
		if d.IsDir() || strings.HasPrefix(filepath.Base(p), ".") {
			return nil
		}
		f, err := os.Open(p)
		if err != nil {
			return nil
		}
		defer f.Close()
		sc := bufio.NewScanner(f)
		for sc.Scan() {
			line := strings.TrimSpace(sc.Text())
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			count++
		}
		return nil
	})
	return count
}
