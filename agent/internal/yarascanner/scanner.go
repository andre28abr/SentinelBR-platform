// Package yarascanner roda o binario `yara` contra um diretorio alvo e parseia
// os matches em Events normalizados.
//
// Pre-req: yara instalado no sistema (brew install yara | apt install yara).
// Em dev/CI sem yara, NewScanner detecta a ausencia e retorna ErrYaraMissing.
//
// Convencao: severidade vem das tags do rule (critical/high/medium/low).
// Output do yara com -g (tags inline): `rule_name [tag1,tag2] /path/to/file`
package yarascanner

import (
	"bufio"
	"bytes"
	"context"
	"errors"
	"fmt"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/sentinelbr/agent/internal/events"
)

const Source = "yara"

var ErrYaraMissing = errors.New("yara binary nao encontrado (brew install yara | apt install yara)")

type Scanner struct {
	YaraBinary string // default "yara"
	RulesPath  string // arquivo .yar OU diretorio com varios .yar
	HostID     string
}

type Match struct {
	RuleName string
	FilePath string
	Tags     []string
	Severity events.Severity
}

func NewScanner(hostID, rulesPath string) (*Scanner, error) {
	bin := "yara"
	if _, err := exec.LookPath(bin); err != nil {
		return nil, ErrYaraMissing
	}
	return &Scanner{YaraBinary: bin, RulesPath: rulesPath, HostID: hostID}, nil
}

// Scan roda yara recursivo no targetPath e devolve matches parseados.
// rulesPath pode ser arquivo OU diretorio (expande *.yar/*.yara).
func (s *Scanner) Scan(ctx context.Context, targetPath string) ([]Match, error) {
	ruleFiles, err := s.expandRules()
	if err != nil {
		return nil, err
	}
	args := append([]string{"-r", "-g"}, ruleFiles...)
	args = append(args, targetPath)
	cmd := exec.CommandContext(ctx, s.YaraBinary, args...)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	runErr := cmd.Run()
	// yara retorna exit-code 0 mesmo com matches (matches vao pra stdout).
	// Erros (regra invalida, path inexistente) vao pra stderr + exit nao-zero.
	if runErr != nil && stdout.Len() == 0 {
		return nil, fmt.Errorf("yara: %w (%s)", runErr, strings.TrimSpace(stderr.String()))
	}

	return parseMatches(stdout.String()), nil
}

// ScanToEvents roda Scan + converte cada Match em events.Event pronto pra stream.
func (s *Scanner) ScanToEvents(ctx context.Context, targetPath string) ([]*events.Event, error) {
	matches, err := s.Scan(ctx, targetPath)
	if err != nil {
		return nil, err
	}
	now := time.Now().UTC()
	out := make([]*events.Event, 0, len(matches))
	for _, m := range matches {
		ev := events.New(s.HostID, Source, now, fmt.Sprintf("%s -> %s", m.RuleName, m.FilePath))
		ev.Severity = m.Severity
		ev.Fields["event.category"] = "malware"
		ev.Fields["event.action"] = "yara_match"
		ev.Fields["event.outcome"] = "alert"
		ev.Fields["yara.rule_name"] = m.RuleName
		ev.Fields["yara.severity"] = string(m.Severity)
		ev.Fields["yara.tags"] = strings.Join(m.Tags, ",")
		ev.Fields["file.path"] = m.FilePath
		out = append(out, ev)
	}
	return out, nil
}

// parseMatches parseia output do `yara -g`.
//
// Format exemplo:
//
//	WebshellPHP [malware,critical] /tmp/x/evil.php
//	CryptoMiner [miner,high] /tmp/x/xmrig.conf
func parseMatches(output string) []Match {
	var out []Match
	sc := bufio.NewScanner(strings.NewReader(output))
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		m := parseLine(line)
		if m != nil {
			out = append(out, *m)
		}
	}
	return out
}

func parseLine(line string) *Match {
	// Tem 2 formatos possiveis:
	//   "rule_name /path/to/file"
	//   "rule_name [tag1,tag2] /path/to/file"
	parts := strings.SplitN(line, " ", 2)
	if len(parts) < 2 {
		return nil
	}
	ruleName := parts[0]
	rest := strings.TrimSpace(parts[1])

	var tags []string
	var filePath string
	if strings.HasPrefix(rest, "[") {
		end := strings.Index(rest, "]")
		if end < 0 {
			return nil
		}
		tagsRaw := rest[1:end]
		tags = strings.Split(tagsRaw, ",")
		for i, t := range tags {
			tags[i] = strings.TrimSpace(t)
		}
		filePath = strings.TrimSpace(rest[end+1:])
	} else {
		filePath = rest
	}

	return &Match{
		RuleName: ruleName,
		FilePath: filePath,
		Tags:     tags,
		Severity: severityFromTags(tags),
	}
}

// expandRules: arquivo unico → [path]; diretorio → walk recursivo coletando .yar/.yara.
func (s *Scanner) expandRules() ([]string, error) {
	info, err := os.Stat(s.RulesPath)
	if err != nil {
		return nil, fmt.Errorf("rules-path %s: %w", s.RulesPath, err)
	}
	if !info.IsDir() {
		return []string{s.RulesPath}, nil
	}
	var out []string
	err = filepath.WalkDir(s.RulesPath, func(p string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.IsDir() {
			return nil
		}
		ext := strings.ToLower(filepath.Ext(p))
		if ext == ".yar" || ext == ".yara" {
			out = append(out, p)
		}
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("walk %s: %w", s.RulesPath, err)
	}
	if len(out) == 0 {
		return nil, fmt.Errorf("nenhum .yar/.yara em %s", s.RulesPath)
	}
	return out, nil
}

func severityFromTags(tags []string) events.Severity {
	for _, t := range tags {
		switch strings.ToLower(t) {
		case "critical":
			return events.SeverityCritical
		case "high":
			return events.SeverityError
		case "medium", "warn":
			return events.SeverityWarn
		case "low", "info":
			return events.SeverityInfo
		}
	}
	return events.SeverityWarn
}
