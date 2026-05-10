//go:build linux

package packagemgr

type apkManager struct{}

func newApk() PackageManager { return apkManager{} }

func (apkManager) Name() string                            { return "apk" }
func (apkManager) ListInstalled() ([]Package, error)       { return nil, ErrNotImplemented }
func (apkManager) ListUpdatesAvailable() ([]Update, error) { return nil, ErrNotImplemented }
func (apkManager) ListSecurityUpdates() ([]Update, error)  { return nil, ErrNotImplemented }
