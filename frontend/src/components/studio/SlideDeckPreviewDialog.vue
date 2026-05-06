<template>

  <v-dialog
    v-model="dialogOpen"
    class="slide-deck-preview-dialog"
    fullscreen
  >
    <v-card
      v-if="deck"
      class="slide-deck-preview-card"
      rounded="0"
    >
      <v-card-title class="slide-deck-preview-header pa-4 pb-2">
        <div class="slide-deck-preview-header-text">
          <div class="slide-deck-preview-title">
            {{ displayTitle }}
          </div>
          <div class="slide-deck-preview-subtitle text-medium-emphasis">
            基于 {{ sourceCountLabel }} 个来源
          </div>
        </div>
        <div class="slide-deck-preview-header-actions">
          <v-btn
            variant="text"
            size="small"
            class="text-none"
            @click="openPdfInNewTab"
          >
            <v-icon
              :size="18"
              class="mr-1"
            >
              mdi-open-in-new
            </v-icon>
            打开 PDF
          </v-btn>
          <v-btn
            variant="text"
            size="small"
            class="text-none"
            :disabled="!mainImageUrl || ocrBusy"
            :loading="ocrBusy"
            @click="runSlideOcr"
          >
            <v-icon
              :size="18"
              class="mr-1"
            >
              mdi-text-recognition
            </v-icon>
            {{ $t('slideOcr.recognize') }}
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
                :disabled="!deck?.file_path || downloadBusy"
              >
                <v-icon :size="20">mdi-dots-horizontal</v-icon>
              </v-btn>
            </template>
            <v-list
              density="compact"
              class="slide-deck-download-menu py-1"
              min-width="240"
            >
              <v-list-item
                :disabled="downloadBusy"
                @click="downloadSlidePdfFile"
              >
                <template #prepend>
                  <v-icon
                    :size="20"
                    class="mr-2"
                  >
                    mdi-file-pdf-box
                  </v-icon>
                </template>
                <v-list-item-title>下载 PDF 文档 (.pdf)</v-list-item-title>
              </v-list-item>
              <v-list-item
                :disabled="downloadBusy"
                @click="downloadSlidePptxFile"
              >
                <template #prepend>
                  <v-icon
                    :size="20"
                    class="mr-2"
                  >
                    mdi-file-powerpoint-box
                  </v-icon>
                </template>
                <v-list-item-title>下载 PowerPoint (.pptx)</v-list-item-title>
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
      <v-card-text class="slide-deck-preview-body pa-0">
        <div
          v-if="loading && !hasAnyLoadedImage"
          class="slide-deck-preview-loading"
        >
          <v-progress-circular
            indeterminate
            color="primary"
            :size="48"
          />
          <span class="text-medium-emphasis mt-3">正在加载幻灯片…</span>
        </div>
        <div
          v-else-if="errorMessage"
          class="slide-deck-preview-error"
        >
          {{ errorMessage }}
        </div>
        <div
          v-else
          class="slide-deck-preview-split"
        >
          <div class="slide-deck-preview-main">
            <div class="slide-deck-preview-main-scroll">
              <div
                class="slide-deck-preview-main-inner"
                :style="mainTransformStyle"
              >
                <div
                  v-if="mainImageUrl"
                  ref="slideFrameRef"
                  class="slide-deck-preview-slide-frame"
                >
                  <img
                    ref="mainImgRef"
                    :src="mainImageUrl"
                    :alt="slideLabel(selectedIndex)"
                    class="slide-deck-preview-main-img"
                    loading="eager"
                    decoding="async"
                    @error="handlePreviewError"
                  />
                  <div
                    v-if="ocrRegions.length > 0"
                    class="slide-deck-ocr-overlay"
                    @mousemove="onOcrOverlayMouseMove"
                    @mouseleave="onOcrOverlayMouseLeave"
                    @dblclick.prevent="onOcrOverlayDblClick"
                  >
                    <div
                      v-if="hoveredRegion"
                      class="slide-deck-ocr-highlight"
                      :style="hoveredHighlightStyle"
                    />
                  </div>
                </div>
                <div
                  v-else
                  class="slide-deck-preview-main-placeholder"
                >
                  <v-progress-circular
                    indeterminate
                    color="primary"
                    :size="32"
                  />
                  <span class="text-medium-emphasis mt-3">正在加载当前幻灯片…</span>
                </div>
              </div>
            </div>
            <div class="slide-deck-preview-zoom">
              <v-btn
                icon
                size="x-small"
                variant="flat"
                class="slide-deck-preview-zoom-btn"
                aria-label="放大"
                @click="zoomIn"
              >
                <v-icon :size="16">mdi-plus</v-icon>
              </v-btn>
              <v-btn
                icon
                size="x-small"
                variant="flat"
                class="slide-deck-preview-zoom-btn"
                aria-label="缩小"
                @click="zoomOut"
              >
                <v-icon :size="16">mdi-minus</v-icon>
              </v-btn>
            </div>
          </div>
          <div class="slide-deck-preview-sidebar">
            <div
              v-for="(thumbUrl, slideIndex) of thumbnailUrls"
              :key="slideIndex"
              class="slide-deck-thumb"
              :class="{ 'is-active': slideIndex === selectedIndex }"
              @click="selectSlide(slideIndex)"
            >
              <div class="slide-deck-thumb-num">
                {{ slideIndex + 1 }}
              </div>
              <img
                v-if="thumbUrl"
                :src="thumbUrl"
                :alt="slideLabel(slideIndex)"
                class="slide-deck-thumb-img"
                loading="lazy"
                decoding="async"
                @error="handleThumbError(slideIndex)"
              />
              <div
                v-else
                class="slide-deck-thumb-placeholder"
              />
              <div class="slide-deck-thumb-caption text-truncate">
                {{ slideTitle(slideIndex) }}
              </div>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>

