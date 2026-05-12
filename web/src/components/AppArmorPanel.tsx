/**
 * <AppArmorPanel> — status + comandos uteis pra AppArmor.
 *
 * Read-only — mudancas em profiles requerem editar arquivos de policy
 * em /etc/apparmor.d/ e recarregar (apparmor_parser).
 *
 * Estados:
 *   "enabled"  — verde, profiles ativos
 *   "disabled" — cinza, kernel module nao carregado
 *   "" (vazio) — host nao tem AppArmor (Fedora/RHEL — usam SELinux)
 */

import { Icon } from '@iconify/react'

interface Props {
  mode: string  // "enabled" | "disabled" | ""
}

export default function AppArmorPanel({ mode }: Props) {
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
          <h3 className="text-base font-semibold">AppArmor</h3>
          <span
            className={`text-xs px-2 py-0.5 rounded font-medium ${cfg.badgeClass}`}
          >
            {cfg.badge}
          </span>
        </div>
      </div>

      <p className="text-sm text-zinc-500">
        Mandatory Access Control (MAC) alternativo ao SELinux. Cada perfil
        confina um programa específico (ex:{' '}
        <code className="font-mono">/etc/apparmor.d/usr.sbin.mysqld</code>).
        Comum em Ubuntu/Debian/SUSE.
      </p>

      <div className={`px-3 py-2 rounded text-sm ${cfg.detailClass}`}>
        {cfg.detail}
      </div>

      {mode === "enabled" && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase text-zinc-500">
            Comandos úteis (rodar no host)
          </h4>
          <CmdHint
            label="Listar profiles e contadores"
            cmd="sudo aa-status"
            description="profiles em enforce/complain, processos confinados, denials"
          />
          <CmdHint
            label="Ver denials recentes"
            cmd="sudo dmesg | grep -i apparmor | tail -20"
            description="também na aba Eventos source=apparmor (capturado pelo SentinelBR)"
          />
          <CmdHint
            label="Profile pra modo permissivo"
            cmd="sudo aa-complain /etc/apparmor.d/usr.sbin.mysqld"
            description="loga violations sem bloquear (debug)"
          />
          <CmdHint
            label="Profile pra modo enforce"
            cmd="sudo aa-enforce /etc/apparmor.d/usr.sbin.mysqld"
            description="bloqueia ações fora do perfil (modo produção)"
          />
          <CmdHint
            label="Recarregar profile editado"
            cmd="sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.mysqld"
            description="aplica mudanças sem reboot"
          />
        </div>
      )}

      {mode !== "enabled" && (
        <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 px-3 py-2 rounded text-xs text-blue-800 dark:text-blue-200">
          <strong>Por que pode estar ausente:</strong> AppArmor não vem em
          Fedora/RHEL/Rocky (essas distros usam SELinux). Em Ubuntu/Debian
          vem por default. Em containers OrbStack/Docker, o LSM AppArmor
          pode estar desabilitado no kernel do host.
        </div>
      )}
    </div>
  )
}

function stateConfig(mode: string) {
  switch (mode) {
    case "enabled":
      return {
        badge: "ativo",
        badgeClass: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200",
        iconColor: "text-emerald-700 dark:text-emerald-400",
        detail: "AppArmor ativo no kernel. Rode `aa-status` no host pra ver quantos profiles estão em enforce vs complain.",
        detailClass: "bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-200",
      }
    case "disabled":
      return {
        badge: "desabilitado",
        badgeClass: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
        iconColor: "text-zinc-400",
        detail: "AppArmor instalado mas LSM kernel não está carregado.",
        detailClass: "bg-zinc-100 dark:bg-zinc-900 text-zinc-700 dark:text-zinc-300",
      }
    default:
      return {
        badge: "não detectado",
        badgeClass: "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
        iconColor: "text-zinc-400",
        detail: "Host não tem AppArmor. Em Fedora/RHEL, use SELinux.",
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
