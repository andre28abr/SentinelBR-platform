// Package mac abstrai o sistema de Mandatory Access Control: SELinux ou AppArmor.
package mac

import (
	"errors"
	"time"
)

var ErrNotImplemented = errors.New("mac: operação não implementada para este OS")

type Mode string

const (
	ModeEnforcing  Mode = "enforcing"
	ModePermissive Mode = "permissive"
	ModeDisabled   Mode = "disabled"
)

type Status struct {
	Name    string // selinux | apparmor
	Mode    Mode
	Version string
}

type Denial struct {
	Timestamp time.Time
	Process   string
	Path      string
	Action    string
	Raw       string
}

type MACSystem interface {
	Name() string
	Status() (*Status, error)
	GetDenials(since time.Time) ([]Denial, error)
}