</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch, withDefaults } from 'vue'
import { useI18n } from 'vue-i18n'
import type {
  SlideDeckData,
  SlideDeckImageData,
  SlideDeckImagesManifest,
} from '@/api/studio'
import { postSlideImageLayoutOcr, type SlideOcrRegion } from '@/api/ocrLayout'
import { shareReadApi } from '@/api/shareRead'
import { studioApi } from '@/api/studio'
import { useChatStore } from '@/stores/useChatStore'
import { useSnackbarStore } from '@/stores/useSnackbarStore'
import { triggerBlobDownload } from '@/utils/exportZip'
import {
  downloadSlidePdfWithFallback,
  openSlidePdfWithFallback,
  type SlidePdfMode,
} from '@/utils/slidePdf'

defineOptions({
  name: 'SlideDeckPreviewDialog',
})

const CLOSE_RESET_MS = 350

const { t } = useI18n()
const snackbar = useSnackbarStore()
const chatStore = useChatStore()

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    deck: SlideDeckData | null
    shareToken?: string | null
    readOnly?: boolean
  }>(),
  { shareToken: null, readOnly: false },
)

const slidePdfMode = computed<SlidePdfMode | undefined>(() =>
  props.shareToken ? { shareToken: props.shareToken } : undefined,
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  afterLeave: []
}>()

const dialogOpen = computed({
  get: () => props.modelValue,
  set: (v: boolean) => {
    emit('update:modelValue', v)
  },
})

const loading = ref(false)
const downloadMenuOpen = ref(false)
const downloadBusy = ref(false)
const errorMessage = ref<string | null>(null)
const manifest = ref<SlideDeckImagesManifest | null>(null)
const thumbnailUrls = ref<Array<string | null>>([])
const previewUrls = ref<Array<string | null>>([])
const selectedIndex = ref(0)
const zoomLevel = ref(1)

const mainImgRef = ref<HTMLImageElement | null>(null)
const slideFrameRef = ref<HTMLElement | null>(null)
const ocrRegions = ref<SlideOcrRegion[]>([])
const ocrBusy = ref(false)
const hoveredRegionIndex = ref<number | null>(null)

let loadGeneration = 0
let closeResetTimer: ReturnType<typeof setTimeout> | null = null

