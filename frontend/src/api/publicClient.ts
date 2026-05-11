import axios from 'axios'

export const publicOnly = axios.create({
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

export interface PublicFeaturedNotebookItem {
  share_token: string
  title: string
  source_count: number
  created_at: string
}

export async function fetchPublicFeaturedNotebooks(): Promise<
  PublicFeaturedNotebookItem[]
> {
  const res = await publicOnly.get<{ items: PublicFeaturedNotebookItem[] }>(
    '/public/featured-notebooks',
  )
  return res.data.items
}
