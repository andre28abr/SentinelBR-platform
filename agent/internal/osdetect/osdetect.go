package osdetect

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strings"
)

// Detect identifica o OS, distro, versão e ferramentas associadas.
// Em Linux: lê /etc/os-release. Em macOS/Windows: usa runtime.GOOS + heurísticas.
func Detect() (*OSInfo, error) {
	switch runtime.GOOS {
	case "linux":
		return detectLinux()
	case "darwin":
		return detectDarwin(), nil
	case "windows":
		return detectWindows(), nil
	default:
		return nil, fmt.Errorf("OS não suportado: %s", runtime.GOOS)
	}
}

func detectLinux() (*OSInfo, error) {
	info := &OSInfo{
		Family:     "linux-unknown",
		Arch:       runtime.GOARCH,
		InitSystem: detectInitSystem(),
		Kernel:     readKernel(),
	}

	rel, err := readOSRelease("/etc/os-release")
	if err != nil {
		return info, fmt.Errorf("ler /etc/os-release: %w", err)
	}

	info.Distro = rel["ID"]
	info.Version = rel["VERSION_ID"]
	info.VersionID = rel["VERSION_ID"]
	info.Codename = rel["VERSION_CODENAME"]

	idLike := rel["ID_LIKE"]
	switch {
	case info.Distro == "ubuntu" || info.Distro == "debian" || strings.Contains(idLike, "debian"):
		info.Family = "debian"
		info.PackageMgr = "apt"
	case info.Distro == "rhel" || info.Distro == "rocky" || info.Distro == "almalinux" ||
		info.Distro == "fedora" || info.Distro == "centos" || info.Distro == "ol" ||
		strings.Contains(idLike, "rhel") || strings.Contains(idLike, "fedora"):
		info.Family = "redhat"
		info.PackageMgr = "dnf"
	case info.Distro == "opensuse-leap" || info.Distro == "opensuse-tumbleweed" ||
		info.Distro == "sles" || strings.Contains(idLike, "suse"):
		info.Family = "suse"
		info.PackageMgr = "zypper"
	case info.Distro == "arch" || info.Distro == "manjaro" || strings.Contains(idLike, "arch"):
		info.Family = "arch"
		info.PackageMgr = "pacman"
	case info.Distro == "alpine":
		info.Family = "alpine"
		info.PackageMgr = "apk"
	}

	info.FirewallTool = detectFirewallLinux(info.Family, info.Distro)
	info.MACSystem = detectMACLinux()

	return info, nil
}

func detectDarwin() *OSInfo {
	ver := ""
	if out, err := exec.Command("sw_vers", "-productVersion").Output(); err == nil {
		ver = strings.TrimSpace(string(out))
	}
	kernel := ""
	if out, err := exec.Command("uname", "-r").Output(); err == nil {
		kernel = strings.TrimSpace(string(out))
	}
	return &OSInfo{
		Family:       "darwin",
		Distro:       "macos",
		Version:      ver,
		Arch:         runtime.GOARCH,
		Kernel:       kernel,
		PackageMgr:   "brew",
		InitSystem:   "launchd",
		FirewallTool: "pf",
		MACSystem:    "none",
	}
}

func detectWindows() *OSInfo {
	return &OSInfo{
		Family:       "windows",
		Distro:       "windows-server",
		Version:      "unknown",
		Arch:         runtime.GOARCH,
		PackageMgr:   "windows",
		InitSystem:   "windows-service",
		FirewallTool: "windows-firewall",
		MACSystem:    "none",
	}
}

// readOSRelease parseia o formato KEY=VALUE de /etc/os-release.
// Aspas duplas em valores são removidas.
func readOSRelease(path string) (map[string]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	out := map[string]string{}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		k, v, ok := strings.Cut(line, "=")
		if !ok {
			continue
		}
		out[k] = strings.Trim(v, `"'`)
	}
	return out, sc.Err()
}

func detectInitSystem() string {
	if runtime.GOOS != "linux" {
		return ""
	}
	if _, err := os.Stat("/run/systemd/system"); err == nil {
		return "systemd"
	}
	if _, err := os.Stat("/sbin/openrc"); err == nil {
		return "openrc"
	}
	return "unknown"
}

func detectFirewallLinux(family, distro string) string {
	switch {
	case fileExists("/usr/sbin/nft") || fileExists("/sbin/nft"):
		if family == "redhat" || family == "suse" {
			if fileExists("/usr/sbin/firewall-cmd") || fileExists("/usr/bin/firewall-cmd") {
				return "firewalld"
			}
		}
		if distro == "ubuntu" && (fileExists("/usr/sbin/ufw") || fileExists("/usr/bin/ufw")) {
			return "ufw"
		}
		return "nftables"
	case fileExists("/usr/sbin/iptables") || fileExists("/sbin/iptables"):
		return "iptables"
	}
	return "none"
}

func detectMACLinux() string {
	if fileExists("/sys/fs/selinux/enforce") {
		return "selinux"
	}
	if fileExists("/sys/kernel/security/apparmor/profiles") {
		return "apparmor"
	}
	return "none"
}

func fileExists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}

func readKernel() string {
	b, err := os.ReadFile("/proc/sys/kernel/osrelease")
	if err == nil {
		return strings.TrimSpace(string(b))
	}
	return ""
}
