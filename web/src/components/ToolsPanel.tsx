/**
 * <ToolsPanel> — agrega as ferramentas de hardening/defesa detectadas no host.
 *
 * Sub-aba "Visao geral" mostra cards-resumo de todas (instaladas vs nao).
 * Cada ferramenta DETECTADA com UI funcional ganha sub-aba propria.
 *
 * Ferramentas sem painel interativo (SELinux/AppArmor, status only) so
 * aparecem nos cards da Visao geral.
 */

import { Icon } from '@iconify/react'

import AidePanel from '@/components/AidePanel'
import AppArmorPanel from '@/components/AppArmorPanel'
import AuditdPanel from '@/components/AuditdPanel'
import ChkrootkitPanel from '@/components/ChkrootkitPanel'
import ErrorBoundary from '@/components/ErrorBoundary'
import Fail2banPanel from '@/components/Fail2banPanel'
import FirewallPanel from '@/components/FirewallPanel'
import LynisPanel from '@/components/LynisPanel'
import RkhunterPanel from '@/components/RkhunterPanel'
import SELinuxPanel from '@/components/SELinuxPanel'
import Tabs from '@/components/Tabs'
import Tooltip from '@/components/Tooltip'

/** Wrap defensivo: se o panel crashar, mostra fallback amigavel em vez de
 *  tela preta. Cada sub-aba tem boundary isolado — bug em fail2ban nao
 *  derruba a aba inteira de Ferramentas. */
function Guarded({ children }: { children: React.ReactNode }) {
  return <ErrorBoundary>{children}</ErrorBoundary>
}

interface ToolsHost {
  id: string
  fail2ban_installed: boolean | null
  fail2ban_banned_ips: number | null
  fail2ban_jails_active: number | null
  fail2ban_status_json: string | null
  firewall_active: string | null
  firewall_status_json: string | null
  auditd_active: boolean | null
  auditd_status_json: string | null
  rkhunter_installed: boolean | null
  lynis_installed: boolean | null
  chkrootkit_installed: boolean | null
  aide_installed: boolean | null
  selinux_mode: string | null
  apparmor_mode: string | null
}

interface Props {
  host: ToolsHost
}

function SubTabLabel({ icon, text }: { icon: string; text: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <Icon icon={icon} className="text-base" aria-hidden />
      {text}
    </span>
  )
}

export default function ToolsPanel({ host }: Props) {
  const items = [
    {
      value: 'overview',
      label: <SubTabLabel icon="lucide:list" text="Visão geral" />,
      content: <Overview host={host} />,
    },
  ]
  if (host.fail2ban_installed) {
    items.push({
      value: 'fail2ban',
      label: <SubTabLabel icon="lucide:shield-ban" text="fail2ban" />,
      content: (
        <Guarded>
          <Fail2banPanel
            hostId={host.id}
            statusJson={host.fail2ban_status_json}
            jailsActive={host.fail2ban_jails_active ?? 0}
            bannedIps={host.fail2ban_banned_ips ?? 0}
          />
        </Guarded>
      ),
    })
  }
  if (host.firewall_active) {
    items.push({
      value: 'firewall',
      label: <SubTabLabel icon="lucide:brick-wall" text="Firewall" />,
      content: (
        <Guarded>
          <FirewallPanel
            hostId={host.id}
            backend={host.firewall_active}
            statusJson={host.firewall_status_json}
          />
        </Guarded>
      ),
    })
  }
  if (host.auditd_active) {
    items.push({
      value: 'auditd',
      label: <SubTabLabel icon="lucide:file-search" text="auditd" />,
      content: (
        <Guarded>
          <AuditdPanel statusJson={host.auditd_status_json} />
        </Guarded>
      ),
    })
  }
  if (host.rkhunter_installed) {
    items.push({
      value: 'rkhunter',
      label: <SubTabLabel icon="lucide:bug-play" text="rkhunter" />,
      content: (
        <Guarded>
          <RkhunterPanel hostId={host.id} />
        </Guarded>
      ),
    })
  }
  if (host.chkrootkit_installed) {
    items.push({
      value: 'chkrootkit',
      label: <SubTabLabel icon="lucide:bug-off" text="chkrootkit" />,
      content: (
        <Guarded>
          <ChkrootkitPanel hostId={host.id} />
        </Guarded>
      ),
    })
  }
  if (host.lynis_installed) {
    items.push({
      value: 'lynis',
      label: <SubTabLabel icon="lucide:clipboard-check" text="lynis" />,
      content: (
        <Guarded>
          <LynisPanel hostId={host.id} />
        </Guarded>
      ),
    })
  }
  if (host.aide_installed) {
    items.push({
      value: 'aide',
      label: <SubTabLabel icon="lucide:database" text="AIDE" />,
      content: (
        <Guarded>
          <AidePanel hostId={host.id} />
        </Guarded>
      ),
    })
  }
  // SELinux/AppArmor: aparecem como sub-aba se o agente reportou modo
  // (mesmo que "Disabled" — pra mostrar status + comandos pra ativar).
  if (host.selinux_mode) {
    items.push({
      value: 'selinux',
      label: <SubTabLabel icon="lucide:shield-check" text="SELinux" />,
      content: (
        <Guarded>
          <SELinuxPanel mode={host.selinux_mode} />
        </Guarded>
      ),
    })
  }
  if (host.apparmor_mode) {
    items.push({
      value: 'apparmor',
      label: <SubTabLabel icon="lucide:shield-check" text="AppArmor" />,
      content: (
        <Guarded>
          <AppArmorPanel mode={host.apparmor_mode} />
        </Guarded>
      ),
    })
  }

  return <Tabs items={items} />
}