const displayTitle = computed(() => {
  if (!props.deck) {
    return ''
  }
  return props.deck.suggested_filename || props.deck.title || '演示文稿'
})

const sourceCountLabel = computed(() => {
  const n = props.deck?.source_count
  if (n != null && n > 0) {
    return n
  }
  return 1
})

const mainTransformStyle = computed(() => ({
  transform: `scale(${zoomLevel.value})`,
}))

const hasAnyLoadedImage = computed(() => {
  return (
    thumbnailUrls.value.some((url) => Boolean(url)) ||
    previewUrls.value.some((url) => Boolean(url))
  )
})

const mainImageUrl = computed(() => {
  const selectedPreview = previewUrls.value[selectedIndex.value]
  if (selectedPreview) {
    return selectedPreview
  }
  const selectedThumb = thumbnailUrls.value[selectedIndex.value]
  if (selectedThumb) {
    return selectedThumb
  }
  return (
    previewUrls.value.find((url) => Boolean(url)) ??
    thumbnailUrls.value.find((url) => Boolean(url)) ??
    null
  )
})

const hoveredRegion = computed(() => {
  const idx = hoveredRegionIndex.value
  if (idx == null) {
    return null
  }
  return ocrRegions.value[idx] ?? null
})

const hoveredHighlightStyle = computed((): Record<string, string> => {
  const region = hoveredRegion.value
  const img = mainImgRef.value
  if (!region || !img?.naturalWidth || !img.naturalHeight) {
    return {}
  }
  const w = img.naturalWidth
  const h = img.naturalHeight
  return {
    left: `${(region.x / w) * 100}%`,
    top: `${(region.y / h) * 100}%`,
    width: `${(region.w / w) * 100}%`,
    height: `${(region.h / h) * 100}%`,
  }
})

function clearOcrLayout() {
  ocrRegions.value = []
  hoveredRegionIndex.value = null
}

function pickRegionIndexAt(nx: number, ny: number): number | null {
  const hits: { index: number; area: number }[] = []
  ocrRegions.value.forEach((region, index) => {
    const insideX = nx >= region.x && nx <= region.x + region.w
    const insideY = ny >= region.y && ny <= region.y + region.h
    if (insideX && insideY) {
      hits.push({ index, area: region.w * region.h })
    }
  })
  if (hits.length === 0) {
    return null
  }
  hits.sort((a, b) => a.area - b.area)
  return hits[0].index
}

function onOcrOverlayMouseMove(event: MouseEvent) {
  const img = mainImgRef.value
  if (!img?.naturalWidth) {
    return
  }
  const rect = img.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) {
    return
  }
  const nx = ((event.clientX - rect.left) / rect.width) * img.naturalWidth
  const ny = ((event.clientY - rect.top) / rect.height) * img.naturalHeight
  hoveredRegionIndex.value = pickRegionIndexAt(nx, ny)
}

function onOcrOverlayMouseLeave() {
  hoveredRegionIndex.value = null
}

function extractOcrErrorMessage(err: unknown): string {
  const ax = err as { response?: { data?: { detail?: unknown } } }
  const detail = ax.response?.data?.detail
  return typeof detail === 'string' ? detail : t('slideOcr.failed')
}

async function runSlideOcr() {
  const url = mainImageUrl.value
  if (!url || ocrBusy.value) {
    return
  }
  const indexAtStart = selectedIndex.value
  const deckId = props.deck?.id
  ocrBusy.value = true
  hoveredRegionIndex.value = null
  try {
    const blob = await fetchSlideImageBlobForOcrPreferred(url)
    const data = await postSlideImageLayoutOcr(blob, props.shareToken)
    if (deckId !== props.deck?.id || indexAtStart !== selectedIndex.value) {
      return
    }
    await nextTick()
    const imgEl = mainImgRef.value
    const pw = imgEl?.naturalWidth
    const ph = imgEl?.naturalHeight
    if (
      pw
      && ph
      && data.width > 0
      && data.height > 0
      && (data.width !== pw || data.height !== ph)
    ) {
      const sx = pw / data.width
      const sy = ph / data.height
      ocrRegions.value = data.regions.map((r) => ({
        ...r,
        x: Math.round(r.x * sx),
        y: Math.round(r.y * sy),
        w: Math.max(1, Math.round(r.w * sx)),
        h: Math.max(1, Math.round(r.h * sy)),
      }))
    } else {
      ocrRegions.value = data.regions
    }
  } catch (err) {
    snackbar.error(extractOcrErrorMessage(err))
    clearOcrLayout()
  } finally {
    ocrBusy.value = false
  }
}

