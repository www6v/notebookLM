import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/useUserStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginPage.vue'),
    },
    {
      path: '/admin',
      name: 'AdminUserList',
      component: () => import('@/views/admin/AdminUserList.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/users/:id',
      name: 'AdminUserDetail',
      component: () => import('@/views/admin/AdminUserDetail.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/featured',
      name: 'AdminFeaturedNotebooks',
      component: () => import('@/views/admin/AdminFeaturedNotebooksPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/admin/desktop',
      name: 'AdminDesktop',
      component: () => import('@/views/admin/AdminDesktopPage.vue'),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: '/',
      redirect: '/admin',
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/admin',
    },
  ],
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth) {
    if (!userStore.isLoggedIn) {
      return '/login'
    }
    if (!userStore.user) {
      await userStore.fetchUser()
    }
    if (to.meta.requiresAdmin && !userStore.isAdmin) {
      return '/login'
    }
  }
})

export default router
