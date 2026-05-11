// Package selinux extrai eventos de denials AVC do auditd (linhas type=AVC em
// /var/log/audit/audit.log).
//
// Formato tipico:
//   type=AVC msg=audit(1715270000.000:1234): avc: denied { read } for pid=5000
//     comm="httpd" name="config.json" dev="dm-0" ino=78901
//     scontext=system_u:system_r:httpd_t:s0
//     tcontext=system_u:object_r:default_t:s0
//     tclass=file permissive=0
package selinux

import (
	"regexp"
	"strings"
	"time"

	"github.com/sentinelbr/agent/internal/events"
)

const Source = "selinux"

var (
	reAVC = regexp.MustCompile(`avc:\s+(denied|granted)\s+\{([^}]+)\}\s+for\s+(.*)`)
	reKV  = regexp.MustCompile(`(\w+)=("([^"]*)"|(\S+))`)
)

// Parse tenta extrair um Event de uma linha de auditd. Apenas linhas com `type=AVC`
// e `denied` viram eventos (granted eh ruido). Retorna nil pra outras.
func Parse(hostID string, ts time.Time, line string) *events.Event {
	line = strings.TrimSpace(line)
	if !strings.Contains(line, "avc:") {
		return nil
	}
	m := reAVC.FindStringSubmatch(line)
	if m == nil {
		return nil
	}
	verdict := m[1]
	if verdict != "denied" {
		return nil
	}
	perms := strings.TrimSpace(m[2])
	rest := m[3]

	ev := events.New(hostID, Source, ts, line)
	ev.Severity = events.SeverityWarn
	ev.Fields["event.category"] = "host"
	ev.Fields["event.action"] = "selinux_denied"
	ev.Fields["event.outcome"] = "failure"
	ev.Fields["selinux.permission"] = perms
	ev.Fields["selinux.permissive"] = "false"

	// Extrai key=value do resto. Aspas duplas em valores com espaco.
	for _, kv := range reKV.FindAllStringSubmatch(rest, -1) {
		key := kv[1]
		val := kv[3]
		if val == "" {
			val = kv[4]
		}
		switch key {
		case "comm":
			ev.Fields["process.name"] = val
		case "pid":
			ev.Fields["process.pid"] = val
		case "scontext":
			ev.Fields["selinux.scontext"] = val
			ev.Fields["selinux.source_type"] = extractType(val)
		case "tcontext":
			ev.Fields["selinux.tcontext"] = val
			ev.Fields["selinux.target_type"] = extractType(val)
		case "tclass":
			ev.Fields["selinux.tclass"] = val
		case "name":
			ev.Fields["file.name"] = val
		case "path":
			ev.Fields["file.path"] = val
		case "dest":
			ev.Fields["network.destination_port"] = val
		case "permissive":
			ev.Fields["selinux.permissive"] = mapBool(val)
		}
	}

	return ev
}

// extractType pega o "type" do contexto SELinux: system_u:system_r:httpd_t:s0 -> httpd_t
func extractType(ctx string) string {
	parts := strings.Split(ctx, ":")
	if len(parts) >= 3 {
		return parts[2]
	}
	return ""
}

func mapBool(s string) string {
	switch s {
	case "1", "true":
		return "true"
	default:
		return "false"
	}
}
