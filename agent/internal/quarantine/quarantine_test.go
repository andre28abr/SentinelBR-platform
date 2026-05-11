package quarantine

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestQuarantine_MovesFileAndWritesSidecar(t *testing.T) {
	base := t.TempDir()
	src := filepath.Join(t.TempDir(), "evil.sh")
	if err := os.WriteFile(src, []byte("malicious"), 0o644); err != nil {
		t.Fatal(err)
	}

	q := New(base)
	q.Now = func() time.Time { return time.Date(2026, 5, 10, 12, 0, 0, 0, time.UTC) }

	side, err := q.Quarantine(src, "test-reason")
	if err != nil {
		t.Fatalf("Quarantine: %v", err)
	}

	// original removido
	if _, err := os.Stat(src); !os.IsNotExist(err) {
		t.Errorf("original ainda existe (%v)", err)
	}

	// destino existe com perm 0400
	st, err := os.Stat(side.QuarantinePath)
	if err != nil {
		t.Fatalf("dest nao existe: %v", err)
	}
	if st.Mode().Perm() != FileMode {
		t.Errorf("perm dest = %o, esperava %o", st.Mode().Perm(), FileMode)
	}

	// sidecar tem campos esperados
	metaPath := side.QuarantinePath + ".json"
	data, err := os.ReadFile(metaPath)
	if err != nil {
		t.Fatal(err)
	}
	var got Sidecar
	if err := json.Unmarshal(data, &got); err != nil {
		t.Fatal(err)
	}
	if got.OriginalPath == "" || got.SHA256 == "" || got.Reason != "test-reason" {
		t.Errorf("sidecar incompleto: %+v", got)
	}
	if got.QuarantinedAt != "2026-05-10T12:00:00Z" {
		t.Errorf("timestamp errado: %s", got.QuarantinedAt)
	}
}

func TestQuarantine_RejectsDirectory(t *testing.T) {
	base := t.TempDir()
	dir := t.TempDir()
	q := New(base)
	if _, err := q.Quarantine(dir, "x"); err == nil {
		t.Errorf("esperava erro pra diretorio, veio nil")
	}
}

func TestQuarantine_NonexistentFile(t *testing.T) {
	q := New(t.TempDir())
	if _, err := q.Quarantine("/nao/existe/aqui", "x"); err == nil {
		t.Errorf("esperava erro pra arquivo inexistente")
	}
}

func TestQuarantine_DuplicateHashOverwritesSidecar(t *testing.T) {
	base := t.TempDir()
	q := New(base)

	// 1a quarentena
	src1 := filepath.Join(t.TempDir(), "a.bin")
	os.WriteFile(src1, []byte("same-content"), 0o644)
	first, err := q.Quarantine(src1, "first")
	if err != nil {
		t.Fatal(err)
	}

	// 2a quarentena com mesmo conteudo (mesmo hash) — outro arquivo
	src2 := filepath.Join(t.TempDir(), "b.bin")
	os.WriteFile(src2, []byte("same-content"), 0o644)
	second, err := q.Quarantine(src2, "second")
	if err != nil {
		t.Fatal(err)
	}

	if first.QuarantinePath != second.QuarantinePath {
		t.Errorf("mesmo conteudo deveria mapear pro mesmo dest")
	}
	if _, err := os.Stat(src2); !os.IsNotExist(err) {
		t.Errorf("segundo original deveria ter sido removido")
	}
	// sidecar atualizado pra "second"
	data, _ := os.ReadFile(second.QuarantinePath + ".json")
	var s Sidecar
	json.Unmarshal(data, &s)
	if s.Reason != "second" {
		t.Errorf("sidecar nao atualizado: reason=%s", s.Reason)
	}
}
