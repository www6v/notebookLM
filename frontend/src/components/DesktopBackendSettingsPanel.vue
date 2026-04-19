
<template>
  <v-card class="settings-card">
    <v-card-title class="text-subtitle-1 font-weight-medium">
      {{ t('admin.desktopBackendTitle') }}
    </v-card-title>
    <v-card-text>
      <p class="text-body-2 text-medium-emphasis mb-4">
        {{ t('admin.desktopBackendHint') }}
      </p>
      <v-text-field
        v-model="backendUrl"
        :label="t('admin.desktopBackendFieldLabel')"
        :placeholder="t('admin.desktopBackendPlaceholder')"
        variant="outlined"
        density="comfortable"
        hide-details="auto"
        :disabled="loading"
      />
      <v-btn
        color="primary"
        class="mt-4"
        :loading="saving"
        :disabled="loading"
        @click="saveBackend"
      >
        {{ t('admin.desktopBackendSave') }}
      </v-btn>
      <p
        v-if="showRestartHint"
        class="text-caption text-medium-emphasis mt-3"
      >
        {{ t('admin.desktopBackendRestartHint') }}
      </p>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { adminApi } from '@/api/admin'
import { fetchPublicClientConfig } from '@/api/publicClient'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({
  name: 'DesktopBackendSettingsPanel',
})

const { t } = useI18n()
const snackbar = useSnackbarStore()
const backendUrl = ref('')
const loading = ref(true)
const saving = ref(false)
const showRestartHint = computed(() => import.meta.env.PROD)

onMounted(async () => {
  loading.value = true
  try {
    const cfg = await fetchPublicClientConfig()
    backendUrl.value = (cfg.desktop_backend_url ?? '').trim()
  } catch {
    snackbar.error(t('admin.desktopBackendLoadFailed'))
  } finally {
    loading.value = false
  }
})

const saveBackend = async () => {
  saving.value = true
  try {
    await adminApi.putClientConfig({
      desktop_backend_url: backendUrl.value.trim(),
    })
    snackbar.success(t('admin.desktopBackendSavedFleet'))
  } catch {
    snackbar.error(t('admin.desktopBackendSaveFailed'))
  } finally {
    saving.value = false
  }
}
</script>
