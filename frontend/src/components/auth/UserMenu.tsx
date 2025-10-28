'use client'

import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { authApi } from '@/lib/api'
import { useTranslations } from '@/hooks/useTranslations'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { User, LogOut, LogIn } from 'lucide-react'

export function UserMenu() {
  const user = useAuthStore(state => state.user)
  const isAuthenticated = useAuthStore(state => state.isAuthenticated)
  const logout = useAuthStore(state => state.logout)
  const { t } = useTranslations()
  const router = useRouter()

  const handleLogout = () => {
    authApi.logout()
    logout()
    router.push('/login')
  }

  const handleLogin = () => {
    router.push('/login')
  }

  if (!isAuthenticated) {
    return (
      <Button onClick={handleLogin} variant="outline" className="flex items-center space-x-2">
        <LogIn className="h-4 w-4" />
        <span>{t('user.login')}</span>
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center space-x-2">
          <User className="h-4 w-4" />
          <span className="hidden md:block">{user?.username}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem disabled>
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user?.username}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleLogout} className="text-red-600">
          <LogOut className="mr-2 h-4 w-4" />
          <span>{t('user.logout')}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
