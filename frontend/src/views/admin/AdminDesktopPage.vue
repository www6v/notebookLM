
<template>
  <div class="admin-desktop-page">
    <header class="admin-desktop-header">
      <v-btn
        icon
        variant="text"
        @click="goAdminUsers"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <h1>{{ t('admin.desktopPageTitle') }}</h1>
    </header>
    <main class="admin-desktop-main">
      <v-alert
        v-if="!isTauriDesktop"
        type="info"
        variant="tonal"
        class="mb-4"
      >
        {{ t('admin.desktopTauriOnly') }}
      </v-alert>
      <DesktopBackendSettingsPanel v-else />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import DesktopBackendSettingsPanel from '@/components/DesktopBackendSettingsPanel.vue'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { isTauriApp } from '@/utils/isTauriApp'

defineOptions({
  name: 'AdminDesktopPage',
})

const { t } = useI18n()
const router = useRouter()
const routeLocale = useRouteLocale()
const isTauriDesktop = isTauriApp()

const goAdminUsers = () => {
  router.push({
    name: 'AdminUserList',
    params: { locale: routeLocale.value },
  })
}
</script>

<style scoped>
.admin-desktop-page {
  min-height: 100vh;
}

.admin-desktop-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.admin-desktop-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.admin-desktop-main {
  max-width: 640px;
  margin: 32px auto;
  padding: 0 24px;
}
</style>
