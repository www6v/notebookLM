import axios from 'axios'
import { useUserStore } from '@/stores/useUserStore'
import router from '@/router'
import { getCurrentLocaleForNavigation } from '@/i18n/locale-resolver'

const client = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const userStore = useUserStore()
      userStore.logout()
      router.push({
        name: 'Login',
        params: { locale: getCurrentLocaleForNavigation() },
      })
    }
    return Promise.reject(error)
  }
)

export default client
