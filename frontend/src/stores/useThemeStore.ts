import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const THEME_KEY = 'app-theme'
export type ThemeMode = 'dark' | 'light'

function loadTheme(): ThemeMode {
  const saved = localStorage.getItem(THEME_KEY) as ThemeMode | null
  if (saved === 'dark' || saved === 'light') {
    return saved
  }
  return 'dark'
}

function applyTheme(mode: ThemeMode) {
  const html = document.documentElement
  if (mode === 'dark') {
    html.classList.add('theme-dark')
    html.classList.remove('theme-light')
  } else {
    html.classList.add('theme-light')
    html.classList.remove('theme-dark')
  }
}

export const useThemeStore = defineStore('theme', () => {
  const theme = ref<ThemeMode>(loadTheme())

  const setTheme = (mode: ThemeMode) => {
    theme.value = mode
    localStorage.setItem(THEME_KEY, mode)
    applyTheme(mode)
  }

  watch(
    theme,
    (mode) => {
      applyTheme(mode)
    },
    { immediate: true },
  )

  return { theme, setTheme }
})
