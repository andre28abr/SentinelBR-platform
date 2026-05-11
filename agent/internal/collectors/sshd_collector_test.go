package collectors

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"
)

const fakeHostID = "11111111-2222-3333-4444-555555555555"

func TestSSHDCollector_ParsesFromFixtureFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "auth.log")

	content := `May 09 02:14:12 web-01 sshd[15234]: Failed password for root from 203.0.113.42 port 38241 ssh2
May 09 02:14:13 web-01 sshd[15235]: Failed password for invalid user admin from 203.0.113.42 port 38242 ssh2
some unrelated junk
May 09 14:23:45 web-01 sshd[12345]: Accepted password for ubuntu from 198.51.100.42 port 54321 ssh2
`
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	src := NewFileSource(path, true) // Once mode
	col := NewSSHDCollector(fakeHostID, src)

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()

	done := make(chan error, 1)
	go func() { done <- col.Run(ctx) }()

	var got []map[string]string
	for ev := range col.Events() {
		got = append(got, ev.Fields)
	}
	if err := <-done; err != nil {
		t.Fatalf("collector run: %v", err)
	}

	if len(got) != 3 {
		t.Fatalf("esperava 3 eventos, veio %d: %+v", len(got), got)
	}
	if got[0]["event.outcome"] != "failure" || got[0]["user.name"] != "root" {
		t.Errorf("evento 0 errado: %+v", got[0])
	}
	if got[1]["event.reason"] != "invalid_user" || got[1]["user.name"] != "admin" {
		t.Errorf("evento 1 errado: %+v", got[1])
	}
	if got[2]["event.outcome"] != "success" || got[2]["user.name"] != "ubuntu" {
		t.Errorf("evento 2 errado: %+v", got[2])
	}
}

func TestStripSyslogPrefix(t *testing.T) {
	cases := []struct {
		in   string
		want string
	}{
		{
			"May 09 02:14:12 web-01 sshd[15234]: Failed password for root from 1.2.3.4 port 22 ssh2",
			"Failed password for root from 1.2.3.4 port 22 ssh2",
		},
		{"Failed password for x from y port z", "Failed password for x from y port z"},
		{"junk without sshd marker", "junk without sshd marker"},
	}
	for _, c := range cases {
		if got := stripSyslogPrefix(c.in); got != c.want {
			t.Errorf("strip(%q)\n  got:  %q\n  want: %q", c.in, got, c.want)
		}
	}
}
