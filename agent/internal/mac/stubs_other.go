//go:build !linux

package mac

func newSELinux() MACSystem  { return NoopMAC{name: "selinux-unavailable"} }
func newAppArmor() MACSystem { return NoopMAC{name: "apparmor-unavailable"} }
