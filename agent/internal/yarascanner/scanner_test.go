package yarascanner

import (
	"testing"

	"github.com/sentinelbr/agent/internal/events"
)

func TestParseMatches_WithTags(t *testing.T) {
	output := `WebshellPHP [malware,critical] /tmp/evil.php
CryptoMinerXMRig [miner,high] /tmp/xmrig.conf
SuspiciousExe [low] /usr/bin/foo
`
	matches := parseMatches(output)
	if len(matches) != 3 {
		t.Fatalf("esperava 3, veio %d", len(matches))
	}

	check := func(i int, name, file string, sev events.Severity, tagFirst string) {
		t.Helper()
		m := matches[i]
		if m.RuleName != name {
			t.Errorf("[%d] rule: %q != %q", i, m.RuleName, name)
		}
		if m.FilePath != file {
			t.Errorf("[%d] file: %q != %q", i, m.FilePath, file)
		}
		if m.Severity != sev {
			t.Errorf("[%d] sev: %q != %q", i, m.Severity, sev)
		}
		if len(m.Tags) == 0 || m.Tags[0] != tagFirst {
			t.Errorf("[%d] tag[0]: %v != %q", i, m.Tags, tagFirst)
		}
	}

	check(0, "WebshellPHP", "/tmp/evil.php", events.SeverityCritical, "malware")
	check(1, "CryptoMinerXMRig", "/tmp/xmrig.conf", events.SeverityError, "miner")
	check(2, "SuspiciousExe", "/usr/bin/foo", events.SeverityInfo, "low")
}

func TestParseMatches_WithoutTags(t *testing.T) {
	output := `WebshellPHP /tmp/evil.php`
	matches := parseMatches(output)
	if len(matches) != 1 {
		t.Fatalf("esperava 1, veio %d", len(matches))
	}
	if matches[0].FilePath != "/tmp/evil.php" {
		t.Errorf("file path errado: %s", matches[0].FilePath)
	}
	// sem tags, default severity = warn
	if matches[0].Severity != events.SeverityWarn {
		t.Errorf("severidade default errada: %s", matches[0].Severity)
	}
}

func TestParseMatches_EmptyOutput(t *testing.T) {
	if matches := parseMatches(""); len(matches) != 0 {
		t.Errorf("esperava vazio, veio %d", len(matches))
	}
	if matches := parseMatches("\n\n   \n"); len(matches) != 0 {
		t.Errorf("esperava vazio, veio %d", len(matches))
	}
}

func TestParseMatches_PathWithSpaces(t *testing.T) {
	output := `Foo [bar] /tmp/path with spaces/file.txt`
	matches := parseMatches(output)
	if len(matches) != 1 {
		t.Fatalf("esperava 1, veio %d", len(matches))
	}
	if matches[0].FilePath != "/tmp/path with spaces/file.txt" {
		t.Errorf("path com espacos: %q", matches[0].FilePath)
	}
}

func TestSeverityFromTags(t *testing.T) {
	cases := []struct {
		tags []string
		want events.Severity
	}{
		{[]string{"malware", "critical"}, events.SeverityCritical},
		{[]string{"high"}, events.SeverityError},
		{[]string{"medium"}, events.SeverityWarn},
		{[]string{"low"}, events.SeverityInfo},
		{[]string{}, events.SeverityWarn},
		{[]string{"random"}, events.SeverityWarn},
	}
	for _, c := range cases {
		got := severityFromTags(c.tags)
		if got != c.want {
			t.Errorf("severityFromTags(%v) = %s, want %s", c.tags, got, c.want)
		}
	}
}
