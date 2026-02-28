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
            <el-select
              v-model="settingsStore.settings.llmProvider"
              style="width: 100%"
            >
              <el-option label="OpenAI" value="openai" />
              <el-option label="Anthropic (Claude)" value="anthropic" />
              <el-option label="Google Gemini" value="google" />
              <el-option label="Azure OpenAI" value="azure" />
              <el-option label="Ollama (Local)" value="ollama" />
            </el-select>
          </el-form-item>
          <el-form-item label="Model">
            <el-input
              v-model="settingsStore.settings.llmModel"
              placeholder="gpt-4o"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              :loading="saving"
              @click="saveSettings"
            >
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
const saving = ref(false)

function onThemeChange(value: ThemeMode) {
  themeStore.setTheme(value)
  ElMessage.success(value === 'dark' ? '已切换为深色模式' : '已切换为浅色模式')
}

async function onOutputLanguageChange(value: string) {
  await settingsStore.setOutputLanguage(value)
  ElMessage.success(`输出语言已设置为 ${value}`)
}

onMounted(async () => {
  await settingsStore.fetchSettings()
})

const saveSettings = async () => {
  saving.value = true
  try {
    await settingsStore.saveAllSettings()
    ElMessage.success('设置已保存')
    router.push('/')
  } catch {
    ElMessage.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
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
