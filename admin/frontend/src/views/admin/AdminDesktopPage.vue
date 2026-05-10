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
      <h1>桌面端设置</h1>
    </header>
    <main class="admin-desktop-main">
      <v-alert
        type="info"
        variant="tonal"
        class="mb-4"
      >
        桌面端后端设置仅在 Tauri 桌面应用中可用，Web 版不支持此功能。
      </v-alert>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

defineOptions({ name: 'AdminDesktopPage' })

const router = useRouter()

function goAdminUsers() {
  router.push({ name: 'AdminUserList' })
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
