<template>
  <div class="source-panel">
    <v-btn
      v-if="!readOnly"
      variant="outlined"
      class="add-source-btn"
      @click="$emit('addSource')"
    >
      <v-icon :size="16">mdi-plus</v-icon>
      <span>{{ t('source.addSource') }}</span>
    </v-btn>

    <DeepResearchCard
      :notebook-id="notebookId"
      :read-only="readOnly"
      :share-token="shareToken"
      @view-report="onDeepResearchViewReport"
      @delete-report="onDeepResearchDeleteReport"
      @import-report="onDeepResearchImportReport"
    />

    <div v-if="sourceStore.loading" class="panel-loading">
      <v-skeleton-loader
        type="list-item-three-line"
        class="mb-2"
      />
      <v-skeleton-loader
        type="list-item-three-line"
        class="mb-2"
      />
      <v-skeleton-loader
        type="list-item-three-line"
        class="mb-2"
      />
      <v-skeleton-loader type="list-item-three-line" />
    </div>

    <div v-else-if="sourceStore.sources.length === 0" class="panel-empty">
      <p class="panel-empty-desc">{{ t('source.emptyDesc') }}</p>
    </div>

    <div v-else class="source-list-wrapper">
      <div
        v-if="!readOnly"
        class="select-all-row"
        @click="handleToggleAll"
      >
        <span class="select-all-label">{{ t('source.selectAll') }}</span>
        <span class="select-all-spacer" />
        <v-checkbox
          :model-value="allActive"
          :indeterminate="someActive"
          density="compact"
          hide-details
          @click.stop
          @update:model-value="handleToggleAll"
        />
      </div>
      <div class="source-list">
        <div
          v-for="source of sourceStore.sources"
          :key="source.id"
          class="source-item"
          :class="{ 'source-item-uploading': source.status === 'uploading' }"
        >
          <template v-if="source.status === 'uploading'">
            <div class="source-info">
              <v-icon
                size="16"
                class="source-type-icon"
              >
                {{ sourceTypeIcon(source.type) }}
              </v-icon>
              <span
                class="source-title"
                :title="source.title"
              >
                {{ source.title }}
              </span>
            </div>
            <v-progress-circular
              indeterminate
              :size="18"
              :width="2"
              color="primary"
            />
          </template>
          <template v-else>
            <div
              class="source-info"
              :class="{ inactive: !source.is_active }"
              @dblclick="handleViewContent(source)"
            >
              <v-icon
                size="16"
                class="source-type-icon"
              >
                {{ sourceTypeIcon(source.type) }}
              </v-icon>
              <span
                class="source-title"
                :title="source.title"
              >
                {{ source.title }}
              </span>
            </div>
            <v-chip
              v-if="source.status === 'pending'"
              size="small"
              color="warning"
              variant="tonal"
            >
              pending
            </v-chip>
            <v-chip
              v-else-if="source.status === 'processing'"
              size="small"
              color="info"
              variant="tonal"
            >
              processing
            </v-chip>
            <v-chip
              v-else-if="source.status === 'error'"
              size="small"
              color="error"
              variant="tonal"
            >
              error
            </v-chip>
            <v-btn
              v-if="!readOnly"
              icon
              variant="text"
              size="small"
              class="source-delete"
              @click="handleDelete(source.id)"
            >
              <v-icon size="14">mdi-delete</v-icon>
            </v-btn>
            <v-checkbox
              v-if="!readOnly"
              :model-value="source.is_active"
              density="compact"
              hide-details
              @update:model-value="(val: boolean | null) => sourceStore.toggleSource(source.id, val === true)"
            />
          </template>
        </div>
      </div>
    </div>

    <v-dialog
      v-model="showContentDialog"
      max-width="700"
      @after-leave="onContentDialogClosed()"
    >
      <v-card>
        <v-card-title>{{ sourceStore.currentContent?.title || 'Source Content' }}</v-card-title>
        <v-card-text>
          <div v-if="sourceStore.contentLoading" class="content-loading">
            <v-skeleton-loader
              type="paragraph"
              class="mb-2"
            />
            <v-skeleton-loader
              type="paragraph"
              class="mb-2"
            />
            <v-skeleton-loader type="paragraph" />
          </div>
          <div v-else-if="sourceStore.currentContent" class="content-viewer">
            <div
              v-if="sourceStore.currentContent.file_url"
              class="content-image"
            >
              <div
                v-if="imageLoading"
                class="image-loading"
              >
                <v-icon
                  size="32"
                  class="rotating"
                >
                  mdi-cached
                </v-icon>
              </div>
              <img
                v-else-if="imageUrl"
                :src="imageUrl"
                :alt="sourceStore.currentContent.title"
                decoding="async"
                @error="onImageError"
              >
              <v-alert
                v-else-if="imageError"
                type="warning"
                variant="tonal"
              >
                Failed to load image
              </v-alert>
            </div>
            <div
              v-if="sourceStore.currentContent.raw_content"
              ref="contentTextRef"
              class="content-text"
              :class="{ 'content-text-with-image': Boolean(sourceStore.currentContent.file_url) }"
              v-html="highlightedContent"
            />
            <v-alert
              v-if="!sourceStore.currentContent.file_url && !sourceStore.currentContent.raw_content"
              type="info"
              variant="tonal"
            >
              No content available for this source
            </v-alert>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, withDefaults } from 'vue'
