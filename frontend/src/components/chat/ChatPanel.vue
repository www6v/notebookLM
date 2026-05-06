<template>
  <div class="chat-panel">
    <!-- Chat Header -->
    <div class="chat-header">
      <div class="chat-header-left">
        <span class="chat-header-title">{{ $t('chat.title') }}</span>
      </div>
      <div
        v-if="!readOnly"
        class="chat-header-right"
      >
        <v-btn
          variant="text"
          size="small"
          icon
          class="config-btn"
          @click="openConfigDialog"
        >
          <v-icon size="18">mdi-cog</v-icon>
        </v-btn>
        <v-menu location="bottom">
          <template #activator="{ props: menuProps }">
            <v-btn
              v-bind="menuProps"
              variant="text"
              size="small"
              icon
              class="more-btn"
            >
              <v-icon size="18">mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-list>
            <v-list-item @click="openConfigDialog">
              {{ $t('chat.configDialog.title') }}
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>

    <div
      v-if="readOnly"
      class="chat-share-readonly"
    >
      <v-icon
        size="48"
        color="primary"
      >
        mdi-eye-lock-outline
      </v-icon>
      <h2 class="chat-share-readonly-title">
        {{ $t('chat.shareReadOnlyTitle') }}
      </h2>
      <p class="chat-share-readonly-desc">
        {{ $t('chat.shareReadOnlyDesc') }}
      </p>
    </div>

    <!-- Messages area -->
    <div
      v-else
      ref="messagesContainer"
      class="messages-container"
    >
      <div v-if="chatStore.messages.length === 0" class="chat-welcome">
        <div class="welcome-icon">
          <v-icon
            size="48"
            color="primary"
          >
            mdi-comment-text
          </v-icon>
        </div>
        <h2>Start a conversation</h2>
        <p>Ask questions about your sources and get AI-powered answers with citations.</p>
        <div class="suggested-questions">
          <v-btn
            v-for="q of suggestedQuestions"
            :key="q"
            variant="tonal"
            size="small"
            rounded
            @click="sendMessage(q)"
          >
            {{ q }}
          </v-btn>
        </div>
      </div>

      <div
        v-for="msg of chatStore.messages"
        :key="msg.id"
        class="message"
        :class="msg.role"
      >
        <div class="message-avatar">
          <v-icon
            v-if="msg.role === 'assistant'"
            size="20"
            color="primary"
          >
            mdi-auto-fix
          </v-icon>
          <v-icon
            v-else
            size="20"
            color="secondary"
          >
            mdi-account
          </v-icon>
        </div>
        <div class="message-content">
          <div class="message-role">
            {{ msg.role === 'assistant' ? 'AI' : 'You' }}
          </div>
          <div
            class="message-text"
            v-html="renderMessageContent(msg)"
            @click="handleCitationClick($event, msg)"
            @mouseenter="handleCitationHover($event, msg)"
          />
          <div v-if="msg.role === 'assistant'" class="message-actions">
            <v-btn
              variant="text"
              size="small"
              @click="saveToNote(msg.content)"
            >
              <v-icon size="14">mdi-note-plus</v-icon>
              Save to note
            </v-btn>
          </div>
        </div>
      </div>

      <div v-if="chatStore.streaming" class="message assistant">
        <div class="message-avatar">
          <v-icon
            size="20"
            color="primary"
          >
            mdi-auto-fix
          </v-icon>
        </div>
        <div class="message-content">
          <div class="message-role">AI</div>
          <div class="typing-indicator">
            <span /><span /><span />
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="!readOnly && streamPanel.visible"
      class="stream-status-panel"
    >
      <div class="stream-status-header">
        <div class="stream-status-title">
          <v-icon
            size="14"
            class="stream-status-icon"
            :class="{ rotating: chatStore.streaming && streamPanel.status !== 'error' }"
          >
            {{ streamPanel.status === 'error' ? 'mdi-alert-circle-outline' : 'mdi-auto-fix' }}
          </v-icon>
          <span>{{ streamPanel.currentAction }}</span>
        </div>
        <span
          class="stream-status-badge"
          :class="`status-${streamPanel.status}`"
        >
          {{ streamPanel.statusText }}
        </span>
      </div>
      <div
        ref="streamOutputContainer"
        class="stream-status-output"
      >
        <div
          v-for="(log, idx) of streamPanel.logs"
          :key="`log-${idx}`"
          class="stream-status-log"
        >
          {{ log }}
        </div>
        <div
          v-if="streamPanel.output"
          class="stream-status-answer"
        >
          {{ streamPanel.output }}
        </div>
      </div>
    </div>

    <!-- Citation Popover -->
    <div
      v-if="!readOnly && citationPopover.visible"
      class="citation-popover"
      :style="citationPopover.style"
      @mouseenter="keepPopoverOpen"
      @mouseleave="hidePopover"
    >
      <div class="citation-popover-header">
        <span class="citation-source-title">
          {{ citationPopover.data?.source_title }}
        </span>
        <span v-if="citationPopover.data?.page_number" class="citation-page">
          Page {{ citationPopover.data.page_number }}
        </span>
      </div>
      <div class="citation-popover-content">
        {{ citationPopover.data?.content }}
      </div>
      <div class="citation-popover-footer">
        <v-btn
          color="primary"
          size="small"
          variant="text"
          @click="jumpToSource(citationPopover.data)"
        >
          View in source
        </v-btn>
      </div>
    </div>

    <!-- Input area -->
    <div
      v-if="!readOnly"
      class="chat-input-area"
    >
      <div class="input-wrapper">
        <v-textarea
          ref="composerFieldRef"
          v-model="inputText"
          :placeholder="$t('chat.configDialog.styleDefaultDesc')"
          rows="1"
          auto-grow
          hide-details
          @keydown.enter.exact.prevent="sendMessage()"
        />
        <v-btn
          color="primary"
          icon
          :disabled="!inputText.trim() || chatStore.streaming"
          @click="sendMessage()"
        >
          <v-icon>mdi-send</v-icon>
        </v-btn>
      </div>
      <div class="input-footer">
        <span class="source-count">{{ $t('chat.sourceCount', { count: sourceStore.activeSourceIds.length }) }}</span>
      </div>
    </div>

    <v-dialog
      v-model="showConfigDialog"
      max-width="560"
      persistent
      class="config-dialog"
    >
      <v-card>
        <v-card-title>{{ $t('chat.configDialog.title') }}</v-card-title>
        <v-card-text>
          <p class="config-description">{{ $t('chat.configDialog.description') }}</p>

          <div class="config-section">
            <h4 class="config-label">{{ $t('chat.configDialog.styleLabel') }}</h4>
            <div class="config-options">
              <button
                v-for="opt of styleOptions"
                :key="opt.value"
                class="config-option-btn"
                :class="{ active: tempStyle === opt.value }"
                @click="tempStyle = opt.value"
              >
                <v-icon
                  v-if="tempStyle === opt.value"
                  size="14"
                  class="check-icon"
                >
                  mdi-check
                </v-icon>
                {{ opt.label }}
              </button>
            </div>

            <div v-if="tempStyle === 'custom'" class="custom-prompt-wrapper">
              <v-textarea
                v-model="tempCustomPrompt"
                rows="4"
                maxlength="10000"
                show-word-limit
                class="mt-2"
              />
            </div>

            <p v-if="tempStyle === 'default'" class="style-desc">
              {{ $t('chat.configDialog.styleDefaultDesc') }}
            </p>
            <p v-else-if="tempStyle === 'learning_guide'" class="style-desc">
              {{ $t('chat.configDialog.styleLearningGuideDesc') }}
            </p>
          </div>

          <div class="config-section">
            <h4 class="config-label">{{ $t('chat.configDialog.lengthLabel') }}</h4>
            <div class="config-options">
              <button
                v-for="opt of lengthOptions"
                :key="opt.value"
                class="config-option-btn"
                :class="{ active: tempLength === opt.value }"
                @click="tempLength = opt.value"
              >
                <v-icon
                  v-if="tempLength === opt.value"
                  size="14"
                  class="check-icon"
                >
                  mdi-check
                </v-icon>
                {{ opt.label }}
              </button>
            </div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="primary"
            @click="saveConfig"
          >
            {{ $t('chat.configDialog.save') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, withDefaults, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import MarkdownIt from 'markdown-it'
import { useChatStore } from '@/stores/useChatStore'
import { useSourceStore } from '@/stores/useSourceStore'
import type { ConversationStyle, AnswerLength } from '@/stores/useChatStore'
import { chatApi } from '@/api/chat'
import type { CitationDetail, Message } from '@/api/chat'
import { noteApi } from '@/api/note'

const { t } = useI18n()
const props = withDefaults(
  defineProps<{ notebookId: string; readOnly?: boolean }>(),
  { readOnly: false },
)

const chatStore = useChatStore()
const sourceStore = useSourceStore()
const snackbar = useSnackbarStore()
const inputText = ref('')
const composerFieldRef = ref<{ $el?: HTMLElement } | null>(null)
const messagesContainer = ref<HTMLElement>()
const streamOutputContainer = ref<HTMLElement>()
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const showConfigDialog = ref(false)
const tempStyle = ref<ConversationStyle>('default')
const tempCustomPrompt = ref('')
const tempLength = ref<AnswerLength>('default')

const styleOptions = computed(() => [
  { value: 'default' as const, label: t('chat.configDialog.styleDefault') },
  { value: 'learning_guide' as const, label: t('chat.configDialog.styleLearningGuide') },
  { value: 'custom' as const, label: t('chat.configDialog.styleCustom') },
])

const lengthOptions = computed(() => [
  { value: 'default' as const, label: t('chat.configDialog.lengthDefault') },
  { value: 'long' as const, label: t('chat.configDialog.lengthLong') },
  { value: 'short' as const, label: t('chat.configDialog.lengthShort') },
])

const openConfigDialog = () => {
  tempStyle.value = chatStore.conversationSettings.style
  tempCustomPrompt.value = chatStore.conversationSettings.customPrompt
  tempLength.value = chatStore.conversationSettings.answerLength
  showConfigDialog.value = true
}

const saveConfig = () => {
  chatStore.updateConversationSettings({
    style: tempStyle.value,
    customPrompt: tempStyle.value === 'custom' ? tempCustomPrompt.value : '',
    answerLength: tempLength.value,
  })
  showConfigDialog.value = false
  snackbar.success(t('chat.configDialog.save'))
}

const suggestedQuestions = [
  'Summarize the key points',
  'What are the main topics?',
  'Find connections between sources',
]

const citationPopover = reactive<{
  visible: boolean
  data: CitationDetail | null
  style: Record<string, string>
}>({
  visible: false,
  data: null,
  style: {},
})

const searchSteps = ref<Record<string, unknown>[]>([])
let popoverTimer: ReturnType<typeof setTimeout> | null = null
let panelHideTimer: ReturnType<typeof setTimeout> | null = null
let fallbackStreaming = false
let doneEventReceived = false

type StreamPanelStatus = 'running' | 'answering' | 'done' | 'error'

const streamPanel = reactive<{
  visible: boolean
  status: StreamPanelStatus
  statusText: string
  currentAction: string
  logs: string[]
  output: string
  hasChunk: boolean
}>({
  visible: false,
  status: 'running',
  statusText: 'Running',
  currentAction: 'Preparing',
  logs: [],
  output: '',
  hasChunk: false,
})

onMounted(async () => {
  if (props.readOnly) {
    return
  }
  await chatStore.fetchSessions(props.notebookId)
  if (chatStore.sessions.length === 0) {
    await chatStore.createSession(props.notebookId)
  } else {
    await chatStore.selectSession(chatStore.sessions[0].id)
  }
})

watch(
  () => chatStore.pendingComposerTick,
  () => {
    if (props.readOnly) {
      return
    }
    const text = chatStore.pendingComposerText?.trim()
    if (!text) {
      return
    }
    inputText.value = text
    nextTick(() => {
      const root = composerFieldRef.value?.$el
      const ta = root?.querySelector?.('textarea') as HTMLTextAreaElement | null
      ta?.focus()
    })
  },
)

const formatStep = (step: Record<string, unknown>): string => {
  const type = step.step as string
  if (type === 'decompose') {
    const subs = step.sub_questions as string[] | undefined
    return `Decomposing query into ${subs?.length || '?'} sub-questions...`
  }
  if (type === 'retrieve') {
    return `Searching: "${(step.sub_question as string || '').slice(0, 60)}..." (${step.chunks_found} chunks found)`
  }
  if (type === 'reflect') {
    return step.sufficient ? 'Context sufficient, generating answer...' : 'Need more information, refining search...'
  }
  return JSON.stringify(step)
}

const getStepAction = (step: Record<string, unknown>): string => {
  const type = step.step as string
  if (type === 'decompose') return 'Planning retrieval'
  if (type === 'retrieve') return 'Searching sources'
  if (type === 'reflect') return 'Evaluating context'
  return 'Running tool step'
}

const scrollStreamOutputToBottom = () => {
  nextTick(() => {
    if (streamOutputContainer.value) {
      streamOutputContainer.value.scrollTop = streamOutputContainer.value.scrollHeight
    }
  })
}

const resetStreamPanel = () => {
  if (panelHideTimer) {
    clearTimeout(panelHideTimer)
    panelHideTimer = null
  }
  streamPanel.visible = true
  streamPanel.status = 'running'
  streamPanel.statusText = 'Running'
  streamPanel.currentAction = 'Preparing context'
  streamPanel.logs = []
  streamPanel.output = ''
  streamPanel.hasChunk = false
  fallbackStreaming = false
  doneEventReceived = false
}

const pushStreamLog = (log: string) => {
  streamPanel.logs.push(log)
  if (streamPanel.logs.length > 60) {
    streamPanel.logs = streamPanel.logs.slice(-60)
  }
  scrollStreamOutputToBottom()
}

const appendStreamOutput = (chunk: string) => {
  if (!chunk) return
  streamPanel.hasChunk = true
  streamPanel.status = 'answering'
  streamPanel.statusText = 'Streaming'
  streamPanel.currentAction = 'Generating answer'
  streamPanel.output += chunk
  scrollStreamOutputToBottom()
}

const streamFallbackOutput = async (fullText: string) => {
  if (!fullText || streamPanel.hasChunk) {
    return
  }
  fallbackStreaming = true
  streamPanel.status = 'answering'
  streamPanel.statusText = 'Streaming'
  streamPanel.currentAction = 'Generating answer'
  const chunkSize = 20
  for (let i = 0; i < fullText.length; i += chunkSize) {
    streamPanel.output += fullText.slice(i, i + chunkSize)
    scrollStreamOutputToBottom()
    await new Promise((resolve) => setTimeout(resolve, 12))
  }
  fallbackStreaming = false
  if (doneEventReceived) {
    closeStreamPanelLater()
  }
}

const closeStreamPanelLater = () => {
  if (panelHideTimer) {
    clearTimeout(panelHideTimer)
  }
  panelHideTimer = setTimeout(() => {
    streamPanel.visible = false
  }, 2200)
}

const sendMessage = async (text?: string) => {
  const content = text || inputText.value.trim()
  if (!content || !chatStore.currentSession) return

  inputText.value = ''
  chatStore.addUserMessage(content)
  scrollToBottom()

  chatStore.streaming = true
  searchSteps.value = []
  resetStreamPanel()

  const { style, customPrompt, answerLength } = chatStore.conversationSettings
  let doneHandled = false

  chatApi.sendMessageStream(
    chatStore.currentSession.id,
    {
      content,
      source_ids: sourceStore.activeSourceIds,
      conversation_style: style,
      custom_prompt: style === 'custom' ? customPrompt : undefined,
      answer_length: answerLength,
    },
    {
      onStep: (step) => {
        searchSteps.value.push(step)
        streamPanel.currentAction = getStepAction(step)
        pushStreamLog(formatStep(step))
        scrollToBottom()
      },
      onChunk: (chunk) => {
        appendStreamOutput(chunk)
      },
      onAnswer: (msg) => {
        if (!streamPanel.hasChunk) {
          void streamFallbackOutput(msg.content)
        }
        chatStore.addAssistantMessage(msg.content, msg.citations)
        scrollToBottom()
      },
      onError: (error) => {
        chatStore.streaming = false
        chatStore.addAssistantMessage(
          `Sorry, an error occurred: ${error}. Please try again.`
        )
        streamPanel.status = 'error'
        streamPanel.statusText = 'Error'
        streamPanel.currentAction = 'Request failed'
        pushStreamLog(`Error: ${error}`)
        closeStreamPanelLater()
      },
      onDone: () => {
        if (doneHandled) return
        doneHandled = true
        doneEventReceived = true
        chatStore.streaming = false
        searchSteps.value = []
        if (streamPanel.status !== 'error') {
          streamPanel.status = 'done'
          streamPanel.statusText = 'Completed'
          streamPanel.currentAction = 'Answer ready'
        }
        if (!fallbackStreaming) {
          closeStreamPanelLater()
        }
        scrollToBottom()
      },
    },
  )
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const renderMessageContent = (msg: Message) => {
  let html = md.render(msg.content)
  if (msg.role === 'assistant' && msg.citations) {
    html = html.replace(
      /\[(\d+)\]/g,
      (match, num) => {
        const citation = (msg.citations as Record<string, CitationDetail>)?.[num]
        if (citation && typeof citation === 'object' && 'source_title' in citation) {
          return `<span class="citation-mark" data-cite-id="${num}" title="${citation.source_title || ''}">[${num}]</span>`
        }
        return match
      },
    )
  }
  return html
}

const getCitationFromEvent = (event: Event, msg: Message): { citeId: string; citation: CitationDetail; target: HTMLElement } | null => {
  const target = event.target as HTMLElement
  if (!target.classList.contains('citation-mark')) return null
  const citeId = target.dataset.citeId
  if (!citeId || !msg.citations?.[citeId]) return null
  return {
    citeId,
    citation: msg.citations[citeId] as unknown as CitationDetail,
    target,
  }
}

const handleCitationHover = (event: Event, msg: Message) => {
  const result = getCitationFromEvent(event, msg)
  if (!result) return
  showPopover(result.citation, result.target)
}

const handleCitationClick = (event: Event, msg: Message) => {
  const result = getCitationFromEvent(event, msg)
  if (!result) return
  event.preventDefault()
  event.stopPropagation()
  showPopover(result.citation, result.target)
}

const showPopover = (citation: CitationDetail, target: HTMLElement) => {
  if (popoverTimer) {
    clearTimeout(popoverTimer)
    popoverTimer = null
  }

  const rect = target.getBoundingClientRect()
  citationPopover.data = citation
  citationPopover.visible = true
  citationPopover.style = {
    top: `${rect.bottom + 8}px`,
    left: `${rect.left}px`,
  }
}

const keepPopoverOpen = () => {
  if (popoverTimer) {
    clearTimeout(popoverTimer)
    popoverTimer = null
  }
}

const hidePopover = () => {
  popoverTimer = setTimeout(() => {
    citationPopover.visible = false
    citationPopover.data = null
  }, 200)
}

const jumpToSource = (citation: CitationDetail | null) => {
  if (!citation) return
  citationPopover.visible = false

  sourceStore.highlightChunk({
    sourceId: citation.source_id,
    chunkId: citation.chunk_id,
    chunkIndex: citation.chunk_index,
    pageNumber: citation.page_number,
    content: citation.content,
  })
}

const saveToNote = async (content: string) => {
  try {
    await noteApi.create(props.notebookId, {
      title: 'Saved from chat',
      content,
    })
    snackbar.success('Saved to notes')
  } catch {
    snackbar.error('Failed to save note')
  }
}

onBeforeUnmount(() => {
  if (popoverTimer) {
    clearTimeout(popoverTimer)
  }
  if (panelHideTimer) {
    clearTimeout(panelHideTimer)
  }
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  position: relative;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 3px 16px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-header-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.chat-header-right {
  display: flex;
  align-items: center;
  gap: 2px;
}

.config-btn,
.more-btn {
  padding: 4px;
  color: var(--text-secondary);
}

.config-btn:hover,
.more-btn:hover {
  color: var(--text-primary);
}

.chat-share-readonly {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
  color: var(--text-secondary);
}

.chat-share-readonly-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 16px 0 8px;
}

.chat-share-readonly-desc {
  font-size: 14px;
  max-width: 360px;
  line-height: 1.5;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 20px 96px;
}

.stream-status-panel {
  position: absolute;
  left: 16px;
  right: 16px;
  bottom: 88px;
  border: 1px solid #d7e3ff;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 8px 20px rgba(66, 133, 244, 0.12);
  padding: 10px 12px;
  z-index: 20;
  backdrop-filter: blur(2px);
}

.stream-status-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.stream-status-title {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: 12px;
  font-weight: 600;
  color: #1f2937;
}

.stream-status-icon {
  color: #4285f4;
}

.stream-status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
  white-space: nowrap;
}

.stream-status-badge.status-running {
  background: #eef4ff;
  color: #2459d6;
  border-color: #d7e3ff;
}

.stream-status-badge.status-answering {
  background: #e8f0fe;
  color: #1a73e8;
  border-color: #c7dafc;
}

.stream-status-badge.status-done {
  background: #ebf7ef;
  color: #1f8a4c;
  border-color: #cde9d7;
}

.stream-status-badge.status-error {
  background: #fff1f0;
  color: #d93025;
  border-color: #ffc9c5;
}

.stream-status-output {
  max-height: 150px;
  overflow-y: auto;
  border-radius: 8px;
  background: #f8faff;
  padding: 8px 10px;
}

.stream-status-log {
  font-size: 12px;
  line-height: 1.45;
  color: #4b5563;
  margin-bottom: 4px;
  word-break: break-word;
}

.stream-status-answer {
  font-size: 12px;
  line-height: 1.55;
  color: #111827;
  white-space: pre-wrap;
  word-break: break-word;
  margin-top: 6px;
  border-top: 1px dashed #d7e3ff;
  padding-top: 6px;
}

.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  color: var(--text-secondary);
}

.welcome-icon {
  margin-bottom: 16px;
}

.chat-welcome h2 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.chat-welcome p {
  font-size: 14px;
  max-width: 400px;
  margin-bottom: 20px;
}

.suggested-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #f1f3f4;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background: #e8f0fe;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-role {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
}

.message-text :deep(p) {
  margin-bottom: 8px;
}

.message-text :deep(code) {
  background: #f1f3f4;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 13px;
}

.message-text :deep(.citation-mark) {
  display: inline-block;
  color: #4285f4;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  padding: 0 2px;
  border-radius: 3px;
  transition: background 0.15s;
  vertical-align: super;
  line-height: 1;
}

.message-text :deep(.citation-mark:hover) {
  background: #e8f0fe;
  text-decoration: underline;
}

.message-actions {
  margin-top: 8px;
}

.search-steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 0;
}

