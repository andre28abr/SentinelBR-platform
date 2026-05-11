package selinux

import (
	"testing"
	"time"
)

const fakeHostID = "11111111-2222-3333-4444-555555555555"

func TestParse_AVCDenied_FileRead(t *testing.T) {
	line := `type=AVC msg=audit(1715270000.000:1234): avc: denied { read } for pid=5000 comm="httpd" name="config.json" dev="dm-0" ino=78901 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:default_t:s0 tclass=file permissive=0`
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento, veio nil")
	}
	expect(t, ev.Fields, "event.action", "selinux_denied")
	expect(t, ev.Fields, "selinux.permission", "read")
	expect(t, ev.Fields, "process.name", "httpd")
	expect(t, ev.Fields, "process.pid", "5000")
	expect(t, ev.Fields, "selinux.source_type", "httpd_t")
	expect(t, ev.Fields, "selinux.target_type", "default_t")
	expect(t, ev.Fields, "selinux.tclass", "file")
	expect(t, ev.Fields, "file.name", "config.json")
	expect(t, ev.Fields, "selinux.permissive", "false")
}

func TestParse_AVCDenied_NetworkConnect(t *testing.T) {
	line := `type=AVC msg=audit(1715270100.000:1235): avc: denied { name_connect } for pid=6000 comm="mysqld" dest=80 scontext=system_u:system_r:mysqld_t:s0 tcontext=system_u:object_r:http_port_t:s0 tclass=tcp_socket permissive=0`
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento")
	}
	expect(t, ev.Fields, "selinux.permission", "name_connect")
	expect(t, ev.Fields, "selinux.tclass", "tcp_socket")
	expect(t, ev.Fields, "selinux.source_type", "mysqld_t")
	expect(t, ev.Fields, "process.name", "mysqld")
	expect(t, ev.Fields, "network.destination_port", "80")
}

func TestParse_AVCGranted_Skipped(t *testing.T) {
	line := `type=AVC msg=audit(1715270200.000:1236): avc: granted { read } for pid=7000 comm="cat" scontext=u:r:ut:s0 tcontext=u:o:tt:s0 tclass=file`
	if ev := Parse(fakeHostID, time.Now(), line); ev != nil {
		t.Errorf("granted nao deve gerar evento: %+v", ev)
	}
}

func TestParse_NonAVC_Skipped(t *testing.T) {
	cases := []string{
		"",
		"type=USER_AUTH random other line",
		"sshd[123]: log line",
		"type=SYSCALL msg=audit(1234:5): syscall=2",
	}
	for _, line := range cases {
		if ev := Parse(fakeHostID, time.Now(), line); ev != nil {
			t.Errorf("nao-AVC nao deve gerar evento: %q -> %+v", line, ev)
		}
	}
}

func TestParse_PermissiveModeRecognized(t *testing.T) {
	line := `type=AVC msg=audit(1715270000.000:1234): avc: denied { read } for pid=5000 comm="httpd" scontext=u:r:t:s0 tcontext=u:o:t:s0 tclass=file permissive=1`
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("nil")
	}
	expect(t, ev.Fields, "selinux.permissive", "true")
}

func expect(t *testing.T, m map[string]string, key, want string) {
	t.Helper()
	if got := m[key]; got != want {
		t.Errorf("%s: esperava %q, veio %q", key, want, got)
	}
}
