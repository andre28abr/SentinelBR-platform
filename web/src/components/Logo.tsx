/**
 * <Logo> — marca textual do SentinelBR, SVG inline + tipografia.
 *
 * Composicao:
 *   [escudo SVG verde] Sentinel + BR (BR em verde)
 *
 * Sem imagem externa — tudo gerado em runtime. Funciona em qualquer
 * tamanho via size prop ("sm" | "md" | "lg").
 */

interface Props {
  size?: 'sm' | 'md' | 'lg'
  /** Esconde o texto, mostra so o icone (escudo). */
  iconOnly?: boolean
}

const SIZES = {
  sm: { icon: 'w-5 h-5', text: 'text-sm', gap: 'gap-1.5' },
  md: { icon: 'w-7 h-7', text: 'text-lg', gap: 'gap-2' },
  lg: { icon: 'w-12 h-12', text: 'text-3xl', gap: 'gap-3' },
}

export default function Logo({ size = 'md', iconOnly = false }: Props) {
  const cfg = SIZES[size]
  return (
    <div className={`inline-flex items-center ${cfg.gap}`} aria-label="SentinelBR">
      <ShieldIcon className={cfg.icon} />
      {!iconOnly && (
        <span className={`${cfg.text} font-bold tracking-tight select-none`}>
          <span className="text-zinc-900 dark:text-zinc-100">Sentinel</span>
          <span className="text-emerald-600 dark:text-emerald-400">BR</span>
        </span>
      )}
    </div>
  )
}

function ShieldIcon({ className }: { className: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      {/* Escudo: outline arredondado em emerald, fill suave */}
      <path
        d="M12 2 L4 5 V11.5 C4 16 7.5 19.5 12 22 C16.5 19.5 20 16 20 11.5 V5 L12 2 Z"
        className="fill-emerald-100 dark:fill-emerald-950 stroke-emerald-600 dark:stroke-emerald-400"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      {/* Check minimalista dentro do escudo */}
      <path
        d="M8.5 12 L11 14.5 L15.5 9.5"
        className="stroke-emerald-700 dark:stroke-emerald-300"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
