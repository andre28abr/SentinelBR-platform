package sshd

import (
	"testing"
	"time"
)

const fakeHostID = "11111111-2222-3333-4444-555555555555"

func TestParse_FailedPassword_RealUser(t *testing.T) {
	line := "Failed password for root from 203.0.113.42 port 38241 ssh2"
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento, veio nil")
	}
	expect(t, ev.Fields, "event.outcome", "failure")
	expect(t, ev.Fields, "event.reason", "wrong_password")
	expect(t, ev.Fields, "user.name", "root")
	expect(t, ev.Fields, "source.ip", "203.0.113.42")
	expect(t, ev.Fields, "source.port", "38241")
	expect(t, ev.Fields, "auth.method", "password")
	if ev.Fields["user.valid"] != "" {
		t.Errorf("real user nao deve ter user.valid setado: %s", ev.Fields["user.valid"])
	}
}

func TestParse_FailedPassword_InvalidUser(t *testing.T) {
	line := "Failed password for invalid user admin from 203.0.113.42 port 38242 ssh2"
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento, veio nil")
	}
	expect(t, ev.Fields, "event.outcome", "failure")
	expect(t, ev.Fields, "event.reason", "invalid_user")
	expect(t, ev.Fields, "user.name", "admin")
	expect(t, ev.Fields, "user.valid", "false")
	expect(t, ev.Fields, "source.ip", "203.0.113.42")
}

func TestParse_AcceptedPassword(t *testing.T) {
	line := "Accepted password for ubuntu from 198.51.100.42 port 54321 ssh2"
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento, veio nil")
	}
	expect(t, ev.Fields, "event.outcome", "success")
	expect(t, ev.Fields, "user.name", "ubuntu")
	expect(t, ev.Fields, "auth.method", "password")
}

func TestParse_AcceptedPublickey(t *testing.T) {
	line := "Accepted publickey for deploy from 10.0.1.50 port 41234 ssh2: RSA SHA256:abc123def456"
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento, veio nil")
	}
	expect(t, ev.Fields, "event.outcome", "success")
	expect(t, ev.Fields, "user.name", "deploy")
	expect(t, ev.Fields, "auth.method", "publickey")
	expect(t, ev.Fields, "auth.key_type", "RSA")
	expect(t, ev.Fields, "auth.key_fingerprint", "SHA256:abc123def456")
}

func TestParse_InvalidUser(t *testing.T) {
	line := "Invalid user backdoor from 198.51.100.99 port 12345"
	ev := Parse(fakeHostID, time.Now(), line)
	if ev == nil {
		t.Fatal("esperava evento, veio nil")
	}
	expect(t, ev.Fields, "event.action", "ssh_invalid_user")
	expect(t, ev.Fields, "user.valid", "false")
	expect(t, ev.Fields, "user.name", "backdoor")
}

func TestParse_UnrecognizedLine_ReturnsNil(t *testing.T) {
	cases := []string{
		"",
		"random unrelated log line",
		"sshd[123]: just info, nothing important",
		"Connection closed by 1.2.3.4 port 22 [preauth]",
	}
	for _, line := range cases {
		if ev := Parse(fakeHostID, time.Now(), line); ev != nil {
			t.Errorf("esperava nil para %q, veio evento %+v", line, ev)
		}
	}
}

func TestParse_PreservesRawAndIDsAndHost(t *testing.T) {
	line := "Failed password for root from 203.0.113.42 port 38241 ssh2"
	ts := time.Date(2026, 5, 9, 14, 23, 45, 0, time.UTC)
	ev := Parse(fakeHostID, ts, line)
	if ev == nil {
		t.Fatal("nil")
	}
	if ev.Raw != line {
		t.Errorf("raw nao preservado: %q", ev.Raw)
	}
	if ev.HostID != fakeHostID {
		t.Errorf("host_id nao preservado")
	}
	if !ev.Timestamp.Equal(ts) {
		t.Errorf("timestamp nao preservado")
	}
	if ev.ID == "" {
		t.Errorf("ID nao gerado")
	}
}

func expect(t *testing.T, m map[string]string, key, want string) {
	t.Helper()
	if got := m[key]; got != want {
		t.Errorf("%s: esperava %q, veio %q", key, want, got)
	}
}
