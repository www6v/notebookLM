import client from './client'

interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  username: string
  password: string
}

interface TokenResponse {
  access_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  email: string
  username: string
  role: string
  is_active: boolean
  created_at: string
  subscription_expires_at: string | null
  subscription_plan: string
}

export const authApi = {
  login: async (data: LoginRequest): Promise<TokenResponse> => {
    const res = await client.post('/auth/login', data)
    return res.data
  },

  register: async (data: RegisterRequest): Promise<UserResponse> => {
    const res = await client.post('/auth/register', data)
    return res.data
  },

  getMe: async (): Promise<UserResponse> => {
    const res = await client.get('/auth/me')
    return res.data
  },
}
