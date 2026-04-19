<template>
  <div class="settings-page">
    <header class="settings-header">
      <v-btn
        icon
        variant="text"
        @click="goHome"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <h1>{{ t('settings.title') }}</h1>
    </header>

    <main class="settings-main">
      <DesktopBackendSettingsPanel v-if="showDesktopBackend" />
      <v-card class="settings-card">
        <v-card-title class="text-subtitle-1 font-weight-medium">
          {{ t('settings.subscriptionPlan') }}
        </v-card-title>
        <v-card-text>
          <div class="plan-info">
            <div class="plan-row">
              <span class="plan-label">{{ t('settings.currentPlan') }}</span>
              <v-chip
                :color="userStore.isPaid ? 'primary' : 'default'"
                size="small"
              >
                {{ userStore.isPaid ? t('settings.planPlus') : t('settings.planFree') }}
              </v-chip>
            </div>
            <div
              v-if="userStore.isPaid && userStore.subscriptionExpiresAt"
              class="plan-row"
            >
              <span class="plan-label">{{ t('settings.expiresAt') }}</span>
              <span class="plan-value">{{ formatExpiryDate(userStore.subscriptionExpiresAt) }}</span>
            </div>
            <div class="plan-row">
              <span class="plan-label">{{ t('settings.notebookLimit') }}</span>
              <span class="plan-value">{{
                t('settings.planNotebooksValue', { count: userStore.isPaid ? 200 : 20 })
              }}</span>
            </div>
            <div class="plan-row">
              <span class="plan-label">{{ t('settings.sourcesPerNotebook') }}</span>
              <span class="plan-value">{{
                t('settings.planSourcesValue', { count: userStore.isPaid ? 50 : 30 })
              }}</span>
            </div>
            <div class="plan-row">
              <span class="plan-label">{{ t('settings.dailyChats') }}</span>
              <span class="plan-value">{{
                t('settings.planChatsValue', { count: userStore.isPaid ? 200 : 50 })
              }}</span>
            </div>
          </div>

          <v-btn
            v-if="userStore.isFree"
            color="primary"
            class="mt-4"
            @click="showPaymentDialog = true"
          >
            {{ t('settings.upgradePlus') }}
          </v-btn>
          <v-btn
            v-else-if="userStore.isPaid"
            color="primary"
            variant="outlined"
            class="mt-4"
            @click="showPaymentDialog = true"
          >
            {{ t('settings.renew') }}
          </v-btn>
        </v-card-text>
      </v-card>

      <v-card class="settings-card">
        <v-card-title class="text-subtitle-1 font-weight-medium">
          {{ t('settings.appearance') }}
        </v-card-title>
        <v-card-text>
          <v-select
            :model-value="themeStore.theme"
            :label="t('settings.siteMode')"
            :items="themeSelectItems"
            item-title="title"
            item-value="value"
            @update:model-value="onThemeChange"
          />
        </v-card-text>
      </v-card>

      <v-card class="settings-card">
        <v-card-title class="text-subtitle-1 font-weight-medium">
          {{ t('settings.outputSection') }}
        </v-card-title>
        <v-card-text>
          <div class="form-label-with-desc mb-2">
            <span class="text-body-2 font-weight-medium">{{ t('settings.outputLanguage') }}</span>
            <span class="form-label-desc text-caption">
              {{ t('settings.outputLanguageHint') }}
            </span>
          </div>
          <v-select
            :model-value="settingsStore.settings.outputLanguage"
            :items="languageOptions"
            item-title="label"
            item-value="value"
            @update:model-value="onOutputLanguageChange"
          />
        </v-card-text>
      </v-card>

      <v-card class="settings-card">
        <v-card-title class="text-subtitle-1 font-weight-medium">
          {{ t('settings.llmSection') }}
        </v-card-title>
        <v-card-text>
          <v-alert
            v-if="userStore.isFree"
            type="info"
            variant="tonal"
            density="compact"
            class="mb-4"
          >
            {{ t('settings.llmFreeHint') }}
          </v-alert>
          <v-select
            v-model="settingsStore.settings.llmProvider"
            :label="t('settings.defaultProvider')"
            :items="llmProviderItems"
            item-title="title"
            item-value="value"
            :disabled="userStore.isFree"
          />
          <v-select
            v-model="settingsStore.settings.llmModel"
            :label="t('settings.model')"
            :items="llmModelItems"
            item-title="title"
            item-value="value"
            class="mt-2"
            :disabled="userStore.isFree"
          />
          <v-btn
            color="primary"
            :loading="saving"
            class="mt-3"
            :disabled="userStore.isFree"
            @click="saveSettings"
          >
            {{ t('settings.saveButton') }}
          </v-btn>
        </v-card-text>
      </v-card>
    </main>

    <PaymentDialog
      v-model="showPaymentDialog"
      @paid="onPaid"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { useThemeStore } from '@/stores/useThemeStore'
