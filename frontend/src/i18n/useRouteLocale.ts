import { computed } from 'vue'
import { useRoute } from 'vue-router'
import type { AppLocale } from '@/i18n/locale-resolver'
import { getCurrentLocaleForNavigation } from '@/i18n/locale-resolver'

export function useRouteLocale() {
  const route = useRoute()
  return computed<AppLocale>(() => {
    const loc = route.params.locale
    if (loc === 'en' || loc === 'zh-CN') {
      return loc
    }
    return getCurrentLocaleForNavigation()
  })
}
