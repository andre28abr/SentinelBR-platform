// Package clamavdetect verifica se ClamAV esta instalado no host e retorna
// metadados (versao + idade do signature DB).
//
// Estrategia: roda `clamscan --version` que retorna algo como:
//
//	ClamAV 1.0.4/27295/Wed Mar  6 04:09:31 2024
//
// Da pra extrair versao + revisao do DB + data. Fallback se output for
// inesperado: marca como nao instalado.
package clamavdetect

import (
	"os/exec"
	"strings"
	"time"
)

// Info eh o que o agente reporta no heartbeat sobre o estado do ClamAV.
type Info struct {
	Installed bool
	Version   string // string completa do --version
	DBAgeDays uint32 // idade do signature DB em dias (0 se nao conseguiu detectar)
}

// Detect retorna o estado atual do ClamAV no sistema.
// Erros viram Info{Installed: false} — UI usa isso pra decidir se mostra UI.
func Detect() Info {
	if _, err := exec.LookPath("clamscan"); err != nil {
		return Info{Installed: false}
	}

	out, err := exec.Command("clamscan", "--version").Output()
	if err != nil {
		return Info{Installed: true} // existe mas nao executou --version
	}

	versionStr := strings.TrimSpace(string(out))
	info := Info{Installed: true, Version: versionStr}

	// Tenta extrair data do DB pra calcular idade.
	// Format: "ClamAV 1.0.4/27295/Wed Mar  6 04:09:31 2024"
	parts := strings.Split(versionStr, "/")
	if len(parts) >= 3 {
		dateStr := strings.TrimSpace(parts[2])
		// "Wed Mar  6 04:09:31 2024" (note 2 espacos pra dias single-digit)
		// Tenta varios layouts
		for _, layout := range []string{
			"Mon Jan _2 15:04:05 2006",
			"Mon Jan 2 15:04:05 2006",
		} {
			t, err := time.Parse(layout, dateStr)
			if err == nil {
				age := time.Since(t).Hours() / 24
				if age >= 0 {
					info.DBAgeDays = uint32(age)
				}
				break
			}
		}
	}

	return info
}
