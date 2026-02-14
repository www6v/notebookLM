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

interface UserResponse {
  id: string
  email: string
  username: string
  created_at: string
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
}