function Overview({ host }: { host: ToolsHost }) {
  return (
    <div className="space-y-3">
      <p className="text-sm text-zinc-500">
        Ferramentas de hardening/defesa detectadas no host. Cards verdes têm
        sub-aba dedicada acima; cinzas mostram instruções de instalação.
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
        <ChkrootkitCard installed={!!host.chkrootkit_installed} />
        <LynisCard installed={!!host.lynis_installed} />
        <AideCard installed={!!host.aide_installed} />
        <SELinuxCard mode={host.selinux_mode ?? ''} />
        <AppArmorCard mode={host.apparmor_mode ?? ''} />
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
  installHint?: { apt?: string; dnf?: string }
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
            Detectada. Veja a sub-aba dedicada acima para interagir.
          </p>
        )
      ) : (
        <div className="space-y-1.5">
          <p className="text-xs text-zinc-500">{description}</p>
          {installHint?.apt && (
            <div className="bg-zinc-100 dark:bg-zinc-900 px-2 py-1 rounded">
              <p className="text-[9px] uppercase text-zinc-500">Debian / Ubuntu</p>
              <code className="text-[11px] font-mono">{installHint.apt}</code>
            </div>
          )}
          {installHint?.dnf && (
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

function Fail2banCard({ installed, jails, banned }: { installed: boolean; jails: number; banned: number }) {
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

function ChkrootkitCard({ installed }: { installed: boolean }) {
  return (
    <ToolCard
      icon="lucide:bug-off"
      name="chkrootkit"
      description="Detector de rootkits alternativo ao rkhunter. Roda ~70 testes de scripts shell."
      installed={installed}
      installHint={{
        apt: 'sudo apt install chkrootkit',
        dnf: 'sudo dnf install chkrootkit',
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

function AideCard({ installed }: { installed: boolean }) {
  return (
    <ToolCard
      icon="lucide:database"
      name="AIDE"
      description="File integrity monitoring — detecta modificações em arquivos críticos (/etc, binários) comparando contra um snapshot."
      installed={installed}
      installHint={{
        apt: 'sudo apt install aide && sudo aide --init',
        dnf: 'sudo dnf install aide && sudo aide --init',
      }}
    />
  )
}

function SELinuxCard({ mode }: { mode: string }) {
  const installed = mode !== '' && mode !== 'Disabled'
  return (
    <ToolCard
      icon="lucide:shield-check"
      name="SELinux"
      description="Mandatory Access Control — confina processos a perfis com permissões mínimas. Comum em RHEL/Fedora."
      installed={installed}
      badge={mode || 'não detectado'}
      details={
        <p className="text-xs text-zinc-600 dark:text-zinc-400">
          Modo: <span className="font-mono font-medium">{mode}</span>
          {mode === 'Permissive' && (
            <> · <span className="text-yellow-700 dark:text-yellow-400">violações são logadas mas não bloqueadas</span></>
          )}
        </p>
      }
    />
  )
}

function AppArmorCard({ mode }: { mode: string }) {
  const installed = mode === 'enabled'
  return (
    <ToolCard
      icon="lucide:shield-check"
      name="AppArmor"
      description="Mandatory Access Control alternativo ao SELinux. Comum em Ubuntu/Debian."
      installed={installed}
      badge={mode || 'não detectado'}
    />
  )
}
