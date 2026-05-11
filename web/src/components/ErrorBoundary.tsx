/**
 * <ErrorBoundary> — captura erros de renderizacao no React.
 *
 * Componentes filhos que jogarem erro vao mostrar o fallback em vez de
 * crashar a pagina inteira ("tela preta"). Imprime no console pra debug.
 *
 * Uso:
 *   <ErrorBoundary>
 *     <ComponenteQuePodeFalhar />
 *   </ErrorBoundary>
 */

import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  err: Error | null
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { err: null }

  static getDerivedStateFromError(err: Error): State {
    return { err }
  }

  componentDidCatch(err: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] render crash:', err, info.componentStack)
  }

  reset = () => this.setState({ err: null })

  render() {
    if (this.state.err) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="p-4 rounded-lg border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950 text-sm">
          <p className="font-semibold text-red-700 dark:text-red-300 mb-1">
            Algo deu errado ao renderizar essa seção.
          </p>
          <p className="text-red-600 dark:text-red-400 font-mono text-xs mb-2 break-all">
            {this.state.err.message || 'erro desconhecido'}
          </p>
          <button
            type="button"
            onClick={this.reset}
            className="text-xs px-2 py-1 rounded bg-red-700 text-white hover:bg-red-800"
          >
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
