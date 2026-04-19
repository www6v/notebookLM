
<template>
  <v-card class="settings-card">
    <v-card-title class="text-subtitle-1 font-weight-medium">
      {{ t('settings.desktopBackendTitle') }}
    </v-card-title>
    <v-card-text>
      <p class="text-body-2 text-medium-emphasis mb-4">
        {{ t('settings.desktopBackendHint') }}
      </p>
      <v-text-field
        v-model="backendUrl"
        :label="t('settings.desktopBackendFieldLabel')"
        :placeholder="t('settings.desktopBackendPlaceholder')"
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
        {{ t('settings.desktopBackendSave') }}
      </v-btn>
      <p
        v-if="showRestartHint"
        class="text-caption text-medium-emphasis mt-3"
      >
        {{ t('settings.desktopBackendRestartHint') }}
      </p>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useSnackbarStore } from '@/stores/useSnackbarStore'
import {
  readDesktopBackendUrl,
  writeDesktopBackendUrl,
} from '@/utils/tauriDesktopBackend'

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
    backendUrl.value = await readDesktopBackendUrl()
  } catch {
    snackbar.error(t('settings.desktopBackendLoadFailed'))
  } finally {
    loading.value = false
  }
})

const saveBackend = async () => {
  saving.value = true
  try {
    await writeDesktopBackendUrl(backendUrl.value.trim())
    snackbar.success(t('settings.desktopBackendSaved'))
  } catch {
    snackbar.error(t('settings.desktopBackendSaveFailed'))
  } finally {
    saving.value = false
  }
}
</script>
