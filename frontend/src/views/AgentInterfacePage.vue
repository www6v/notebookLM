<template>
  <div class="agent-page">
    <header class="agent-header">
      <v-btn
        icon
        variant="text"
        :aria-label="t('common.back')"
        @click="goBack"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>
      <div class="agent-header-text">
        <h1>{{ t('agentInterface.title') }}</h1>
        <p>{{ t('agentInterface.subtitle') }}</p>
      </div>
    </header>

    <main class="agent-main">
      <section class="agent-step">
        <h2 class="step-title">
          <v-icon
            size="18"
            color="success"
            class="step-icon"
          >
            mdi-send
          </v-icon>
          {{ t('agentInterface.step1Title') }}
        </h2>
        <p class="step-hint">{{ t('agentInterface.step1Hint') }}</p>
        <v-card
          class="agent-card"
          variant="outlined"
        >
          <v-card-text>
            <pre class="install-prompt">{{ installPromptText }}</pre>
            <div class="card-actions">
              <v-btn
                color="grey-darken-4"
                :loading="copyingInstall"
                @click="copyInstallPrompt"
              >
                {{ t('agentInterface.step1Copy') }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </section>

      <section class="agent-step">
        <h2 class="step-title">
          <v-icon
            size="18"
            color="success"
            class="step-icon"
          >
            mdi-send
          </v-icon>
          {{ t('agentInterface.step2Title') }}
        </h2>

        <v-card
          v-if="loading"
          class="agent-card"
          variant="outlined"
        >
          <v-card-text class="d-flex justify-center py-8">
            <v-progress-circular
              indeterminate
              color="primary"
            />
          </v-card-text>
        </v-card>

        <v-card
          v-else-if="!status?.has_credential"
          class="agent-card"
          variant="outlined"
        >
          <v-card-text>
            <p class="empty-title">{{ t('agentInterface.emptyHint') }}</p>
            <p class="empty-desc">{{ t('agentInterface.emptyDesc') }}</p>
            <v-btn
              color="grey-darken-4"
              class="mt-4"
              :loading="creating"
              @click="onGetApiKey"
            >
              {{ t('agentInterface.getApiKey') }}
            </v-btn>
          </v-card-text>
        </v-card>

        <v-card
          v-else
          class="agent-card"
          variant="outlined"
        >
          <v-card-text>
            <div class="meta-row">
              <span class="meta-label">{{ t('agentInterface.clientId') }}</span>
              <div
                class="meta-value-row"
              >
                <code class="meta-code">{{ status.client_id }}</code>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  :aria-label="t('agentInterface.copyField')"
                  @click="copyText(status.client_id || '')"
                >
                  <v-icon size="18">mdi-content-copy</v-icon>
                </v-btn>
              </div>
            </div>
            <div
              class="meta-row"
            >
              <span class="meta-label">{{ t('agentInterface.status') }}</span>
              <span
                class="meta-value"
                :class="{ 'status-expired': status.status === 'expired' }"
              >
                {{ status.status_label }}
              </span>
            </div>
            <div
              class="meta-row"
            >
              <span class="meta-label">{{ t('agentInterface.expiresAt') }}</span>
              <span class="meta-value">{{ formatExpiry(status.expires_at) }}</span>
            </div>
            <div
              class="card-actions split-actions"
            >
              <v-btn
                variant="outlined"
                color="error"
                :loading="deleting"
                @click="showDeleteDialog = true"
              >
                {{ t('agentInterface.deleteApiKey') }}
              </v-btn>
              <v-btn
                color="grey-darken-4"
                :loading="regenerating"
                @click="onRegenerate"
              >
                {{ t('agentInterface.regenerate') }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </section>

      <p class="dev-docs">
        <a
          href="https://github.com/notebooklm/notebookLM/blob/main/skill-claw/references/api.md"
          target="_blank"
          rel="noopener noreferrer"
        >
          {{ t('agentInterface.devDocs') }}
        </a>
      </p>
    </main>

    <v-dialog
      v-model="revealDialog"
      max-width="520"
      persistent
    >
      <v-card class="reveal-dialog">
        <v-card-title class="reveal-dialog-title">
          <span>{{ t('agentInterface.revealTitle') }}</span>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="closeRevealDialog"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-alert
            type="error"
            variant="tonal"
            density="compact"
            class="reveal-alert"
          >
            {{ t('agentInterface.revealWarning') }}
          </v-alert>
          <div
            v-if="revealData"
            class="reveal-fields"
          >
            <label class="field-label">{{ t('agentInterface.apiKeyLabel') }}</label>
            <div class="field-row">
              <v-text-field
                :model-value="revealData.api_key"
                readonly
                density="compact"
                variant="outlined"
                hide-details
              />
              <v-btn
                icon
                variant="text"
                @click="copyText(revealData.api_key)"
              >
                <v-icon>mdi-content-copy</v-icon>
              </v-btn>
            </div>
            <label class="field-label">{{ t('agentInterface.clientId') }}</label>
            <div class="field-row">
              <v-text-field
                :model-value="revealData.client_id"
                readonly
                density="compact"
                variant="outlined"
                hide-details
              />
              <v-btn
                icon
                variant="text"
                @click="copyText(revealData.client_id)"
              >
                <v-icon>mdi-content-copy</v-icon>
              </v-btn>
            </div>
          </div>
        </v-card-text>
        <v-card-actions class="reveal-actions">
          <v-spacer />
          <v-btn
            color="grey-darken-4"
            @click="copyRevealAll"
          >
            {{ t('agentInterface.copyAll') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showDeleteDialog"
      max-width="400"
    >
      <v-card>
        <v-card-title class="delete-title">
          <v-icon
            color="error"
            class="mr-2"
          >
            mdi-alert-circle
          </v-icon>
          {{ t('agentInterface.deleteConfirmTitle') }}
        </v-card-title>
        <v-card-text>{{ t('agentInterface.deleteConfirmText') }}</v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDeleteDialog = false"
          >
            {{ t('agentInterface.cancel') }}
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="deleting"
            @click="onConfirmDelete"
          >
            {{ t('agentInterface.confirm') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { isAxiosError } from 'axios'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { copyTextToClipboard } from '@/utils/copyToClipboard'
import {
  createOpenApiCredential,
  deleteOpenApiCredential,
  fetchOpenApiCredentialStatus,
  regenerateOpenApiCredential,
  type OpenApiCredentialReveal,
  type OpenApiCredentialStatus,
} from '@/api/openApi'

defineOptions({ name: 'AgentInterfacePage' })

const { t } = useI18n()
const router = useRouter()
const routeLocale = useRouteLocale()
const snackbar = useSnackbarStore()

const SKILL_VERSION = '1.0.0'
const loading = ref(true)
const creating = ref(false)
const regenerating = ref(false)
const deleting = ref(false)
const copyingInstall = ref(false)
const revealDialog = ref(false)
const showDeleteDialog = ref(false)
const status = ref<OpenApiCredentialStatus | null>(null)
const revealData = ref<OpenApiCredentialReveal | null>(null)

const skillZipUrl = computed(() => {
  const base = typeof window !== 'undefined' ? window.location.origin : ''
  return `${base}/skills/notebooklm-skills-${SKILL_VERSION}.zip`
})

const agentPageUrl = computed(() => {
  const base = typeof window !== 'undefined' ? window.location.origin : ''
  return `${base}/${routeLocale.value}/agent-interface`
})

const installPromptText = computed(() => {
  return [
    '请安装 NotebookLM 技能',
    skillZipUrl.value,
    `获取 API Key：${agentPageUrl.value}`,
  ].join('\n')
})

function apiErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError(err)) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
  }
  return fallback
}

function formatExpiry(iso: string | null | undefined): string {
  if (!iso) {
    return '—'
  }
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) {
    return iso
  }
  return d.toLocaleDateString()
}

async function loadStatus() {
  loading.value = true
  try {
    status.value = await fetchOpenApiCredentialStatus()
  } catch {
    snackbar.error(t('agentInterface.loadFailed'))
    status.value = { has_credential: false }
  } finally {
    loading.value = false
  }
}

function openReveal(data: OpenApiCredentialReveal) {
  revealData.value = data
  revealDialog.value = true
}

function closeRevealDialog() {
  revealDialog.value = false
  revealData.value = null
}

function applyStatusFromReveal(data: OpenApiCredentialReveal) {
  status.value = {
    has_credential: true,
    client_id: data.client_id,
    status: data.status,
    status_label: data.status_label,
    expires_at: data.expires_at,
  }
}

async function onGetApiKey() {
  creating.value = true
  try {
    const data = await createOpenApiCredential()
    applyStatusFromReveal(data)
    openReveal(data)
    snackbar.success(t('agentInterface.createOk'))
  } catch (err) {
    snackbar.error(apiErrorMessage(err, t('agentInterface.createFailed')))
  } finally {
    creating.value = false
  }
}

async function onRegenerate() {
  regenerating.value = true
  try {
    const data = await regenerateOpenApiCredential()
    applyStatusFromReveal(data)
    openReveal(data)
    snackbar.success(t('agentInterface.regenerateOk'))
  } catch (err) {
    snackbar.error(apiErrorMessage(err, t('agentInterface.regenerateFailed')))
  } finally {
    regenerating.value = false
  }
}

async function onConfirmDelete() {
  deleting.value = true
  try {
    await deleteOpenApiCredential()
    showDeleteDialog.value = false
    status.value = { has_credential: false }
    snackbar.success(t('agentInterface.deleteOk'))
  } catch (err) {
    snackbar.error(apiErrorMessage(err, t('agentInterface.deleteFailed')))
  } finally {
    deleting.value = false
  }
}

async function copyText(text: string) {
  const ok = await copyTextToClipboard(text)
  if (ok) {
    snackbar.success(t('agentInterface.copied'))
  } else {
    snackbar.error(t('agentInterface.step1CopyFailed'))
  }
}

async function copyInstallPrompt() {
  copyingInstall.value = true
  const ok = await copyTextToClipboard(installPromptText.value)
  copyingInstall.value = false
  if (ok) {
    snackbar.success(t('agentInterface.step1Copied'))
  } else {
    snackbar.error(t('agentInterface.step1CopyFailed'))
  }
}

async function copyRevealAll() {
  if (!revealData.value) {
    return
  }
  const block = [
    `API Key: ${revealData.value.api_key}`,
    `Client ID: ${revealData.value.client_id}`,
  ].join('\n')
  await copyText(block)
}

function goBack() {
  router.push({ name: 'Settings', params: { locale: routeLocale.value } })
}

onMounted(() => {
  loadStatus()
})
</script>

<style scoped>
.agent-page {
  min-height: 100vh;
  background: var(--bg-color);
}

.agent-header {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-color);
  background: var(--surface-color);
}

.agent-header-text h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary);
}

