//go:build linux

package packagemgr

import (
	"bufio"
	"fmt"
	"os/exec"
	"strings"
)

type dnfManager struct{}

func newDnf() PackageManager { return dnfManager{} }

func (dnfManager) Name() string { return "dnf" }

// ListInstalled usa `rpm -qa` (mais leve que `dnf list installed` e nao requer
// repos ativos). Inclui pacotes instalados via dnf, yum, ou rpm direto.
func (dnfManager) ListInstalled() ([]Package, error) {
	out, err := exec.Command("rpm", "-qa", "--queryformat", "%{NAME}|%{VERSION}-%{RELEASE}|%{ARCH}\n").Output()
	if err != nil {
		return nil, fmt.Errorf("rpm -qa: %w", err)
	}
	var pkgs []Package
	sc := bufio.NewScanner(strings.NewReader(string(out)))
	for sc.Scan() {
		parts := strings.SplitN(sc.Text(), "|", 3)
		if len(parts) != 3 {
			continue
		}
		pkgs = append(pkgs, Package{
			Name:    parts[0],
			Version: parts[1],
			Arch:    parts[2],
			Source:  "dnf",
		})
	}
	return pkgs, sc.Err()
}

func (dnfManager) ListUpdatesAvailable() ([]Update, error) { return nil, ErrNotImplemented }
func (dnfManager) ListSecurityUpdates() ([]Update, error)  { return nil, ErrNotImplemented }
