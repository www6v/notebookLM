import router from '@/router'
import { setLocale } from '@/plugins/i18n'
import type { AppLocale } from '@/i18n/locale-resolver'

/**
 * Persist locale, update vue-i18n, and swap the :locale segment when on a
 * localized route.
 */
export function setAppLocale(next: AppLocale): void {
  setLocale(next)
  const r = router.currentRoute.value
  const cur = r.params.locale
  if ((cur === 'en' || cur === 'zh-CN') && r.name) {
    router.replace({
      name: r.name,
      params: { ...r.params, locale: next },
      query: r.query,
      hash: r.hash,
    })
  }
}
