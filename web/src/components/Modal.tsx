/**
 * <Modal> — wrapper consistente pra modais. Usa useModalShell (ESC + body
 * scroll lock + focus restore) e segue mesmo visual em todo lugar.
 *
 * Antes: ClamavPanel, YaraPanel, Fail2banPanel, FirewallPanel cada um tinha
 * seu div inline ou `function Modal()` local — comportamento divergente
 * (sem ESC, sem scroll lock, sem focus restore).
 *
 * Uso:
 *   <Modal open={open} onClose={() => setOpen(false)} title="Banir IP">
 *     <form>...</form>
 *   </Modal>
 */

import { useId } from 'react'

import { useModalShell } from '@/lib/useModalShell'

interface Props {
  open: boolean
  onClose: () => void
  title?: string
  /** "lg" pra forms maiores. Default "md" (max-w-md). */
  size?: 'md' | 'lg'
  children: React.ReactNode
}

export default function Modal({ open, onClose, title, size = 'md', children }: Props) {
  useModalShell({ open, onClose })
  const titleId = useId()
  if (!open) return null
  const widthClass = size === 'lg' ? 'max-w-2xl' : 'max-w-md'
  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? titleId : undefined}
    >
      <div
        className={`bg-white dark:bg-zinc-950 rounded-lg shadow-xl ${widthClass} w-full p-5 border border-zinc-200 dark:border-zinc-800 max-h-[90vh] overflow-y-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <h3 id={titleId} className="text-base font-semibold mb-3">
            {title}
          </h3>
        )}
        {children}
      </div>
    </div>
  )
}
