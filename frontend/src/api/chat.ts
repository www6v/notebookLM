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

export interface CitationDetail {
  source_id: string
  source_title: string
  chunk_id: string
  chunk_index: number
  page_number: number | null
  paragraph_index: number | null
  content: string
  highlight_text: string | null
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

  sendMessage: async (sessionId: string, data: { content: string; source_ids?: string[] }): Promise<Message> => {
    const res = await client.post(`/chat/${sessionId}/messages`, data, {
      timeout: 120000,
    })
    return res.data
  },

  sendMessageStream: (
    sessionId: string,
    data: {
      content: string
      source_ids?: string[]
      conversation_style?: string
      custom_prompt?: string
      answer_length?: string
    },
    callbacks: {
      onStep?: (step: Record<string, unknown>) => void
      onChunk?: (chunk: string) => void
      onAnswer?: (message: Message) => void
      onError?: (error: string) => void
      onDone?: () => void
    },
  ) => {
    const streamAdapter = async (config: { baseURL?: string; url?: string; method?: string; headers?: Record<string, string>; data?: string }) => {
      const path = (config.baseURL ?? '') + (config.url ?? '')
      const url = typeof window !== 'undefined' && window.location?.origin ? window.location.origin + path : path
      const headers: Record<string, string> = { ...(config.headers as Record<string, string>) }
      if (config.data && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json'
      }
      const response = await fetch(url, {
        method: config.method ?? 'POST',
        headers,
        body: config.data,
      })
      const axiosHeaders: Record<string, string> = {}
      response.headers.forEach((v, k) => {
        axiosHeaders[k] = v
      })
      if (!response.ok || !response.body) {
        callbacks.onError?.('Failed to connect to stream')
        return { data: null, status: response.status, statusText: response.statusText, headers: axiosHeaders, config: config as never, request: null }
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const jsonStr = line.slice(6).trim()
          if (!jsonStr) continue
          try {
            const event = JSON.parse(jsonStr)
            if (event.type === 'step') callbacks.onStep?.(event.data)
            else if (event.type === 'chunk' || event.type === 'token' || event.type === 'delta') {
              callbacks.onChunk?.(String(event.data?.content ?? event.data?.text ?? event.data ?? ''))
            }
            else if (event.type === 'answer') callbacks.onAnswer?.(event.data as Message)
            else if (event.type === 'error') callbacks.onError?.(event.data?.message ?? 'Unknown error')
            else if (event.type === 'done') callbacks.onDone?.()
          } catch {
            // skip malformed lines
          }
        }
      }
      callbacks.onDone?.()
      return { data: null, status: 200, statusText: 'OK', headers: axiosHeaders, config: config as never, request: null }
    }

    client.request({
      method: 'POST',
      url: `/chat/${sessionId}/messages/stream`,
      data,
      adapter: streamAdapter as never,
    }).catch((err: { message?: string }) => {
      callbacks.onError?.(err?.message ?? 'Stream connection failed')
    })
  },
}
