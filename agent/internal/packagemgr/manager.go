// Package packagemgr abstrai o gerenciador de pacotes do OS.
// Cada distro implementa a interface PackageManager. Escolha da implementação
// é feita pela factory New() baseada em OSInfo.PackageMgr.
package packagemgr

import "errors"

var ErrNotImplemented = errors.New("packagemgr: operação não implementada para este OS")

type Package struct {
	Name    string
	Version string
	Arch    string
	Source  string // apt | dnf | zypper | pacman | apk | brew
}

type Update struct {
	Package    string
	From       string
	To         string
	IsSecurity bool
	CVEs       []string
}

type PackageManager interface {
	// Name retorna o identificador do gerenciador (apt, dnf, ...).
	Name() string

	// ListInstalled enumera todos os pacotes instalados.
	ListInstalled() ([]Package, error)

	// ListUpdatesAvailable lista atualizações pendentes.
	ListUpdatesAvailable() ([]Update, error)

	// ListSecurityUpdates filtra apenas atualizações classificadas como segurança.
	ListSecurityUpdates() ([]Update, error)
}
