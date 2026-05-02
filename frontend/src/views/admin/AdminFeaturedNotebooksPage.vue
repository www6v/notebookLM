<template>
  <div class="admin-featured-page">
    <header class="admin-featured-header">
      <v-btn
        icon
        variant="text"
        @click="goAdminUsers"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <h1>{{ t('admin.featuredPageTitle') }}</h1>
    </header>
    <main class="admin-featured-main">
      <p class="admin-featured-intro">
        {{ t('admin.featuredIntro') }}
      </p>
      <v-alert
        type="info"
        variant="tonal"
        class="mb-4"
        density="compact"
      >
        {{ t('admin.featuredHint') }}
      </v-alert>
      <v-textarea
        v-model="tokensText"
        :label="t('admin.featuredTokensLabel')"
        variant="outlined"
        rows="10"
        auto-grow
        :disabled="loading"
      />
      <div class="admin-featured-actions">
        <v-btn
          color="primary"
          :loading="saving"
          :disabled="loading"
          @click="handleSave"
        >
          {{ t('common.save') }}
        </v-btn>
        <v-btn
          variant="text"
          :disabled="loading || saving"
          @click="reloadFromServer"
        >
          {{ t('admin.featuredReload') }}
        </v-btn>
      </div>
      <v-progress-linear
        v-if="loading"
        indeterminate
        class="mt-4"
      />
      <v-card
        v-if="!loading && previewRows.length > 0"
        class="mt-6"
        variant="outlined"
      >
        <v-card-title class="text-subtitle-1">
          {{ t('admin.featuredPreviewTitle') }}
        </v-card-title>
        <v-list density="compact">
          <v-list-item
            v-for="row of previewRows"
            :key="row.share_token"
          >
            <v-list-item-title>
              {{ row.resolved_title || row.share_token }}
            </v-list-item-title>
            <v-list-item-subtitle>
              <span
                v-if="row.notebook_found"
                class="ok"
              >
                {{ t('admin.featuredStatusOk') }}
              </span>
              <span
                v-else
                class="warn"
              >
                {{ t('admin.featuredStatusMissing') }}
              </span>
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import {
  adminApi,
  type AdminFeaturedNotebookItem,
} from '@/api/admin'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({
  name: 'AdminFeaturedNotebooksPage',
})

const { t } = useI18n()
const router = useRouter()
const routeLocale = useRouteLocale()
const snackbar = useSnackbarStore()

const tokensText = ref('')
const previewRows = ref<AdminFeaturedNotebookItem[]>([])
const loading = ref(false)
const saving = ref(false)

function goAdminUsers() {
  router.push({
    name: 'AdminUserList',
    params: { locale: routeLocale.value },
  })
}

function applyRowsToText(rows: AdminFeaturedNotebookItem[]) {
  tokensText.value = rows.map((r) => r.share_token).join('\n')
}

async function reloadFromServer() {
  loading.value = true
  try {
    const res = await adminApi.listFeaturedNotebooks()
    previewRows.value = res.items
    applyRowsToText(res.items)
  } catch {
    snackbar.error(t('admin.featuredLoadFailed'))
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  const lines = tokensText.value
    .split(/\r?\n/)
    .map((s) => s.trim())
    .filter(Boolean)
  const items = lines.map((share_token) => ({ share_token, custom_title: null }))
  saving.value = true
  try {
    const res = await adminApi.putFeaturedNotebooks({ items })
    previewRows.value = res.items
    applyRowsToText(res.items)
    snackbar.success(t('admin.featuredSaved'))
  } catch {
    snackbar.error(t('admin.featuredSaveFailed'))
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  void reloadFromServer()
})
</script>

<style scoped>
.admin-featured-page {
  min-height: 100vh;
}

.admin-featured-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.admin-featured-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.admin-featured-main {
  max-width: 720px;
  margin: 32px auto;
  padding: 0 24px;
}

.admin-featured-intro {
  margin-bottom: 16px;
  color: rgba(var(--v-theme-on-surface), 0.75);
  line-height: 1.5;
}

.admin-featured-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.ok {
  color: rgb(var(--v-theme-success));
}

.warn {
  color: rgb(var(--v-theme-warning));
}
</style>