function onOcrOverlayDblClick() {
  const region = hoveredRegion.value
  const text = region?.text?.trim()
  if (!text) {
    snackbar.info(t('slideOcr.noText'))
    return
  }
  if (props.readOnly) {
    snackbar.info(t('slideOcr.readOnlyInject'))
    return
  }
  chatStore.injectComposerText(text)
}

function closeDialog() {
  emit('update:modelValue', false)
}

function isBlobUrl(url: string | null | undefined): boolean {
  return typeof url === 'string' && url.startsWith('blob:')
}

function isApiProxyUrl(url: string | null | undefined): boolean {
  return typeof url === 'string' && url.startsWith('/api/')
}

/**
 * True when fetch(url) would be cross-origin (e.g. OSS presigned URL).
 * Display via <img src> does not need CORS; reading bytes with fetch does.
 */
function isCrossOriginUrl(url: string): boolean {
  try {
    const parsed = new URL(url, window.location.href)
    if (parsed.protocol === 'blob:') {
      return false
    }
    return parsed.origin !== window.location.origin
  } catch {
    return true
  }
}

type SlideImageVariant = 'export' | 'preview' | 'thumb'

/**
 * Prefer high-res export for OCR; map regions back to on-screen preview in runSlideOcr.
 */
async function fetchSlideImageBlobForOcrPreferred(url: string): Promise<Blob> {
  const deck = props.deck
  const index = selectedIndex.value
  if (deck?.id) {
    const variants: SlideImageVariant[] = ['export', 'preview', 'thumb']
    const tok = props.shareToken
    let lastErr: unknown
    for (const variant of variants) {
      try {
        const buffer = tok
          ? await shareReadApi.getSlideImageArrayBuffer(
            tok,
            deck.id,
            index,
            variant,
          )
          : await studioApi.getSlideImageArrayBuffer(deck.id, index, variant)
        return new Blob([buffer])
      } catch (err) {
        lastErr = err
      }
    }
    if (lastErr) {
      throw lastErr
    }
  }
  if (!isCrossOriginUrl(url)) {
    const res = await fetch(url)
    if (!res.ok) {
      throw new Error(`Image fetch failed: ${res.status}`)
    }
    return await res.blob()
  }
  throw new Error('Slide deck not found')
}

function revokeUrl(url: string | null | undefined) {
  if (isBlobUrl(url)) {
    URL.revokeObjectURL(url as string)
  }
}

function revokeVariantUrls(urls: Array<string | null>) {
  urls.forEach((url) => {
    revokeUrl(url)
  })
}

function resetState() {
  loadGeneration += 1
  revokeVariantUrls(thumbnailUrls.value)
  revokeVariantUrls(previewUrls.value)
  manifest.value = null
  thumbnailUrls.value = []
  previewUrls.value = []
  errorMessage.value = null
  loading.value = false
  downloadMenuOpen.value = false
  downloadBusy.value = false
  selectedIndex.value = 0
  zoomLevel.value = 1
  ocrBusy.value = false
  clearOcrLayout()
}

function slideTitle(index: number): string {
  const image = getManifestImage(index)
  if (image?.title.trim()) {
    return image.title.trim()
  }
  const slides = getSlidesMeta()
  const row = slides[index]
  if (row && typeof row.title === 'string' && row.title.trim()) {
    return row.title.trim()
  }
  return `第 ${index + 1} 页`
}

function slideLabel(index: number): string {
  return `幻灯片 ${index + 1}：${slideTitle(index)}`
}

