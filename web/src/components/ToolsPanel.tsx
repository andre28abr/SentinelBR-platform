/**
 * <ToolsPanel> — overview das ferramentas de seguranca/hardening detectadas
 * pelo agente. Cada ferramenta tem um card "instalado" (verde) ou "nao
 * detectado" (cinza) com hint de instalacao.
 *
 * UI de interacao funcional (banir/desbanir IP no fail2ban, rodar lynis audit,
 * etc) vem em fases seguintes.
 */

import { Icon } from '@iconify/react'

import Tooltip from '@/components/Tooltip'

interface ToolsHost {
  fail2ban_installed: boolean | null
  fail2ban_banned_ips: number | null
  fail2ban_jails_active: number | null
  firewall_active: string | null
  auditd_active: boolean | null
  rkhunter_installed: boolean | null
  lynis_installed: boolean | null
}

interface Props {
  host: ToolsHost
}

export default function ToolsPanel({ host }: Props) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-zinc-500">
        Ferramentas de hardening/defesa detectadas no host. Cards verdes indicam
        ferramentas ativas — clicar mostra detalhes. Cards cinzas mostram
        instruções de instalação.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Fail2banCard
          installed={!!host.fail2ban_installed}
          jails={host.fail2ban_jails_active ?? 0}
          banned={host.fail2ban_banned_ips ?? 0}
        />
        <FirewallCard active={host.firewall_active ?? ''} />
        <AuditdCard active={!!host.auditd_active} />
        <RkhunterCard installed={!!host.rkhunter_installed} />
        <LynisCard installed={!!host.lynis_installed} />
      </div>
    </div>
  )
}

function ToolCard({
  icon,
  name,
  description,
  installed,
  badge,
  details,
  installHint,
}: {
  icon: string
  name: string
  description: string
  installed: boolean
  badge?: string
  details?: React.ReactNode
  installHint: { apt?: string; dnf?: string }
}) {
  return (
    <div
      className={`p-4 rounded-lg border ${
        installed
          ? 'border-emerald-300 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/30'
          : 'border-zinc-200 dark:border-zinc-800'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <Icon
            icon={icon}
            className={`text-xl ${installed ? 'text-emerald-700 dark:text-emerald-400' : 'text-zinc-400'}`}
            aria-hidden
          />
          <Tooltip content={description}>
            <h4 className="text-sm font-semibold cursor-help">{name}</h4>
          </Tooltip>
        </div>
        <span
          className={`text-[10px] px-2 py-0.5 rounded font-medium ${
            installed
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200'
              : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400'
          }`}
        >
          {badge ?? (installed ? 'instalado' : 'não detectado')}
        </span>
      </div>

      {installed ? (
        details ?? (
          <p className="text-xs text-zinc-500">
            Detectada e funcionando. UI de interação chegará em breve.
          </p>
        )
      ) : (
        <div className="space-y-1.5">
          <p className="text-xs text-zinc-500">{description}</p>
          {installHint.apt && (
            <div className="bg-zinc-100 dark:bg-zinc-900 px-2 py-1 rounded">
              <p className="text-[9px] uppercase text-zinc-500">Debian / Ubuntu</p>
              <code className="text-[11px] font-mono">{installHint.apt}</code>
            </div>
          )}
          {installHint.dnf && (
            <div className="bg-zinc-100 dark:bg-zinc-900 px-2 py-1 rounded">
              <p className="text-[9px] uppercase text-zinc-500">RHEL / Fedora</p>
              <code className="text-[11px] font-mono">{installHint.dnf}</code>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function Fail2banCard({
  installed,
  jails,
  banned,
}: {
  installed: boolean
  jails: number
  banned: number
}) {
  return (
    <ToolCard
      icon="lucide:shield-ban"
      name="fail2ban"
      description="Bloqueia IPs automaticamente após N tentativas falhas de login (SSH, HTTP, etc). Essencial pra qualquer servidor exposto à internet."
      installed={installed}
      details={
        <div className="text-xs text-zinc-600 dark:text-zinc-400 space-y-0.5">
          <p>
            <span className="font-mono font-medium">{jails}</span> jail
            {jails === 1 ? '' : 's'} configurado{jails === 1 ? '' : 's'}
          </p>
          <p>
            <span className="font-mono font-medium">{banned}</span> IP
            {banned === 1 ? '' : 's'} banido{banned === 1 ? '' : 's'} no momento
          </p>
        </div>
      }
      installHint={{
        apt: 'sudo apt install fail2ban && sudo systemctl enable --now fail2ban',
        dnf: 'sudo dnf install fail2ban && sudo systemctl enable --now fail2ban',
      }}
    />
  )
}

function FirewallCard({ active }: { active: string }) {
  const installed = active !== ''
  return (
    <ToolCard
      icon="lucide:brick-wall"
      name="Firewall"
      description="Controle de tráfego de rede. SentinelBR detecta ufw (Ubuntu), firewalld (Fedora/RHEL), nftables ou iptables."
      installed={installed}
      badge={installed ? active : 'não detectado'}
      details={
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          <span className="font-mono font-medium">{active}</span> ativo no host.
        </p>
      }
      installHint={{
        apt: 'sudo apt install ufw && sudo ufw enable',
        dnf: 'sudo dnf install firewalld && sudo systemctl enable --now firewalld',
      }}
    />
  )
}

function AuditdCard({ active }: { active: boolean }) {
  return (
    <ToolCard
      icon="lucide:file-search"
      name="auditd"
      description="Registra eventos de syscall do kernel — quem rodou o quê, quando, de onde. Indispensável pra forensics e compliance."
      installed={active}
      badge={active ? 'ativo' : 'não detectado'}
      installHint={{
        apt: 'sudo apt install auditd && sudo systemctl enable --now auditd',
        dnf: 'sudo dnf install audit && sudo systemctl enable --now auditd',
      }}
    />
  )
}

function RkhunterCard({ installed }: { installed: boolean }) {
  return (
    <ToolCard
      icon="lucide:bug-play"
      name="rkhunter"
      description="Rootkit hunter — verifica sinais de rootkits, backdoors e kits exploits comuns no Linux."
      installed={installed}
      installHint={{
        apt: 'sudo apt install rkhunter && sudo rkhunter --update',
        dnf: 'sudo dnf install rkhunter && sudo rkhunter --update',
      }}
    />
  )
}

function LynisCard({ installed }: { installed: boolean }) {
  return (
    <ToolCard
      icon="lucide:clipboard-check"
      name="lynis"
      description="Auditoria de hardening — gera score (0-100) e lista de recomendações pra deixar o servidor mais seguro."
      installed={installed}
      installHint={{
        apt: 'sudo apt install lynis',
        dnf: 'sudo dnf install lynis',
      }}
    />
  )
}
