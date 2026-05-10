//go:build linux

package packagemgr

import (
	"bufio"
	"fmt"
	"os/exec"
	"strings"
)

type aptManager struct{}

func newApt() PackageManager { return aptManager{} }

func (aptManager) Name() string { return "apt" }

func (aptManager) ListInstalled() ([]Package, error) {
	out, err := exec.Command("dpkg-query", "-W", "-f=${Package}|${Version}|${Architecture}\n").Output()
	if err != nil {
		return nil, fmt.Errorf("dpkg-query: %w", err)
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
			Source:  "apt",
		})
	}
	return pkgs, sc.Err()
}

func (aptManager) ListUpdatesAvailable() ([]Update, error) {
	return nil, ErrNotImplemented
}

func (aptManager) ListSecurityUpdates() ([]Update, error) {
	return nil, ErrNotImplemented
}
