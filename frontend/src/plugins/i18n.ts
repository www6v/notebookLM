import { createI18n } from 'vue-i18n'
import en from '@/locales/en'
import zhCN from '@/locales/zh-CN'
import {
  detectLocaleForRedirect,
  LOCALE_KEY,
} from '@/i18n/locale-resolver'

function getInitialLocale(): string {
  if (typeof window === 'undefined') {
    return 'zh-CN'
  }
  return detectLocaleForRedirect(window.location.pathname)
}

export const i18n = createI18n({
  legacy: false,
  locale: getInitialLocale(),
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
