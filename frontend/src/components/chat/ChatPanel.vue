<template>
  <div class="chat-panel">
    <!-- Messages area -->
    <div ref="messagesContainer" class="messages-container">
      <div v-if="chatStore.messages.length === 0" class="chat-welcome">
        <div class="welcome-icon">
          <el-icon size="48" color="#4285f4">
            <ChatDotRound />
          </el-icon>
        </div>
        <h2>Start a conversation</h2>
        <p>Ask questions about your sources and get AI-powered answers with citations.</p>
        <div class="suggested-questions">
          <el-button
            v-for="q of suggestedQuestions"
            :key="q"
            round
            size="small"
            @click="sendMessage(q)"
          >
            {{ q }}
          </el-button>
        </div>
      </div>

      <div
        v-for="msg of chatStore.messages"
        :key="msg.id"
        class="message"
        :class="msg.role"
      >
        <div class="message-avatar">
          <el-icon v-if="msg.role === 'assistant'" size="20" color="#4285f4">
            <MagicStick />
          </el-icon>
          <el-icon v-else size="20" color="#5f6368">
            <User />
          </el-icon>
        </div>
        <div class="message-content">
          <div class="message-role">
            {{ msg.role === 'assistant' ? 'AI' : 'You' }}
          </div>
          <div class="message-text" v-html="renderMarkdown(msg.content)" />
          <div v-if="msg.role === 'assistant'" class="message-actions">
            <el-button text size="small" @click="saveToNote(msg.content)">
              <el-icon size="14">
                <DocumentAdd />
              </el-icon>
              Save to note
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="chatStore.streaming" class="message assistant">
        <div class="message-avatar">
          <el-icon size="20" color="#4285f4">
            <MagicStick />
          </el-icon>
        </div>
        <div class="message-content">
          <div class="message-role">AI</div>
          <div class="typing-indicator">
            <span /><span /><span />
          </div>
        </div>
      </div>
    </div>

    <!-- Input area -->
    <div class="chat-input-area">
      <div class="input-wrapper">
        <el-input
          v-model="inputText"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="Ask about your sources..."
          @keydown.enter.exact.prevent="sendMessage()"
        />
        <el-button
          type="primary"
          circle
          :disabled="!inputText.trim()"
          @click="sendMessage()"
        >
          <el-icon>
            <Promotion />
          </el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound, MagicStick, User, Promotion, DocumentAdd,
} from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import { useChatStore } from '@/stores/useChatStore'
import { noteApi } from '@/api/note'

const props = defineProps<{ notebookId: string }>()

const chatStore = useChatStore()
const inputText = ref('')
const messagesContainer = ref<HTMLElement>()
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const suggestedQuestions = [
  'Summarize the key points',
  'What are the main topics?',
  'Find connections between sources',
]

onMounted(async () => {
  await chatStore.fetchSessions(props.notebookId)
  if (chatStore.sessions.length === 0) {
    await chatStore.createSession(props.notebookId)
  } else {
    await chatStore.selectSession(chatStore.sessions[0].id)
  }
})

const sendMessage = async (text?: string) => {
  const content = text || inputText.value.trim()
  if (!content) return

  inputText.value = ''
  chatStore.addUserMessage(content)
  scrollToBottom()

  // Simulate AI response (will be replaced with real WebSocket streaming)
  chatStore.streaming = true
  setTimeout(() => {
    chatStore.addAssistantMessage(
      `I understand you're asking about: "${content}". This is a placeholder response. Once the RAG pipeline is connected, I'll provide answers grounded in your sources with citations like [1][2].`
    )
    chatStore.streaming = false
    scrollToBottom()
  }, 1500)
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const renderMarkdown = (text: string) => {
  return md.render(text)
}

const saveToNote = async (content: string) => {
  try {
    await noteApi.create(props.notebookId, {
      title: 'Saved from chat',
      content,
    })
    ElMessage.success('Saved to notes')
  } catch {
    ElMessage.error('Failed to save note')
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
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

.message-actions {
  margin-top: 8px;
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

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 20px;
  padding: 10px 16px;
  resize: none;
}
</style>
