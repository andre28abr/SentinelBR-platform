// Package quarantine isola arquivos maliciosos: move pra um diretorio
// dedicado com permissoes restritivas e gera metadata sidecar (.json)
// pra forensics.
//
// Layout no disco (default /var/sentinelbr/quarantine):
//
//	<sha256>.bin          # arquivo original (renomeado)
//	<sha256>.bin.json     # {original_path, sha256, quarantined_at, reason}
//
// Permissoes: dir 0700, arquivos 0400 (read-only pro root), sidecar 0600.
package quarantine

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"
)

const (
	DefaultDir = "/var/sentinelbr/quarantine"
	DirMode    = 0o700
	FileMode   = 0o400
	MetaMode   = 0o600
)

type Quarantiner struct {
	BaseDir string // default DefaultDir
	Now     func() time.Time
}

type Sidecar struct {
	OriginalPath   string `json:"original_path"`
	SHA256         string `json:"sha256"`
	SizeBytes      int64  `json:"size_bytes"`
	QuarantinedAt  string `json:"quarantined_at"`
	Reason         string `json:"reason"`
	QuarantinePath string `json:"quarantine_path"`
}

func New(baseDir string) *Quarantiner {
	if baseDir == "" {
		baseDir = DefaultDir
	}
	return &Quarantiner{BaseDir: baseDir, Now: time.Now}
}

// Quarantine move srcPath para o diretorio de quarentena, escreve sidecar
// e devolve a Sidecar gerada. Se srcPath nao existe ou ja esta na quarentena,
// retorna erro descritivo.
func (q *Quarantiner) Quarantine(srcPath, reason string) (*Sidecar, error) {
	abs, err := filepath.Abs(srcPath)
	if err != nil {
		return nil, fmt.Errorf("path absoluto %s: %w", srcPath, err)
	}
	info, err := os.Stat(abs)
	if err != nil {
		return nil, fmt.Errorf("stat %s: %w", abs, err)
	}
	if info.IsDir() {
		return nil, fmt.Errorf("%s eh diretorio (apenas arquivos)", abs)
	}

	if err := os.MkdirAll(q.BaseDir, DirMode); err != nil {
		return nil, fmt.Errorf("mkdir quarentena %s: %w", q.BaseDir, err)
	}

	sum, err := hashFile(abs)
	if err != nil {
		return nil, fmt.Errorf("hash %s: %w", abs, err)
	}

	destBin := filepath.Join(q.BaseDir, sum+".bin")
	destMeta := destBin + ".json"

	// Se ja existe (mesmo hash, ja em quarentena), tudo bem — re-escreve sidecar
	// pra atualizar reason/timestamp e remove o original.
	if _, err := os.Stat(destBin); err == nil {
		if err := os.Remove(abs); err != nil {
			return nil, fmt.Errorf("ja em quarentena, mas falhou remover original %s: %w", abs, err)
		}
	} else if errors.Is(err, os.ErrNotExist) {
		if err := moveFile(abs, destBin); err != nil {
			return nil, fmt.Errorf("mover pra quarentena: %w", err)
		}
		if err := os.Chmod(destBin, FileMode); err != nil {
			return nil, fmt.Errorf("chmod %s: %w", destBin, err)
		}
	} else {
		return nil, fmt.Errorf("stat dest %s: %w", destBin, err)
	}

	side := &Sidecar{
		OriginalPath:   abs,
		SHA256:         sum,
		SizeBytes:      info.Size(),
		QuarantinedAt:  q.Now().UTC().Format(time.RFC3339),
		Reason:         reason,
		QuarantinePath: destBin,
	}
	if err := writeJSON(destMeta, side); err != nil {
		return nil, fmt.Errorf("escrever sidecar %s: %w", destMeta, err)
	}
	return side, nil
}

func hashFile(p string) (string, error) {
	f, err := os.Open(p)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

// moveFile tenta os.Rename primeiro (rapido se mesmo filesystem), se falhar
// (cross-device), copia + remove.
func moveFile(src, dst string) error {
	if err := os.Rename(src, dst); err == nil {
		return nil
	}
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.OpenFile(dst, os.O_WRONLY|os.O_CREATE|os.O_EXCL, FileMode)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		os.Remove(dst)
		return err
	}
	if err := out.Close(); err != nil {
		os.Remove(dst)
		return err
	}
	in.Close()
	return os.Remove(src)
}

func writeJSON(path string, v any) error {
	data, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, MetaMode)
}
