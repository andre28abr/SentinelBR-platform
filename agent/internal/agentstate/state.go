// Package agentstate gerencia o estado persistente do agente apos enrollment:
// CA cert, client cert, client key, host_id e endpoint do gRPC server.
//
// Localizacao padrao: $HOME/.sentinelbr/  (no futuro: /etc/sentinelbr/ quando rodando como root).
package agentstate

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

const (
	caFileName     = "ca.crt"
	certFileName   = "client.crt"
	keyFileName    = "client.key"
	stateFileName  = "state.json"
)

type State struct {
	HostID       string `json:"host_id"`
	GRPCEndpoint string `json:"grpc_endpoint"`
	ServerURL    string `json:"server_url"`
}

type Paths struct {
	Dir       string
	CACert    string
	ClientCert string
	ClientKey  string
	StateFile  string
}

// DefaultDir retorna $HOME/.sentinelbr (pode ser sobrescrito por env SENTINEL_DIR).
func DefaultDir() (string, error) {
	if d := os.Getenv("SENTINEL_DIR"); d != "" {
		return d, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("home dir: %w", err)
	}
	return filepath.Join(home, ".sentinelbr"), nil
}

func PathsFromDir(dir string) Paths {
	return Paths{
		Dir:        dir,
		CACert:     filepath.Join(dir, caFileName),
		ClientCert: filepath.Join(dir, certFileName),
		ClientKey:  filepath.Join(dir, keyFileName),
		StateFile:  filepath.Join(dir, stateFileName),
	}
}

func Save(dir string, st State, caPEM, certPEM, keyPEM []byte) error {
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return fmt.Errorf("criar dir %s: %w", dir, err)
	}
	p := PathsFromDir(dir)

	if err := os.WriteFile(p.CACert, caPEM, 0o644); err != nil {
		return fmt.Errorf("escrever ca.crt: %w", err)
	}
	if err := os.WriteFile(p.ClientCert, certPEM, 0o644); err != nil {
		return fmt.Errorf("escrever client.crt: %w", err)
	}
	if err := os.WriteFile(p.ClientKey, keyPEM, 0o600); err != nil {
		return fmt.Errorf("escrever client.key: %w", err)
	}
	stateBytes, err := json.MarshalIndent(st, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal state: %w", err)
	}
	if err := os.WriteFile(p.StateFile, stateBytes, 0o600); err != nil {
		return fmt.Errorf("escrever state.json: %w", err)
	}
	return nil
}

func Load(dir string) (*State, Paths, error) {
	p := PathsFromDir(dir)
	data, err := os.ReadFile(p.StateFile)
	if err != nil {
		return nil, p, fmt.Errorf("ler %s: %w (rode `sentinel-agent enroll` primeiro)", p.StateFile, err)
	}
	var st State
	if err := json.Unmarshal(data, &st); err != nil {
		return nil, p, fmt.Errorf("parse state.json: %w", err)
	}
	return &st, p, nil
}
