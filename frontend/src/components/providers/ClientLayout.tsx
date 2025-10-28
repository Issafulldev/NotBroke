'use client'

import { useEffect } from 'react'

interface ClientLayoutProps {
  children: React.ReactNode
}

export function ClientLayout({ children }: ClientLayoutProps) {
  useEffect(() => {
    const preloadTranslations = async () => {
      const locales = ['fr', 'en', 'ru']
      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

      for (const locale of locales) {
        const cacheKey = `translations_${locale}`

        // Vérifier si déjà en cache
        if (localStorage.getItem(cacheKey)) {
          console.log(`[i18n] ${locale} déjà en cache`)
          continue
        }

        try {
          console.log(`[i18n] Pré-chargement des traductions: ${locale}`)
          const response = await fetch(`${baseUrl}/translations/${locale}`)

          if (response.ok) {
            const data = await response.json()
            localStorage.setItem(cacheKey, JSON.stringify(data.translations || {}))
            console.log(`[i18n] ${locale} pré-chargé en cache ✅`)
          } else {
            console.warn(`[i18n] Erreur au pré-chargement ${locale}: ${response.status}`)
          }
        } catch (err) {
          console.error(`[i18n] Erreur pré-chargement ${locale}:`, err)
        }
      }
    }

    preloadTranslations()
  }, [])

  return <>{children}</>
}
