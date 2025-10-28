'use client'

import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from './dropdown-menu'
import { Button } from './button'
import { Globe } from 'lucide-react'

interface LanguageSelectorProps {
  currentLocale: string
  onLocaleChange: (locale: string) => void
}

const languages = [
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'ru', label: 'Русский', flag: '🇷🇺' },
]

export function LanguageSelector({ currentLocale, onLocaleChange }: LanguageSelectorProps) {
  const currentLanguage = languages.find((lang) => lang.code === currentLocale)

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="gap-2 px-3 py-2 rounded-lg bg-white/10 backdrop-blur-sm border border-white/20 hover:bg-white/20 hover:border-white/40 transition-all duration-200 text-gray-900 font-semibold shadow-lg hover:shadow-xl"
        >
          <span className="text-xs font-bold">
            {currentLanguage?.code.toUpperCase()}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="backdrop-blur-sm bg-white/95 border border-gray-200 shadow-xl rounded-lg">
        {languages.map((language) => (
          <DropdownMenuItem
            key={language.code}
            onClick={() => onLocaleChange(language.code)}
            className={`cursor-pointer transition-all duration-150 ${currentLocale === language.code ? 'bg-emerald-100 text-emerald-900 font-semibold' : 'hover:bg-gray-100'}`}
          >
            <span className="mr-2">{language.flag}</span>
            {language.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