function getSlidesMeta(): { title?: string }[] {
  const raw = props.deck?.slides_data
  if (!raw || typeof raw !== 'object') {
    return []
  }
  const slides = (raw as { slides?: unknown }).slides
  if (!Array.isArray(slides)) {
    return []
  }
  return slides.filter((s) => s && typeof s === 'object') as { title?: string }[]
}

function getManifestImages(): SlideDeckImageData[] {
  return manifest.value?.images ?? []
}

function getManifestImage(index: number): SlideDeckImageData | null {
  const images = getManifestImages()
  if (index < 0 || index >= images.length) {
    return null
  }
  return images[index] ?? null
}

function selectSlide(index: number) {
  clearOcrLayout()
  selectedIndex.value = index
  if (props.modelValue) {
    void ensurePreviewReady(index, loadGeneration)
    void preloadAdjacentPreviews(index, loadGeneration)
  }
}

function zoomIn() {
  zoomLevel.value = Math.min(3, Math.round((zoomLevel.value + 0.2) * 10) / 10)
}

function zoomOut() {
  zoomLevel.value = Math.max(0.5, Math.round((zoomLevel.value - 0.2) * 10) / 10)
}

function getVariantCandidates(
  image: SlideDeckImageData,
  variant: 'thumb' | 'preview' | 'export'
): string[] {
  const urls = new Set<string>()
  const current = image.variants[variant]
  const add = (value?: string | null) => {
    if (typeof value === 'string' && value.trim()) {
      urls.add(value.trim())
    }
  }
  add(current.preferred_url)
  add(current.url)
  add(current.proxy_url)
  if (variant === 'thumb') {
    add(image.variants.preview.proxy_url)
  }
  if (variant === 'preview') {
    add(image.variants.export.proxy_url)
  }
  return Array.from(urls)
}

function preloadImage(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve()
    image.onerror = () => reject(new Error('Image preload failed'))
    image.src = url
  })
}

function setVariantUrl(
  target: typeof thumbnailUrls,
  index: number,
  url: string
) {
  revokeUrl(target.value[index])
  target.value[index] = url
}

async function loadAuthenticatedProxyVariant(
  index: number,
  variant: 'thumb' | 'preview'
): Promise<string> {
  if (!props.deck) {
    throw new Error('Slide deck not found')
  }
  const tok = props.shareToken
  const buffer = tok
    ? await shareReadApi.getSlideImageArrayBuffer(
      tok,
      props.deck.id,
      index,
      variant,
    )
    : await studioApi.getSlideImageArrayBuffer(
      props.deck.id,
      index,
      variant
    )
  return URL.createObjectURL(new Blob([buffer], { type: 'image/webp' }))
}

async function resolveVariantUrl(
  index: number,
  variant: 'thumb' | 'preview',
  gen: number,
  options: {
    failedUrl?: string | null
    preload?: boolean
    force?: boolean
  } = {}
): Promise<boolean> {
  const image = getManifestImage(index)
  if (!image) {
    return false
  }
  const target = variant === 'thumb' ? thumbnailUrls : previewUrls
  const current = target.value[index]
  if (!options.force && current) {
    return true
  }
  for (const candidate of getVariantCandidates(image, variant)) {
    if (!candidate || candidate === current || candidate === options.failedUrl) {
      continue
    }
    try {
      let resolvedUrl = candidate
      if (isApiProxyUrl(candidate)) {
        resolvedUrl = await loadAuthenticatedProxyVariant(index, variant)
      } else if (options.preload) {
        await preloadImage(candidate)
      }
      if (gen !== loadGeneration) {
        revokeUrl(resolvedUrl)
        return false
      }
      setVariantUrl(target, index, resolvedUrl)
      if (loading.value && hasAnyLoadedImage.value) {
        loading.value = false
      }
      return true
    } catch {
      continue
    }
  }
  return false
}

async function ensurePreviewReady(index: number, gen: number): Promise<boolean> {
  return resolveVariantUrl(index, 'preview', gen, { preload: true })
}

async function preloadAdjacentPreviews(index: number, gen: number) {
  const images = getManifestImages()
  const tasks = [index - 1, index + 1]
    .filter((candidate) => candidate >= 0 && candidate < images.length)
    .map((candidate) => ensurePreviewReady(candidate, gen))
  await Promise.allSettled(tasks)
}

