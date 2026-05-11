package apparmor

import (
	"testing"
	"time"
)

const fakeHostID = "11111111-2222-3333-4444-555555555555"

func TestParse_AppArmorDenied_FileOpen(t *testing.T) {
	line := `audit: type=1400 audit(1234567890.123:456): apparmor="DENIED" operation="open" profile="snap.firefox.firefox" name="/etc/passwd" pid=1234 comm="firefox" requested_mask="r" denied_mask="r" fsuid=1000 ouid=0`
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento")
	}
	expect(t, ev.Fields, "event.action", "apparmor_denied")
	expect(t, ev.Fields, "apparmor.operation", "open")
	expect(t, ev.Fields, "apparmor.profile", "snap.firefox.firefox")
	expect(t, ev.Fields, "apparmor.requested_mask", "r")
	expect(t, ev.Fields, "process.name", "firefox")
	expect(t, ev.Fields, "process.pid", "1234")
	expect(t, ev.Fields, "file.name", "/etc/passwd")
}

func TestParse_AppArmorAllowed_Skipped(t *testing.T) {
	line := `audit: type=1400 audit(1234:5): apparmor="ALLOWED" operation="open" profile="x" name="/y" pid=1`
	if ev := Parse(fakeHostID, time.Now(), line); ev != nil {
		t.Errorf("ALLOWED nao deve gerar evento: %+v", ev)
	}
}

func TestParse_AppArmorAudit_Skipped(t *testing.T) {
	// status="STATUS" tambem nao eh DENIED
	line := `audit: type=1400 audit(1234:5): apparmor="STATUS" operation="profile_load" name="/etc/apparmor.d/x"`
	if ev := Parse(fakeHostID, time.Now(), line); ev != nil {
		t.Errorf("STATUS nao deve gerar evento: %+v", ev)
	}
}

func TestParse_NonAppArmor_Skipped(t *testing.T) {
	cases := []string{
		"",
		"sshd[123]: random line",
		"type=AVC msg=audit(1:2): avc: denied { read } for pid=1",
	}
	for _, line := range cases {
		if ev := Parse(fakeHostID, time.Now(), line); ev != nil {
			t.Errorf("linha nao-apparmor: %q -> %+v", line, ev)
		}
	}
}

func expect(t *testing.T, m map[string]string, key, want string) {
	t.Helper()
	if got := m[key]; got != want {
		t.Errorf("%s: esperava %q, veio %q", key, want, got)
	}
}
