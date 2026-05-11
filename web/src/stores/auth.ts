import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface Organization {
  id: string
  name: string
  slug: string
}

interface User {
  id: string
  org_id: string
  email: string
  name: string
  role: string
  org?: Organization
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setTokens: (access: string, refresh: string) => void
  setUser: (user: User | null) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      logout: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'sentinelbr-auth' },
  ),
)
