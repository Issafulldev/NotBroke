'use client'

import { RegisterForm } from '@/components/auth/RegisterForm'
import { useTranslations } from '@/hooks/useTranslations'
import { LanguageSelector } from '@/components/ui/language-selector'

export default function RegisterPage() {
  const { locale, setLocale } = useTranslations()

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute top-0 left-1/4 w-72 h-72 bg-emerald-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-72 h-72 bg-teal-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse animation-delay-2000"></div>
      </div>

      {/* Language Selector in top-right */}
      <div className="absolute top-4 right-4 z-10">
        <LanguageSelector
          currentLocale={locale}
          onLocaleChange={setLocale}
        />
      </div>

      {/* Register Content */}
      <div className="w-full max-w-md animate-fade-in pt-8">
        <RegisterForm />
      </div>
    </div>
  )
}
