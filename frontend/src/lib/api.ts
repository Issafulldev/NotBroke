import axios from 'axios'

// Configuration de base d'Axios
const apiBaseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL: apiBaseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // 🔐 CRITICAL: Send cookies with every request
})

// Intercepteur pour gérer les erreurs 401 (token expiré)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expiré ou invalide, déconnecter l'utilisateur
      // Le cookie httpOnly est géré automatiquement par le navigateur
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types pour les entités
export interface Category {
  id: number
  name: string
  description?: string
  parent_id?: number | null
  full_path?: string
  children?: Category[]
  created_at: string
  updated_at: string
}

export interface Expense {
  id: number
  amount: number
  note: string
  category_id: number
  created_at: string
  category_path?: string
}

export interface PaginationMeta {
  page: number
  per_page: number
  total: number
  has_next: boolean
  has_previous: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  meta: PaginationMeta
}

export interface MonthlySummary {
  total: number
  category_totals: Record<string, number>
  start_date: string
  end_date: string
  category_id: number | null
  month?: string
}

// Types pour l'authentification
export interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export interface AuthToken {
  access_token: string
  token_type: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// 🔐 Fonctions d'authentification - SANS localStorage
export const authApi = {
  register: async (userData: RegisterData): Promise<User> => {
    const response = await api.post('/auth/register', userData)
    return response.data
  },

  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials)
    return response.data
  },

  logout: async (): Promise<void> => {
    // 🔐 Appel au backend pour supprimer le cookie
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Even if logout fails, clear local state
      console.error('Logout error:', error)
    }
  },

  isAuthenticated: async (): Promise<boolean> => {
    try {
      // Faire un test ping pour vérifier que le token est valide
      // Utiliser GET /auth/me pour vérifier l'authentification
      await api.get('/auth/me')
      return true
    } catch {
      return false
    }
  },

  getCurrentUser: async (): Promise<User | null> => {
    try {
      const response = await api.get('/auth/me')
      return response.data
    } catch {
      return null
    }
  },
}

// API Categories
export const categoriesApi = {
  getAll: async (params?: { page?: number; per_page?: number }): Promise<PaginatedResponse<Category>> => {
    const response = await api.get('/categories', { params })
    return response.data
  },

  getById: async (id: number): Promise<Category> => {
    const response = await api.get(`/categories/${id}`)
    return response.data
  },

  create: async (data: Omit<Category, 'id' | 'created_at' | 'updated_at'>): Promise<Category> => {
    const response = await api.post('/categories', data)
    return response.data
  },

  update: async (id: number, data: Partial<Category>): Promise<Category> => {
    const response = await api.patch(`/categories/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/categories/${id}`)
  },
}

// API Expenses
export const expensesApi = {
  getAll: async (params?: {
    category_id?: number
    start_date?: string
    end_date?: string
    page?: number
    per_page?: number
  }): Promise<PaginatedResponse<Expense>> => {
    const response = await api.get('/expenses', { params })
    return response.data
  },

  getByCategory: async (
    categoryId: number,
    params?: {
      start_date?: string
      end_date?: string
      page?: number
      per_page?: number
    }
  ): Promise<PaginatedResponse<Expense>> => {
    const response = await api.get(`/categories/${categoryId}/expenses`, { params })
    return response.data
  },

  create: async (data: Omit<Expense, 'id' | 'created_at' | 'updated_at'>): Promise<Expense> => {
    const response = await api.post('/expenses', data)
    return response.data
  },

  update: async (id: number, data: Partial<Expense>): Promise<Expense> => {
    const response = await api.patch(`/expenses/${id}`, data)
    return response.data
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/expenses/${id}`)
  },

  export: async (params?: {
    format?: 'csv' | 'xlsx'
    category_id?: number
    start_date?: string
    end_date?: string
  }): Promise<Blob> => {
    const response = await api.get('/expenses/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },
}

// API Summary
export const summaryApi = {
  get: async (params?: {
    start_date?: string
    end_date?: string
    category_id?: number
  }): Promise<MonthlySummary> => {
    const response = await api.get('/summary', { params })
    return response.data
  },
}
