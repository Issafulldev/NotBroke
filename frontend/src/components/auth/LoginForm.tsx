'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { authApi } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import { useTranslations } from '@/hooks/useTranslations'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function LoginForm() {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const { t, locale, translateError } = useTranslations()

  const login = useAuthStore(state => state.login)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      const response = await authApi.login(formData)
      const user = response.user

      if (!user) {
        throw new Error('Failed to fetch user information')
      }

      login(response.access_token, user)
      router.push('/')
    } catch (err: any) {
      const errorMessage = translateError(err.response?.data?.detail || err.message) || t('auth.login.errors.invalidCredentials') || 'Erreur de connexion'
      setError(errorMessage)
      console.error('Login error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  return (
    <Card className="w-full max-w-md mx-auto border-0 rounded-xl bg-white/95 backdrop-blur-sm">
      <CardHeader className="space-y-2 text-center pb-4">
        <div>
          <CardTitle className="text-2xl font-bold text-gray-900">
            {t('auth.login.title') || 'Connexion'}
          </CardTitle>
          <CardDescription className="mt-1 text-sm text-gray-600">
            {t('auth.login.subtitle') || 'Connectez-vous à votre compte NotBroke'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm font-medium text-gray-700">
              {t('auth.login.username') || 'Nom d\'utilisateur'}
            </Label>
            <Input
              id="username"
              name="username"
              type="text"
              placeholder={t('auth.login.usernamePlaceholder') || 'Nom d\'utilisateur'}
              value={formData.username}
              onChange={handleChange}
              required
              disabled={isLoading}
              minLength={3}
              maxLength={50}
              className="h-10 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium text-gray-700">
              {t('auth.login.password') || 'Mot de passe'}
            </Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder={t('auth.login.passwordPlaceholder') || '••••••••'}
              value={formData.password}
              onChange={handleChange}
              required
              disabled={isLoading}
              minLength={8}
              className="h-10 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 p-2 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          <Button
            type="submit"
            className="w-full h-10 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg text-sm"
            disabled={isLoading}
          >
            {isLoading ? (t('auth.login.connecting') || 'Connexion...') : (t('auth.login.button') || 'Se connecter')}
          </Button>
        </form>

        <div className="mt-4 text-center text-xs">
          <span className="text-gray-600">{t('auth.login.noAccount') || 'Pas encore de compte ? '}</span>
          <button
            type="button"
            onClick={() => router.push('/register')}
            className="ml-1 text-emerald-600 hover:text-emerald-700 font-semibold transition-colors"
            disabled={isLoading}
          >
            {t('auth.login.register') || 'S\'inscrire'}
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
