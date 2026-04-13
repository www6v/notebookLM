
<template>

  <v-dialog
    v-model="dialogOpen"
    class="infographic-preview-dialog"
    max-width="960"
    scrollable
  >
    <v-card
      v-if="infographic"
      class="infographic-preview-card"
      rounded="xl"
    >
      <v-card-title class="infographic-preview-header pa-4 pb-2">
        <div class="infographic-preview-header-text">
          <div class="infographic-preview-title">
            {{ displayTitle }}
          </div>
          <div class="infographic-preview-subtitle text-medium-emphasis">
            基于 {{ sourceCountLabel }} 个来源
          </div>
        </div>
        <div class="infographic-preview-header-actions">
          <v-btn
            variant="text"
            size="small"
            class="text-none"
            @click="openImageInNewTab"
          >
            <v-icon
              :size="18"
              class="mr-1"
            >
              mdi-open-in-new
            </v-icon>
            新窗口打开
          </v-btn>
          <v-menu
            v-model="downloadMenuOpen"
            location="bottom"
          >
            <template #activator="{ props: menuActivatorProps }">
              <v-btn
                v-bind="menuActivatorProps"
                icon
                variant="text"
                size="small"
                aria-label="更多"
                :disabled="!infographic?.file_path || downloadBusy"
              >
                <v-icon :size="20">mdi-dots-horizontal</v-icon>
              </v-btn>
            </template>
            <v-list
              density="compact"
              class="infographic-preview-download-menu py-1"
              min-width="200"
            >
              <v-list-item
                :disabled="downloadBusy"
                @click="downloadInfographicPng"
              >
                <template #prepend>
                  <v-icon
                    :size="20"
                    class="mr-2"
                  >
                    mdi-download
                  </v-icon>
                </template>
                <v-list-item-title>下载</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          <v-btn
            icon
            variant="text"
            size="small"
            aria-label="关闭"
            @click="closeDialog"
          >
            <v-icon :size="20">mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-title>
      <v-divider />
      <v-card-text class="infographic-preview-body pa-0">
        <div
          v-if="loading"
          class="infographic-preview-loading"
        >
          <v-progress-circular
            indeterminate
            color="primary"
            :size="48"
          />
          <span class="text-medium-emphasis mt-3">正在加载信息图…</span>
        </div>
        <div
          v-else-if="errorMessage"
          class="infographic-preview-error"
        >
          {{ errorMessage }}
        </div>
        <div
          v-else
          class="infographic-preview-main"
        >
          <div class="infographic-preview-main-scroll">
            <div
              class="infographic-preview-main-inner"
              :style="mainTransformStyle"
            >
              <img
                v-if="imageUrl"
                :src="imageUrl"
                :alt="displayTitle"
                class="infographic-preview-img"
              />
            </div>
          </div>
          <div class="infographic-preview-zoom">
            <v-btn
              icon
              size="x-small"
              variant="flat"
              class="infographic-preview-zoom-btn"
              aria-label="放大"
              @click="zoomIn"
            >
              <v-icon :size="16">mdi-plus</v-icon>
            </v-btn>
            <v-btn
              icon
              size="x-small"
              variant="flat"
              class="infographic-preview-zoom-btn"
              aria-label="缩小"
              @click="zoomOut"
            >
              <v-icon :size="16">mdi-minus</v-icon>
            </v-btn>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>

</template>

<script setup lang="ts">
import { computed, ref, watch, withDefaults } from 'vue'
import { shareReadApi } from '@/api/shareRead'
import type { InfographicData } from '@/api/studio'
import { studioApi } from '@/api/studio'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

defineOptions({
  name: 'InfographicPreviewDialog',
})

const CLOSE_RESET_MS = 350

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    infographic: InfographicData | null
    shareToken?: string | null
  }>(),
  { shareToken: null },
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  afterLeave: []
}>()

const snackbar = useSnackbarStore()

const dialogOpen = computed({
  get: () => props.modelValue,
  set: (v: boolean) => {
    emit('update:modelValue', v)
  },
})

const loading = ref(false)
const errorMessage = ref<string | null>(null)
const imageUrl = ref<string | null>(null)
const zoomLevel = ref(1)
const downloadMenuOpen = ref(false)
const downloadBusy = ref(false)

let loadGeneration = 0
let closeResetTimer: ReturnType<typeof setTimeout> | null = null

const displayTitle = computed(() => {
  if (!props.infographic) {
    return ''
  }
  return (
    props.infographic.suggested_filename
    || props.infographic.title
    || '信息图'
  )
})

const sourceCountLabel = computed(() => {
  const n = props.infographic?.source_count
  if (n != null && n > 0) {
    return n
  }
  return 1
})

const mainTransformStyle = computed(() => ({
  transform: `scale(${zoomLevel.value})`,
}))

function closeDialog() {
  emit('update:modelValue', false)
}

function resetState() {
  loadGeneration += 1
  imageUrl.value = null
  errorMessage.value = null
  loading.value = false
  zoomLevel.value = 1
  downloadMenuOpen.value = false
  downloadBusy.value = false
}

