package packagemgr

import "github.com/sentinelbr/agent/internal/osdetect"

// New escolhe a implementação concreta de PackageManager baseado no OS detectado.
// Retorna NoopManager se nenhuma implementação casa (ex: macOS dev, distro nova).
func New(info *osdetect.OSInfo) PackageManager {
	switch info.PackageMgr {
	case "apt":
		return newApt()
	case "dnf":
		return newDnf()
	case "zypper":
		return newZypper()
	case "pacman":
		return newPacman()
	case "apk":
		return newApk()
	default:
		return NoopManager{name: info.PackageMgr}
	}
}

// NoopManager é o fallback quando o OS não tem implementação ou é dev (macOS).
// Todos os métodos retornam ErrNotImplemented.
type NoopManager struct{ name string }

func (n NoopManager) Name() string                              { return "noop:" + n.name }
func (n NoopManager) ListInstalled() ([]Package, error)         { return nil, ErrNotImplemented }
func (n NoopManager) ListUpdatesAvailable() ([]Update, error)   { return nil, ErrNotImplemented }
func (n NoopManager) ListSecurityUpdates() ([]Update, error)    { return nil, ErrNotImplemented }
