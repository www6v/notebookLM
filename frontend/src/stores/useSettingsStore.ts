import { defineStore } from 'pinia'
import { ref } from 'vue'

const SETTINGS_KEY = 'app-global-settings'

export interface GlobalSettings {
  outputLanguage: string
}

const DEFAULT_SETTINGS: GlobalSettings = {
  outputLanguage: '简体中文',
}

function loadSettings(): GlobalSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
    }
  } catch {
    /* ignore */
  }
  return { ...DEFAULT_SETTINGS }
}

function persistSettings(settings: GlobalSettings) {
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
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
  const settings = ref<GlobalSettings>(loadSettings())

  const setOutputLanguage = (language: string) => {
    settings.value.outputLanguage = language
    persistSettings(settings.value)
  }

  return {
    settings,
    setOutputLanguage,
  }
})
