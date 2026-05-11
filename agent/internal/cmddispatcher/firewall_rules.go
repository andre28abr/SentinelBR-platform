// Handlers de add/remove firewall rule (Fase H6). Suporta ufw e firewalld,
// outros backends retornam UNSUPPORTED.
//
// Validacao defensiva: server ja validou via Pydantic, mas re-checamos no
// agente pra evitar shell injection em caso de payload malicioso.
package cmddispatcher

import (
	"context"
	"fmt"
	"net"
	"os/exec"
	"strconv"
	"strings"
	"time"

	pb "github.com/sentinelbr/agent/internal/grpc/pb"
)

const firewallCmdTimeout = 10 * time.Second

// validVerb / validProto / validPort ajudam a impedir shell injection.
func validVerb(v string) bool { return v == "allow" || v == "deny" }
func validProto(v string) bool { return v == "tcp" || v == "udp" }

// validPort: aceita "80" | "80,443" | "1000:2000". So digitos + ":" + ","
func validPort(v string) bool {
	if v == "" {
		return false
	}
	for _, r := range v {
		if !(r >= '0' && r <= '9') && r != ':' && r != ',' {
			return false
		}
	}
	return true
}

// validCIDR aceita string vazia OU CIDR valido.
func validCIDR(v string) bool {
	if v == "" {
		return true
	}
	_, _, err := net.ParseCIDR(v)
	return err == nil
}

func (d *Dispatcher) handleAddFirewallRule(c *pb.AddFirewallRuleCommand) (pb.CommandStatus, string) {
	if !validVerb(c.Verb) || !validProto(c.Protocol) || !validPort(c.Port) || !validCIDR(c.SourceCidr) {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "parametros invalidos"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN add_firewall_rule",
			"backend", c.Backend, "verb", c.Verb, "proto", c.Protocol,
			"port", c.Port, "source", c.SourceCidr, "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), firewallCmdTimeout)
	defer cancel()

	switch c.Backend {
	case "ufw":
		if _, err := exec.LookPath("ufw"); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "ufw nao instalado"
		}
		args := []string{c.Verb}
		if c.SourceCidr != "" {
			args = append(args, "from", c.SourceCidr, "to", "any")
		}
		args = append(args, "port", c.Port, "proto", c.Protocol)
		out, err := exec.CommandContext(ctx, "ufw", args...).CombinedOutput()
		if err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED,
				fmt.Sprintf("ufw: %s", strings.TrimSpace(string(out)))
		}
		d.Log.Info("ufw rule adicionada", "args", args)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	case "firewalld":
		if _, err := exec.LookPath("firewall-cmd"); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "firewall-cmd nao instalado"
		}
		rule := buildFirewalldRichRule(c)
		// Adiciona permanente + recarrega + adiciona em runtime tambem
		if out, err := exec.CommandContext(ctx, "firewall-cmd", "--permanent", "--add-rich-rule="+rule).CombinedOutput(); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED,
				fmt.Sprintf("firewall-cmd: %s", strings.TrimSpace(string(out)))
		}
		if out, err := exec.CommandContext(ctx, "firewall-cmd", "--reload").CombinedOutput(); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED,
				fmt.Sprintf("firewall-cmd reload: %s", strings.TrimSpace(string(out)))
		}
		d.Log.Info("firewalld rule adicionada", "rule", rule)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	default:
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED,
			"backend nao suportado pela UI: " + c.Backend
	}
}

func (d *Dispatcher) handleRemoveFirewallRule(c *pb.RemoveFirewallRuleCommand) (pb.CommandStatus, string) {
	if c.RuleId == "" {
		return pb.CommandStatus_COMMAND_STATUS_FAILED, "rule_id vazio"
	}
	if d.DryRun {
		d.Log.Info("DRY-RUN remove_firewall_rule",
			"backend", c.Backend, "rule_id", c.RuleId, "reason", c.Reason)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), firewallCmdTimeout)
	defer cancel()

	switch c.Backend {
	case "ufw":
		if _, err := exec.LookPath("ufw"); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "ufw nao instalado"
		}
		if _, err := strconv.Atoi(c.RuleId); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED, "ufw rule_id deve ser numero"
		}
		out, err := exec.CommandContext(ctx, "ufw", "--force", "delete", c.RuleId).CombinedOutput()
		if err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED,
				fmt.Sprintf("ufw delete: %s", strings.TrimSpace(string(out)))
		}
		d.Log.Info("ufw rule removida", "num", c.RuleId)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	case "firewalld":
		if _, err := exec.LookPath("firewall-cmd"); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED, "firewall-cmd nao instalado"
		}
		// rule_id no firewalld eh o rich-rule completo.
		if out, err := exec.CommandContext(ctx, "firewall-cmd", "--permanent", "--remove-rich-rule="+c.RuleId).CombinedOutput(); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED,
				fmt.Sprintf("firewall-cmd remove: %s", strings.TrimSpace(string(out)))
		}
		if out, err := exec.CommandContext(ctx, "firewall-cmd", "--reload").CombinedOutput(); err != nil {
			return pb.CommandStatus_COMMAND_STATUS_FAILED,
				fmt.Sprintf("firewall-cmd reload: %s", strings.TrimSpace(string(out)))
		}
		d.Log.Info("firewalld rule removida", "rule", c.RuleId)
		return pb.CommandStatus_COMMAND_STATUS_OK, ""
	default:
		return pb.CommandStatus_COMMAND_STATUS_UNSUPPORTED,
			"backend nao suportado: " + c.Backend
	}
}

// buildFirewalldRichRule monta a string esperada por `firewall-cmd --add-rich-rule=`.
// Format: rule family="ipv4" [source address="cidr"] port port="N" protocol="tcp" accept|reject
func buildFirewalldRichRule(c *pb.AddFirewallRuleCommand) string {
	var sb strings.Builder
	sb.WriteString(`rule family="ipv4"`)
	if c.SourceCidr != "" {
		sb.WriteString(` source address="`)
		sb.WriteString(c.SourceCidr)
		sb.WriteString(`"`)
	}
	sb.WriteString(` port port="`)
	sb.WriteString(c.Port)
	sb.WriteString(`" protocol="`)
	sb.WriteString(c.Protocol)
	sb.WriteString(`" `)
	if c.Verb == "allow" {
		sb.WriteString("accept")
	} else {
		sb.WriteString("reject")
	}
	return sb.String()
}
