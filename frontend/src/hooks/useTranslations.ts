'use client'

import { useEffect, useState } from 'react'
import { useLocaleStore } from '@/lib/store'

type TranslationsData = Record<string, string>

interface UseTranslationsReturn {
  translations: TranslationsData
  locale: string
  setLocale: (locale: string) => void
  isLoading: boolean
  error: string | null
  t: (key: string) => string
  translateError: (errorMessage: string | undefined | null) => string
}

const SUPPORTED_LOCALES = ['fr', 'en', 'ru']
const DEFAULT_LOCALE = 'fr'
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

export function useTranslations(): UseTranslationsReturn {
  const locale = useLocaleStore((state) => state.locale)
  const setLocaleGlobal = useLocaleStore((state) => state.setLocale)

  const [translations, setTranslations] = useState<TranslationsData>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load translations when locale changes
  useEffect(() => {
    const loadTranslations = async () => {
      setIsLoading(true)
      setError(null)
      try {
        console.log(`[i18n] Loading translations for locale: ${locale}`)
        console.log(`[i18n] API URL: ${API_BASE_URL}/translations/${locale}`)

        const response = await fetch(`${API_BASE_URL}/translations/${locale}`)

        console.log(`[i18n] Response status: ${response.status}`)

        if (!response.ok) {
          throw new Error(`Failed to load translations for locale: ${locale} (status: ${response.status})`)
        }

        const data = await response.json()
        console.log(`[i18n] Received translations:`, data)

        setTranslations(data.translations || {})
        console.log(`[i18n] Translations loaded successfully for ${locale}`)
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error'
        setError(errorMessage)
        console.error(`[i18n] Failed to load translations:`, errorMessage)
        // Fallback to empty object
        setTranslations({})
      } finally {
        setIsLoading(false)
      }
    }

    loadTranslations()
  }, [locale])

  const setLocale = (newLocale: string) => {
    if (SUPPORTED_LOCALES.includes(newLocale)) {
      setLocaleGlobal(newLocale)
    }
  }

  const t = (key: string): string => {
    return translations[key] || key
  }

  const translateError = (errorMessage: string | undefined | null): string => {
    if (!errorMessage) return 'Une erreur s\'est produite'

    // Map common error messages to translation keys
    const errorMappings: Record<string, string> = {
      'Incorrect username or password': 'errors.invalidCredentials',
      'Nom d\'utilisateur ou mot de passe incorrect': 'errors.invalidCredentials',
      'Too many login attempts': 'errors.rateLimitLogin',
      'Trop de tentatives de connexion': 'errors.rateLimitLogin',
      'Too many registration attempts': 'errors.rateLimitRegister',
      'Trop de tentatives d\'inscription': 'errors.rateLimitRegister',
      'Too many requests': 'errors.rateLimitGeneral',
      'Trop de requêtes': 'errors.rateLimitGeneral',
      'already exists': 'errors.userAlreadyExists',
      'existe déjà': 'errors.userAlreadyExists',
      'Category not found': 'errors.categoryNotFound',
      'Catégorie non trouvée': 'errors.categoryNotFound',
      'Expense not found': 'errors.expenseNotFound',
      'Dépense non trouvée': 'errors.expenseNotFound',
      'Could not validate credentials': 'errors.couldNotValidateCredentials',
      'Impossible de valider': 'errors.couldNotValidateCredentials',
    }

    // Try to find a matching translation key
    for (const [keyword, translationKey] of Object.entries(errorMappings)) {
      if (errorMessage.toLowerCase().includes(keyword.toLowerCase())) {
        return t(translationKey)
      }
    }

    // If no match found, return the original message
    return errorMessage
  }

  return {
    translations,
    locale,
    setLocale,
    isLoading,
    error,
    t,
    translateError,
  }
}
