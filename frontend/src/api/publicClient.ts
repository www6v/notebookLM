import axios from 'axios'

const publicOnly = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

export interface PublicClientConfig {
  desktop_backend_url: string | null
}

export async function fetchPublicClientConfig(): Promise<PublicClientConfig> {
  const res = await publicOnly.get<PublicClientConfig>('/public/client-config')
  return res.data
}
