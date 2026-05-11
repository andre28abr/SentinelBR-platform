/**
 * <Tooltip> — wrapper sobre Radix Tooltip pra usar em qualquer elemento.
 *
 * Uso:
 *   <Tooltip content="Reiniciar serviço nginx">
 *     <button>Reiniciar</button>
 *   </Tooltip>
 *
 * Recomendado pra:
 *  - Badges cryptic (CVSS, MTTR, severity)
 *  - Botões de ícone (sem texto)
 *  - Métricas com nomes técnicos (load_avg, mem_used, etc)
 *  - Qualquer coisa que mereça explicação rápida sem click.
 */

import * as RadixTooltip from '@radix-ui/react-tooltip'
import type { ReactNode } from 'react'

interface Props {
  content: ReactNode
  children: ReactNode
  /** Posição preferida. Radix ajusta se não couber. */
  side?: 'top' | 'right' | 'bottom' | 'left'
  /** Atrasa exibição (ms). Default 300. */
  delayMs?: number
}

export default function Tooltip({ content, children, side = 'top', delayMs = 300 }: Props) {
  return (
    <RadixTooltip.Provider delayDuration={delayMs}>
      <RadixTooltip.Root>
        <RadixTooltip.Trigger asChild>{children}</RadixTooltip.Trigger>
        <RadixTooltip.Portal>
          <RadixTooltip.Content
            side={side}
            sideOffset={6}
            className="z-50 max-w-xs rounded-md bg-zinc-900 dark:bg-zinc-100 px-2.5 py-1.5 text-xs text-zinc-100 dark:text-zinc-900 shadow-md animate-in fade-in-0 zoom-in-95"
          >
            {content}
            <RadixTooltip.Arrow className="fill-zinc-900 dark:fill-zinc-100" />
          </RadixTooltip.Content>
        </RadixTooltip.Portal>
      </RadixTooltip.Root>
    </RadixTooltip.Provider>
  )
}
