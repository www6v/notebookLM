/** URL / storage / navigator locale helpers for the SPA. */

export const LOCALE_KEY = 'notebooklm-locale'

export const SUPPORTED_LOCALES = ['en', 'zh-CN'] as const

export type AppLocale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: AppLocale = 'zh-CN'

export function parseLocaleFromPath(pathname: string): AppLocale | null {
  const segment = pathname.replace(/^\/*/, '').split('/').filter(Boolean)[0]
  if (segment === 'en' || segment === 'zh-CN') {
    return segment
  }
  return null
}

function readStoredLocale(): AppLocale | null {
  try {
    const saved = localStorage.getItem(LOCALE_KEY)
    if (saved === 'en' || saved === 'zh-CN') {
      return saved
    }
  } catch {
    /* ignore */
  }
  return null
}

function detectFromNavigator(): AppLocale {
  const raw =
    typeof navigator !== 'undefined' && navigator.languages?.length
      ? navigator.languages
      : typeof navigator !== 'undefined'
        ? [navigator.language]
        : []
  for (const lang of raw) {
    const lower = String(lang).toLowerCase().split(';')[0].trim()
    if (lower.startsWith('zh')) {
      return 'zh-CN'
    }
    if (lower.startsWith('en')) {
      return 'en'
    }
  }
  return 'en'
}

/**
 * Pick locale for redirects: path prefix, then storage, then navigator, then
 * default.
 */
export function detectLocaleForRedirect(pathname?: string): AppLocale {
  const path =
    pathname ??
    (typeof window !== 'undefined' ? window.location.pathname : '/')
  const fromPath = parseLocaleFromPath(path)
  if (fromPath) {
    return fromPath
  }
  const stored = readStoredLocale()
  if (stored) {
    return stored
  }
  if (typeof navigator !== 'undefined') {
    return detectFromNavigator()
  }
  return DEFAULT_LOCALE
}

/** Resolve locale for navigation when route params may be missing (e.g. 401). */
export function getCurrentLocaleForNavigation(): AppLocale {
  if (typeof window === 'undefined') {
    return DEFAULT_LOCALE
  }
  return detectLocaleForRedirect(window.location.pathname)
}
