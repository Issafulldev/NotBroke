import { create } from 'zustand'
import type { User } from './api'

// Store pour les catégories actives et l'état global de l'application
interface CategoryStore {
  activeCategoryId: number | null
  setActiveCategoryId: (id: number | null) => void
  clearActiveCategory: () => void
}

export const useCategoryStore = create<CategoryStore>((set) => ({
  activeCategoryId: null,
  setActiveCategoryId: (id) => set({ activeCategoryId: id }),
  clearActiveCategory: () => set({ activeCategoryId: null }),
}))

// Store pour la gestion des formulaires et erreurs
interface UIStore {
  formError: string
  setFormError: (error: string) => void
  clearFormError: () => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
}

export const useUIStore = create<UIStore>((set) => ({
  formError: '',
  setFormError: (error) => set({ formError: error }),
  clearFormError: () => set({ formError: '' }),
  isLoading: false,
  setIsLoading: (loading) => set({ isLoading: loading }),
}))

// 🔐 Store pour l'authentification - Utilise UNIQUEMENT les cookies httpOnly
// Les données utilisateur sont stockées EN MÉMOIRE uniquement (pas de localStorage)
interface AuthStore {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,

  login: (token: string, user: User) => {
    // 🔐 Token is in httpOnly cookie, we just store it in memory for the session
    // The cookie will be sent automatically with every request
    set({ token, user, isAuthenticated: true })
  },

  logout: () => {
    // 🔐 Token cleanup is done by the browser (httpOnly cookie is cleared by server)
    set({ token: null, user: null, isAuthenticated: false })
  },

  setUser: (user: User) => {
    set({ user })
  },
}))

// ============================================================================
// LOCALE (i18n)
// ============================================================================

interface LocaleStore {
  locale: string
  setLocale: (locale: string) => void
}

const SUPPORTED_LOCALES = ['fr', 'en', 'ru']
const DEFAULT_LOCALE = 'fr'
const STORAGE_KEY = 'notbroke_locale'

// Initialize locale from localStorage
const getInitialLocale = () => {
  if (typeof window === 'undefined') return DEFAULT_LOCALE

  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved && SUPPORTED_LOCALES.includes(saved)) {
    return saved
  }

  const browser = navigator.language.split('-')[0]
  return SUPPORTED_LOCALES.includes(browser) ? browser : DEFAULT_LOCALE
}

export const useLocaleStore = create<LocaleStore>((set) => ({
  locale: getInitialLocale(),
  setLocale: (locale: string) => {
    if (SUPPORTED_LOCALES.includes(locale)) {
      localStorage.setItem(STORAGE_KEY, locale)
      set({ locale })
    }
  },
}))