import { useI18n } from 'vue-i18n'
import { useSourceStore } from '@/stores/useSourceStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useConfirmStore } from '@/stores/useConfirmStore'
import { shareReadApi } from '@/api/shareRead'
import { sourceApi, type Source } from '@/api/source'
import { importDeepResearchAsSource } from '@/api/deepResearch'
import DeepResearchCard from './DeepResearchCard.vue'
import type { DeepResearchReport } from './deepResearchTypes'

const props = withDefaults(
  defineProps<{
    notebookId: string
    readOnly?: boolean
    shareToken?: string | null
  }>(),
  { readOnly: false, shareToken: null },
)
defineEmits<{ addSource: [] }>()

const { t } = useI18n()
const sourceStore = useSourceStore()
const snackbar = useSnackbarStore()
const confirmStore = useConfirmStore()

const toggleableSources = computed(() =>
  sourceStore.sources.filter((s) => s.status !== 'uploading')
)
const allActive = computed(() =>
  toggleableSources.value.length > 0 && toggleableSources.value.every((s) => s.is_active)
)
const someActive = computed(() =>
  !allActive.value && toggleableSources.value.some((s) => s.is_active)
)

const handleToggleAll = () => {
  if (props.readOnly) {
    return
  }
  sourceStore.toggleAllSources(!allActive.value)
}

const showContentDialog = ref(false)
const imageUrl = ref<string | null>(null)
const imageLoading = ref(false)
const imageError = ref(false)
const currentContentId = ref<string | null>(null)
const contentTextRef = ref<HTMLElement>()

function sourceTypeIcon(type: string) {
  if (type === 'pdf') return 'mdi-file-document'
  if (type === 'web') return 'mdi-link'
  if (type === 'youtube') return 'mdi-play'
  if (type === 'bilibili') return 'mdi-television-play'
  if (type === 'csv') return 'mdi-file-delimited'
  if (type === 'pptx') return 'mdi-file-powerpoint'
  if (type === 'image') return 'mdi-image'
  if (type === 'audio') return 'mdi-music-note'
  if (type === 'video') return 'mdi-video'
  return 'mdi-file-document'
}

watch(() => sourceStore.showContentViewer, (val) => {
  if (val) {
    showContentDialog.value = true
    sourceStore.showContentViewer = false
    nextTick(() => scrollToHighlight())
  }
})

const highlightedContent = computed(() => {
  const raw = sourceStore.currentContent?.raw_content
  if (!raw) return ''

  const highlight = sourceStore.highlightRequest
  if (!highlight?.content) {
    return `<pre>${escapeHtml(raw)}</pre>`
  }

  const searchText = highlight.content.trim().substring(0, 100)
  const idx = raw.indexOf(searchText)
  if (idx === -1) {
    return `<pre>${escapeHtml(raw)}</pre>`
  }

  const before = escapeHtml(raw.substring(0, idx))
  const match = escapeHtml(raw.substring(idx, idx + highlight.content.length))
  const after = escapeHtml(raw.substring(idx + highlight.content.length))

  return `<pre>${before}<mark class="citation-highlight" id="citation-highlight-target">${match}</mark>${after}</pre>`
})

