import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const LAST_LOGIN_ACCOUNT_KEY = 'lastLoginAccount'

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
  const isPaid = computed(() => user.value?.role === 'paid')
  const isFree = computed(() => !user.value || user.value.role === 'free')
  const subscriptionActive = computed(() => {
    if (!user.value || user.value.role !== 'paid') return false
    if (!user.value.subscription_expires_at) return false
    return new Date(user.value.subscription_expires_at) > new Date()
  })
  const subscriptionExpiresAt = computed(() => user.value?.subscription_expires_at ?? null)

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

  const register = async (email: string, username: string, password: string) => {
    const res = await authApi.register({ email, username, password })
    user.value = {
      id: res.id,
      email: res.email,
      username: res.username,
      role: res.role,
      is_active: res.is_active,
      subscription_expires_at: res.subscription_expires_at ?? null,
      subscription_plan: res.subscription_plan ?? 'free',
    }
  }

  const logout = () => {
    const email = user.value?.email
    if (email) {
      localStorage.setItem(LAST_LOGIN_ACCOUNT_KEY, email)
    }
    clearToken()
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    isPaid,
    isFree,
    subscriptionActive,
    subscriptionExpiresAt,
    login,
    register,
    logout,
    setToken,
    fetchUser,
  }
})
