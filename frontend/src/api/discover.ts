import client from './client'
import { publicOnly } from './publicClient'

export interface DiscoverNotebookListItem {
  id: string
  title: string
  description: string
  category: string
  cover_url: string
  subscriber_count: number
  source_count: number
  owner_display_name: string
}

export interface DiscoverNotebookListResponse {
  items: DiscoverNotebookListItem[]
  total: number
}

export interface DiscoverNotebookDetail extends DiscoverNotebookListItem {
  share_token: string | null
}

export async function fetchDiscoverNotebooks(params: {
  q?: string
  category?: string
  offset?: number
  limit?: number
}): Promise<DiscoverNotebookListResponse> {
  const res = await publicOnly.get<DiscoverNotebookListResponse>(
    '/public/discover/notebooks',
    { params },
  )
  return res.data
}

export async function fetchDiscoverNotebookDetail(
  id: string,
): Promise<DiscoverNotebookDetail> {
  const res = await publicOnly.get<DiscoverNotebookDetail>(
    `/public/discover/notebooks/${id}`,
  )
  return res.data
}

export async function subscribeDiscoverNotebook(id: string): Promise<void> {
  await client.post(`/discover/notebooks/${id}/subscribe`)
}

export async function unsubscribeDiscoverNotebook(id: string): Promise<void> {
  await client.delete(`/discover/notebooks/${id}/subscribe`)
}
