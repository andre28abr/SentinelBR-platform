//go:build linux

package packagemgr

type pacmanManager struct{}

func newPacman() PackageManager { return pacmanManager{} }

func (pacmanManager) Name() string                            { return "pacman" }
func (pacmanManager) ListInstalled() ([]Package, error)       { return nil, ErrNotImplemented }
func (pacmanManager) ListUpdatesAvailable() ([]Update, error) { return nil, ErrNotImplemented }
func (pacmanManager) ListSecurityUpdates() ([]Update, error)  { return nil, ErrNotImplemented }
