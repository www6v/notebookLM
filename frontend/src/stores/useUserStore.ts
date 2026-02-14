import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<{ id: string; email: string; username: string } | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  const setToken = (t: string) => {
    token.value = t
    localStorage.setItem('token', t)
  }

  const clearToken = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  const login = async (email: string, password: string) => {
    const res = await authApi.login({ email, password })
    setToken(res.access_token)
  }

  const register = async (email: string, username: string, password: string) => {
    const res = await authApi.register({ email, username, password })
    user.value = res
  }

  const logout = () => {
    clearToken()
  }

  return { token, user, isLoggedIn, login, register, logout, setToken }
})
