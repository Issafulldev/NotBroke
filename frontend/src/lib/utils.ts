import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Fonction de formatage de devise
export function formatCurrency(amount: number, currency: string = 'EUR', locale: string = 'fr-FR'): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount)
}

// Obtenir le symbole d'une devise (liste simplifiée)
export function getCurrencySymbol(currencyCode: string): string {
  const symbols: Record<string, string> = {
    'EUR': '€', 'USD': '$', 'GBP': '£', 'JPY': '¥', 'CHF': 'CHF',
    'CAD': 'C$', 'AUD': 'A$', 'NZD': 'NZ$', 'SEK': 'kr', 'NOK': 'kr',
    'DKK': 'kr', 'PLN': 'zł', 'CZK': 'Kč', 'HUF': 'Ft', 'RUB': '₽',
    'TRY': '₺', 'CNY': '¥', 'INR': '₹', 'BRL': 'R$', 'ZAR': 'R',
    'MXN': '$', 'SGD': 'S$', 'HKD': 'HK$', 'KRW': '₩'
  }
  return symbols[currencyCode] || currencyCode
}

// Obtenir la devise par défaut selon la langue
export function getDefaultCurrencyByLocale(locale: string): string {
  const localeToCurrency: Record<string, string> = {
    'fr': 'EUR',  // Français → Euro
    'en': 'USD',  // Anglais → Dollar US
    'ru': 'RUB',  // Russe → Rouble
  }
  return localeToCurrency[locale] || 'EUR' // Par défaut EUR si langue non reconnue
}

export function formatDateOnly(input: string | Date | null | undefined): string {
  if (!input) return ''
  const str = typeof input === 'string' ? input : (input as Date).toISOString()
  if (str.includes('T')) return str.split('T')[0]
  const m = str.match(/\d{4}-\d{2}-\d{2}/)
  return m ? m[0] : str
}

// tree helpers removed (API now returns an already-built tree)
