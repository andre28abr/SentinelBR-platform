/**
 * <OsIcon> — badge visual indicando a distro/sistema operacional do host.
 * Renderiza um quadrado colorido com inicial do distro (estilo "favicon").
 * Fallback: generico "L" cinza pra Linux desconhecido.
 */

interface Props {
  distro?: string | null
  family?: string | null
  size?: 'sm' | 'md' | 'lg'
}

const PALETTE: Record<string, { bg: string; text: string; letter: string; label: string }> = {
  debian: {
    bg: 'bg-red-100 dark:bg-red-950',
    text: 'text-red-700 dark:text-red-300',
    letter: 'D',
    label: 'Debian',
  },
  ubuntu: {
    bg: 'bg-orange-100 dark:bg-orange-950',
    text: 'text-orange-700 dark:text-orange-300',
    letter: 'U',
    label: 'Ubuntu',
  },
  fedora: {
    bg: 'bg-blue-100 dark:bg-blue-950',
    text: 'text-blue-700 dark:text-blue-300',
    letter: 'F',
    label: 'Fedora',
  },
  rocky: {
    bg: 'bg-emerald-100 dark:bg-emerald-950',
    text: 'text-emerald-700 dark:text-emerald-300',
    letter: 'R',
    label: 'Rocky Linux',
  },
  almalinux: {
    bg: 'bg-rose-100 dark:bg-rose-950',
    text: 'text-rose-700 dark:text-rose-300',
    letter: 'A',
    label: 'AlmaLinux',
  },
  alma: {
    bg: 'bg-rose-100 dark:bg-rose-950',
    text: 'text-rose-700 dark:text-rose-300',
    letter: 'A',
    label: 'AlmaLinux',
  },
  centos: {
    bg: 'bg-purple-100 dark:bg-purple-950',
    text: 'text-purple-700 dark:text-purple-300',
    letter: 'C',
    label: 'CentOS',
  },
  opensuse: {
    bg: 'bg-green-100 dark:bg-green-950',
    text: 'text-green-700 dark:text-green-300',
    letter: 'S',
    label: 'openSUSE',
  },
  arch: {
    bg: 'bg-sky-100 dark:bg-sky-950',
    text: 'text-sky-700 dark:text-sky-300',
    letter: 'A',
    label: 'Arch Linux',
  },
  alpine: {
    bg: 'bg-indigo-100 dark:bg-indigo-950',
    text: 'text-indigo-700 dark:text-indigo-300',
    letter: 'A',
    label: 'Alpine',
  },
  macos: {
    bg: 'bg-zinc-200 dark:bg-zinc-800',
    text: 'text-zinc-700 dark:text-zinc-300',
    letter: '',
    label: 'macOS',
  },
  darwin: {
    bg: 'bg-zinc-200 dark:bg-zinc-800',
    text: 'text-zinc-700 dark:text-zinc-300',
    letter: '',
    label: 'macOS',
  },
  windows: {
    bg: 'bg-cyan-100 dark:bg-cyan-950',
    text: 'text-cyan-700 dark:text-cyan-300',
    letter: 'W',
    label: 'Windows',
  },
}

export default function OsIcon({ distro, family, size = 'md' }: Props) {
  const key = (distro || family || '').toLowerCase()
  const cfg = PALETTE[key] || {
    bg: 'bg-zinc-100 dark:bg-zinc-900',
    text: 'text-zinc-500',
    letter: 'L',
    label: 'Linux',
  }

  const sizeCls = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-base',
  }[size]

  return (
    <div
      className={`${sizeCls} ${cfg.bg} ${cfg.text} rounded-md flex items-center justify-center font-bold flex-shrink-0`}
      title={cfg.label}
      aria-label={cfg.label}
    >
      {cfg.letter}
    </div>
  )
}

/** Texto humano pro distro (ex: "Debian 11.7"). */
// eslint-disable-next-line react-refresh/only-export-components
export function osLabel(distro?: string | null, version?: string | null, family?: string | null): string {
  if (!distro && !family) return 'OS desconhecido'
  const key = (distro || family || '').toLowerCase()
  const cfg = PALETTE[key]
  const name = cfg?.label || distro || family || 'Linux'
  return version ? `${name} ${version}` : name
}
