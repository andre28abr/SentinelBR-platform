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
  user: User | null
  setAccessToken: (access: string) => void
  setUser: (user: User | null) => void
  /** Limpa estado local. Pra logout completo usar logout() em api.ts (chama
   *  /auth/logout no server pra apagar o cookie httpOnly de refresh). */
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      setAccessToken: (access) => set({ accessToken: access }),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ accessToken: null, user: null }),
    }),
    { name: 'sentinelbr-auth' },
  ),
)
