//go:build linux

package mac

func newSELinux() MACSystem  { return NoopMAC{name: "selinux-stub"} }
func newAppArmor() MACSystem { return NoopMAC{name: "apparmor-stub"} }
