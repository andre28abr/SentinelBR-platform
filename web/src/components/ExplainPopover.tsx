/**
 * <ExplainPopover> — botao ⓘ que abre modal com explicacao leiga
 * ("o que aconteceu? devo me preocupar? o que fazer?")
 * pra alertas, eventos, actions e CVEs.
 *
 * Uso:
 *   <ExplainPopover kind="rule" ruleId="ssh_brute_force_ip" />
 *   <ExplainPopover kind="action" actionType="block_ip" />
 *   <ExplainPopover kind="cve" cve={{cve_id, severity, package_name, ...}} />
 *
 * Pra "rule" e "action", chama /api/v1/kb/explain pra puxar texto leigo.
 * Pra "cve", monta texto local com os dados que ja foram carregados pela
 * tabela (evita roundtrip pra DB so pra um modal).
 */

import { useEffect, useState } from 'react'

import { ApiError, api } from '@/lib/api'

interface Technique {
  id: string
  name: string
  severity: string
  summary_simple?: {
    what_happened: string
    should_worry: string
    what_to_do: string[]
    jargon?: Record<string, string>
  }
}

interface ActionExplainer {
  title: string
  what_happened: string
  should_worry: string
  what_to_do: string[]
}

interface CveData {
  cve_id: string
  package_name: string
  installed_version: string
  fixed_version: string | null
  severity: string
  summary: string | null
  references?: string[] | null
}

interface EventData {
  source: string
  fields: Record<string, string>
  raw: string
  timestamp: string
  severity: string
}

type ExplainKind =
  | { kind: 'rule'; ruleId: string }
  | { kind: 'action'; actionType: string }
  | { kind: 'cve'; cve: CveData }
  | { kind: 'event'; event: EventData }

/** variant:
 *   "icon"  — botão ⓘ pequeno (default, inline)
 *   "link"  — texto "ver" estilo link, ideal pra coluna "Detalhes" em tabela
 */
type Props = ExplainKind & { variant?: 'icon' | 'link'; label?: string }

export default function ExplainPopover(props: Props) {
  const [open, setOpen] = useState(false)
  const variant = props.variant ?? 'icon'

  const trigger =
    variant === 'link' ? (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen(true)
        }}
        className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
      >
        {props.label ?? 'ver'}
      </button>
    ) : (
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setOpen(true)
        }}
        title="O que isso significa?"
        className="inline-flex items-center justify-center w-5 h-5 rounded-full border border-zinc-300 dark:border-zinc-700 text-[10px] text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 hover:text-zinc-900 dark:hover:text-zinc-100"
        aria-label="explicar"
      >
        ?
      </button>
    )

  return (
    <>
      {trigger}
      {open && <ExplainModal {...props} onClose={() => setOpen(false)} />}
    </>
  )
}

function ExplainModal({ onClose, ...props }: Props & { onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-zinc-950 rounded-lg shadow-xl max-w-2xl w-full max-h-[85vh] overflow-y-auto border border-zinc-200 dark:border-zinc-800"
        onClick={(e) => e.stopPropagation()}
      >
        {props.kind === 'rule' && <RuleExplain ruleId={props.ruleId} />}
        {props.kind === 'action' && <ActionExplain actionType={props.actionType} />}
        {props.kind === 'cve' && <CveExplain cve={props.cve} />}
        {props.kind === 'event' && <EventExplain event={props.event} />}

        <footer className="px-5 py-3 border-t border-zinc-200 dark:border-zinc-800 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="text-sm px-3 py-1.5 rounded bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900"
          >
            Fechar
          </button>
        </footer>
      </div>
    </div>
  )
}

