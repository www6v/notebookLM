import { createI18n } from 'vue-i18n'
import en from '@/locales/en'
import zhCN from '@/locales/zh-CN'

const LOCALE_KEY = 'notebooklm-locale'

function getSavedLocale(): string {
  try {
    const saved = localStorage.getItem(LOCALE_KEY)
    if (saved === 'en' || saved === 'zh-CN') return saved
  } catch {
    /* ignore */
  }
  return 'zh-CN'
}

export const i18n = createI18n({
  legacy: false,
  locale: getSavedLocale(),
  fallbackLocale: 'en',
  messages: {
    en,
    'zh-CN': zhCN,
  },
})

export function setLocale(locale: 'en' | 'zh-CN'): void {
  i18n.global.locale.value = locale
  try {
    localStorage.setItem(LOCALE_KEY, locale)
  } catch {
    /* ignore */
  }
}

export function getLocale(): 'en' | 'zh-CN' {
  const current = i18n.global.locale.value
  return current === 'zh-CN' ? 'zh-CN' : 'en'
}
