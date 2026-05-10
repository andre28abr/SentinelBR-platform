package osdetect

// OSInfo descreve o ambiente onde o agente está rodando.
// Populado uma vez na inicialização e propagado para escolha de implementações
// concretas de PackageManager, FirewallExecutor e MACSystem.
type OSInfo struct {
	Family       string // debian | redhat | suse | arch | alpine | darwin | windows
	Distro       string // ubuntu | debian | rocky | almalinux | rhel | fedora | opensuse-leap | sles | arch | alpine | macos | windows-server
	Version      string // 22.04 | 12 | 9.3 | ...
	VersionID    string // ID interno do /etc/os-release
	Codename     string // jammy | bookworm | ...
	Arch         string // amd64 | arm64
	Kernel       string // versão do kernel
	PackageMgr   string // apt | dnf | zypper | pacman | apk | brew | windows
	InitSystem   string // systemd | openrc | launchd | windows-service
	FirewallTool string // nftables | iptables | firewalld | ufw | windows-firewall | pf
	MACSystem    string // selinux | apparmor | none
}
