import { Suspense, lazy } from 'react'
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'

import LoginPage from '@/pages/LoginPage'
import { useAuthStore } from '@/stores/auth'

// Lazy load das paginas internas — bundle inicial fica menor (~250kb gzip
// em vez de ~770kb), recharts e outras deps pesadas so baixam quando o user
// navega pra elas. LoginPage NAO eh lazy: eh a primeira tela e o usuario
// nao deveria esperar JS extra pra digitar credenciais.
const HostsPage = lazy(() => import('@/pages/HostsPage'))
const HostDetailPage = lazy(() => import('@/pages/HostDetailPage'))
const AlertsPage = lazy(() => import('@/pages/AlertsPage'))
const CompliancePage = lazy(() => import('@/pages/CompliancePage'))  // recharts
const KbPage = lazy(() => import('@/pages/KbPage'))
const HuntingPage = lazy(() => import('@/pages/HuntingPage'))
const PurpleTeamPage = lazy(() => import('@/pages/PurpleTeamPage'))
const LabPage = lazy(() => import('@/pages/LabPage'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken)
  if (!accessToken) return <Navigate to="/login" replace />
  return <>{children}</>
}

function PageLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center text-sm text-zinc-500">
      Carregando…
    </div>
  )
}

export default function App() {
  return (
    <Router>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HostsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/hosts/:id"
            element={
              <ProtectedRoute>
                <HostDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/alerts"
            element={
              <ProtectedRoute>
                <AlertsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/compliance"
            element={
              <ProtectedRoute>
                <CompliancePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/kb"
            element={
              <ProtectedRoute>
                <KbPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/hunting"
            element={
              <ProtectedRoute>
                <HuntingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/purple-team"
            element={
              <ProtectedRoute>
                <PurpleTeamPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lab"
            element={
              <ProtectedRoute>
                <LabPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Suspense>
    </Router>
  )
}
