package filewatcher

import (
	"testing"

	"github.com/fsnotify/fsnotify"
)

func TestShouldScan_OnlyCreateAndWrite(t *testing.T) {
	cases := []struct {
		op   fsnotify.Op
		want bool
	}{
		{fsnotify.Create, true},
		{fsnotify.Write, true},
		{fsnotify.Create | fsnotify.Write, true},
		{fsnotify.Chmod, false},
		{fsnotify.Remove, false},
		{fsnotify.Rename, false},
	}
	for _, c := range cases {
		ev := fsnotify.Event{Name: "/tmp/foo.txt", Op: c.op}
		if got := shouldScan(ev, nil); got != c.want {
			t.Errorf("op=%s want=%v got=%v", c.op, c.want, got)
		}
	}
}

func TestShouldScan_IgnoresHiddenAndSuffixes(t *testing.T) {
	ignore := []string{".swp", "~"}
	cases := []struct {
		name string
		want bool
	}{
		{"/tmp/normal.txt", true},
		{"/tmp/.hidden", false},
		{"/tmp/foo.swp", false},
		{"/tmp/backup~", false},
		{"/tmp/normal.sh", true},
	}
	for _, c := range cases {
		ev := fsnotify.Event{Name: c.name, Op: fsnotify.Write}
		if got := shouldScan(ev, ignore); got != c.want {
			t.Errorf("name=%s want=%v got=%v", c.name, c.want, got)
		}
	}
}
