import { describe, it, expect, vi } from 'vitest'
import { authApi } from '@/lib/api'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      post: vi.fn(),
      get: vi.fn(),
      interceptors: {
        response: {
          use: vi.fn(),
        },
      },
    })),
  },
}))

describe('authApi', () => {
  it('should have all required methods', () => {
    expect(authApi).toHaveProperty('register')
    expect(authApi).toHaveProperty('login')
    expect(authApi).toHaveProperty('logout')
    expect(authApi).toHaveProperty('getCurrentUser')
    expect(authApi).toHaveProperty('isAuthenticated')
  })

  it('should call login endpoint', async () => {
    const mockApi = axios.create() as any
    mockApi.post.mockResolvedValue({
      data: {
        access_token: 'test-token',
        token_type: 'bearer',
        user: { id: 1, username: 'test' },
      },
    })

    const result = await authApi.login({
      username: 'test',
      password: 'password123',
    })

    expect(result).toHaveProperty('access_token')
    expect(result).toHaveProperty('user')
  })
})

