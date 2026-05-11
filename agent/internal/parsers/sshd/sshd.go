// Package sshd extrai eventos de seguranca de logs do sshd (auth.log, /var/log/secure, journald).
//
// Reconhece os padroes que importam pra deteccao de brute force e auditoria de acesso:
//   - Failed password for <user> from <ip> port <port>
//   - Failed password for invalid user <user> from <ip> port <port>
//   - Accepted password for <user> from <ip> port <port>
//   - Accepted publickey for <user> from <ip> port <port> ssh2: <type> <fingerprint>
//   - Invalid user <user> from <ip> port <port>
//
// Linhas que nao casam retornam (nil, nil) — silencioso (logs ssh tem muito ruido).
package sshd

import (
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/sentinelbr/agent/internal/events"
)

const Source = "sshd"

var (
	// "Failed password for invalid user admin from 203.0.113.42 port 38242 ssh2"
	// "Failed password for root from 203.0.113.42 port 38241 ssh2"
	reFailedPassword = regexp.MustCompile(
		`^Failed password for (?:invalid user )?(\S+) from (\S+) port (\d+)`,
	)

	// "Accepted password for ubuntu from 198.51.100.42 port 54321 ssh2"
	reAcceptedPassword = regexp.MustCompile(
		`^Accepted password for (\S+) from (\S+) port (\d+)`,
	)

	// "Accepted publickey for deploy from 10.0.1.50 port 41234 ssh2: RSA SHA256:abc..."
	reAcceptedPubkey = regexp.MustCompile(
		`^Accepted publickey for (\S+) from (\S+) port (\d+) ssh2:?\s*(\S+)?\s*(\S+)?`,
	)

	// "Invalid user admin from 203.0.113.42 port 12345"
	reInvalidUser = regexp.MustCompile(
		`^Invalid user (\S+) from (\S+) port (\d+)`,
	)

	// "Disconnected from invalid user admin 203.0.113.42 port 12345 [preauth]"
	reDisconnectedInvalid = regexp.MustCompile(
		`^Disconnected from invalid user (\S+) (\S+) port (\d+)`,
	)
)

// Parse tenta extrair um Event de uma linha de log do sshd. Linhas nao reconhecidas
// retornam nil (skip).
//
// `hostID` eh o UUID do host (pra preencher no Event), `ts` eh o timestamp da linha
// (extraido pelo collector — sshd lida com horarios em formatos variados, fica fora
// do parser).
func Parse(hostID string, ts time.Time, line string) *events.Event {
	line = strings.TrimSpace(line)

	if m := reFailedPassword.FindStringSubmatch(line); m != nil {
		invalid := strings.Contains(line, "invalid user")
		ev := events.New(hostID, Source, ts, line)
		ev.Severity = events.SeverityWarn
		ev.Fields["event.category"] = "authentication"
		ev.Fields["event.action"] = "ssh_login"
		ev.Fields["event.outcome"] = "failure"
		if invalid {
			ev.Fields["event.reason"] = "invalid_user"
			ev.Fields["user.valid"] = "false"
		} else {
			ev.Fields["event.reason"] = "wrong_password"
		}
		ev.Fields["user.name"] = m[1]
		ev.Fields["source.ip"] = m[2]
		ev.Fields["source.port"] = m[3]
		ev.Fields["auth.method"] = "password"
		return ev
	}

	if m := reAcceptedPassword.FindStringSubmatch(line); m != nil {
		ev := events.New(hostID, Source, ts, line)
		ev.Severity = events.SeverityInfo
		ev.Fields["event.category"] = "authentication"
		ev.Fields["event.action"] = "ssh_login"
		ev.Fields["event.outcome"] = "success"
		ev.Fields["user.name"] = m[1]
		ev.Fields["source.ip"] = m[2]
		ev.Fields["source.port"] = m[3]
		ev.Fields["auth.method"] = "password"
		return ev
	}

	if m := reAcceptedPubkey.FindStringSubmatch(line); m != nil {
		ev := events.New(hostID, Source, ts, line)
		ev.Severity = events.SeverityInfo
		ev.Fields["event.category"] = "authentication"
		ev.Fields["event.action"] = "ssh_login"
		ev.Fields["event.outcome"] = "success"
		ev.Fields["user.name"] = m[1]
		ev.Fields["source.ip"] = m[2]
		ev.Fields["source.port"] = m[3]
		ev.Fields["auth.method"] = "publickey"
		if len(m) > 4 && m[4] != "" {
			ev.Fields["auth.key_type"] = m[4]
		}
		if len(m) > 5 && m[5] != "" {
			ev.Fields["auth.key_fingerprint"] = m[5]
		}
		return ev
	}

	if m := reInvalidUser.FindStringSubmatch(line); m != nil {
		ev := events.New(hostID, Source, ts, line)
		ev.Severity = events.SeverityWarn
		ev.Fields["event.category"] = "authentication"
		ev.Fields["event.action"] = "ssh_invalid_user"
		ev.Fields["event.outcome"] = "failure"
		ev.Fields["event.reason"] = "invalid_user"
		ev.Fields["user.name"] = m[1]
		ev.Fields["user.valid"] = "false"
		ev.Fields["source.ip"] = m[2]
		ev.Fields["source.port"] = m[3]
		return ev
	}

	if m := reDisconnectedInvalid.FindStringSubmatch(line); m != nil {
		ev := events.New(hostID, Source, ts, line)
		ev.Severity = events.SeverityInfo
		ev.Fields["event.category"] = "authentication"
		ev.Fields["event.action"] = "ssh_disconnect"
		ev.Fields["event.outcome"] = "failure"
		ev.Fields["user.name"] = m[1]
		ev.Fields["source.ip"] = m[2]
		ev.Fields["source.port"] = m[3]
		return ev
	}

	return nil
}

// strToInt eh helper exportado pra collectors que precisam validar port etc.
func strToInt(s string) (int, error) { return strconv.Atoi(s) }
