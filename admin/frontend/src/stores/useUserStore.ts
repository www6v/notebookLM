import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

interface UserInfo {
  id: string
  email: string
  username: string
  role: string
  is_active: boolean
  subscription_expires_at: string | null
  subscription_plan: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  const setToken = (t: string) => {
    token.value = t
    localStorage.setItem('token', t)
  }

  const clearToken = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const u = await authApi.getMe()
      user.value = {
        id: u.id,
        email: u.email,
        username: u.username,
        role: u.role,
        is_active: u.is_active,
        subscription_expires_at: u.subscription_expires_at ?? null,
        subscription_plan: u.subscription_plan ?? 'free',
      }
    } catch {
      clearToken()
    }
  }

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password })
    setToken(res.access_token)
    await fetchUser()
  }

  const logout = () => {
    clearToken()
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    login,
    logout,
    setToken,
    fetchUser,
  }
})
