import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sourceApi } from '@/api/source'
import type { Source } from '@/api/source'

export interface SourceContent {
  id: string
  title: string
  raw_content: string | null
  chunk_count: number
  file_url: string | null  // 图片时为本源文件接口路径，前端用 getFile 取二进制流再显示
}

export const useSourceStore = defineStore('source', () => {
  const sources = ref<Source[]>([])
  const loading = ref(false)
  const contentLoading = ref(false)
  const currentContent = ref<SourceContent | null>(null)

  const fetchSources = async (notebookId: string) => {
    loading.value = true
    try {
      sources.value = await sourceApi.list(notebookId)
    } finally {
      loading.value = false
    }
  }

  const addSource = async (notebookId: string, data: { title?: string; type: string; url?: string }) => {
    const s = await sourceApi.add(notebookId, data)
    sources.value.unshift(s)
    return s
  }

  const uploadSource = async (notebookId: string, file: File, title?: string) => {
    const s = await sourceApi.upload(notebookId, file, title)
    sources.value.unshift(s)
    return s
  }

  const toggleSource = async (sourceId: string, isActive: boolean) => {
    const s = await sourceApi.update(sourceId, { is_active: isActive })
    const idx = sources.value.findIndex((src) => src.id === sourceId)
    if (idx !== -1) {
      sources.value[idx] = s
    }
  }

  const removeSource = async (sourceId: string) => {
    await sourceApi.remove(sourceId)
    sources.value = sources.value.filter((s) => s.id !== sourceId)
  }

  const getContent = async (sourceId: string) => {
    contentLoading.value = true
    try {
      currentContent.value = await sourceApi.getContent(sourceId)
      return currentContent.value
    } finally {
      contentLoading.value = false
    }
  }

  /** Set minimal content for image source (avoids extra GET /content for image). */
  const setContentForImage = (source: Source) => {
    currentContent.value = {
      id: source.id,
      title: source.title,
      raw_content: null,
      chunk_count: 0,
      file_url: `/api/sources/${source.id}/file`,
    }
  }

  const clearContent = () => {
    currentContent.value = null
  }

  const activeSourceIds = computed(() =>
    sources.value.filter((s) => s.is_active).map((s) => s.id)
  )

  return {
    sources,
    loading,
    contentLoading,
    currentContent,
    activeSourceIds,
    fetchSources,
    addSource,
    uploadSource,
    toggleSource,
    removeSource,
    getContent,
    setContentForImage,
    clearContent,
  }
})
