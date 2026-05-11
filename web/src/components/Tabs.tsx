/**
 * <Tabs> — wrapper sobre @radix-ui/react-tabs.
 *
 * Acessibilidade nativa (ARIA, navegacao por teclado).
 * Estilo SentinelBR: underline na aba ativa, hover discreto.
 */

import * as RadixTabs from '@radix-ui/react-tabs'
import type { ReactNode } from 'react'

interface TabItem {
  value: string
  label: ReactNode
  content: ReactNode
}

interface Props {
  items: TabItem[]
  defaultValue?: string
  value?: string
  onValueChange?: (v: string) => void
  className?: string
}

export default function Tabs({ items, defaultValue, value, onValueChange, className }: Props) {
  return (
    <RadixTabs.Root
      defaultValue={defaultValue ?? items[0]?.value}
      value={value}
      onValueChange={onValueChange}
      className={className}
    >
      <RadixTabs.List className="flex flex-wrap gap-1 border-b border-zinc-200 dark:border-zinc-800 mb-4 -mx-1 px-1 overflow-x-auto">
        {items.map((item) => (
          <RadixTabs.Trigger
            key={item.value}
            value={item.value}
            className="px-4 py-2 text-sm font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-100 border-b-2 border-transparent data-[state=active]:border-zinc-900 dark:data-[state=active]:border-zinc-100 data-[state=active]:text-zinc-900 dark:data-[state=active]:text-zinc-100 transition-colors whitespace-nowrap"
          >
            {item.label}
          </RadixTabs.Trigger>
        ))}
      </RadixTabs.List>
      {items.map((item) => (
        <RadixTabs.Content key={item.value} value={item.value} className="focus-visible:outline-none">
          {item.content}
        </RadixTabs.Content>
      ))}
    </RadixTabs.Root>
  )
}
