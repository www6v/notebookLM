import client from './client'

export interface Note {
  id: string
  notebook_id: string
  title: string
  content: string
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export const noteApi = {
  list: async (notebookId: string): Promise<Note[]> => {
    const res = await client.get(`/notebooks/${notebookId}/notes`)
    return res.data
  },

  create: async (notebookId: string, data: { title?: string; content?: string; is_pinned?: boolean }): Promise<Note> => {
    const res = await client.post(`/notebooks/${notebookId}/notes`, data)
    return res.data
  },

  update: async (noteId: string, data: { title?: string; content?: string; is_pinned?: boolean }): Promise<Note> => {
    const res = await client.put(`/notes/${noteId}`, data)
    return res.data
  },

  remove: async (noteId: string): Promise<void> => {
    await client.delete(`/notes/${noteId}`)
  },
}
