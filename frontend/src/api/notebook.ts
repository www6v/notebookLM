import client from './client'

export interface Notebook {
  id: string
  user_id: string
  title: string
  description: string
  created_at: string
  updated_at: string
  source_count: number
  share_enabled?: boolean
}

interface NotebookListResponse {
  notebooks: Notebook[]
  total: number
}

export const notebookApi = {
  list: async (): Promise<NotebookListResponse> => {
    const res = await client.get('/notebooks')
    return res.data
  },

  get: async (id: string): Promise<Notebook> => {
    const res = await client.get(`/notebooks/${id}`)
    return res.data
  },

  create: async (data: { title: string; description?: string }): Promise<Notebook> => {
    const res = await client.post('/notebooks', data)
    return res.data
  },

  update: async (id: string, data: { title?: string; description?: string }): Promise<Notebook> => {
    const res = await client.put(`/notebooks/${id}`, data)
    return res.data
  },

  remove: async (id: string): Promise<void> => {
    await client.delete(`/notebooks/${id}`)
  },

  enableShare: async (
    id: string,
    body: { regenerate?: boolean } = {},
  ): Promise<{ share_token: string }> => {
    const res = await client.post(`/notebooks/${id}/share`, body)
    return res.data
  },

  disableShare: async (id: string): Promise<void> => {
    await client.delete(`/notebooks/${id}/share`)
  },
}
