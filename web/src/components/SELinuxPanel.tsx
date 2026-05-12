/**
 * <SELinuxPanel> — status + comandos uteis pra SELinux.
 *
 * Read-only — SELinux mode change requer reboot e edicao de
 * /etc/selinux/config (nao expomos via API por seguranca).
 *
 * Estados:
 *   Enforcing    — verde, "tudo ok"
 *   Permissive   — amarelo, "logando mas nao bloqueando"
 *   Disabled     — cinza, info pra ativar
 *   "" (vazio)   — host nao tem SELinux (Ubuntu/Debian, ou container OrbStack)
 */

import { Icon } from '@iconify/react'

interface Props {
  mode: string  // "Enforcing" | "Permissive" | "Disabled" | ""
}

export default function SELinuxPanel({ mode }: Props) {
  const cfg = stateConfig(mode)

  return (
    <div className="space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Icon
            icon="lucide:shield-check"
            className={`text-xl ${cfg.iconColor}`}
            aria-hidden
          />
          <h3 className="text-base font-semibold">SELinux</h3>
          <span
            className={`text-xs px-2 py-0.5 rounded font-medium ${cfg.badgeClass}`}
          >
            {cfg.badge}
          </span>
        </div>
      </div>

      <p className="text-sm text-zinc-500">
        Mandatory Access Control (MAC) do kernel Linux — confina processos a
        perfis com permissões mínimas. Exploit num serviço web fica preso ao
        contexto do <code className="font-mono">httpd_t</code>, não ataca o
        sistema todo.
      </p>

      <div className={`px-3 py-2 rounded text-sm ${cfg.detailClass}`}>
        {cfg.detail}
      </div>

      {mode && mode !== "" && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase text-zinc-500">
            Comandos úteis (rodar no host)
          </h4>
          <CmdHint
            label="Status detalhado"
            cmd="sestatus"
            description="mostra modo + policy carregada + boolean state"
          />
          <CmdHint
            label="Trocar pra Enforcing"
            cmd="sudo setenforce 1"
            description="aplica imediatamente (não persiste reboot)"
          />
          <CmdHint
            label="Persistir entre reboots"
            cmd="sudo sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config"
            description="edita /etc/selinux/config e reboot pra aplicar"
          />
          <CmdHint
            label="Ver denials recentes (auditd)"
            cmd="sudo ausearch -m AVC -ts recent"
            description="se houver denials, SentinelBR já capturou via MAC collector — veja aba Eventos source=selinux"
          />
          <CmdHint
            label="Gerar policy a partir de denial"
            cmd="sudo audit2allow -a -M mymodule && sudo semodule -i mymodule.pp"
            description="cuidado: cria exceção. Só se for falso positivo confirmado"
          />
        </div>
      )}

      {(mode === "" || mode === "Disabled") && (
        <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 px-3 py-2 rounded text-xs text-blue-800 dark:text-blue-200">
          <strong>Por que pode estar desabilitado:</strong> em containers
          (Docker/OrbStack/LXC), SELinux geralmente está desabilitado no
          kernel do host — não tem como ativar dentro do container. Em VM
          real ou bare metal Fedora/RHEL/Rocky, vem ativo por default.
        </div>
      )}
    </div>
  )
}

function stateConfig(mode: string) {
  switch (mode) {
    case "Enforcing":
      return {
        badge: "Enforcing",
        badgeClass: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200",
        iconColor: "text-emerald-700 dark:text-emerald-400",
        detail: "Sistema confinado — exploits ficam contidos ao contexto do processo. Estado ideal pra produção.",
        detailClass: "bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-200",
      }
    case "Permissive":
      return {
        badge: "Permissive",
        badgeClass: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        iconColor: "text-yellow-700 dark:text-yellow-400",
        detail: "Violations são logadas mas não bloqueadas. Útil pra debug/diagnose, mas não protege em prod.",
        detailClass: "bg-yellow-50 dark:bg-yellow-950 text-yellow-800 dark:text-yellow-200",
      }
    case "Disabled":
      return {
        badge: "Disabled",
        badgeClass: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
        iconColor: "text-zinc-400",
        detail: "SELinux instalado mas inativo. Containers OrbStack/Docker não suportam — limitação do kernel host.",
        detailClass: "bg-zinc-100 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300",
      }
    default:
      return {
        badge: "não detectado",
        badgeClass: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
        iconColor: "text-zinc-400",
        detail: "Host não tem SELinux instalado. Comum em Ubuntu/Debian (que usam AppArmor).",
        detailClass: "bg-zinc-100 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300",
      }
  }
}

function CmdHint({ label, cmd, description }: { label: string; cmd: string; description: string }) {
  return (
    <div className="bg-zinc-100 dark:bg-zinc-900 px-3 py-2 rounded">
      <p className="text-[10px] uppercase text-zinc-500 mb-1">{label}</p>
      <code className="text-xs font-mono block mb-1 break-all">{cmd}</code>
      <p className="text-[11px] text-zinc-500">{description}</p>
    </div>
  )
}
