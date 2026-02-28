<template>
  <div class="settings-page">
    <header class="settings-header">
      <el-button text @click="router.push('/')">
        <el-icon size="18">
          <ArrowLeft />
        </el-icon>
      </el-button>
      <h1>设置</h1>
    </header>

    <main class="settings-main">
      <el-card class="settings-card">
        <template #header>
          <h3>外观</h3>
        </template>
        <el-form label-position="top">
          <el-form-item label="网站模式">
            <el-select
              :model-value="themeStore.theme"
              style="width: 100%"
              @update:model-value="onThemeChange"
            >
              <el-option label="浅色模式" value="light" />
              <el-option label="深色模式" value="dark" />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

      <el-card class="settings-card">
        <template #header>
          <h3>输出设置</h3>
        </template>
        <el-form label-position="top">
          <el-form-item>
            <template #label>
              <div class="form-label-with-desc">
                <span>输出语言</span>
                <span class="form-label-desc">思维导图、信息图、演示文稿等 AI 生成内容的语言</span>
              </div>
            </template>
            <el-select
              :model-value="settingsStore.settings.outputLanguage"
              style="width: 100%"
              @update:model-value="onOutputLanguageChange"
            >
              <el-option
                v-for="opt in languageOptions"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </el-form-item>
        </el-form>
      </el-card>

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
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useThemeStore } from '@/stores/useThemeStore'
import type { ThemeMode } from '@/stores/useThemeStore'
import { useSettingsStore, OUTPUT_LANGUAGE_OPTIONS } from '@/stores/useSettingsStore'

const router = useRouter()
const themeStore = useThemeStore()
const settingsStore = useSettingsStore()
const languageOptions = OUTPUT_LANGUAGE_OPTIONS
const llmProvider = ref('openai')
const llmModel = ref('gpt-4o')
const apiKey = ref('')
function onThemeChange(value: ThemeMode) {
  themeStore.setTheme(value)
  ElMessage.success(value === 'dark' ? '已切换为深色模式' : '已切换为浅色模式')
}

function onOutputLanguageChange(value: string) {
  settingsStore.setOutputLanguage(value)
  ElMessage.success(`输出语言已设置为 ${value}`)
}

onMounted(() => {
  const raw = localStorage.getItem('llm_settings')
  if (raw) {
    try {
      const data = JSON.parse(raw)
      if (data.provider) llmProvider.value = data.provider
      if (data.model) llmModel.value = data.model
    } catch {
      /* ignore */
    }
  }
})

const saveSettings = () => {
  // Settings would be persisted to backend in a real implementation
  localStorage.setItem('llm_settings', JSON.stringify({
    provider: llmProvider.value,
    model: llmModel.value,
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

.form-label-with-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.form-label-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  font-weight: 400;
}
</style>
