import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '@/api/settings'

export interface GlobalSettings {
  outputLanguage: string
  llmProvider: string
  llmModel: string
}

const DEFAULT_SETTINGS: GlobalSettings = {
  outputLanguage: '简体中文',
  llmProvider: 'openai',
  llmModel: 'gpt-4o',
}

export const OUTPUT_LANGUAGE_OPTIONS = [
  { value: '简体中文', label: '简体中文' },
  { value: '繁體中文', label: '繁體中文' },
  { value: 'English', label: 'English' },
  { value: '日本語', label: '日本語' },
  { value: '한국어', label: '한국어' },
  { value: 'Español', label: 'Español' },
  { value: 'Français', label: 'Français' },
  { value: 'Deutsch', label: 'Deutsch' },
  { value: 'Português', label: 'Português' },
  { value: 'Русский', label: 'Русский' },
  { value: 'العربية', label: 'العربية' },
]

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<GlobalSettings>({ ...DEFAULT_SETTINGS })
  const loaded = ref(false)

  const fetchSettings = async () => {
    try {
      const data = await settingsApi.get()
      settings.value = {
        outputLanguage: data.output_language,
        llmProvider: data.llm_provider,
        llmModel: data.llm_model,
      }
    } catch {
      /* keep defaults when unauthenticated or network fails */
    } finally {
      loaded.value = true
    }
  }

  const setOutputLanguage = async (language: string) => {
    settings.value.outputLanguage = language
    try {
      await settingsApi.patch({ output_language: language })
    } catch {
      /* ignore – value is already updated in memory */
    }
  }

  const setLlmProvider = async (provider: string) => {
    settings.value.llmProvider = provider
    try {
      await settingsApi.patch({ llm_provider: provider })
    } catch {
      /* ignore */
    }
  }

  const setLlmModel = async (model: string) => {
    settings.value.llmModel = model
    try {
      await settingsApi.patch({ llm_model: model })
    } catch {
      /* ignore */
    }
  }

  const saveAllSettings = async () => {
    await settingsApi.patch({
      output_language: settings.value.outputLanguage,
      llm_provider: settings.value.llmProvider,
      llm_model: settings.value.llmModel,
    })
  }

  return {
    settings,
    loaded,
    fetchSettings,
    setOutputLanguage,
    setLlmProvider,
    setLlmModel,
    saveAllSettings,
  }
})
