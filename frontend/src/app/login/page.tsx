'use client'

import { LoginForm } from '@/components/auth/LoginForm'
import { useTranslations } from '@/hooks/useTranslations'
import { LanguageSelector } from '@/components/ui/language-selector'
import { Zap } from 'lucide-react'

export default function LoginPage() {
  const { t, locale, setLocale } = useTranslations()

  return (
    <div className="min-h-screen flex flex-col px-4 relative overflow-hidden">
      {/* Language Selector in top-right */}
      <div className="absolute right-4 z-10" style={{ top: '1.32rem' }}>
        <LanguageSelector
          currentLocale={locale}
          onLocaleChange={setLocale}
        />
      </div>

      {/* Header - Title & Subtitle at top */}
      <div className="w-full max-w-md self-start ml-auto mr-auto animate-fade-in" style={{ paddingTop: '1.32rem' }}>
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-0">
            <div className="p-3 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl shadow-lg">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-orange-300 to-yellow-200" style={{ fontFamily: "'Poppins', sans-serif", fontWeight: 800 }}>
              {t('dashboard.title')}
            </h1>
          </div>
          <p className="text-lg text-white font-semibold tracking-wide" style={{ fontFamily: "'Poppins', sans-serif" }}>
            {t('dashboard.subtitle')}
          </p>
        </div>
      </div>

      {/* Login Form - Centered in remaining space */}
      <div className="flex-1 flex items-center justify-center w-full">
        <div className="w-full max-w-md animate-fade-in">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}
