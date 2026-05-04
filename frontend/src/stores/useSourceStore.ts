import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { shareReadApi } from '@/api/shareRead'
import { sourceApi } from '@/api/source'
import { streamTaskUntilTerminal } from '@/api/taskEvents'
import type { Source, ChunkContext, SourceContent } from '@/api/source'
import { useSnackbarStore } from '@/stores/useSnackbarStore'

export type { SourceContent }

export interface HighlightRequest {
  sourceId: string
  chunkId: string
  chunkIndex: number
  pageNumber: number | null
  content: string
}

export const useSourceStore = defineStore('source', () => {
  const activeShareToken = ref<string | null>(null)

  const setShareToken = (token: string | null) => {
    activeShareToken.value = token
  }

  const sources = ref<Source[]>([])
  const loading = ref(false)
  const contentLoading = ref(false)
  const currentContent = ref<SourceContent | null>(null)
  const highlightRequest = ref<HighlightRequest | null>(null)
  const showContentViewer = ref(false)
  const POLL_INTERVAL_MS = 2500
  const FIRST_POLL_DELAY_MS = 500
  const MAX_CONSECUTIVE_POLL_ERRORS = 5
  const inFlightSourceWaits = new Set<string>()

  const upsertSource = (source: Source) => {
    const idx = sources.value.findIndex((item) => item.id === source.id)
    if (idx !== -1) {
      sources.value[idx] = source
    } else {
      sources.value.unshift(source)
    }
  }

  const pollUntilTerminal = (
    sourceId: string,
    onUpdate?: (source: Source) => void
  ): Promise<Source> => {
    return new Promise((resolve, reject) => {
      let consecutiveErrors = 0

      const tick = async () => {
        try {
          const tok = activeShareToken.value
          const updated = tok
            ? await shareReadApi.getSource(tok, sourceId)
            : await sourceApi.get(sourceId)
          consecutiveErrors = 0
          onUpdate?.(updated)
          if (updated.status === 'ready' || updated.status === 'error') {
            resolve(updated)
            return
          }
          window.setTimeout(tick, POLL_INTERVAL_MS)
        } catch (err) {
          consecutiveErrors += 1
          if (consecutiveErrors >= MAX_CONSECUTIVE_POLL_ERRORS) {
            reject(err)
            return
          }
          window.setTimeout(tick, POLL_INTERVAL_MS)
        }
      }

      window.setTimeout(tick, FIRST_POLL_DELAY_MS)
    })
  }

  const waitUntilTerminal = async (
    sourceId: string,
    onUpdate?: (source: Source) => void
  ) => {
    const tok = activeShareToken.value
    if (tok) {
      return pollUntilTerminal(sourceId, onUpdate)
    }
    try {
      const updated = await streamTaskUntilTerminal<Source>({
        resourceType: 'source',
        resourceId: sourceId,
        fetchCurrent: () => sourceApi.get(sourceId),
        onEvent: (payload) => {
          const idx = sources.value.findIndex((item) => item.id === sourceId)
          if (idx !== -1 && payload.status) {
            sources.value[idx] = {
              ...sources.value[idx],
              status: payload.status,
            }
          }
        },
      })
      onUpdate?.(updated)
      return updated
    } catch {
      return pollUntilTerminal(sourceId, onUpdate)
    }
  }

  const watchPendingSource = (sourceId: string) => {
    if (inFlightSourceWaits.has(sourceId)) {
      return
    }

    inFlightSourceWaits.add(sourceId)
    void waitUntilTerminal(sourceId, (updated) => {
      upsertSource(updated)
    })
      .catch(async () => {
        try {
          const tok = activeShareToken.value
          const updated = tok
            ? await shareReadApi.getSource(tok, sourceId)
            : await sourceApi.get(sourceId)
          upsertSource(updated)
        } catch {
          /* ignore missing source */
        }
      })
      .finally(() => {
        inFlightSourceWaits.delete(sourceId)
      })
  }

  const maybeWatchSource = (source: Source) => {
    if (source.status === 'pending' || source.status === 'processing') {
      watchPendingSource(source.id)
    }
  }

  const fetchSources = async (notebookId: string) => {
    loading.value = true
    try {
      const tok = activeShareToken.value
      sources.value = tok
        ? await shareReadApi.listSources(tok)
        : await sourceApi.list(notebookId)
      sources.value.forEach((source) => {
        maybeWatchSource(source)
      })
    } finally {
      loading.value = false
    }
  }

  const addSource = async (notebookId: string, data: { title?: string; type: string; url?: string }) => {
    const s = await sourceApi.add(notebookId, data)
    sources.value.unshift(s)
    maybeWatchSource(s)
    return s
  }

  const uploadSource = async (notebookId: string, file: File, title?: string) => {
    const s = await sourceApi.upload(notebookId, file, title)
    sources.value.unshift(s)
    maybeWatchSource(s)
    return s
  }

  const uploadSourceInBackground = (notebookId: string, file: File) => {
    const snackbar = useSnackbarStore()
    const tempId = `__uploading_${Date.now()}_${Math.random().toString(36).slice(2)}`
    const placeholder: Source = {
      id: tempId,
      notebook_id: notebookId,
      title: file.name,
      type: 'file',
      original_url: null,
      is_active: true,
      status: 'uploading',
      created_at: new Date().toISOString(),
    }
    sources.value.unshift(placeholder)

    sourceApi.upload(notebookId, file)
      .then((s) => {
        const idx = sources.value.findIndex((src) => src.id === tempId)
        if (idx !== -1) {
          sources.value.splice(idx, 1, s)
        } else {
          sources.value.unshift(s)
        }
        maybeWatchSource(s)
        snackbar.success('文件上传成功')
      })
      .catch((err) => {
        sources.value = sources.value.filter((src) => src.id !== tempId)
        const detail = err?.response?.data?.detail
        snackbar.error(detail || '文件上传失败')
      })
  }

  const toggleSource = async (sourceId: string, isActive: boolean) => {
    const s = await sourceApi.update(sourceId, { is_active: isActive })
    const idx = sources.value.findIndex((src) => src.id === sourceId)
    if (idx !== -1) {
      sources.value[idx] = s
    }
  }

  const toggleAllSources = async (isActive: boolean) => {
    const toggleable = sources.value.filter((s) => s.status !== 'uploading')
    toggleable.forEach((s) => { s.is_active = isActive })
    await Promise.all(
      toggleable.map((s) => sourceApi.update(s.id, { is_active: isActive }).catch(() => {}))
    )
  }

  const removeSource = async (sourceId: string) => {
    await sourceApi.remove(sourceId)
    sources.value = sources.value.filter((s) => s.id !== sourceId)
  }

  const getContent = async (sourceId: string) => {
    contentLoading.value = true
    try {
      const tok = activeShareToken.value
      currentContent.value = tok
        ? await shareReadApi.getSourceContent(tok, sourceId)
        : await sourceApi.getContent(sourceId)
      return currentContent.value
    } finally {
      contentLoading.value = false
    }
  }

  const clearContent = () => {
    currentContent.value = null
    highlightRequest.value = null
  }

  const highlightChunk = async (request: HighlightRequest) => {
    highlightRequest.value = request
    await getContent(request.sourceId)
    showContentViewer.value = true
  }

  const clearHighlight = () => {
    highlightRequest.value = null
  }

  const activeSourceIds = computed(() =>
    sources.value
      .filter((s) => s.is_active && s.status !== 'uploading')
      .map((s) => s.id)
  )

  return {
    sources,
    loading,
    contentLoading,
    currentContent,
    highlightRequest,
    showContentViewer,
    activeSourceIds,
    setShareToken,
    fetchSources,
    addSource,
    uploadSource,
    uploadSourceInBackground,
    toggleSource,
    toggleAllSources,
    removeSource,
    getContent,
    clearContent,
    highlightChunk,
    clearHighlight,
  }
})