function RuleExplain({ ruleId }: { ruleId: string }) {
  const [tech, setTech] = useState<Technique | null | undefined>(undefined)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<{ technique: Technique | null }>(`/api/v1/kb/explain?rule_id=${encodeURIComponent(ruleId)}`)
      .then((d) => setTech(d.technique))
      .catch((e) => setErr(e instanceof ApiError ? String(e.detail) : 'erro'))
  }, [ruleId])

  if (err) return <ErrorState message={err} />
  if (tech === undefined) return <LoadingState />
  if (tech === null) {
    return (
      <Body title={`Regra: ${ruleId}`} subtitle="Sem explicação cadastrada">
        <p className="text-sm text-zinc-500">
          Essa regra ainda não tem texto explicativo. Veja a aba "Eventos recentes" pra
          contexto, ou a página <a href="/kb" className="text-blue-600 dark:text-blue-400 underline">/kb</a> pra
          referências MITRE ATT&CK relacionadas.
        </p>
      </Body>
    )
  }

  const s = tech.summary_simple
  return (
    <Body
      title={tech.name}
      subtitle={`Regra: ${ruleId} · Técnica MITRE: ${tech.id}`}
      severity={tech.severity}
    >
      {s ? (
        <>
          <Section title="O que aconteceu?" text={s.what_happened} />
          <Section title="Devo me preocupar?" text={s.should_worry} />
          <ListSection title="O que fazer agora?" items={s.what_to_do} />
          {s.jargon && Object.keys(s.jargon).length > 0 && (
            <JargonSection terms={s.jargon} />
          )}
        </>
      ) : (
        <p className="text-sm text-zinc-500 italic">
          Texto leigo ainda não escrito. Veja <a href={`/kb`} className="text-blue-600 dark:text-blue-400 underline">/kb</a> pra detalhes técnicos.
        </p>
      )}
      <p className="text-xs text-zinc-500 mt-4 pt-3 border-t border-zinc-200 dark:border-zinc-800">
        Quer entender mais? Veja <a href="/kb" className="text-blue-600 dark:text-blue-400 underline">/kb → {tech.id}</a> com mitigações e referências oficiais.
      </p>
    </Body>
  )
}

function ActionExplain({ actionType }: { actionType: string }) {
  const [exp, setExp] = useState<ActionExplainer | null | undefined>(undefined)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<{ explainer: ActionExplainer | null }>(`/api/v1/kb/explain?action_type=${encodeURIComponent(actionType)}`)
      .then((d) => setExp(d.explainer))
      .catch((e) => setErr(e instanceof ApiError ? String(e.detail) : 'erro'))
  }, [actionType])

  if (err) return <ErrorState message={err} />
  if (exp === undefined) return <LoadingState />
  if (exp === null) {
    return (
      <Body title={`Ação: ${actionType}`} subtitle="Sem explicação cadastrada">
        <p className="text-sm text-zinc-500">
          Esse tipo de ação ainda não tem texto explicativo.
        </p>
      </Body>
    )
  }
  return (
    <Body title={exp.title} subtitle={`Tipo: ${actionType}`}>
      <Section title="O que aconteceu?" text={exp.what_happened} />
      <Section title="Devo me preocupar?" text={exp.should_worry} />
      <ListSection title="O que fazer agora?" items={exp.what_to_do} />
    </Body>
  )
}

