import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { chatApi } from '@/api/chat'
import type { ChatSession, Message } from '@/api/chat'
import { createClientUuid } from '@/utils/clientUuid'

export type ConversationStyle = 'default' | 'learning_guide' | 'custom'
export type AnswerLength = 'default' | 'long' | 'short'

export interface ConversationSettings {
  style: ConversationStyle
  customPrompt: string
  answerLength: AnswerLength
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<ChatSession[]>([])
  const currentSession = ref<ChatSession | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const streaming = ref(false)

  const conversationSettings = reactive<ConversationSettings>({
    style: 'default',
    customPrompt: '',
    answerLength: 'default',
  })

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
      id: createClientUuid(),
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
      id: createClientUuid(),
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

  const updateConversationSettings = (settings: Partial<ConversationSettings>) => {
    if (settings.style !== undefined) conversationSettings.style = settings.style
    if (settings.customPrompt !== undefined) conversationSettings.customPrompt = settings.customPrompt
    if (settings.answerLength !== undefined) conversationSettings.answerLength = settings.answerLength
  }

  /** Bump to push text into ChatPanel composer (see ChatPanel watch). */
  const pendingComposerTick = ref(0)
  const pendingComposerText = ref('')

  const injectComposerText = (text: string) => {
    pendingComposerText.value = text
    pendingComposerTick.value += 1
  }

  return {
    sessions,
    currentSession,
    messages,
    loading,
    streaming,
    conversationSettings,
    fetchSessions,
    createSession,
    selectSession,
    addUserMessage,
    addAssistantMessage,
    updateLastAssistantMessage,
    updateConversationSettings,
    pendingComposerTick,
    pendingComposerText,
    injectComposerText,
  }
})
