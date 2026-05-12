/**
 * <DocsPage> — renderiza markdown do diretorio /docs do repo no app.
 *
 * Layout: sidebar (TOC com indice numerado) + main (markdown renderizado).
 * Slug vem da URL: /docs ou /docs/<slug>. Default = primeiro doc.
 *
 * Lazy-loaded — bundle so baixa quando user clica no link da nav.
 * react-markdown + remark-gfm pra suportar tabelas, checklists, etc.
 * react-syntax-highlighter pra blocos de codigo coloridos.
 */

import { Icon } from '@iconify/react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism'
import remarkGfm from 'remark-gfm'

import AppHeader from '@/components/AppHeader'
import { ApiError, api } from '@/lib/api'

interface DocSummary {
  slug: string
  title: string
  order: number
}

interface DocContent {
  slug: string
  title: string
  markdown: string
}

export default function DocsPage() {
  const { slug } = useParams<{ slug?: string }>()
  const navigate = useNavigate()
  const [index, setIndex] = useState<DocSummary[] | null>(null)
  const [content, setContent] = useState<DocContent | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Carrega indice 1x ao montar
  useEffect(() => {
    api
      .get<DocSummary[]>('/api/v1/docs')
      .then((data) => setIndex(data))
      .catch((err) => {
        setError(err instanceof ApiError ? String(err.detail) : 'erro ao carregar docs')
      })
  }, [])

  // Slug efetivo: se URL nao tem, usa o primeiro do indice
  const activeSlug = useMemo(() => {
    if (slug) return slug
    if (index && index.length > 0) return index[0].slug
    return null
  }, [slug, index])

  // Carrega doc atual quando slug muda. Estado "loading" eh derivado
  // (content.slug !== activeSlug) — sem setState sync no inicio do effect.
  useEffect(() => {
    if (!activeSlug) return
    let cancelled = false
    api
      .get<DocContent>(`/api/v1/docs/${activeSlug}`)
      .then((data) => {
        if (cancelled) return
        setContent(data)
        setError(null)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof ApiError ? String(err.detail) : 'doc nao encontrado')
        setContent(null)
      })
    return () => {
      cancelled = true
    }
  }, [activeSlug])

  // Derivado: loading = content nao bate com slug pedido.
  const loading = content?.slug !== activeSlug

  // Se URL eh /docs sem slug, redireciona pro primeiro
  useEffect(() => {
    if (!slug && index && index.length > 0) {
      navigate(`/docs/${index[0].slug}`, { replace: true })
    }
  }, [slug, index, navigate])

  return (
    <main className="max-w-7xl mx-auto p-4 sm:p-6">
      <AppHeader />

      <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6">
        {/* Sidebar TOC */}
        <aside className="lg:sticky lg:top-4 lg:self-start space-y-1">
          <h2 className="text-xs font-semibold uppercase text-zinc-500 mb-2 flex items-center gap-1.5">
            <Icon icon="lucide:book-open" aria-hidden />
            Documentação
          </h2>
          {index === null ? (
            <p className="text-xs text-zinc-500">Carregando…</p>
          ) : index.length === 0 ? (
            <p className="text-xs text-zinc-500">Nenhum doc.</p>
          ) : (
            <nav className="space-y-0.5 text-sm">
              {index.map((d) => (
                <Link
                  key={d.slug}
                  to={`/docs/${d.slug}`}
                  className={`block px-2 py-1.5 rounded hover:bg-zinc-100 dark:hover:bg-zinc-900 ${
                    activeSlug === d.slug
                      ? 'bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 font-medium'
                      : 'text-zinc-600 dark:text-zinc-400'
                  }`}
                >
                  <span className="text-xs opacity-60 mr-1.5">{String(d.order).padStart(2, '0')}</span>
                  {d.title}
                </Link>
              ))}
            </nav>
          )}
        </aside>

        {/* Main content */}
        <article className="min-w-0">
          {error && (
            <div
              role="alert"
              className="rounded-md border border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-950/30 p-3 text-sm text-red-900 dark:text-red-200"
            >
              {error}
            </div>
          )}
          {loading && !content && (
            <p className="text-sm text-zinc-500">Carregando…</p>
          )}
          {content && <MarkdownArticle markdown={content.markdown} />}
        </article>
      </div>
    </main>
  )
}

/** Render do markdown com Tailwind prose-like. */
function MarkdownArticle({ markdown }: { markdown: string }) {
  // Detecta dark mode atual pra escolher tema do syntax highlighter
  const isDark =
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark')

  return (
    <div className="markdown-body max-w-none text-sm leading-7 text-zinc-700 dark:text-zinc-300">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-2xl font-bold mt-0 mb-4 text-zinc-900 dark:text-zinc-100 border-b border-zinc-200 dark:border-zinc-800 pb-2">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-xl font-semibold mt-8 mb-3 text-zinc-900 dark:text-zinc-100">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold mt-6 mb-2 text-zinc-900 dark:text-zinc-100">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="my-3">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-6 my-3 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-6 my-3 space-y-1">{children}</ol>,
          a: ({ href, children }) => (
            <a
              href={href}
              target={href?.startsWith('http') ? '_blank' : undefined}
              rel={href?.startsWith('http') ? 'noopener noreferrer' : undefined}
              className="text-blue-600 dark:text-blue-400 hover:underline"
            >
              {children}
            </a>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-amber-400 dark:border-amber-600 bg-amber-50 dark:bg-amber-950/30 px-4 py-2 my-3 italic text-zinc-700 dark:text-zinc-300">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full text-sm border border-zinc-200 dark:border-zinc-800">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="text-left px-3 py-1.5 font-semibold bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-1.5 border border-zinc-200 dark:border-zinc-800 align-top">
              {children}
            </td>
          ),
          code: ({ className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '')
            const codeStr = String(children).replace(/\n$/, '')
            // Inline code (sem language) — render simples com bg
            if (!match) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-900 font-mono text-[0.85em] text-zinc-800 dark:text-zinc-200"
                  {...props}
                >
                  {children}
                </code>
              )
            }
            // Block code com syntax highlight
            return (
              <SyntaxHighlighter
                language={match[1]}
                style={isDark ? oneDark : oneLight}
                PreTag="div"
                customStyle={{ borderRadius: '0.5rem', fontSize: '0.85em' }}
              >
                {codeStr}
              </SyntaxHighlighter>
            )
          },
        }}
      >
        {markdown}
      </Markdown>
    </div>
  )
}
