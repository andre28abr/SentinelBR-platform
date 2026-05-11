/**
 * <RowActionsMenu> — botao "⋯" que abre dropdown com lista de acoes contextuais.
 * Pra usar em colunas "Ações" das tabelas (alerts, actions, events, etc).
 *
 * Quando ha apenas 1 acao, mostra ela direto como botao (sem dropdown).
 * Quando ha 2+, mostra "⋯" que abre o menu.
 *
 * Uso:
 *   <RowActionsMenu items={[
 *     { label: 'Desbloquear', onClick: () => unblock(action.id) },
 *     { label: 'Deletar', onClick: () => del(action.id), danger: true },
 *   ]} />
 */

import { useEffect, useRef, useState } from 'react'

export interface MenuItem {
  label: string
  onClick: () => void | Promise<void>
  danger?: boolean
  disabled?: boolean
}

interface Props {
  items: MenuItem[]
  /** texto do botao quando ha apenas 1 item. Default usa o label do item. */
  singleLabel?: string
}

export default function RowActionsMenu({ items }: Props) {
  const [open, setOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const enabled = items.filter((i) => !i.disabled)
  if (enabled.length === 0) return <span className="text-zinc-400">—</span>

  // 1 acao -> renderiza direto como link (sem dropdown)
  if (enabled.length === 1) {
    const it = enabled[0]
    return (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          void it.onClick()
        }}
        className={`text-xs hover:underline ${it.danger ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'}`}
      >
        {it.label}
      </button>
    )
  }

  // 2+ acoes -> dropdown
  return (
    <div className="relative inline-block" ref={menuRef}>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen(!open)
        }}
        className="px-2 py-0.5 rounded text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100 text-base leading-none"
        aria-label="acoes"
        aria-expanded={open}
      >
        ⋯
      </button>
      {open && (
        <div className="absolute right-0 mt-1 z-30 min-w-[160px] rounded-md border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-lg py-1">
          {items.map((it, i) => (
            <button
              key={i}
              type="button"
              disabled={it.disabled}
              onClick={(e) => {
                e.stopPropagation()
                setOpen(false)
                if (!it.disabled) void it.onClick()
              }}
              className={`block w-full text-left px-3 py-1.5 text-sm hover:bg-zinc-100 dark:hover:bg-zinc-900 ${
                it.disabled
                  ? 'text-zinc-400 cursor-not-allowed'
                  : it.danger
                    ? 'text-red-600 dark:text-red-400'
                    : 'text-zinc-700 dark:text-zinc-200'
              }`}
            >
              {it.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
