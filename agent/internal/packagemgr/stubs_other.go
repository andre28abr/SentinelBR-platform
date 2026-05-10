//go:build !linux

package packagemgr

// Em macOS/Windows os impls de Linux são compilados fora.
// Stubs aqui garantem que a factory continua compilando, retornando NoopManager.

func newApt() PackageManager    { return NoopManager{name: "apt-unavailable"} }
func newDnf() PackageManager    { return NoopManager{name: "dnf-unavailable"} }
func newZypper() PackageManager { return NoopManager{name: "zypper-unavailable"} }
func newPacman() PackageManager { return NoopManager{name: "pacman-unavailable"} }
func newApk() PackageManager    { return NoopManager{name: "apk-unavailable"} }