.search-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #5f6368;
  animation: stepFadeIn 0.3s ease-out;
}

@keyframes stepFadeIn {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}

.step-icon.rotating {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.step-icon {
  color: #4285f4;
  flex-shrink: 0;
}

.step-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4285f4;
  animation: typing 1.4s infinite both;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

.citation-popover {
  position: fixed;
  z-index: 2000;
  background: #fff;
  border: 1px solid #e8eaed;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 14px;
  max-width: 380px;
  min-width: 240px;
  animation: popoverIn 0.15s ease-out;
}

@keyframes popoverIn {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

.citation-popover-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.citation-source-title {
  font-weight: 600;
  font-size: 13px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.citation-page {
  font-size: 11px;
  color: #5f6368;
  background: #f1f3f4;
  padding: 2px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}

.citation-popover-content {
  font-size: 12px;
  line-height: 1.5;
  color: #5f6368;
  max-height: 120px;
  overflow-y: auto;
  margin-bottom: 8px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.citation-popover-footer {
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f1f3f4;
  padding-top: 6px;
}

.chat-input-area {
  padding: 12px 20px 20px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}

.input-wrapper {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-wrapper :deep(.v-field) {
  border-radius: 20px;
  padding: 10px 16px;
  resize: none;
}

.input-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 6px;
}

.source-count {
  font-size: 12px;
  color: var(--text-secondary);
}

.config-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 24px;
  line-height: 1.6;
}

.config-section {
  margin-bottom: 24px;
}

.config-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.config-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.config-option-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  border-radius: 20px;
  border: 1px solid #dcdfe6;
  background: #fff;
  font-size: 14px;
  color: #333;
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
}

.config-option-btn:hover {
  border-color: #000000;
  color: #000000;
}

.config-option-btn.active {
  background: #000000;
  color: #fff;
  border-color: #000000;
}

.check-icon {
  margin-right: -2px;
}

.custom-prompt-wrapper {
  margin-top: 12px;
}

.style-desc {
  margin-top: 10px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>
