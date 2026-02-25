import { defineStore } from 'pinia'
import { ref } from 'vue'
import { studioApi } from '@/api/studio'
import type { MindMapData, SlideDeckData, InfographicData } from '@/api/studio'

export const useStudioStore = defineStore('studio', () => {
  const mindMaps = ref<MindMapData[]>([])
  const slideDecks = ref<SlideDeckData[]>([])
  const infographics = ref<InfographicData[]>([])
  const loading = ref(false)

  const fetchMindMaps = async (notebookId: string) => {
    mindMaps.value = await studioApi.listMindMaps(notebookId)
  }

  const POLL_INTERVAL_MS = 2500
  const pollMindMapUntilReady = (mindmapId: string): Promise<MindMapData> => {
    return new Promise((resolve, reject) => {
      const tick = async () => {
        try {
          const updated = await studioApi.getMindMap(mindmapId)
          if (updated.status === 'ready') {
            resolve(updated)
            return
          }
          if (updated.status === 'error') {
            reject(new Error('Mind map generation failed'))
            return
          }
          const idx = mindMaps.value.findIndex((m) => m.id === mindmapId)
          if (idx !== -1) mindMaps.value[idx] = updated
          setTimeout(tick, POLL_INTERVAL_MS)
        } catch (e) {
          reject(e)
        }
      }
      tick()
    })
  }

  const generateMindMap = async (notebookId: string, sourceIds: string[], title: string = 'Mind Map') => {
    loading.value = true
    try {
      const mindMap = await studioApi.generateMindMap(notebookId, {
        title,
        source_ids: sourceIds.length > 0 ? sourceIds : undefined,
      })
      mindMaps.value.unshift(mindMap)
      if (mindMap.status === 'pending' || mindMap.status === 'processing') {
        const updated = await pollMindMapUntilReady(mindMap.id)
        const idx = mindMaps.value.findIndex((m) => m.id === mindMap.id)
        if (idx !== -1) mindMaps.value[idx] = updated
        return updated
      }
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

  const pollSlideDeckUntilReady = (slideId: string): Promise<SlideDeckData> => {
    return new Promise((resolve, reject) => {
      const tick = async () => {
        try {
          const updated = await studioApi.getSlide(slideId)
          if (updated.status === 'ready') {
            resolve(updated)
            return
          }
          if (updated.status === 'error') {
            reject(new Error('Slide deck generation failed'))
            return
          }
          const idx = slideDecks.value.findIndex((d) => d.id === slideId)
          if (idx !== -1) slideDecks.value[idx] = updated
          setTimeout(tick, POLL_INTERVAL_MS)
        } catch (e) {
          reject(e)
        }
      }
      tick()
    })
  }

  const generateSlides = async (notebookId: string, data: { title?: string; theme?: string }) => {
    loading.value = true
    try {
      const deck = await studioApi.generateSlides(notebookId, data)
      slideDecks.value.unshift(deck)
      if (deck.status === 'pending' || deck.status === 'processing') {
        const updated = await pollSlideDeckUntilReady(deck.id)
        const idx = slideDecks.value.findIndex((d) => d.id === deck.id)
        if (idx !== -1) slideDecks.value[idx] = updated
        return updated
      }
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
