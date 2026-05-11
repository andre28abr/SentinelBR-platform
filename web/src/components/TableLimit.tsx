/**
 * useTableLimit — hook pra limitar visualizacao de listas grandes.
 *
 * Default: mostra 10 items dentro de container scrollavel (max-h fixo).
 * Botao "Ver tudo" expande sem limite.
 *
 * Uso:
 *   const { visible, hasMore, expanded, toggle, containerClass } =
 *     useTableLimit(items, { defaultVisible: 10 })
 *
 *   <div className={containerClass}>
 *     <table>{visible.map(...)}</table>
 *   </div>
 *   <TableLimitFooter total={items.length} visible={visible.length}
 *                     expanded={expanded} onToggle={toggle} />
 */

import { useState } from 'react'

interface Options {
  defaultVisible?: number
  /** Quando recolhido, altura maxima do container (com scroll interno). */
  collapsedMaxHeight?: string
}

// eslint-disable-next-line react-refresh/only-export-components
export function useTableLimit<T>(items: T[], opts: Options = {}) {
  const defaultVisible = opts.defaultVisible ?? 10
  const maxHeight = opts.collapsedMaxHeight ?? 'max-h-[480px]'

  const [expanded, setExpanded] = useState(false)
  const hasMore = items.length > defaultVisible

  // Quando expandido: mostra tudo, sem max-h.
  // Quando recolhido E tem mais que o limite: mostra TUDO mas container scrollavel
  //   (assim o usuario pode rolar dentro da tabela em vez de paginar).
  const visible = items
  const containerClass = !expanded && hasMore ? `${maxHeight} overflow-y-auto` : ''

  return {
    visible,
    hasMore,
    expanded,
    toggle: () => setExpanded((v) => !v),
    containerClass,
    /** Quantos items "cabem" na visao recolhida (estimativa, pra footer). */
    collapsedCount: defaultVisible,
  }
}

interface FooterProps {
  total: number
  expanded: boolean
  onToggle: () => void
  /** Quantos cabem na visao recolhida — mostrado no texto "X de N". */
  collapsedCount: number
}

export function TableLimitFooter({ total, expanded, onToggle, collapsedCount }: FooterProps) {
  return (
    <div className="mt-2 flex items-center justify-between text-xs text-zinc-500 px-1">
      <span>
        {expanded ? (
          <>{total} items · scroll interno desabilitado</>
        ) : (
          <>~{collapsedCount} visíveis · {total} no total · role pra ver mais</>
        )}
      </span>
      <button
        type="button"
        onClick={onToggle}
        className="text-blue-600 dark:text-blue-400 hover:underline"
      >
        {expanded ? 'Recolher' : 'Ver tudo'}
      </button>
    </div>
  )
}