.agent-header-text p {
  margin-top: 4px;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.agent-main {
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 20px 48px;
}

.agent-step {
  margin-bottom: 32px;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.step-hint {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.agent-card {
  border-radius: var(--radius-lg);
  background: var(--surface-color);
}

.install-prompt {
  white-space: pre-wrap;
  word-break: break-all;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--text-primary);
  margin: 0 0 16px;
  padding: 12px;
  background: var(--bg-color);
  border-radius: var(--radius);
  border: 1px solid var(--border-color);
}

.card-actions {
  display: flex;
  justify-content: flex-end;
}

.split-actions {
  gap: 12px;
  margin-top: 8px;
}

.empty-title {
  font-size: 0.9375rem;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.meta-row {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.meta-row:last-of-type {
  border-bottom: none;
}

.meta-label {
  flex: 0 0 100px;
  font-size: 0.875rem;
  color: var(--text-secondary);
}

.meta-value {
  font-size: 0.875rem;
  color: var(--text-primary);
}

.meta-value-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.meta-code {
  font-family: ui-monospace, monospace;
  font-size: 0.8125rem;
  word-break: break-all;
}

.status-expired {
  color: #d93025;
}

.dev-docs {
  text-align: center;
  font-size: 0.8125rem;
  margin-top: 24px;
}

.reveal-dialog-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.reveal-alert {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 6px;
  margin-top: 12px;
}

.field-label:first-child {
  margin-top: 0;
}

.field-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.reveal-actions {
  padding: 12px 16px 16px;
}

.delete-title {
  display: flex;
  align-items: center;
  font-size: 1rem;
}
</style>
