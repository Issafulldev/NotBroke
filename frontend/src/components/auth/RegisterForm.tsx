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

export function RegisterForm() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const { t, translateError } = useTranslations()

  const login = useAuthStore(state => state.login)
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError(t('auth.register.passwordMismatch') || 'Les mots de passe ne correspondent pas')
      setIsLoading(false)
      return
    }

    try {
      const userData = {
        username: formData.username,
        email: formData.email,
        password: formData.password
      }

      // Register the user
      const registeredUser = await authApi.register(userData)

      // Auto-login après inscription
      const response = await authApi.login({
        username: formData.username,
        password: formData.password
      })

      // 🔐 Token is stored in httpOnly cookie by the server
      // Get the full user info
      const user = await authApi.getCurrentUser()

      if (!user) {
        throw new Error('Failed to fetch user information')
      }

      // Update Zustand store
      login(response.access_token, user)

      router.push('/')
    } catch (err: any) {
      const errorMessage = translateError(err.response?.data?.detail || err.message || 'Erreur lors de l\'inscription')
      setError(errorMessage)
      console.error('Registration error:', err)
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
            {t('auth.register.title') || 'Inscription'}
          </CardTitle>
          <CardDescription className="mt-1 text-sm text-gray-600">
            {t('auth.register.subtitle') || 'Créez votre compte pour commencer'}
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm font-medium text-gray-700">
              {t('auth.register.username') || 'Nom d\'utilisateur'}
            </Label>
            <Input
              id="username"
              name="username"
              type="text"
              placeholder={t('auth.register.usernamePlaceholder') || 'Nom d\'utilisateur'}
              value={formData.username}
              onChange={handleChange}
              required
              disabled={isLoading}
              minLength={3}
              maxLength={50}
              pattern="^[a-zA-Z0-9_-]+$"
              title="Alphanumeric characters, underscore and dash only"
              className="h-10 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
            <p className="text-xs text-gray-500">{t('auth.register.usernameHelp') || '3-50 caractères, alphanumériques'}</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="email" className="text-sm font-medium text-gray-700">
              {t('auth.register.email') || 'Email'}
            </Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder={t('auth.register.emailPlaceholder') || 'votre@email.com'}
              value={formData.email}
              onChange={handleChange}
              required
              disabled={isLoading}
              className="h-10 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm font-medium text-gray-700">
              {t('auth.register.password') || 'Mot de passe'}
            </Label>
            <Input
              id="password"
              name="password"
              type="password"
              placeholder={t('auth.register.passwordPlaceholder') || '••••••••'}
              value={formData.password}
              onChange={handleChange}
              required
              disabled={isLoading}
              minLength={8}
              maxLength={128}
              className="h-10 border-gray-300 focus:border-emerald-500 focus:ring-emerald-500"
            />
            <p className="text-xs text-gray-500">
              {t('auth.register.passwordHelp') || 'Minimum 8 caractères avec majuscule, minuscule, chiffre et caractère spécial'}
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-sm font-medium text-gray-700">
              {t('auth.register.confirmPassword') || 'Confirmer le mot de passe'}
            </Label>
            <Input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              placeholder={t('auth.register.confirmPasswordPlaceholder') || '••••••••'}
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              disabled={isLoading}
              minLength={8}
              maxLength={128}
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
            {isLoading ? (t('auth.register.registering') || 'Inscription en cours...') : (t('auth.register.button') || 'S\'inscrire')}
          </Button>
        </form>

        <div className="mt-4 text-center text-xs">
          <span className="text-gray-600">{t('auth.register.noAccount') || 'Vous avez déjà un compte ? '}</span>
          <button
            type="button"
            onClick={() => router.push('/login')}
            className="ml-1 text-emerald-600 hover:text-emerald-700 font-semibold transition-colors"
            disabled={isLoading}
          >
            {t('auth.register.login') || 'Se connecter'}
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
