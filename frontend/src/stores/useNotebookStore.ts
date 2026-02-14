import { defineStore } from 'pinia'
import { ref } from 'vue'
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
    createNotebook,
    updateNotebook,
    deleteNotebook,
  }
})