async function primeThumbnailUrls(gen: number) {
  thumbnailUrls.value = Array.from(
    { length: getManifestImages().length },
    () => null
  )
  const tasks = getManifestImages().map((_, index) => {
    return resolveVariantUrl(index, 'thumb', gen)
  })
  await Promise.allSettled(tasks)
}

async function loadDeckManifest() {
  if (!props.deck) {
    return
  }
  const gen = ++loadGeneration
  loading.value = true
  errorMessage.value = null
  manifest.value = null
  thumbnailUrls.value = []
  previewUrls.value = []
  selectedIndex.value = 0
  try {
    const tok = props.shareToken
    const loadedManifest = tok
      ? await shareReadApi.getSlideImagesManifest(tok, props.deck.id)
      : await studioApi.getSlideImagesManifest(props.deck.id)
    if (gen !== loadGeneration) {
      return
    }
    if (loadedManifest.image_count < 1) {
      errorMessage.value = '无法加载演示文稿图片，请稍后重试或改用「打开 PDF」。'
      return
    }
    manifest.value = loadedManifest
    previewUrls.value = Array.from(
      { length: loadedManifest.image_count },
      () => null
    )
    const [ready] = await Promise.all([
      ensurePreviewReady(0, gen),
      primeThumbnailUrls(gen),
    ])
    if (gen !== loadGeneration) {
      return
    }
    if (!ready && !hasAnyLoadedImage.value) {
      errorMessage.value = '无法加载演示文稿图片，请稍后重试或改用「打开 PDF」。'
      return
    }
    void preloadAdjacentPreviews(0, gen)
  } catch {
    manifest.value = null
    thumbnailUrls.value = []
    previewUrls.value = []
    if (gen === loadGeneration) {
      errorMessage.value = '无法加载演示文稿图片，请稍后重试或改用「打开 PDF」。'
    }
  } finally {
    if (gen === loadGeneration) {
      loading.value = false
    }
  }
}

function handleThumbError(index: number) {
  const failedUrl = thumbnailUrls.value[index]
  revokeUrl(failedUrl)
  thumbnailUrls.value[index] = null
  void resolveVariantUrl(index, 'thumb', loadGeneration, {
    failedUrl,
    force: true,
  })
}

function handlePreviewError() {
  const failedUrl = previewUrls.value[selectedIndex.value]
  revokeUrl(failedUrl)
  previewUrls.value[selectedIndex.value] = null
  void resolveVariantUrl(selectedIndex.value, 'preview', loadGeneration, {
    failedUrl,
    force: true,
  })
}

