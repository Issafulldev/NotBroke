'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { authApi } from '@/lib/api'
import { UserMenu } from '@/components/auth/UserMenu'
import { Loader2 } from 'lucide-react'

interface AuthProviderProps {
  children: React.ReactNode
}

const AUTH_PAGES = ['/login', '/register']

export function AuthProvider({ children }: AuthProviderProps) {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const login = useAuthStore(state => state.login)
  const logout = useAuthStore(state => state.logout)
  const router = useRouter()
  const pathname = usePathname()

  const [isInitialized, setIsInitialized] = useState(false)

  useEffect(() => {
    let isMounted = true

    const initializeAuth = async () => {
      // Skip auth check on public auth pages
      if (AUTH_PAGES.includes(pathname)) {
        setIsInitialized(true)
        return
      }

      try {
        const user = await authApi.getCurrentUser()

        if (user) {
          login('', user)
        } else {
          logout()
        }
      } catch (error) {
        logout()
      } finally {
        if (isMounted) {
          setIsInitialized(true)
        }
      }
    }

    initializeAuth()

    return () => {
      isMounted = false
    }
  }, [pathname, login, logout])

  useEffect(() => {
    if (!isInitialized) return

    if (!isAuthenticated && !AUTH_PAGES.includes(pathname)) {
      router.push('/login')
    }
  }, [isAuthenticated, pathname, router, isInitialized])

  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-emerald-400" />
          <p className="text-white">Vérification de l'authentification...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen">
        {children}
      </div>
    )
  }

  return (
    <>
      {isAuthenticated && (
        <header className="border-b bg-white shadow-sm">
          <div className="container mx-auto px-4 py-3 flex justify-center items-center">
            <div className="flex items-center justify-center">
              <UserMenu />
            </div>
          </div>
        </header>
      )}
      <main className="">
        {children}
      </main>
    </>
  )
}
