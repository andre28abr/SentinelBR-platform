import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom'

import HostDetailPage from '@/pages/HostDetailPage'
import HostsPage from '@/pages/HostsPage'
import LoginPage from '@/pages/LoginPage'
import { useAuthStore } from '@/stores/auth'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken)
  if (!accessToken) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Router>
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
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}