function CveExplain({ cve }: { cve: CveData }) {
  const refs = (cve.references ?? []).filter((r): r is string => typeof r === 'string' && r.length > 0).slice(0, 5)
  return (
    <Body
      title={cve.cve_id}
      subtitle={`Vulnerabilidade em ${cve.package_name} ${cve.installed_version}`}
      severity={cve.severity}
    >
      <Section
        title="O que aconteceu?"
        text={`O pacote ${cve.package_name} versão ${cve.installed_version} no seu servidor tem uma vulnerabilidade conhecida (${cve.cve_id}). Cadastrada por pesquisadores em base pública (OSV.dev).`}
      />
      <Section
        title="Devo me preocupar?"
        text={severityAdvice(cve.severity)}
      />
      <ListSection
        title="O que fazer agora?"
        items={[
          cve.fixed_version
            ? `Atualize ${cve.package_name} pra versão ${cve.fixed_version} ou superior (sudo apt update && sudo apt upgrade ${cve.package_name})`
            : `Atualize ${cve.package_name} pra versão mais recente disponível no repositório da sua distro`,
          'Reinicie serviços que usam essa biblioteca (ex: sudo systemctl restart nginx)',
          'Confirme que outros servidores com a mesma versão também foram patcheados',
          'Se sua distro está LTS antiga, verifique se há patches de backport disponíveis',
        ]}
      />
      {cve.summary && (
        <Section
          title="Descrição técnica (OSV)"
          text={cve.summary}
        />
      )}
      {refs.length > 0 && (
        <section className="mb-4">
          <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-2">Referências</h3>
          <ul className="space-y-1">
            {refs.map((r) => (
              <li key={r} className="text-xs">
                <a
                  href={r}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 dark:text-blue-400 hover:underline break-all"
                >
                  {r}
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </Body>
  )
}

interface EventSourceExplainer {
  title: string
  what: string
  fields: Record<string, string>
}

function EventExplain({ event }: { event: EventData }) {
  const [src, setSrc] = useState<EventSourceExplainer | null | undefined>(undefined)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<{ explainer: EventSourceExplainer | null }>(
        `/api/v1/kb/explain?event_source=${encodeURIComponent(event.source)}`,
      )
      .then((d) => setSrc(d.explainer))
      .catch((e) => setErr(e instanceof ApiError ? String(e.detail) : 'erro'))
  }, [event.source])

  if (err) return <ErrorState message={err} />

  const action = event.fields['event.action']
  const title = src?.title || action || `Evento ${event.source}`
  const subtitle = `Source: ${event.source} · ${new Date(event.timestamp).toLocaleString('pt-BR')}`

  return (
    <Body title={title} subtitle={subtitle} severity={event.severity}>
      {src && (
        <>
          <Section title="O que é esse evento?" text={src.what} />
        </>
      )}
      {src === undefined && <p className="text-xs text-zinc-500 italic mb-3">Carregando contexto…</p>}

      <section className="mb-4">
        <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">Campos parseados</h3>
        <dl className="text-xs grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1">
          {Object.entries(event.fields).map(([k, v]) => (
            <div key={k} className="contents">
              <dt className="font-mono text-zinc-500">{describeField(k, src?.fields)}:</dt>
              <dd className="font-mono break-all">{v}</dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="mb-2">
        <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">Linha original (log)</h3>
        <pre className="text-[11px] bg-zinc-100 dark:bg-zinc-900 p-3 rounded overflow-x-auto whitespace-pre-wrap break-all">
          {event.raw || '(vazio)'}
        </pre>
      </section>
    </Body>
  )
}

function describeField(key: string, descriptions?: Record<string, string>): string {
  return descriptions?.[key] || key
}

function Body({
  title,
  subtitle,
  severity,
  children,
}: {
  title: string
  subtitle?: string
  severity?: string
  children: React.ReactNode
}) {
  return (
    <div className="p-5">
      <header className="mb-4 pb-3 border-b border-zinc-200 dark:border-zinc-800">
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-lg font-bold">{title}</h2>
          {severity && <SeverityPill sev={severity} />}
        </div>
        {subtitle && <p className="text-xs text-zinc-500 font-mono">{subtitle}</p>}
      </header>
      {children}
    </div>
  )
}

function Section({ title, text }: { title: string; text: string }) {
  return (
    <section className="mb-4">
      <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">{title}</h3>
      <p className="text-sm whitespace-pre-wrap">{text}</p>
    </section>
  )
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="mb-4">
      <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-1">{title}</h3>
      <ol className="text-sm list-decimal list-inside space-y-1">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ol>
    </section>
  )
}

function JargonSection({ terms }: { terms: Record<string, string> }) {
  return (
    <section className="mb-4 pt-3 border-t border-zinc-100 dark:border-zinc-900">
      <h3 className="text-xs font-semibold uppercase text-zinc-500 mb-2">Glossário</h3>
      <dl className="space-y-1.5">
        {Object.entries(terms).map(([term, def]) => (
          <div key={term} className="text-xs">
            <dt className="font-semibold inline">{term}:</dt>{' '}
            <dd className="inline text-zinc-600 dark:text-zinc-400">{def}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

function LoadingState() {
  return <div className="p-5 text-sm text-zinc-500">Carregando…</div>
}

function ErrorState({ message }: { message: string }) {
  return <div className="p-5 text-sm text-red-600">Erro: {message}</div>
}

function SeverityPill({ sev }: { sev: string }) {
  const color =
    sev === 'critical'
      ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200'
      : sev === 'high'
        ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200'
        : sev === 'medium'
          ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
          : 'bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300'
  return (
    <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${color}`}>
      {sev}
    </span>
  )
}

function severityAdvice(sev: string): string {
  switch (sev) {
    case 'critical':
      return 'SIM, CRÍTICO. Patch o quanto antes — vulnerabilidades critical geralmente têm exploit público disponível.'
    case 'high':
      return 'Sim, alta prioridade. Agende patch nessa semana.'
    case 'medium':
      return 'Moderado. Patch no próximo ciclo de manutenção (próximas 2-4 semanas).'
    case 'low':
      return 'Baixo risco isolado, mas vale incluir no próximo update batch.'
    default:
      return 'Severidade não classificada. Veja descrição técnica abaixo pra avaliar.'
  }
}
