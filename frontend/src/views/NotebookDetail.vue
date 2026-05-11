<template>
  <div class="notebook-detail">
    <header class="nb-header">
      <div class="header-left">
        <v-btn
          icon
          variant="text"
          size="small"
          @click="goHome"
        >
          <v-icon size="18">mdi-arrow-left</v-icon>
        </v-btn>
        <div class="header-title-wrap">
          <input
            v-if="notebookStore.currentNotebook && !isSharedView"
            ref="titleInputRef"
            v-model="editingTitle"
            class="nb-title-input"
            @focus="onTitleFocus"
            @blur="onTitleBlur"
            @keydown.enter="titleInputRef?.blur()"
          >
          <h1
            v-else-if="notebookStore.currentNotebook && isSharedView"
            class="nb-title"
          >
            {{ notebookStore.currentNotebook.title }}
          </h1>
          <h1
            v-else
            class="nb-title"
          >
            {{ t('notebook.loading') }}
          </h1>
          <span
            v-if="
              !isSharedView
                && notebookStore.currentNotebook?.share_enabled
            "
            class="nb-shared-badge"
          >
            <v-icon
              class="nb-shared-badge-icon"
              size="16"
            >
              mdi-link-variant
            </v-icon>
            {{ t('notebook.sharedBadge') }}
          </span>
        </div>
      </div>
      <div class="header-right">
        <v-btn
          v-if="!isSharedView && userStore.user"
          variant="text"
          size="small"
          class="header-share-btn"
          @click="openShareDialog"
        >
          <v-icon size="18">mdi-share-variant-outline</v-icon>
          <span class="header-share-label">{{ t('notebook.shareNotebook') }}</span>
        </v-btn>
        <div
          v-if="!isSharedView && userStore.user && notebookStore.currentNotebook"
          class="header-discover-wrap"
        >
          <v-switch
            :model-value="discoverListed"
            hide-details
            density="compact"
            color="primary"
            inset
            :disabled="discoverPublishBusy"
            :label="t('notebook.discoverPublishLabel')"
            @update:model-value="onToggleDiscoverListed"
          />
        </div>
        <v-btn
          v-if="!isSharedView"
          icon
          variant="text"
          size="small"
          @click="goSettings"
        >
          <v-icon size="18">mdi-cog</v-icon>
        </v-btn>
        <div
          v-if="!isSharedView && userStore.user"
          class="header-username"
          :title="displayName"
        >
          {{ displayName }}
        </div>
      </div>
    </header>

    <!-- Three-panel layout -->
    <div class="nb-panels" :class="{ 'is-resizing': isResizing }">
      <!-- Left: Sources Panel -->
      <aside
        class="panel panel-sources"
        :class="{ collapsed: sourcesCollapsed }"
        :style="sourcesCollapsed ? {} : { width: sourcesWidth + 'px' }"
      >
        <div class="panel-header">
          <h3>{{ t('notebook.sources') }}</h3>
        </div>
        <div v-if="!sourcesCollapsed" class="panel-body">
          <SourcePanel
            :notebook-id="notebookId"
            :read-only="isSharedView"
            :share-token="shareTokenParam"
            @add-source="showAddSource = true"
          />
        </div>
      </aside>

      <!-- Resizer: Left | Center -->
      <div
        class="panel-resizer"
        @mousedown="startResize('left', $event)"
      />

      <!-- Center: Chat Panel -->
      <main class="panel panel-chat">
        <ChatPanel
          :notebook-id="notebookId"
          :read-only="isSharedView"
        />
      </main>

      <!-- Resizer: Center | Right -->
      <div
        class="panel-resizer"
        @mousedown="startResize('right', $event)"
      />

      <!-- Right: Studio Panel -->
      <aside
        class="panel panel-studio"
        :class="{ collapsed: studioCollapsed }"
        :style="studioCollapsed ? {} : { width: studioWidth + 'px' }"
      >
        <div class="panel-header">
          <h3>Studio</h3>
        </div>
        <div v-if="!studioCollapsed" class="panel-body">
          <StudioPanel
            :notebook-id="notebookId"
            :read-only="isSharedView"
            :share-token="shareTokenParam"
          />
        </div>
      </aside>
    </div>

    <v-dialog
      v-model="showAddSource"
      max-width="624"
      persistent
      @after-leave="onAddSourceDialogClosed"
    >
      <v-card>
        <v-card-title>{{ t('notebook.addSourceTitle') }}</v-card-title>
        <v-card-text>
          <div v-if="addSourceStep === 'choose'" class="add-resource-main">
            <input
              ref="fileInputRef"
              type="file"
              class="d-none"
              :accept="uploadAccept"
              @change="onFileInputChange"
            >
            <v-card
              variant="outlined"
              class="add-resource-drop-zone"
              :class="{ 'drop-zone-active': dragOver, 'drop-zone-uploading': addingSource }"
              @click="triggerUploadClick"
              @dragover.prevent="dragOver = true"
              @dragleave="dragOver = false"
              @drop.prevent="onDrop"
            >
              <template v-if="addingSource">
                <v-progress-circular
                  indeterminate
                  color="primary"
                  :size="32"
                  :width="3"
                />
                <div class="add-resource-drop-text">{{ t('notebook.uploadBusy') }}</div>
              </template>
              <template v-else>
                <div class="add-resource-drop-text">
                  {{ dragOver ? t('notebook.dropRelease') : t('notebook.dropOrDrag') }}
                </div>
                <div class="add-resource-types">
                  <template
                    v-for="(item, index) of supportedFileTypeHints"
                    :key="item.label"
                  >
                    <span
                      class="add-resource-type-chip"
                      :title="item.extensions"
                    >
                      {{ item.label }}
                    </span>
                    <span v-if="index < supportedFileTypeHints.length - 1">、</span>
                  </template>
                  <span>{{ t('notebook.fileTypesSuffix') }}</span>
                </div>
              </template>
              <div v-if="!addingSource" class="add-resource-actions">
                <v-btn
                  variant="text"
                  class="add-resource-action-btn"
                  @click.stop="triggerUploadClick"
                >
                  <v-icon :size="20">mdi-upload</v-icon>
                  <span>{{ t('notebook.uploadFile') }}</span>
                </v-btn>
                <v-btn
                  variant="text"
                  class="add-resource-action-btn"
                  @click.stop="addSourceStep = 'url'"
                >
                  <v-icon :size="20">mdi-link</v-icon>
                  <span>{{ t('notebook.website') }}</span>
                </v-btn>
                <v-btn
                  variant="text"
                  class="add-resource-action-btn"
                  @click.stop="onCloudDriveClick"
                >
                  <v-icon :size="20">mdi-cloud-upload</v-icon>
                  <span>{{ t('notebook.cloudDrive') }}</span>
                </v-btn>
                <v-btn
                  variant="text"
                  class="add-resource-action-btn"
                  @click.stop="addSourceStep = 'paste'"
                >
                  <v-icon :size="20">mdi-content-copy</v-icon>
                  <span>{{ t('notebook.copiedText') }}</span>
                </v-btn>
              </div>
            </v-card>
          </div>
          <div v-else-if="addSourceStep === 'url'" class="add-resource-form">
            <v-btn
              variant="text"
              class="add-resource-back mb-3"
              @click="addSourceStep = 'choose'"
            >
              <v-icon>mdi-arrow-left</v-icon>
              {{ t('common.back') }}
            </v-btn>
            <v-text-field
              v-model="sourceUrl"
              label="URL"
              :placeholder="t('notebook.urlPlaceholder')"
            />
            <v-select
              v-model="sourceType"
              :label="t('notebook.typeLabel')"
              :items="sourceTypeSelectItems"
              item-title="title"
              item-value="value"
              class="mt-2"
            />
          </div>
          <div v-else-if="addSourceStep === 'paste'" class="add-resource-form">
            <v-btn
              variant="text"
              class="add-resource-back mb-3"
              @click="addSourceStep = 'choose'"
            >
              <v-icon>mdi-arrow-left</v-icon>
              {{ t('common.back') }}
            </v-btn>
            <v-textarea
              v-model="pastedText"
              :label="t('notebook.pasteLabel')"
              :placeholder="t('notebook.pastePlaceholder')"
              rows="6"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <template v-if="addSourceStep === 'choose'">
            <v-btn
              variant="text"
              @click="showAddSource = false"
            >
              {{ t('common.cancel') }}
            </v-btn>
            <v-btn
              color="primary"
              :loading="addingSource"
              :disabled="!selectedFile"
              @click="handleAddSourceFile"
            >
              {{ t('notebook.addSource') }}
            </v-btn>
          </template>
          <template v-else-if="addSourceStep === 'url'">
            <v-btn
              variant="text"
              @click="addSourceStep = 'choose'"
            >
              {{ t('common.cancel') }}
            </v-btn>
            <v-btn
              color="primary"
              :loading="addingSource"
              :disabled="!sourceUrl.trim()"
              @click="handleAddSourceUrl"
            >
              {{ t('notebook.addSource') }}
            </v-btn>
          </template>
          <template v-else>
            <v-btn
              variant="text"
              @click="addSourceStep = 'choose'"
            >
              {{ t('common.cancel') }}
            </v-btn>
            <v-btn
              color="primary"
              :loading="addingSource"
              :disabled="!pastedText.trim()"
              @click="handleAddSourcePaste"
            >
              {{ t('notebook.addSource') }}
            </v-btn>
          </template>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog
      v-model="showShareDialog"
      max-width="520"
    >
      <v-card>
        <v-card-title>{{ t('notebook.shareDialogTitle') }}</v-card-title>
        <v-card-text>
          <p class="share-dialog-desc">
            {{ t('notebook.shareDialogDesc') }}
          </p>
          <v-text-field
            v-if="resolvedShareUrl"
            :model-value="resolvedShareUrl"
            readonly
            density="comfortable"
            variant="outlined"
            class="mt-2"
          />
        </v-card-text>
        <v-card-actions>
          <v-btn
            v-if="notebookStore.currentNotebook?.share_enabled"
            color="error"
            variant="text"
            :loading="shareActionBusy"
            @click="onRevokeShare"
          >
            {{ t('notebook.shareStop') }}
          </v-btn>
          <v-spacer />
          <v-btn
            v-if="notebookStore.currentNotebook?.share_enabled"
            variant="text"
            :loading="shareActionBusy"
            @click="onRegenerateShare"
          >
            {{ t('notebook.shareRegenerate') }}
          </v-btn>
          <v-btn
            color="primary"
            :loading="shareActionBusy"
            @click="onCopyShareLink"
          >
            {{ t('notebook.shareCopyLink') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { notebookApi } from '@/api/notebook'
import { useNotebookStore } from '@/stores/useNotebookStore'
import { useSourceStore } from '@/stores/useSourceStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { useStudioStore } from '@/stores/useStudioStore'
import { useUserStore } from '@/stores/useUserStore'
import SourcePanel from '@/components/source/SourcePanel.vue'
import ChatPanel from '@/components/chat/ChatPanel.vue'
import StudioPanel from '@/components/studio/StudioPanel.vue'
import { useRouteLocale } from '@/i18n/useRouteLocale'
import { copyTextToClipboard } from '@/utils/copyToClipboard'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const locale = useRouteLocale()
const notebookStore = useNotebookStore()
const sourceStore = useSourceStore()
const studioStore = useStudioStore()
const snackbar = useSnackbarStore()
const userStore = useUserStore()

const isSharedView = computed(() => route.name === 'SharedNotebook')
const shareTokenParam = computed(() => {
  const raw = route.params.shareToken
  const v = Array.isArray(raw) ? raw[0] : raw
  return typeof v === 'string' ? v : ''
})

const displayName = computed(() => {
  const u = userStore.user
  if (!u) return ''
  return (u.username && u.username.trim()) || u.email || t('notebook.userFallback')
})

const sourceTypeSelectItems = computed(() => [
  { title: t('notebook.typeWeb'), value: 'web' },
  { title: t('notebook.typeYoutube'), value: 'youtube' },
  { title: t('notebook.typeBilibili'), value: 'bilibili' },
])

const notebookId = computed(() => {
  if (isSharedView.value) {
    return notebookStore.currentNotebook?.id ?? ''
  }
  return route.params.id as string
})

const loadNotebookContext = async () => {
  if (isSharedView.value) {
    const token = shareTokenParam.value
    if (!token) {
      return
    }
    sourceStore.setShareToken(token)
    studioStore.setShareToken(token)
    try {
      await notebookStore.fetchSharedNotebookPreview(token)
    } catch {
      snackbar.error(t('notebook.shareInvalidOrExpired'))
      router.push({ name: 'Landing', params: { locale: locale.value } })
      return
    }
    const id = notebookStore.currentNotebook?.id
    if (id) {
      await sourceStore.fetchSources(id)
    }
    return
  }
  sourceStore.setShareToken(null)
  studioStore.setShareToken(null)
  const id = route.params.id as string
  if (!id) {
    return
  }
  await notebookStore.fetchNotebook(id)
  await sourceStore.fetchSources(id)
}

watch(
  () => ({
    name: route.name,
    nbId: route.params.id,
    token: shareTokenParam.value,
  }),
  () => {
    void loadNotebookContext()
  },
  { immediate: true },
)

const showShareDialog = ref(false)
const shareActionBusy = ref(false)
const resolvedShareUrl = ref('')
const discoverListed = ref(false)
const discoverPublishBusy = ref(false)

async function syncDiscoverListed() {
  if (isSharedView.value || !notebookStore.currentNotebook) {
    discoverListed.value = false
    return
  }
  try {
    const r = await notebookApi.listPublished()
    discoverListed.value = r.notebooks.some(
      (n) => n.id === notebookStore.currentNotebook!.id,
    )
  } catch {
    discoverListed.value = false
  }
}

watch(
  () => [isSharedView.value, notebookStore.currentNotebook?.id] as const,
  () => {
    void syncDiscoverListed()
  },
)

async function onToggleDiscoverListed(val: boolean | null) {
  if (val === null) {
    return
  }
  const nb = notebookStore.currentNotebook
  if (!nb) {
    return
  }
  discoverPublishBusy.value = true
  const prev = discoverListed.value
  discoverListed.value = val
  try {
    if (val) {
      await notebookApi.publishToDiscover(nb.id, {})
      snackbar.success(t('notebook.discoverPublishOn'))
    } else {
      await notebookApi.unpublishFromDiscover(nb.id)
      snackbar.success(t('notebook.discoverPublishOff'))
    }
    await syncDiscoverListed()
    await notebookStore.fetchNotebook(nb.id)
  } catch (err: unknown) {
    discoverListed.value = prev
    snackbar.error(
      extractErrorDetail(err) || t('notebook.discoverPublishFailed'),
    )
  } finally {
    discoverPublishBusy.value = false
  }
}

async function refreshResolvedShareUrl() {
  const nb = notebookStore.currentNotebook
  if (!nb?.share_enabled) {
    resolvedShareUrl.value = ''
    return
  }
  try {
    const { share_token: shareToken } = await notebookApi.enableShare(nb.id, {
      regenerate: false,
    })
    const href = router.resolve({
      name: 'SharedNotebook',
      params: { locale: locale.value, shareToken },
    }).href
    resolvedShareUrl.value = `${window.location.origin}${href}`
  } catch {
    resolvedShareUrl.value = ''
  }
}

watch(showShareDialog, (open) => {
  if (open) {
    void refreshResolvedShareUrl()
  }
})

function openShareDialog() {
  showShareDialog.value = true
}

async function onCopyShareLink() {
  const nb = notebookStore.currentNotebook
  if (!nb) {
    return
  }
  shareActionBusy.value = true
  try {
    const { share_token: shareToken } = await notebookApi.enableShare(nb.id, {
      regenerate: false,
    })
    await notebookStore.fetchNotebook(nb.id)
    const href = router.resolve({
      name: 'SharedNotebook',
      params: { locale: locale.value, shareToken },
    }).href
    const full = `${window.location.origin}${href}`
    resolvedShareUrl.value = full
    const copied = await copyTextToClipboard(full)
    if (copied) {
      snackbar.success(t('notebook.shareLinkCopied'))
    } else {
      snackbar.success(t('notebook.shareLinkGeneratedManualCopy'))
    }
  } catch (err: unknown) {
    snackbar.error(extractErrorDetail(err) || t('notebook.shareLinkFailed'))
  } finally {
    shareActionBusy.value = false
  }
}

async function onRegenerateShare() {
  const nb = notebookStore.currentNotebook
  if (!nb) {
    return
  }
  shareActionBusy.value = true
  try {
    const { share_token: shareToken } = await notebookApi.enableShare(nb.id, {
      regenerate: true,
    })
    await notebookStore.fetchNotebook(nb.id)
    const href = router.resolve({
      name: 'SharedNotebook',
      params: { locale: locale.value, shareToken },
    }).href
    const full = `${window.location.origin}${href}`
    resolvedShareUrl.value = full
    const copied = await copyTextToClipboard(full)
    if (copied) {
      snackbar.success(t('notebook.shareRegenerated'))
    } else {
      snackbar.success(t('notebook.shareRegeneratedManualCopy'))
    }
  } catch (err: unknown) {
    snackbar.error(extractErrorDetail(err) || t('notebook.shareRegenerateFailed'))
  } finally {
    shareActionBusy.value = false
  }
}

async function onRevokeShare() {
  const nb = notebookStore.currentNotebook
  if (!nb) {
    return
  }
  shareActionBusy.value = true
  try {
    await notebookApi.disableShare(nb.id)
    await notebookStore.fetchNotebook(nb.id)
    resolvedShareUrl.value = ''
    snackbar.success(t('notebook.shareStopped'))
  } catch (err: unknown) {
    snackbar.error(extractErrorDetail(err) || t('notebook.shareStopFailed'))
  } finally {
    shareActionBusy.value = false
  }
}

function goHome() {
  if (isSharedView.value) {
    router.push({ name: 'Landing', params: { locale: locale.value } })
    return
  }
  router.push({ name: 'Home', params: { locale: locale.value } })
}

function goSettings() {
  router.push({ name: 'Settings', params: { locale: locale.value } })
}
const titleInputRef = ref<HTMLInputElement | null>(null)
const editingTitle = ref('')
let titleBeforeEdit = ''

watch(
  () => notebookStore.currentNotebook?.title,
  (val) => {
    if (val) {
      editingTitle.value = val
    }
  },
  { immediate: true },
)

const onTitleFocus = () => {
  titleBeforeEdit = editingTitle.value
}

const onTitleBlur = async () => {
  if (isSharedView.value) {
    return
  }
  const trimmed = editingTitle.value.trim()
  if (!trimmed) {
    editingTitle.value = titleBeforeEdit
    return
  }
  if (trimmed === titleBeforeEdit) return
  try {
    await notebookStore.updateNotebook(notebookId.value, { title: trimmed })
  } catch {
    editingTitle.value = titleBeforeEdit
    snackbar.error(t('notebook.renameFailed'))
  }
}

const sourcesCollapsed = ref(false)
const studioCollapsed = ref(false)
const sourcesWidth = ref(280)
const studioWidth = ref(320)
const isResizing = ref(false)

const startResize = (side: 'left' | 'right', e: MouseEvent) => {
  e.preventDefault()
  isResizing.value = true
  const startX = e.clientX
  const startWidth = side === 'left' ? sourcesWidth.value : studioWidth.value

  const onMouseMove = (moveEvent: MouseEvent) => {
    const delta = moveEvent.clientX - startX
    if (side === 'left') {
      sourcesWidth.value = Math.min(520, Math.max(180, startWidth + delta))
    } else {
      studioWidth.value = Math.min(600, Math.max(200, startWidth - delta))
    }
  }

  const onMouseUp = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}
const showAddSource = ref(false)
const addSourceStep = ref<'choose' | 'url' | 'paste'>('choose')
const addingSource = ref(false)
const sourceUrl = ref('')
const sourceType = ref('web')
const selectedFile = ref<File | null>(null)
const pastedText = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)
const uploadAccept = '.pdf,.docx,.doc,.txt,.md,.csv,.pptx,.jpg,.jpeg,.png,.gif,.webp,.bmp,.ico,.mp3,.wav,.m4a,.aac,.ogg,.opus,.mp4,.avi,.mpeg'
const supportedFileTypeHints = computed(() => [
  {
    label: t('notebook.fileLabelImage'),
    extensions: '.jpg, .jpeg, .png, .gif, .webp, .bmp, .ico',
  },
  {
    label: t('notebook.fileLabelDoc'),
    extensions: '.pdf, .docx, .doc, .txt, .md, .csv, .pptx',
  },
  {
    label: t('notebook.fileLabelAudio'),
    extensions: '.mp3, .wav, .m4a, .aac, .ogg, .opus',
  },
  {
    label: t('notebook.fileLabelVideo'),
    extensions: '.mp4, .avi, .mpeg',
  },
])

const MAX_TEXT_IMAGE_SIZE = 5 * 1024 * 1024
const MAX_MEDIA_SIZE = 50 * 1024 * 1024

const AUTO_UPLOAD_EXTENSIONS: Record<string, 'text' | 'image' | 'audio' | 'video'> = {
  txt: 'text', md: 'text', pdf: 'text', docx: 'text', doc: 'text', csv: 'text', pptx: 'text',
  jpg: 'image', jpeg: 'image', png: 'image', gif: 'image', webp: 'image', bmp: 'image', ico: 'image',
  mp3: 'audio', wav: 'audio', m4a: 'audio', aac: 'audio', ogg: 'audio', opus: 'audio',
  mp4: 'video', avi: 'video', mpeg: 'video',
}

function getFileCategory(file: File): 'text' | 'image' | 'audio' | 'video' | null {
  const ext = file.name.split('.').pop()?.toLowerCase() ?? ''
  return AUTO_UPLOAD_EXTENSIONS[ext] ?? null
}

function validateFileSize(file: File, category: 'text' | 'image' | 'audio' | 'video'): string | null {
  const limit = category === 'text' || category === 'image' ? MAX_TEXT_IMAGE_SIZE : MAX_MEDIA_SIZE
  const limitLabel = category === 'text' || category === 'image' ? '5MB' : '50MB'
  if (file.size > limit) {
    return t('notebook.fileTooLarge', { name: file.name, limit: limitLabel })
  }
  return null
}

const extractErrorDetail = (err: unknown): string | null => {
  if (err && typeof err === 'object' && 'response' in err) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    return axiosErr.response?.data?.detail || null
  }
  return null
}

