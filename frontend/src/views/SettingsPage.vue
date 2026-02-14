<template>
  <div class="settings-page">
    <header class="settings-header">
      <el-button text @click="router.push('/')">
        <el-icon size="18">
          <ArrowLeft />
        </el-icon>
      </el-button>
      <h1>Settings</h1>
    </header>

    <main class="settings-main">
      <el-card class="settings-card">
        <template #header>
          <h3>LLM Provider Configuration</h3>
        </template>
        <el-form label-position="top">
          <el-form-item label="Default Provider">
            <el-select v-model="llmProvider" style="width: 100%">
              <el-option label="OpenAI" value="openai" />
              <el-option label="Anthropic (Claude)" value="anthropic" />
              <el-option label="Google Gemini" value="google" />
              <el-option label="Azure OpenAI" value="azure" />
              <el-option label="Ollama (Local)" value="ollama" />
            </el-select>
          </el-form-item>
          <el-form-item label="Model">
            <el-input v-model="llmModel" placeholder="gpt-4o" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input
              v-model="apiKey"
              type="password"
              show-password
              placeholder="sk-..."
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="saveSettings">
              Save Settings
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <h3>Chat Settings</h3>
        </template>
        <el-form label-position="top">
          <el-form-item label="Conversational Style">
            <el-select v-model="chatStyle" style="width: 100%">
              <el-option label="Default" value="default" />
              <el-option label="Learning Guide" value="learning_guide" />
              <el-option label="Custom" value="custom" />
            </el-select>
          </el-form-item>
          <el-form-item label="Response Length">
            <el-select v-model="responseLength" style="width: 100%">
              <el-option label="Shorter" value="shorter" />
              <el-option label="Default" value="default" />
              <el-option label="Longer" value="longer" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const llmProvider = ref('openai')
const llmModel = ref('gpt-4o')
const apiKey = ref('')
const chatStyle = ref('default')
const responseLength = ref('default')

const saveSettings = () => {
  // Settings would be persisted to backend in a real implementation
  localStorage.setItem('llm_settings', JSON.stringify({
    provider: llmProvider.value,
    model: llmModel.value,
    chatStyle: chatStyle.value,
    responseLength: responseLength.value,
  }))
  ElMessage.success('Settings saved')
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
}

.settings-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.settings-main {
  max-width: 640px;
  margin: 32px auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-card h3 {
  font-size: 16px;
  font-weight: 600;
}
</style>