const escapeHtml = (text: string) => {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

const scrollToHighlight = () => {
  nextTick(() => {
    const target = document.getElementById('citation-highlight-target')
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  })
}

function clearImageUrl() {
  if (imageUrl.value?.startsWith('blob:')) {
    URL.revokeObjectURL(imageUrl.value)
  }
  imageUrl.value = null
  imageError.value = false
}

function onContentDialogClosed() {
  clearImageUrl()
  currentContentId.value = null
  sourceStore.clearContent()
  sourceStore.clearHighlight()
}

async function onImageError() {
  if (!currentContentId.value) return
  if (imageUrl.value?.startsWith('blob:')) return
  imageLoading.value = true
  try {
    const tok = props.shareToken
    const blob = tok
      ? await shareReadApi.getFileStream(tok, currentContentId.value)
      : await sourceApi.getFileStream(currentContentId.value)
    if (imageUrl.value?.startsWith('blob:')) return
    imageUrl.value = URL.createObjectURL(blob)
    imageError.value = false
  } catch {
    imageError.value = true
  } finally {
    imageLoading.value = false
  }
}

async function loadImageIfNeeded(content: { id: string; file_url: string | null } | null) {
  clearImageUrl()
  if (!content?.file_url) {
    currentContentId.value = null
    return
  }
  currentContentId.value = content.id
  imageLoading.value = true
  imageError.value = false
  try {
    const tok = props.shareToken
    const { url } = tok
      ? await shareReadApi.getFileUrl(tok, content.id)
      : await sourceApi.getFileUrl(content.id)
    imageUrl.value = url
  } catch {
    imageError.value = true
  } finally {
    imageLoading.value = false
  }
}

const handleDelete = async (sourceId: string) => {
  if (props.readOnly) {
    return
  }
  try {
    const ok = await confirmStore.confirm({
      title: 'Remove Source',
      text: 'Remove this source?',
      confirmButtonText: 'Remove',
      cancelButtonText: 'Cancel',
    })
    if (!ok) return
    await sourceStore.removeSource(sourceId)
    snackbar.success('Source removed')
  } catch {
    // cancelled
  }
}

const handleViewContent = async (source: Source) => {
  showContentDialog.value = true
  try {
    const content = await sourceStore.getContent(source.id)
    await loadImageIfNeeded(content ?? null)
  } catch {
    snackbar.error('Failed to load source content')
  }
}

function onDeepResearchViewReport(_report: DeepResearchReport) {
  // 查看在 DeepResearchCard 内弹窗处理
}

function onDeepResearchDeleteReport(_report: DeepResearchReport) {
  snackbar.success(t('source.deleteReportOk'))
}

async function onDeepResearchImportReport(report: DeepResearchReport) {
  try {
    await importDeepResearchAsSource(props.notebookId, report.id)
    await sourceStore.fetchSources(props.notebookId)
    snackbar.success(t('source.importOk'))
  } catch (err) {
    const detail = (err as { response?: { data?: { detail?: string } } })?.response
      ?.data?.detail
    snackbar.error(
      typeof detail === 'string' ? detail : t('source.importFail')
    )
  }
}
</script>

<style scoped>
.source-panel {
  padding: 8px;
}

.add-source-btn {
  margin-bottom: 12px;
  width: 100%;
}

.panel-loading,
.panel-empty {
  padding: 20px 12px;
  text-align: center;
  color: var(--text-secondary);
  font-size: 13px;
}

.panel-empty-desc {
  margin: 0;
}

.panel-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 120px;
}

.source-list-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.select-all-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.select-all-row:hover {
  background: #f1f3f4;
}

.select-all-label {
  flex: 1;
  font-size: 13px;
  color: #1a73e8;
  user-select: none;
}

.select-all-spacer {
  width: 28px;
  flex-shrink: 0;
}

.source-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.source-item:hover {
  background: #f1f3f4;
}

.source-item-uploading {
  opacity: 0.7;
  pointer-events: none;
}

.source-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  cursor: pointer;
}

.source-info.inactive {
  opacity: 0.5;
}

.source-type-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
}

.source-title {
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-delete {
  opacity: 0;
  transition: opacity 0.15s;
}

.source-item:hover .source-delete {
  opacity: 1;
}

.content-loading {
  padding: 16px 0;
}

.content-viewer {
  max-height: 70vh;
  overflow-y: auto;
}

.content-image {
  display: flex;
  justify-content: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8eaed;
}

.image-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 120px;
  color: var(--primary-color);
}

.rotating {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.content-image img {
  max-width: 100%;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
}

.content-text {
  background: #f8f9fa;
  border: 1px solid #e8eaed;
  border-radius: 8px;
  padding: 16px;
}

.content-text-with-image {
  margin-top: 12px;
  max-height: 35vh;
  overflow-y: auto;
}

.content-text :deep(pre) {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #333;
}

.content-text :deep(.citation-highlight) {
  background: #fff3cd;
  border-radius: 3px;
  padding: 2px 0;
  border-bottom: 2px solid #ffc107;
  animation: highlightPulse 2s ease-in-out;
}

@keyframes highlightPulse {
  0%, 100% { background: #fff3cd; }
  50% { background: #ffe082; }
}
</style>
