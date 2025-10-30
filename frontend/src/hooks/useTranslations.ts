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
const TRANSLATIONS_CACHE_VERSION = 'v2'

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
        // 🆕 NOUVEAU: Vérifier le cache localStorage d'abord
        const cacheKey = `translations_${TRANSLATIONS_CACHE_VERSION}_${locale}`
        const legacyCacheKey = `translations_${locale}`
        const cachedTranslations = localStorage.getItem(cacheKey)

        if (cachedTranslations) {
          console.log(`[i18n] Chargeant depuis le cache: ${locale}`)
          setTranslations(JSON.parse(cachedTranslations))
          setIsLoading(false)
          return
        }

        if (localStorage.getItem(legacyCacheKey)) {
          localStorage.removeItem(legacyCacheKey)
        }

        console.log(`[i18n] Loading translations for locale: ${locale}`)
        console.log(`[i18n] API URL: ${API_BASE_URL}/translations/${locale}`)

        const response = await fetch(`${API_BASE_URL}/translations/${locale}`)

        console.log(`[i18n] Response status: ${response.status}`)

        if (!response.ok) {
          throw new Error(`Failed to load translations for locale: ${locale} (status: ${response.status})`)
        }

        const data = await response.json()
        console.log(`[i18n] Received translations:`, data)

        // 🆕 NOUVEAU: Stocker en cache pour la prochaine fois
        const translationsData = data.translations || {}
        localStorage.setItem(cacheKey, JSON.stringify(translationsData))

        setTranslations(translationsData)
        console.log(`[i18n] Translations loaded and cached for ${locale}`)
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
    const translation = translations[key]
    // Si la traduction existe et n'est pas vide, la retourner
    // Sinon retourner la clé (qui sera utilisée comme fallback dans le composant)
    return translation && translation !== '' ? translation : key
  }

  const translateError = (errorMessage: string | undefined | null | any): string => {
    if (!errorMessage) return 'Une erreur s\'est produite'

    // Convert errorMessage to string if it's not already
    let errorStr: string
    if (typeof errorMessage === 'string') {
      errorStr = errorMessage
    } else if (errorMessage && typeof errorMessage === 'object') {
      // Handle Pydantic validation errors or other error objects
      if (Array.isArray(errorMessage)) {
        // Array of validation errors
        errorStr = errorMessage.map((e: any) => {
          if (typeof e === 'string') return e
          if (e?.msg) return e.msg
          if (e?.message) return e.message
          return JSON.stringify(e)
        }).join(', ')
      } else if (errorMessage.detail) {
        // FastAPI error detail
        errorStr = typeof errorMessage.detail === 'string' 
          ? errorMessage.detail 
          : JSON.stringify(errorMessage.detail)
      } else if (errorMessage.message) {
        errorStr = errorMessage.message
      } else {
        errorStr = JSON.stringify(errorMessage)
      }
    } else {
      errorStr = String(errorMessage)
    }

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
      'password must contain at least one uppercase letter': 'errors.passwordUppercase',
      'password must contain at least one lowercase letter': 'errors.passwordLowercase',
      'password must contain at least one digit': 'errors.passwordDigit',
      'password must contain at least one special character': 'errors.passwordSpecial',
      'password must contain at least one special character (!@#$%^&*...)': 'errors.passwordSpecial',
      'string should have at least 8 characters': 'errors.passwordLength',
    }

    // Try to find a matching translation key
    for (const [keyword, translationKey] of Object.entries(errorMappings)) {
      if (errorStr.toLowerCase().includes(keyword.toLowerCase())) {
        return t(translationKey)
      }
    }

    // If no match found, return the original message
    return errorStr
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
