import { defineStore } from 'pinia'
import { ref } from 'vue'
import { studioApi } from '@/api/studio'
import type { MindMapData, SlideDeckData, InfographicData } from '@/api/studio'

export const useStudioStore = defineStore('studio', () => {
  const activeTab = ref<'notes' | 'mindmap' | 'slides' | 'infographic' | 'reports'>('notes')
  const mindMaps = ref<MindMapData[]>([])
  const slideDecks = ref<SlideDeckData[]>([])
  const infographics = ref<InfographicData[]>([])
  const loading = ref(false)

  const fetchMindMaps = async (notebookId: string) => {
    mindMaps.value = await studioApi.listMindMaps(notebookId)
  }

  const generateMindMap = async (notebookId: string, sourceIds: string[], title: string = 'Mind Map') => {
    loading.value = true
    try {
      const mindMap = await studioApi.generateMindMap(notebookId, {
        title,
        source_ids: sourceIds.length > 0 ? sourceIds : undefined,
      })
      mindMaps.value.unshift(mindMap)
      return mindMap
    } finally {
      loading.value = false
    }
  }

  const removeMindMap = async (mindmapId: string) => {
    await studioApi.deleteMindMap(mindmapId)
    mindMaps.value = mindMaps.value.filter((m) => m.id !== mindmapId)
  }

  const fetchSlideDecks = async (notebookId: string) => {
    slideDecks.value = await studioApi.listSlides(notebookId)
  }

  const generateSlides = async (notebookId: string, data: { title?: string; theme?: string }) => {
    loading.value = true
    try {
      const deck = await studioApi.generateSlides(notebookId, data)
      slideDecks.value.unshift(deck)
      return deck
    } finally {
      loading.value = false
    }
  }

  const fetchInfographics = async (notebookId: string) => {
    infographics.value = await studioApi.listInfographics(notebookId)
  }

  const generateInfographic = async (notebookId: string, data: { title?: string; template_type?: string }) => {
    loading.value = true
    try {
      const info = await studioApi.generateInfographic(notebookId, data)
      infographics.value.unshift(info)
      return info
    } finally {
      loading.value = false
    }
  }

  return {
    activeTab,
    mindMaps,
    slideDecks,
    infographics,
    loading,
    fetchMindMaps,
    generateMindMap,
    removeMindMap,
    fetchSlideDecks,
    generateSlides,
    fetchInfographics,
    generateInfographic,
  }
})
