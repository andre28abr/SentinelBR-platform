//go:build linux

package packagemgr

type zypperManager struct{}

func newZypper() PackageManager { return zypperManager{} }

func (zypperManager) Name() string                            { return "zypper" }
func (zypperManager) ListInstalled() ([]Package, error)       { return nil, ErrNotImplemented }
func (zypperManager) ListUpdatesAvailable() ([]Update, error) { return nil, ErrNotImplemented }
func (zypperManager) ListSecurityUpdates() ([]Update, error)  { return nil, ErrNotImplemented }