function autoUploadFile(file: File) {
  showAddSource.value = false
  sourceStore.uploadSourceInBackground(notebookId.value, file)
}

function onFileInputChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) {
    const category = getFileCategory(file)
    if (category) {
      const sizeError = validateFileSize(file, category)
      if (sizeError) {
        snackbar.error(sizeError)
      } else {
        autoUploadFile(file)
      }
    } else {
      selectedFile.value = file
    }
  }
  input.value = ''
}

function triggerUploadClick() {
  fileInputRef.value?.click()
}

function onDrop(e: DragEvent) {
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (!file) return

  const category = getFileCategory(file)
  if (category) {
    const sizeError = validateFileSize(file, category)
    if (sizeError) {
      snackbar.error(sizeError)
      return
    }
    autoUploadFile(file)
  } else {
    selectedFile.value = file
  }
}

const onCloudDriveClick = () => {
  snackbar.info(t('notebook.comingSoon'))
}

const onAddSourceDialogClosed = () => {
  addSourceStep.value = 'choose'
  sourceUrl.value = ''
  pastedText.value = ''
  selectedFile.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const handleAddSourceFile = async () => {
  if (!selectedFile.value) return
  addingSource.value = true
  try {
    await sourceStore.uploadSource(notebookId.value, selectedFile.value)
    snackbar.success(t('notebook.uploadSuccess'))
    showAddSource.value = false
    selectedFile.value = null
    if (fileInputRef.value) fileInputRef.value.value = ''
  } catch (err: unknown) {
    snackbar.error(extractErrorDetail(err) || t('notebook.addSourceFailed'))
  } finally {
    addingSource.value = false
  }
}

const handleAddSourceUrl = async () => {
  const url = sourceUrl.value.trim()
  if (!url) return
  addingSource.value = true
  try {
    await sourceStore.addSource(notebookId.value, {
      type: sourceType.value,
      url,
    })
    snackbar.success(t('notebook.addSourceSuccess'))
    showAddSource.value = false
    sourceUrl.value = ''
    addSourceStep.value = 'choose'
  } catch (err: unknown) {
    snackbar.error(extractErrorDetail(err) || t('notebook.addSourceFailed'))
  } finally {
    addingSource.value = false
  }
}

const handleAddSourcePaste = async () => {
  const text = pastedText.value.trim()
  if (!text) return
  addingSource.value = true
  try {
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const file = new File([blob], 'pasted.txt', { type: 'text/plain' })
    await sourceStore.uploadSource(notebookId.value, file)
    snackbar.success(t('notebook.addSourceSuccess'))
    showAddSource.value = false
    pastedText.value = ''
    addSourceStep.value = 'choose'
  } catch (err: unknown) {
    snackbar.error(extractErrorDetail(err) || t('notebook.addSourceFailed'))
  } finally {
    addingSource.value = false
  }
}
</script>

<style scoped>
.notebook-detail {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.nb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--surface-color);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.header-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.nb-shared-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding: 5px 10px;
  border-radius: 6px;
  background: #ffffff;
  border: 1px solid var(--border-color);
  color: #202124;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.2;
}

