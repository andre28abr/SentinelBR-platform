// Package apparmor extrai eventos de denials AppArmor do dmesg/journald/audit.log.
//
// Formato tipico:
//   audit: type=1400 audit(1234567890.123:456): apparmor="DENIED"
//     operation="open" profile="snap.firefox.firefox" name="/etc/passwd"
//     pid=1234 comm="firefox" requested_mask="r" denied_mask="r"
//     fsuid=1000 ouid=0
package apparmor

import (
	"regexp"
	"strings"
	"time"

	"github.com/sentinelbr/agent/internal/events"
)

const Source = "apparmor"

var reKV = regexp.MustCompile(`(\w+)=("([^"]*)"|(\S+))`)

func Parse(hostID string, ts time.Time, line string) *events.Event {
	line = strings.TrimSpace(line)
	if !strings.Contains(line, "apparmor=") {
		return nil
	}

	fields := map[string]string{}
	for _, kv := range reKV.FindAllStringSubmatch(line, -1) {
		key := kv[1]
		val := kv[3]
		if val == "" {
			val = kv[4]
		}
		fields[key] = val
	}

	verdict := fields["apparmor"]
	if verdict != "DENIED" {
		return nil
	}

	ev := events.New(hostID, Source, ts, line)
	ev.Severity = events.SeverityWarn
	ev.Fields["event.category"] = "host"
	ev.Fields["event.action"] = "apparmor_denied"
	ev.Fields["event.outcome"] = "failure"

	if v, ok := fields["operation"]; ok {
		ev.Fields["apparmor.operation"] = v
	}
	if v, ok := fields["profile"]; ok {
		ev.Fields["apparmor.profile"] = v
	}
	if v, ok := fields["requested_mask"]; ok {
		ev.Fields["apparmor.requested_mask"] = v
	}
	if v, ok := fields["denied_mask"]; ok {
		ev.Fields["apparmor.denied_mask"] = v
	}
	if v, ok := fields["comm"]; ok {
		ev.Fields["process.name"] = v
	}
	if v, ok := fields["pid"]; ok {
		ev.Fields["process.pid"] = v
	}
	if v, ok := fields["name"]; ok {
		ev.Fields["file.name"] = v
	}

	return ev
}
