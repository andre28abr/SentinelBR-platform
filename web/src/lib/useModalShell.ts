/**
 * useModalShell — hook reusavel pra modais com:
 *   - ESC fecha
 *   - body scroll lock enquanto aberto
 *   - foco volta pro elemento que abriu o modal ao fechar
 *
 * Uso:
 *   useModalShell({ open: true, onClose: () => setOpen(false) })
 *
 * Garante consistencia entre Fail2banModal, ClamavModal, ExplainPopover,
 * AddRuleModal etc — antes cada um tinha (ou nao tinha) parte disso.
 */

import { useEffect, useRef } from 'react'

interface Opts {
  open: boolean
  onClose: () => void
}

export function useModalShell({ open, onClose }: Opts) {
  // Salva o elemento focado quando o modal abriu pra restaurar foco no close.
  const previousActive = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!open) return

    previousActive.current = document.activeElement as HTMLElement | null

    // Bloqueia scroll do body — modal fica fixed mas page nao deve rolar.
    const originalOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }
    document.addEventListener('keydown', onKey)

    return () => {
      document.body.style.overflow = originalOverflow
      document.removeEventListener('keydown', onKey)
      // Restaura foco no trigger (ex: o botao que abriu o modal).
      previousActive.current?.focus?.()
    }
  }, [open, onClose])
}