import type { ThemeMode } from '@/stores/useThemeStore'
import { useSettingsStore, OUTPUT_LANGUAGE_OPTIONS } from '@/stores/useSettingsStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useUserStore } from '@/stores/useUserStore'
import DesktopBackendSettingsPanel from '@/components/DesktopBackendSettingsPanel.vue'
import PaymentDialog from '@/components/PaymentDialog.vue'
import { isTauriApp } from '@/utils/isTauriApp'

const { t, locale: i18nLocale } = useI18n()
const router = useRouter()
const routeLocale = useRouteLocale()
const themeStore = useThemeStore()
const settingsStore = useSettingsStore()
const snackbar = useSnackbarStore()
const userStore = useUserStore()
const languageOptions = OUTPUT_LANGUAGE_OPTIONS
const saving = ref(false)
const showDesktopBackend = isTauriApp()

function goHome() {
  router.push({ name: 'Home', params: { locale: routeLocale.value } })
}

const themeSelectItems = computed(() => [
  { title: t('settings.themeLight'), value: 'light' as const },
  { title: t('settings.themeDark'), value: 'dark' as const },
])
const showPaymentDialog = ref(false)

const llmProviderItems = [
  { title: 'Qwen', value: 'dashscope' },
  { title: 'Google Gemini', value: 'google' },
]

const llmModelsQwen = [
  { title: 'Qwen3', value: 'Qwen3' },
  { title: 'Qwen3-VL', value: 'Qwen3-VL' },
  { title: 'Qwen3-Image', value: 'Qwen3-Image' },
  { title: 'Qwen3.5', value: 'Qwen3.5' },
]

const llmModelsGemini = [
  { title: 'Gemini 2.5 Pro', value: 'Gemini 2.5 Pro' },
  { title: 'Gemini 2.5 Flash', value: 'Gemini 2.5 Flash' },
  { title: 'Gemini 2.5 Flash-Lite', value: 'Gemini 2.5 Flash-Lite' },
  { title: 'Nano Banana', value: 'Nano Banana' },
]

const llmModelItems = computed(() => {
  return settingsStore.settings.llmProvider === 'google'
    ? llmModelsGemini
    : llmModelsQwen
})

function normalizeLlmSettingsAfterLoad() {
  const legacyProviders = new Set([
    'openai',
    'anthropic',
    'azure',
    'ollama',
  ])
  const p = settingsStore.settings.llmProvider
  if (legacyProviders.has(p) || (p !== 'google' && p !== 'dashscope')) {
    settingsStore.settings.llmProvider = 'dashscope'
  }
  const items =
    settingsStore.settings.llmProvider === 'google'
      ? llmModelsGemini
      : llmModelsQwen
  if (!items.some((i) => i.value === settingsStore.settings.llmModel)) {
    settingsStore.settings.llmModel = items[0].value
  }
}

watch(
  () => settingsStore.settings.llmProvider,
  (provider) => {
    const items = provider === 'google' ? llmModelsGemini : llmModelsQwen
    if (!items.some((i) => i.value === settingsStore.settings.llmModel)) {
      settingsStore.settings.llmModel = items[0].value
    }
  },
)

function formatExpiryDate(dateStr: string) {
  const d = new Date(dateStr)
  const tag = i18nLocale.value === 'zh-CN' ? 'zh-CN' : 'en-US'
  return d.toLocaleDateString(tag, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

async function onThemeChange(value: ThemeMode) {
  await settingsStore.setTheme(value)
  snackbar.success(
    value === 'dark' ? t('settings.themeDarkOk') : t('settings.themeLightOk'),
  )
}

async function onOutputLanguageChange(value: string) {
  await settingsStore.setOutputLanguage(value)
  snackbar.success(t('settings.outputLangOk', { lang: value }))
}

function onPaid() {
  snackbar.success(t('settings.paidOk'))
}

onMounted(async () => {
  await settingsStore.fetchSettings()
  normalizeLlmSettingsAfterLoad()
})

const saveSettings = async () => {
  saving.value = true
  try {
    await settingsStore.saveAllSettings()
    snackbar.success(t('settings.savedOk'))
    goHome()
  } catch {
    snackbar.error(t('settings.saveFailed'))
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 24px;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.settings-header h1 {
  font-size: 20px;
  font-weight: 600;
}

.settings-main {
  max-width: 640px;
  margin: 32px auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.settings-card h3 {
  font-size: 16px;
  font-weight: 600;
}

.form-label-with-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.form-label-desc {
  font-size: 12px;
  opacity: 0.8;
  font-weight: 400;
}

.plan-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.plan-label {
  font-size: 14px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.plan-value {
  font-size: 14px;
  font-weight: 500;
}
</style>