function zoomIn() {
  zoomLevel.value = Math.min(3, Math.round((zoomLevel.value + 0.2) * 10) / 10)
}

function zoomOut() {
  zoomLevel.value = Math.max(0.5, Math.round((zoomLevel.value - 0.2) * 10) / 10)
}

async function loadImage() {
  if (!props.infographic?.file_path) {
    errorMessage.value = '该信息图的图片尚未就绪'
    return
  }
  const gen = ++loadGeneration
  loading.value = true
  errorMessage.value = null
  imageUrl.value = null
  try {
    const tok = props.shareToken
    const { url } = tok
      ? await shareReadApi.getInfographicImageUrl(tok, props.infographic.id)
      : await studioApi.getInfographicImageUrl(props.infographic.id)
    if (gen !== loadGeneration) {
      return
    }
    imageUrl.value = url
  } catch {
    if (gen === loadGeneration) {
      errorMessage.value = '无法加载信息图，请稍后重试或改用「新窗口打开」。'
    }
  } finally {
    if (gen === loadGeneration) {
      loading.value = false
    }
  }
}

async function openImageInNewTab() {
  if (!props.infographic?.file_path) {
    return
  }
  try {
    const tok = props.shareToken
    const { url } = tok
      ? await shareReadApi.getInfographicImageUrl(tok, props.infographic.id)
      : await studioApi.getInfographicImageUrl(props.infographic.id)
    window.open(url, '_blank', 'noopener,noreferrer')
  } catch {
    errorMessage.value = '获取图片链接失败'
  }
}

function suggestedDownloadBasename(): string {
  const info = props.infographic
  if (!info) {
    return 'infographic'
  }
  let base = (info.suggested_filename || info.title || 'infographic').replace(
    /["\\/:*?<>|]/g,
    '_'
  )
  const lower = base.toLowerCase()
  if (lower.endsWith('.png')) {
    base = base.slice(0, -4)
  }
  return base.trim() || 'infographic'
}

function triggerBlobDownload(blob: Blob, filename: string) {
  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = filename
  anchor.rel = 'noopener'
  anchor.click()
  window.setTimeout(() => {
    URL.revokeObjectURL(objectUrl)
  }, 120000)
}

async function downloadInfographicPng() {
  if (!props.infographic?.file_path) {
    return
  }
  downloadBusy.value = true
  try {
    const tok = props.shareToken
    const buf = tok
      ? await shareReadApi.getInfographicImageArrayBuffer(
        tok,
        props.infographic.id,
      )
      : await studioApi.getInfographicImageArrayBuffer(
        props.infographic.id,
      )
    const blob = new Blob([buf], { type: 'image/png' })
    triggerBlobDownload(blob, `${suggestedDownloadBasename()}.png`)
    downloadMenuOpen.value = false
  } catch {
    snackbar.error('下载图片失败')
  } finally {
    downloadBusy.value = false
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (closeResetTimer != null) {
      clearTimeout(closeResetTimer)
      closeResetTimer = null
    }
    if (open && props.infographic) {
      void loadImage()
      return
    }
    if (!open) {
      closeResetTimer = setTimeout(() => {
        closeResetTimer = null
        if (!props.modelValue) {
          resetState()
          emit('afterLeave')
        }
      }, CLOSE_RESET_MS)
    }
  }
)

watch(
  () => props.infographic?.id,
  () => {
    if (props.modelValue && props.infographic) {
      void loadImage()
    }
  }
)

</script>

<style scoped lang="scss">
.infographic-preview-dialog :deep(.v-overlay__content) {
  width: min(96vw, 960px);
  max-width: min(96vw, 960px);
}

.infographic-preview-card {
  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
}

.infographic-preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.infographic-preview-header-text {
  min-width: 0;
}

.infographic-preview-title {
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.3;
  word-break: break-word;
}

.infographic-preview-subtitle {
  font-size: 0.8rem;
  margin-top: 4px;
}

.infographic-preview-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.infographic-preview-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.infographic-preview-loading,
.infographic-preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  padding: 32px;
}

.infographic-preview-error {
  color: rgb(var(--v-theme-error));
}

.infographic-preview-main {
  position: relative;
  flex: 1;
  min-height: min(72vh, 720px);
  max-height: min(72vh, 720px);
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 0 0 12px 12px;
}

.infographic-preview-main-scroll {
  position: absolute;
  inset: 0;
  overflow: auto;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 16px;
}

.infographic-preview-main-inner {
  transform-origin: top center;
  transition: transform 0.15s ease-out;
}

.infographic-preview-img {
  display: block;
  max-width: 100%;
  width: auto;
  height: auto;
  border-radius: 8px;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
  background: #fff;
}

.infographic-preview-zoom {
  position: absolute;
  right: 16px;
  bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}

.infographic-preview-zoom-btn {
  min-width: 28px !important;
  width: 28px;
  height: 28px;
}
</style>