.nb-shared-badge-icon {
  color: #202124;
  flex-shrink: 0;
}

.theme-dark .nb-shared-badge {
  border-color: rgba(0, 0, 0, 0.08);
  box-shadow: var(--shadow-sm);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-share-btn {
  text-transform: none;
  letter-spacing: normal;
}

.header-share-label {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 500;
}

.header-discover-wrap {
  max-width: 200px;
}

.header-discover-wrap :deep(.v-label) {
  font-size: 12px;
  white-space: nowrap;
}

.share-dialog-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.header-username {
  min-width: 32px;
  height: 32px;
  padding: 0 12px;
  border-radius: 16px;
  background: var(--text-primary);
  color: var(--surface-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
  white-space: nowrap;
}

.nb-title {
  font-size: 18px;
  font-weight: 600;
}

.nb-title-input {
  font-size: 18px;
  font-weight: 600;
  border: 1px solid transparent;
  border-radius: 4px;
  outline: none;
  background: transparent;
  padding: 2px 6px;
  color: inherit;
  font-family: inherit;
  line-height: 1.4;
  min-width: 60px;
  max-width: 360px;
}

.nb-title-input:hover {
  border-color: var(--border-color);
}

.nb-title-input:focus {
  border-color: var(--primary-color);
  background: var(--surface-color);
}

.nb-panels {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.nb-panels.is-resizing {
  user-select: none;
  cursor: col-resize;
}

.nb-panels.is-resizing * {
  pointer-events: none;
}

.nb-panels.is-resizing .panel-resizer {
  pointer-events: auto;
}

.panel {
  display: flex;
  flex-direction: column;
  background: var(--surface-color);
  overflow: hidden;
}

.panel-sources {
  width: 280px;
  flex-shrink: 0;
  border-right: none;
  transition: width 0.2s ease;
}

.panel-sources.collapsed {
  width: 48px;
}

.panel-chat {
  flex: 1;
  min-width: 0;
  border-left: 1px solid var(--border-color);
  border-right: 1px solid var(--border-color);
}

.panel-studio {
  width: 320px;
  flex-shrink: 0;
  transition: width 0.2s ease;
}

.panel-studio.collapsed {
  width: 48px;
}

.nb-panels.is-resizing .panel-sources,
.nb-panels.is-resizing .panel-studio {
  transition: none;
}

.panel-resizer {
  width: 4px;
  flex-shrink: 0;
  background: var(--border-color);
  cursor: col-resize;
  position: relative;
  z-index: 10;
  transition: background 0.15s;
}

.panel-resizer::after {
  content: '';
  position: absolute;
  inset: 0 -3px;
}

.panel-resizer:hover,
.nb-panels.is-resizing .panel-resizer {
  background: var(--primary-color);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.panel-header h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.panel-header-actions {
  display: flex;
  gap: 4px;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
}

.add-resource-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.add-resource-drop-zone {
  width: 100%;
  min-height: 260px;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.add-resource-drop-zone.drop-zone-active {
  border-color: rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.06);
}

.add-resource-drop-zone.drop-zone-uploading {
  pointer-events: none;
  opacity: 0.7;
}

.add-resource-drop-text {
  font-size: 15px;
  color: var(--text-primary);
}

.add-resource-types {
  font-size: 13px;
  color: var(--text-secondary);
}

.add-resource-type-chip {
  cursor: help;
  text-decoration: underline dotted;
  text-underline-offset: 2px;
}

.add-resource-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
  width: 100%;
  margin-top: 16px;
}

.add-resource-action-btn {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  min-width: 80px;
}

.add-resource-form {
  padding: 8px 0;
}

.add-resource-back {
  margin-bottom: 16px;
}
</style>
