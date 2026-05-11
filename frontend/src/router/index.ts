import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserStore } from '@/stores/useUserStore'
import { i18n } from '@/plugins/i18n'
import {
  detectLocaleForRedirect,
  type AppLocale,
} from '@/i18n/locale-resolver'

const localizedChildren: RouteRecordRaw[] = [
  {
    path: '',
    name: 'Landing',
    component: () => import('@/views/LandingPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: 'login',
    name: 'Login',
    component: () => import('@/views/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: 'register',
    name: 'Register',
    component: () => import('@/views/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: 'app',
    name: 'Home',
    component: () => import('@/views/HomePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'discover',
    name: 'Discover',
    component: () => import('@/views/DiscoverPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: 'notebook/:id',
    name: 'NotebookDetail',
    component: () => import('@/views/NotebookDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'shared/:shareToken',
    name: 'SharedNotebook',
    component: () => import('@/views/NotebookDetail.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: 'settings',
    name: 'Settings',
    component: () => import('@/views/SettingsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: 'pricing',
    name: 'Pricing',
    component: () => import('@/views/PricingPage.vue'),
    meta: { requiresAuth: false },
  },
]

const routes: RouteRecordRaw[] = [
  {
    path: '/oauth/callback',
    name: 'OAuthCallback',
    component: () => import('@/views/OAuthCallbackPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    redirect: () => {
      const locale = detectLocaleForRedirect()
      return `/${locale}`
    },
  },
  {
    path: '/:locale(en|zh-CN)',
    component: () => import('@/views/LocaleShell.vue'),
    children: localizedChildren,
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: (to) => {
      const locale = detectLocaleForRedirect()
      return `/${locale}${to.path}`
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function syncI18nFromRoute(locale: string | undefined): void {
  if (locale === 'en' || locale === 'zh-CN') {
    i18n.global.locale.value = locale
  }
}

function localeForGuard(to: {
  params: Record<string, string | string[]>
  path: string
}): AppLocale {
  const raw = to.params.locale
  const loc = Array.isArray(raw) ? raw[0] : raw
  if (loc === 'en' || loc === 'zh-CN') {
    return loc
  }
  return detectLocaleForRedirect(to.path)
}

router.beforeEach(async (to) => {
  syncI18nFromRoute(
    Array.isArray(to.params.locale)
      ? to.params.locale[0]
      : to.params.locale,
  )

  const userStore = useUserStore()
  if (to.meta.requiresAuth !== false) {
    if (!userStore.isLoggedIn) {
      return {
        name: 'Login',
        params: { locale: localeForGuard(to) },
      }
    }
    if (!userStore.user && userStore.token) {
      await userStore.fetchUser()
    }
  }
})

export default router
