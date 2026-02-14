import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '@/api/chat'
import type { ChatSession, Message } from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const streaming = ref(false)

  const fetchSessions = async (notebookId: string) => {
    sessions.value = await chatApi.listSessions(notebookId)
  }

  const createSession = async (notebookId: string, title: string = 'New Chat') => {
    const session = await chatApi.createSession(notebookId, { title })
    sessions.value.unshift(session)
    currentSession.value = session
    messages.value = []
    return session
  }

  const selectSession = async (sessionId: string) => {
    const session = sessions.value.find((s) => s.id === sessionId)
    if (session) {
      currentSession.value = session
      messages.value = await chatApi.listMessages(sessionId)
    }
  }

  const addUserMessage = (content: string) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      session_id: currentSession.value?.id || '',
      role: 'user',
      content,
      citations: null,
      created_at: new Date().toISOString(),
    }
    messages.value.push(msg)
    return msg
  }

  const addAssistantMessage = (content: string, citations: Record<string, unknown> | null = null) => {
    const msg: Message = {
      id: crypto.randomUUID(),
      session_id: currentSession.value?.id || '',
      role: 'assistant',
      content,
      citations,
      created_at: new Date().toISOString(),
    }
    messages.value.push(msg)
    return msg
  }

  const updateLastAssistantMessage = (content: string) => {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content = content
    }
  }

  return {
    sessions,
    currentSession,
    messages,
    loading,
    streaming,
    fetchSessions,
    createSession,
    selectSession,
    addUserMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
  }
})
