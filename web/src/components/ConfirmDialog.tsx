/**
 * <ConfirmDialog> — modal "voce tem certeza?" que substitui confirm() nativo.
 *
 * Vantagens vs window.confirm:
 *   - segue dark mode + design system
 *   - usa lucide:triangle-alert no header (sem emoji nativo)
 *   - bloqueia interaction com backdrop, fecha em ESC
 *   - mensagem pode ter formatacao rica (codigo, listas)
 */

import { Icon } from '@iconify/react'
import { useEffect } from 'react'

interface Props {
  open: boolean
  title: string
  message: React.ReactNode
  confirmLabel?: string
  cancelLabel?: string
  /** "danger" pinta o botao confirm em vermelho. Default neutro. */
  variant?: 'danger' | 'neutral'
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  variant = 'neutral',
  onConfirm,
  onCancel,
}: Props) {
  // ESC fecha
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onCancel()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onCancel])

  if (!open) return null

  const confirmCls =
    variant === 'danger'
      ? 'bg-red-700 hover:bg-red-800 text-white'
      : 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900'

  return (
    <div
      className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
    >
      <div
        className="bg-white dark:bg-zinc-950 rounded-lg shadow-xl max-w-md w-full p-5 border border-zinc-200 dark:border-zinc-800"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-3 mb-3">
          <Icon
            icon={variant === 'danger' ? 'lucide:triangle-alert' : 'lucide:circle-help'}
            className={`text-2xl mt-0.5 flex-shrink-0 ${variant === 'danger' ? 'text-red-600' : 'text-zinc-500'}`}
            aria-hidden
          />
          <div>
            <h3 id="confirm-dialog-title" className="text-base font-semibold mb-1">
              {title}
            </h3>
            <div className="text-sm text-zinc-600 dark:text-zinc-400">{message}</div>
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button
            type="button"
            onClick={onCancel}
            className="px-3 py-2 text-sm rounded border border-zinc-300 dark:border-zinc-700"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            autoFocus
            className={`px-3 py-2 text-sm rounded font-medium ${confirmCls}`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
