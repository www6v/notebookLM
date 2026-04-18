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

const extractErrorDetail = (payload: unknown): string | null => {
  if (!payload || typeof payload !== 'object') {
    return null
  }
  const d = (payload as { detail?: unknown }).detail
  if (typeof d === 'string') {
    return d
  }
  if (Array.isArray(d)) {
    return JSON.stringify(d)
  }
  return null
}

const extractJsonAnswer = (
  payload: unknown,
): { content: string; citations: Record<string, unknown> | null; steps: Record<string, unknown>[] } => {
  if (payload === null || payload === undefined) {
    return { content: '', citations: null, steps: [] }
  }
  if (typeof payload === 'string') {
    return { content: payload, citations: null, steps: [] }
  }
  if (typeof payload !== 'object') {
    return { content: String(payload), citations: null, steps: [] }
  }
  const root = payload as Record<string, unknown>
  const data =
    root.data !== undefined && typeof root.data === 'object' && root.data !== null
      ? (root.data as Record<string, unknown>)
      : root
  const stepsRaw = data.steps ?? data.search_steps ?? root.steps
  const steps = Array.isArray(stepsRaw)
    ? (stepsRaw as Record<string, unknown>[])
    : []
  const content =
    (typeof data.answer === 'string' && data.answer) ||
    (typeof data.content === 'string' && data.content) ||
    (typeof data.result === 'string' && data.result) ||
    (typeof data.message === 'string' && data.message) ||
    (typeof data.text === 'string' && data.text) ||
    (typeof data.final_answer === 'string' && data.final_answer) ||
    (typeof root.answer === 'string' && root.answer) ||
    ''
  const citations =
    (data.citations as Record<string, unknown> | null | undefined) ??
    (root.citations as Record<string, unknown> | null | undefined) ??
    null
  return { content, citations, steps }
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
      const contentType = response.headers.get('content-type') ?? ''
      if (!contentType.includes('text/event-stream')) {
        const raw = await response.text()
        let parsed: unknown
        try {
          parsed = raw ? JSON.parse(raw) : null
        } catch {
          callbacks.onError?.('Invalid response from server')
          callbacks.onDone?.()
          return { data: null, status: response.status, statusText: response.statusText, headers: axiosHeaders, config: config as never, request: null }
        }
        const httpErr = extractErrorDetail(parsed)
        if (httpErr) {
          callbacks.onError?.(httpErr)
          callbacks.onDone?.()
          return { data: null, status: response.status, statusText: response.statusText, headers: axiosHeaders, config: config as never, request: null }
        }
        if (parsed === null) {
          callbacks.onError?.('Empty response from search service')
          callbacks.onDone?.()
          return { data: null, status: response.status, statusText: response.statusText, headers: axiosHeaders, config: config as never, request: null }
        }
        const { content, citations, steps } = extractJsonAnswer(parsed)
        for (const step of steps) {
          callbacks.onStep?.(step)
        }
        if (!content.trim()) {
          callbacks.onError?.('No answer content in response')
          callbacks.onDone?.()
          return { data: null, status: response.status, statusText: response.statusText, headers: axiosHeaders, config: config as never, request: null }
        }
        const assistantMsg: Message = {
          id: typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : `tmp-${Date.now()}`,
          session_id: sessionId,
          role: 'assistant',
          content,
          citations,
          created_at: new Date().toISOString(),
        }
        callbacks.onAnswer?.(assistantMsg)
        callbacks.onDone?.()
        return { data: null, status: 200, statusText: 'OK', headers: axiosHeaders, config: config as never, request: null }
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
