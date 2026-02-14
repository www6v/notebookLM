import client from './client'

export interface ChatSession {
  id: string
  notebook_id: string
  title: string
  settings: Record<string, unknown> | null
  created_at: string
}

export interface Message {
  id: string
  session_id: string
  role: string
  content: string
  citations: Record<string, unknown> | null
  created_at: string
}

export const chatApi = {
  createSession: async (notebookId: string, data: { title?: string }): Promise<ChatSession> => {
    const res = await client.post(`/notebooks/${notebookId}/chat/sessions`, data)
    return res.data
  },

  listSessions: async (notebookId: string): Promise<ChatSession[]> => {
    const res = await client.get(`/notebooks/${notebookId}/chat/sessions`)
    return res.data
  },

  listMessages: async (sessionId: string): Promise<Message[]> => {
    const res = await client.get(`/chat/${sessionId}/messages`)
    return res.data
  },
}
