//go:build linux

package packagemgr

type dnfManager struct{}

func newDnf() PackageManager { return dnfManager{} }

func (dnfManager) Name() string                            { return "dnf" }
func (dnfManager) ListInstalled() ([]Package, error)       { return nil, ErrNotImplemented }
func (dnfManager) ListUpdatesAvailable() ([]Update, error) { return nil, ErrNotImplemented }
func (dnfManager) ListSecurityUpdates() ([]Update, error)  { return nil, ErrNotImplemented }
