package mac

import (
	"time"

	"github.com/sentinelbr/agent/internal/osdetect"
)

func New(info *osdetect.OSInfo) MACSystem {
	switch info.MACSystem {
	case "selinux":
		return newSELinux()
	case "apparmor":
		return newAppArmor()
	default:
		return NoopMAC{name: info.MACSystem}
	}
}

type NoopMAC struct{ name string }

func (n NoopMAC) Name() string                           { return "noop:" + n.name }
func (NoopMAC) Status() (*Status, error)                 { return nil, ErrNotImplemented }
func (NoopMAC) GetDenials(_ time.Time) ([]Denial, error) { return nil, ErrNotImplemented }
