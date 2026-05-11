/**
 * <OsIcon> — logo oficial da distro/SO via Iconify (pack "logos").
 *
 * Logos sao SVGs oficiais com cores oficiais (Debian swirl vermelho,
 * Ubuntu circle laranja, Fedora F azul, etc). Cache automatico pelo
 * Iconify apos primeira renderizacao.
 *
 * Fallback: pinguim Tux generico quando distro nao mapeado.
 */

import { Icon } from '@iconify/react'

interface Props {
  distro?: string | null
  family?: string | null
  size?: 'sm' | 'md' | 'lg'
}

/** Mapeamento distro/family -> nome de icone Iconify (pack "logos:*"). */
const ICONS: Record<string, string> = {
  debian: 'logos:debian',
  ubuntu: 'logos:ubuntu',
  fedora: 'logos:fedora',
  rocky: 'logos:rocky-linux',
  rockylinux: 'logos:rocky-linux',
  alma: 'logos:almalinux',
  almalinux: 'logos:almalinux',
  centos: 'logos:centos-icon',
  opensuse: 'logos:opensuse',
  arch: 'logos:archlinux',
  archlinux: 'logos:archlinux',
  alpine: 'logos:alpinelinux',
  alpinelinux: 'logos:alpinelinux',
  redhat: 'logos:redhat',
  rhel: 'logos:redhat',
  oracle: 'logos:oracle',
  kali: 'logos:kali-linux',
  gentoo: 'logos:gentoo',
  void: 'logos:void',
  // SO genericos
  macos: 'logos:apple',
  darwin: 'logos:apple',
  apple: 'logos:apple',
  windows: 'logos:microsoft-windows-icon',
  linux: 'logos:linux-tux',
}

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

  return (
    <div
      className={`${sizeCls} flex items-center justify-center flex-shrink-0`}
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
