/**
 * <OsIcon> — logo oficial da distro/SO via Iconify (pack "logos").
 *
 * Logos sao SVGs oficiais com cores oficiais (Debian swirl vermelho,
 * Ubuntu circle laranja, Fedora F azul, etc). Cache automatico pelo
 * Iconify apos primeira renderizacao.
 *
 * Algumas distros (Alpine, Rocky) tem logo oficial muito escuro/preto,
 * o que fica ilegivel em dark mode. Pra essas usamos `simple-icons:*`
 * (monocromaticos via currentColor) que se adaptam ao tema.
 *
 * Fallback: pinguim Tux generico quando distro nao mapeado.
 */

import { Icon } from '@iconify/react'

interface Props {
  distro?: string | null
  family?: string | null
  size?: 'sm' | 'md' | 'lg'
}

/** Mapeamento distro/family -> nome de icone Iconify.
 *
 * Maioria usa pack "logos:*" (logo oficial colorido). Exceções monocromaticas
 * via "simple-icons:*" pra distros cujos logos oficiais sao muito escuros e
 * ficariam invisiveis em dark mode (Alpine, Rocky, Void). simple-icons
 * renderiza em currentColor — herda a cor do CSS pai e se adapta ao tema.
 */
const ICONS: Record<string, string> = {
  debian: 'logos:debian',
  ubuntu: 'logos:ubuntu',
  fedora: 'logos:fedora',
  rocky: 'simple-icons:rockylinux',
  rockylinux: 'simple-icons:rockylinux',
  alma: 'logos:almalinux',
  almalinux: 'logos:almalinux',
  centos: 'logos:centos-icon',
  opensuse: 'logos:opensuse',
  arch: 'logos:archlinux',
  archlinux: 'logos:archlinux',
  alpine: 'simple-icons:alpinelinux',
  alpinelinux: 'simple-icons:alpinelinux',
  redhat: 'logos:redhat',
  rhel: 'logos:redhat',
  oracle: 'logos:oracle',
  kali: 'logos:kali-linux',
  gentoo: 'logos:gentoo',
  void: 'simple-icons:voidlinux',
  // SO genericos
  macos: 'logos:apple',
  darwin: 'logos:apple',
  apple: 'logos:apple',
  windows: 'logos:microsoft-windows-icon',
  linux: 'logos:linux-tux',
}

/** Distros usando simple-icons (monocromaticos) que precisam de cor explicita
 * pra ficarem visiveis no tema. simple-icons renderiza em currentColor por
 * default — se nao definirmos, herda a cor do pai (que pode ser branco em
 * dark mode dentro de fundo branco = invisivel). Forcamos zinc-700 (light)
 * + zinc-300 (dark) pra contraste consistente independente do contexto pai.
 */
const MONO_ICONS = new Set([
  'simple-icons:rockylinux',
  'simple-icons:alpinelinux',
  'simple-icons:voidlinux',
])

const NAMES: Record<string, string> = {
  debian: 'Debian',
  ubuntu: 'Ubuntu',
  fedora: 'Fedora',
  rocky: 'Rocky Linux',
  rockylinux: 'Rocky Linux',
  alma: 'AlmaLinux',
  almalinux: 'AlmaLinux',
  centos: 'CentOS',
  opensuse: 'openSUSE',
  arch: 'Arch Linux',
  archlinux: 'Arch Linux',
  alpine: 'Alpine',
  alpinelinux: 'Alpine',
  redhat: 'RHEL',
  rhel: 'RHEL',
  oracle: 'Oracle Linux',
  kali: 'Kali Linux',
  gentoo: 'Gentoo',
  void: 'Void Linux',
  macos: 'macOS',
  darwin: 'macOS',
  apple: 'macOS',
  windows: 'Windows',
  linux: 'Linux',
}

const SIZES = {
  sm: 'w-6 h-6',
  md: 'w-9 h-9',
  lg: 'w-12 h-12',
}

export default function OsIcon({ distro, family, size = 'md' }: Props) {
  const key = (distro || family || '').toLowerCase().replace(/[^a-z]/g, '')
  const iconName = ICONS[key] || 'logos:linux-tux'
  const label = NAMES[key] || distro || family || 'Linux'
  const sizeCls = SIZES[size]
  // Pra simple-icons (monocromaticos) forcamos cor zinc adaptada ao tema.
  // Logos coloridos do pack "logos:" usam SVG fill proprio — herdam nada.
  const iconColorCls = MONO_ICONS.has(iconName)
    ? 'text-zinc-700 dark:text-zinc-300'
    : ''

  return (
    <div
      className={`${sizeCls} flex items-center justify-center flex-shrink-0 ${iconColorCls}`}
      title={label}
      aria-label={label}
    >
      <Icon icon={iconName} className="w-full h-full" />
    </div>
  )
}

/** Texto humano pro distro (ex: "Debian 11.7"). */
// eslint-disable-next-line react-refresh/only-export-components
export function osLabel(
  distro?: string | null,
  version?: string | null,
  family?: string | null,
): string {
  if (!distro && !family) return 'OS desconhecido'
  const key = (distro || family || '').toLowerCase().replace(/[^a-z]/g, '')
  const name = NAMES[key] || distro || family || 'Linux'
  return version ? `${name} ${version}` : name
}
