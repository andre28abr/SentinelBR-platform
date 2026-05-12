// Tests pros parsers pure-function dos handlers de scan. Cobre o output
// real (anonimizado) de cada ferramenta. Sem mocks — funcoes nao tocam
// I/O nem rede, perfeitas pra testar com tabela de fixtures.

package cmddispatcher

import (
	"testing"
)

func TestParseClamavOutput(t *testing.T) {
	out := `/tmp/foo.exe: Win.Trojan.Agent FOUND
/var/www/upload/shell.php: Php.Webshell.Generic FOUND
/tmp/clean.txt: OK
some random line that does not match`
	matches := parseClamavOutput(out)
	if len(matches) != 2 {
		t.Fatalf("esperado 2 matches, veio %d", len(matches))
	}
	if matches[0].FilePath != "/tmp/foo.exe" || matches[0].Signature != "Win.Trojan.Agent" {
		t.Errorf("match 0 errado: %+v", matches[0])
	}
	if matches[1].FilePath != "/var/www/upload/shell.php" {
		t.Errorf("match 1 path errado: %+v", matches[1])
	}
}

func TestParseClamavOutput_Empty(t *testing.T) {
	if got := parseClamavOutput(""); len(got) != 0 {
		t.Errorf("esperado 0, veio %d", len(got))
	}
	if got := parseClamavOutput("/tmp/clean: OK\n"); len(got) != 0 {
		t.Errorf("OK nao deveria ser match, veio %d", len(got))
	}
}

func TestParseRkhunterWarnings(t *testing.T) {
	out := `Rootkit Hunter version 1.4.6
Warning: Suspicious file in /etc/cron.d
Warning: Hidden directory found: /tmp/.evil
Info: clean install
[blah] some other line`
	ws := parseRkhunterWarnings(out)
	if len(ws) != 2 {
		t.Fatalf("esperado 2 warnings, veio %d (%v)", len(ws), ws)
	}
	if ws[0] != "Suspicious file in /etc/cron.d" {
		t.Errorf("warning 0 errado: %q", ws[0])
	}
}

func TestParseChkrootkitOutput(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want int
	}{
		{"clean", "Checking lkm... not infected\n", 0},
		{"infected", "Checking sniffer...INFECTED\n", 1},
		{"warning", "Warning: bad file detected\n", 1},
		{
			"mix",
			"Checking lastlog... INFECTED\nWarning: hidden process\nClean stuff",
			2,
		},
		// Bug pre-fix: 'No Warnings found' contém substring 'Warning' — antes
		// virava falso positivo. Regex anchored corrige.
		{"false positive containing word", "No Warnings found in scan\n", 0},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			got := parseChkrootkitOutput(tc.in)
			if len(got) != tc.want {
				t.Errorf("input=%q: esperado %d, veio %d (%v)", tc.in, tc.want, len(got), got)
			}
		})
	}
}

func TestParseLynisOutput(t *testing.T) {
	out := `Lynis 3.0
Suggestion: AUTH-9229 - test1
Warning: KRNL-5677 - kernel module
Hardening index : 78 [Some text]
Suggestion: HOME-1234 - extra
Some other line ignored`
	score, findings := parseLynisOutput(out)
	if score != 78 {
		t.Errorf("score esperado 78, veio %d", score)
	}
	if len(findings) != 3 {
		t.Errorf("esperado 3 findings, veio %d (%v)", len(findings), findings)
	}
}

func TestParseAideSummary(t *testing.T) {
	out := `AIDE found differences between database and filesystem!!
Summary:
  Total number of entries:      12345
  Added entries:                3
  Removed entries:              1
  Changed entries:              7`
	added, changed, removed := parseAideSummary(out)
	if added != 3 || changed != 7 || removed != 1 {
		t.Errorf("counts errados: a=%d c=%d r=%d", added, changed, removed)
	}
}

func TestParseAideSummary_Clean(t *testing.T) {
	out := `AIDE database OK\nNo differences found`
	added, changed, removed := parseAideSummary(out)
	if added != 0 || changed != 0 || removed != 0 {
		t.Errorf("clean deveria zerar tudo: a=%d c=%d r=%d", added, changed, removed)
	}
}
