import { defineStore } from 'pinia'
import { ref } from 'vue'
import { shareReadApi } from '@/api/shareRead'
import { notebookApi } from '@/api/notebook'
import type { Notebook } from '@/api/notebook'

export const useNotebookStore = defineStore('notebook', () => {
  const notebooks = ref<Notebook[]>([])
  const currentNotebook = ref<Notebook | null>(null)
  const loading = ref(false)

  const fetchNotebooks = async () => {
    loading.value = true
    try {
      const res = await notebookApi.list()
      notebooks.value = res.notebooks
    } finally {
      loading.value = false
    }
  }

  const fetchNotebook = async (id: string) => {
    loading.value = true
    try {
      currentNotebook.value = await notebookApi.get(id)
    } finally {
      loading.value = false
    }
  }

  const fetchSharedNotebookPreview = async (shareToken: string) => {
    loading.value = true
    try {
      const dto = await shareReadApi.getNotebook(shareToken)
      currentNotebook.value = {
        id: dto.id,
        user_id: '',
        title: dto.title,
        description: dto.description,
        created_at: dto.created_at,
        updated_at: dto.updated_at,
        source_count: dto.source_count,
        share_enabled: false,
      }
    } catch (e) {
      currentNotebook.value = null
      throw e
    } finally {
      loading.value = false
    }
  }

  const createNotebook = async (title: string, description: string = '') => {
    const nb = await notebookApi.create({ title, description })
    notebooks.value.unshift(nb)
    return nb
  }

  const updateNotebook = async (id: string, data: { title?: string; description?: string }) => {
    const nb = await notebookApi.update(id, data)
    const idx = notebooks.value.findIndex((n) => n.id === id)
    if (idx !== -1) {
      notebooks.value[idx] = nb
    }
    if (currentNotebook.value?.id === id) {
      currentNotebook.value = nb
    }
    return nb
  }

  const deleteNotebook = async (id: string) => {
    await notebookApi.remove(id)
    notebooks.value = notebooks.value.filter((n) => n.id !== id)
    if (currentNotebook.value?.id === id) {
      currentNotebook.value = null
    }
  }

  return {
    notebooks,
    currentNotebook,
    loading,
    fetchNotebooks,
    fetchNotebook,
    fetchSharedNotebookPreview,
    createNotebook,
    updateNotebook,
    deleteNotebook,
  }
})