function suggestedDownloadBasename(): string {
  const d = props.deck
  if (!d) {
    return 'slides'
  }
  let base = (d.suggested_filename || d.title || 'slides').replace(
    /["\\/:*?<>|]/g,
    '_'
  )
  let lower = base.toLowerCase()
  if (lower.endsWith('.pdf')) {
    base = base.slice(0, -4)
    lower = base.toLowerCase()
  }
  if (lower.endsWith('.pptx')) {
    base = base.slice(0, -5)
  }
  return base.trim() || 'slides'
}

async function downloadSlidePdfFile() {
  if (!props.deck?.file_path) {
    return
  }
  downloadBusy.value = true
  errorMessage.value = null
  try {
    await downloadSlidePdfWithFallback(
      props.deck.id,
      suggestedDownloadBasename(),
      slidePdfMode.value,
    )
    downloadMenuOpen.value = false
  } catch {
    errorMessage.value = '下载 PDF 失败'
  } finally {
    downloadBusy.value = false
  }
}

async function downloadSlidePptxFile() {
  if (!props.deck?.file_path) {
    return
  }
  downloadBusy.value = true
  errorMessage.value = null
  try {
    const tok = props.shareToken
    const buf = tok
      ? await shareReadApi.getSlidePptxArrayBuffer(tok, props.deck.id)
      : await studioApi.getSlidePptxArrayBuffer(props.deck.id)
    triggerBlobDownload(
      new Blob([buf], {
        type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      }),
      `${suggestedDownloadBasename()}.pptx`
    )
    downloadMenuOpen.value = false
  } catch {
    errorMessage.value = '下载 PowerPoint 失败'
  } finally {
    downloadBusy.value = false
  }
}

async function openPdfInNewTab() {
  if (!props.deck?.file_path) {
    return
  }
  try {
    await openSlidePdfWithFallback(
      props.deck.id,
      suggestedDownloadBasename(),
      slidePdfMode.value,
    )
  } catch {
    errorMessage.value = '打开 PDF 失败'
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (closeResetTimer != null) {
      clearTimeout(closeResetTimer)
      closeResetTimer = null
    }
    if (open && props.deck) {
      void loadDeckManifest()
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
  () => props.deck?.id,
  () => {
    if (props.modelValue && props.deck) {
      void loadDeckManifest()
    }
  }
)

</script>

<style scoped lang="scss">
.slide-deck-preview-dialog :deep(.v-overlay__content) {
  width: 100%;
  max-width: 100%;
  height: 100%;
  max-height: 100%;
  margin: 0;
}

.slide-deck-preview-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
}

.slide-deck-preview-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
}

.slide-deck-preview-header-text {
  min-width: 0;
}

.slide-deck-preview-title {
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.3;
  word-break: break-word;
}

.slide-deck-preview-subtitle {
  font-size: 0.8rem;
  margin-top: 4px;
}

.slide-deck-preview-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.slide-deck-download-menu {
  border-radius: 12px;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.08),
    0 1px 3px rgba(0, 0, 0, 0.06);
}

.slide-deck-preview-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.slide-deck-preview-loading,
.slide-deck-preview-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  padding: 32px;
}

.slide-deck-preview-error {
  color: rgb(var(--v-theme-error));
}

.slide-deck-preview-split {
  display: flex;
  flex: 1;
  min-height: 0;
}

.slide-deck-preview-main {
  flex: 1;
  position: relative;
  min-width: 0;
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 0;
}

.slide-deck-preview-main-scroll {
  position: absolute;
  inset: 0;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}

.slide-deck-preview-main-inner {
  transform-origin: center center;
  transition: transform 0.15s ease-out;
}

.slide-deck-preview-main-img {
  display: block;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
  background: #fff;
}

.slide-deck-preview-slide-frame {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.slide-deck-ocr-overlay {
  position: absolute;
  inset: 0;
  cursor: crosshair;
}

.slide-deck-ocr-highlight {
  position: absolute;
  box-sizing: border-box;
  border: 2px solid #e53935;
  pointer-events: none;
  border-radius: 4px;
}

.slide-deck-preview-main-placeholder {
  min-width: min(100%, 720px);
  min-height: 320px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow:
    0 1px 3px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.06);
}

.slide-deck-preview-zoom {
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

.slide-deck-preview-zoom-btn {
  min-width: 28px !important;
  width: 28px;
  height: 28px;
}

.slide-deck-preview-sidebar {
  width: 220px;
  flex-shrink: 0;
  overflow-y: auto;
  padding: 12px 10px;
  border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
}

.slide-deck-thumb {
  border-radius: 10px;
  padding: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  border: 2px solid transparent;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.slide-deck-thumb:hover {
  background: rgba(var(--v-theme-primary), 0.06);
}

.slide-deck-thumb.is-active {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}

.slide-deck-thumb-num {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.55);
  margin-bottom: 6px;
}

.slide-deck-thumb-img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 6px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.slide-deck-thumb-placeholder {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 6px;
  background:
    linear-gradient(
      90deg,
      rgba(0, 0, 0, 0.04) 0%,
      rgba(0, 0, 0, 0.08) 50%,
      rgba(0, 0, 0, 0.04) 100%
    );
  background-size: 200% 100%;
  animation: slide-deck-placeholder-shimmer 1.2s linear infinite;
}

.slide-deck-thumb-caption {
  margin-top: 6px;
  font-size: 0.72rem;
  line-height: 1.3;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

@keyframes slide-deck-placeholder-shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
