import { defineStore } from 'pinia'
import { ref } from 'vue'
import { shareReadApi } from '@/api/shareRead'
import { studioApi } from '@/api/studio'
import { streamTaskUntilTerminal } from '@/api/taskEvents'
import type {
  MindMapData,
  SlideDeckData,
  InfographicData,
  ReportData,
  PodcastData,
  SlideDeckCreateOptions,
  SlideDeckUpdateOptions,
  InfographicCreateOptions,
  InfographicUpdateOptions,
  ReportCreateOptions,
  ReportUpdateOptions,
  PodcastCreateOptions,
} from '@/api/studio'

export const useStudioStore = defineStore('studio', () => {
  /** When set, list/detail fetches use public share API (read-only). */
  const activeShareToken = ref<string | null>(null)

  const setShareToken = (token: string | null) => {
    activeShareToken.value = token
  }

  const mindMaps = ref<MindMapData[]>([])
  const slideDecks = ref<SlideDeckData[]>([])
  const infographics = ref<InfographicData[]>([])
  const reports = ref<ReportData[]>([])
  const podcasts = ref<PodcastData[]>([])
  const loading = ref(false)
  /** Tracks in-flight HTTP calls only (not background polling). */
  let loadingDepth = 0
  const beginLoading = () => {
    loadingDepth += 1
    loading.value = true
  }
  const endLoading = () => {
    loadingDepth -= 1
    if (loadingDepth <= 0) {
      loadingDepth = 0
      loading.value = false
    }
  }

  const fetchMindMaps = async (notebookId: string) => {
    const tok = activeShareToken.value
    mindMaps.value = tok
      ? await shareReadApi.listMindMaps(tok)
      : await studioApi.listMindMaps(notebookId)
    mindMaps.value.forEach((mindMap) => {
      if (mindMap.status === 'pending' || mindMap.status === 'processing') {
        watchPendingTask<MindMapData>({
          resourceType: 'mindmap',
          resourceId: mindMap.id,
          fetch: () =>
            tok
              ? shareReadApi.getMindMap(tok, mindMap.id)
              : studioApi.getMindMap(mindMap.id),
          onUpdate: (updated) => {
            const idx = mindMaps.value.findIndex((m) => m.id === mindMap.id)
            if (idx !== -1) mindMaps.value[idx] = updated
          },
          errorMessage: 'Mind map generation failed',
        })
      }
    })
  }

  const POLL_INTERVAL_MS = 2500
  const FIRST_POLL_DELAY_MS = 500
  const MAX_CONSECUTIVE_POLL_ERRORS = 5

  type PollableData = { id: string; status?: string; error_message?: string | null }
  type TaskResourceType =
    | 'mindmap'
    | 'slide'
    | 'infographic'
    | 'report'
    | 'podcast'
  const inFlightTaskWaits = new Set<string>()

  const buildTaskWaitKey = (resourceType: TaskResourceType, resourceId: string) => {
    return `${resourceType}:${resourceId}`
  }

  const pollUntilReady = <T extends PollableData>(options: {
    fetch: () => Promise<T>
    onUpdate?: (data: T) => void
    errorMessage: string
    maxConsecutiveErrors?: number
  }): Promise<T> => {
    const {
      fetch: doFetch,
      onUpdate,
      errorMessage,
      maxConsecutiveErrors = MAX_CONSECUTIVE_POLL_ERRORS,
    } = options
    return new Promise((resolve, reject) => {
      let consecutiveErrors = 0
      const tick = async () => {
        try {
          const updated = await doFetch()
          consecutiveErrors = 0
          if (updated.status === 'ready') {
            resolve(updated)
            return
          }
          if (updated.status === 'error') {
            reject(new Error(updated.error_message || errorMessage))
            return
          }
          onUpdate?.(updated)
          setTimeout(tick, POLL_INTERVAL_MS)
        } catch (e) {
          consecutiveErrors += 1
          if (consecutiveErrors >= maxConsecutiveErrors) {
            reject(e)
            return
          }
          setTimeout(tick, POLL_INTERVAL_MS)
        }
      }
      setTimeout(tick, FIRST_POLL_DELAY_MS)
    })
  }

  const waitUntilReady = async <T extends PollableData>(options: {
    resourceType: TaskResourceType
    resourceId: string
    fetch: () => Promise<T>
    onUpdate?: (data: T) => void
    errorMessage: string
    maxConsecutiveErrors?: number
  }): Promise<T> => {
    const {
      resourceType,
      resourceId,
      fetch: doFetch,
      onUpdate,
      errorMessage,
      maxConsecutiveErrors,
    } = options

    if (activeShareToken.value) {
      return pollUntilReady({
        fetch: doFetch,
        onUpdate,
        errorMessage,
        maxConsecutiveErrors,
      })
    }
    try {
      const updated = await streamTaskUntilTerminal<T>({
        resourceType,
        resourceId,
        fetchCurrent: doFetch,
      })
      onUpdate?.(updated)
      if (updated.status === 'error') {
        throw new Error(updated.error_message || errorMessage)
      }
      return updated
    } catch {
      return pollUntilReady({
        fetch: doFetch,
        onUpdate,
        errorMessage,
        maxConsecutiveErrors,
      })
    }
  }

  const watchPendingTask = <T extends PollableData>(options: {
    resourceType: TaskResourceType
    resourceId: string
    fetch: () => Promise<T>
    onUpdate?: (data: T) => void
    errorMessage: string
    maxConsecutiveErrors?: number
  }) => {
    const {
      resourceType,
      resourceId,
      fetch: doFetch,
      onUpdate,
      errorMessage,
      maxConsecutiveErrors,
    } = options
    const key = buildTaskWaitKey(resourceType, resourceId)

    if (inFlightTaskWaits.has(key)) {
      return
    }

    inFlightTaskWaits.add(key)
    void waitUntilReady({
      resourceType,
      resourceId,
      fetch: doFetch,
      onUpdate,
      errorMessage,
      maxConsecutiveErrors,
    })
      .then((updated) => {
        onUpdate?.(updated)
      })
      .catch(async () => {
        try {
          const current = await doFetch()
          onUpdate?.(current)
        } catch {
          /* ignore */
        }
      })
      .finally(() => {
        inFlightTaskWaits.delete(key)
      })
  }

  const pollMindMapUntilReady = (mindmapId: string): Promise<MindMapData> => {
    const tok = activeShareToken.value
    return waitUntilReady<MindMapData>({
      resourceType: 'mindmap',
      resourceId: mindmapId,
      fetch: () =>
        tok
          ? shareReadApi.getMindMap(tok, mindmapId)
          : studioApi.getMindMap(mindmapId),
      onUpdate: (updated) => {
        const idx = mindMaps.value.findIndex((m) => m.id === mindmapId)
        if (idx !== -1) mindMaps.value[idx] = updated
      },
      errorMessage: 'Mind map generation failed',
    })
  }

  const generateMindMap = async (
    notebookId: string,
    sourceIds: string[],
    title: string = 'Mind Map',
    outputLanguage: string = '简体中文',
  ) => {
    beginLoading()
    try {
      const mindMap = await studioApi.generateMindMap(notebookId, {
        title,
        source_ids: sourceIds.length > 0 ? sourceIds : undefined,
        output_language: outputLanguage,
      })
      mindMaps.value.unshift(mindMap)
      if (mindMap.status === 'pending' || mindMap.status === 'processing') {
        watchPendingTask<MindMapData>({
          resourceType: 'mindmap',
          resourceId: mindMap.id,
          fetch: () => studioApi.getMindMap(mindMap.id),
          onUpdate: (updated) => {
            const idx = mindMaps.value.findIndex((m) => m.id === mindMap.id)
            if (idx !== -1) mindMaps.value[idx] = updated
          },
          errorMessage: 'Mind map generation failed',
        })
      }
      return mindMap
    } finally {
      endLoading()
    }
  }

  const removeMindMap = async (mindmapId: string) => {
    await studioApi.deleteMindMap(mindmapId)
    mindMaps.value = mindMaps.value.filter((m) => m.id !== mindmapId)
  }

  const fetchSlideDecks = async (notebookId: string) => {
    const tok = activeShareToken.value
    slideDecks.value = tok
      ? await shareReadApi.listSlides(tok)
      : await studioApi.listSlides(notebookId)
    slideDecks.value.forEach((deck) => {
      if (deck.status === 'pending' || deck.status === 'processing') {
        watchPendingTask<SlideDeckData>({
          resourceType: 'slide',
          resourceId: deck.id,
          fetch: () =>
            tok ? shareReadApi.getSlide(tok, deck.id) : studioApi.getSlide(deck.id),
          onUpdate: (updated) => {
            const idx = slideDecks.value.findIndex((d) => d.id === deck.id)
            if (idx !== -1) slideDecks.value[idx] = updated
          },
          errorMessage: 'Slide deck generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
    })
  }

  const pollSlideDeckUntilReady = (slideId: string): Promise<SlideDeckData> => {
    const tok = activeShareToken.value
    return waitUntilReady<SlideDeckData>({
      resourceType: 'slide',
      resourceId: slideId,
      fetch: () =>
        tok
          ? shareReadApi.getSlide(tok, slideId)
          : studioApi.getSlide(slideId),
      onUpdate: (updated) => {
        const idx = slideDecks.value.findIndex((d) => d.id === slideId)
        if (idx !== -1) slideDecks.value[idx] = updated
      },
      errorMessage: 'Slide deck generation failed',
      maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
    })
  }

  const generateSlides = async (notebookId: string, data: SlideDeckCreateOptions) => {
    beginLoading()
    try {
      const deck = await studioApi.generateSlides(notebookId, data)
      slideDecks.value.unshift(deck)
      if (deck.status === 'pending' || deck.status === 'processing') {
        watchPendingTask<SlideDeckData>({
          resourceType: 'slide',
          resourceId: deck.id,
          fetch: () => studioApi.getSlide(deck.id),
          onUpdate: (updated) => {
            const idx = slideDecks.value.findIndex((d) => d.id === deck.id)
            if (idx !== -1) slideDecks.value[idx] = updated
          },
          errorMessage: 'Slide deck generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return deck
    } finally {
      endLoading()
    }
  }

  const updateSlideDeck = async (slideId: string, data: SlideDeckUpdateOptions) => {
    const deck = await studioApi.updateSlide(slideId, data)
    const idx = slideDecks.value.findIndex((d) => d.id === slideId)
    if (idx !== -1) slideDecks.value[idx] = deck
    return deck
  }

  const regenerateSlideDeck = async (slideId: string, data: SlideDeckUpdateOptions) => {
    beginLoading()
    try {
      const deck = await studioApi.regenerateSlide(slideId, data)
      const idx = slideDecks.value.findIndex((d) => d.id === slideId)
      if (idx !== -1) slideDecks.value[idx] = deck
      if (deck.status === 'pending' || deck.status === 'processing') {
        watchPendingTask<SlideDeckData>({
          resourceType: 'slide',
          resourceId: deck.id,
          fetch: () => studioApi.getSlide(deck.id),
          onUpdate: (updated) => {
            const i = slideDecks.value.findIndex((d) => d.id === deck.id)
            if (i !== -1) slideDecks.value[i] = updated
          },
          errorMessage: 'Slide deck generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return deck
    } finally {
      endLoading()
    }
  }

  const fetchInfographics = async (notebookId: string) => {
    const tok = activeShareToken.value
    infographics.value = tok
      ? await shareReadApi.listInfographics(tok)
      : await studioApi.listInfographics(notebookId)
    infographics.value.forEach((info) => {
      if (info.status === 'pending' || info.status === 'processing') {
        watchPendingTask<InfographicData>({
          resourceType: 'infographic',
          resourceId: info.id,
          fetch: () =>
            tok
              ? shareReadApi.getInfographic(tok, info.id)
              : studioApi.getInfographic(info.id),
          onUpdate: (updated) => {
            const idx = infographics.value.findIndex((i) => i.id === info.id)
            if (idx !== -1) infographics.value[idx] = updated
          },
          errorMessage: 'Infographic generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
    })
  }

  const pollInfographicUntilReady = (infographicId: string): Promise<InfographicData> => {
    const tok = activeShareToken.value
    return waitUntilReady<InfographicData>({
      resourceType: 'infographic',
      resourceId: infographicId,
      fetch: () =>
        tok
          ? shareReadApi.getInfographic(tok, infographicId)
          : studioApi.getInfographic(infographicId),
      onUpdate: (updated) => {
        const idx = infographics.value.findIndex((i) => i.id === infographicId)
        if (idx !== -1) infographics.value[idx] = updated
      },
      errorMessage: 'Infographic generation failed',
      maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
    })
  }

  const generateInfographic = async (
    notebookId: string,
    data: InfographicCreateOptions,
  ) => {
    beginLoading()
    try {
      const info = await studioApi.generateInfographic(notebookId, data)
      infographics.value.unshift(info)
      if (info.status === 'pending' || info.status === 'processing') {
        watchPendingTask<InfographicData>({
          resourceType: 'infographic',
          resourceId: info.id,
          fetch: () => studioApi.getInfographic(info.id),
          onUpdate: (updated) => {
            const idx = infographics.value.findIndex((i) => i.id === info.id)
            if (idx !== -1) infographics.value[idx] = updated
          },
          errorMessage: 'Infographic generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return info
    } finally {
      endLoading()
    }
  }

  const updateInfographic = async (infographicId: string, data: InfographicUpdateOptions) => {
    const info = await studioApi.updateInfographic(infographicId, data)
    const idx = infographics.value.findIndex((i) => i.id === infographicId)
    if (idx !== -1) infographics.value[idx] = info
    return info
  }

  const regenerateInfographic = async (infographicId: string, data: InfographicUpdateOptions) => {
    beginLoading()
    try {
      const info = await studioApi.regenerateInfographic(infographicId, data)
      const idx = infographics.value.findIndex((i) => i.id === infographicId)
      if (idx !== -1) infographics.value[idx] = info
      if (info.status === 'pending' || info.status === 'processing') {
        watchPendingTask<InfographicData>({
          resourceType: 'infographic',
          resourceId: info.id,
          fetch: () => studioApi.getInfographic(info.id),
          onUpdate: (updated) => {
            const i = infographics.value.findIndex((x) => x.id === info.id)
            if (i !== -1) infographics.value[i] = updated
          },
          errorMessage: 'Infographic generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return info
    } finally {
      endLoading()
    }
  }

  const removeInfographic = async (infographicId: string) => {
    await studioApi.deleteInfographic(infographicId)
    infographics.value = infographics.value.filter((i) => i.id !== infographicId)
  }

  const fetchReports = async (notebookId: string) => {
    const tok = activeShareToken.value
    reports.value = tok
      ? await shareReadApi.listReports(tok)
      : await studioApi.listReports(notebookId)
    reports.value.forEach((report) => {
      if (report.status === 'pending' || report.status === 'processing') {
        watchPendingTask<ReportData>({
          resourceType: 'report',
          resourceId: report.id,
          fetch: () =>
            tok
              ? shareReadApi.getReport(tok, report.id)
              : studioApi.getReport(report.id),
          onUpdate: (updated) => {
            const idx = reports.value.findIndex((r) => r.id === report.id)
            if (idx !== -1) reports.value[idx] = updated
          },
          errorMessage: 'Report generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
    })
  }

  const pollReportUntilReady = (reportId: string): Promise<ReportData> => {
    const tok = activeShareToken.value
    return waitUntilReady<ReportData>({
      resourceType: 'report',
      resourceId: reportId,
      fetch: () =>
        tok
          ? shareReadApi.getReport(tok, reportId)
          : studioApi.getReport(reportId),
      onUpdate: (updated) => {
        const idx = reports.value.findIndex((r) => r.id === reportId)
        if (idx !== -1) reports.value[idx] = updated
      },
      errorMessage: 'Report generation failed',
      maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
    })
  }

  const generateReport = async (notebookId: string, data: ReportCreateOptions) => {
    beginLoading()
    try {
      const report = await studioApi.generateReport(notebookId, data)
      reports.value.unshift(report)
      if (report.status === 'pending' || report.status === 'processing') {
        watchPendingTask<ReportData>({
          resourceType: 'report',
          resourceId: report.id,
          fetch: () => studioApi.getReport(report.id),
          onUpdate: (updated) => {
            const idx = reports.value.findIndex((r) => r.id === report.id)
            if (idx !== -1) reports.value[idx] = updated
          },
          errorMessage: 'Report generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return report
    } finally {
      endLoading()
    }
  }

  const updateReport = async (reportId: string, data: ReportUpdateOptions) => {
    const report = await studioApi.updateReport(reportId, data)
    const idx = reports.value.findIndex((r) => r.id === reportId)
    if (idx !== -1) reports.value[idx] = report
    return report
  }

  const regenerateReport = async (reportId: string, data: ReportUpdateOptions) => {
    beginLoading()
    try {
      const report = await studioApi.regenerateReport(reportId, data)
      const idx = reports.value.findIndex((r) => r.id === reportId)
      if (idx !== -1) reports.value[idx] = report
      if (report.status === 'pending' || report.status === 'processing') {
        watchPendingTask<ReportData>({
          resourceType: 'report',
          resourceId: report.id,
          fetch: () => studioApi.getReport(report.id),
          onUpdate: (updated) => {
            const i = reports.value.findIndex((r) => r.id === report.id)
            if (i !== -1) reports.value[i] = updated
          },
          errorMessage: 'Report generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return report
    } finally {
      endLoading()
    }
  }

  const removeReport = async (reportId: string) => {
    await studioApi.deleteReport(reportId)
    reports.value = reports.value.filter((r) => r.id !== reportId)
  }

  const fetchPodcasts = async (notebookId: string) => {
    const tok = activeShareToken.value
    podcasts.value = tok
      ? await shareReadApi.listPodcasts(tok)
      : await studioApi.listPodcasts(notebookId)
    podcasts.value.forEach((podcast) => {
      if (podcast.status === 'pending' || podcast.status === 'processing') {
        watchPendingTask<PodcastData>({
          resourceType: 'podcast',
          resourceId: podcast.id,
          fetch: () =>
            tok
              ? shareReadApi.getPodcast(tok, podcast.id)
              : studioApi.getPodcast(podcast.id),
          onUpdate: (updated) => {
            const idx = podcasts.value.findIndex((p) => p.id === podcast.id)
            if (idx !== -1) podcasts.value[idx] = updated
          },
          errorMessage: 'Podcast generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
    })
  }

  const generatePodcast = async (
    notebookId: string,
    data: PodcastCreateOptions,
  ) => {
    beginLoading()
    try {
      const podcast = await studioApi.generatePodcast(notebookId, data)
      podcasts.value.unshift(podcast)
      if (podcast.status === 'pending' || podcast.status === 'processing') {
        watchPendingTask<PodcastData>({
          resourceType: 'podcast',
          resourceId: podcast.id,
          fetch: () => studioApi.getPodcast(podcast.id),
          onUpdate: (updated) => {
            const idx = podcasts.value.findIndex((p) => p.id === podcast.id)
            if (idx !== -1) podcasts.value[idx] = updated
          },
          errorMessage: 'Podcast generation failed',
          maxConsecutiveErrors: MAX_CONSECUTIVE_POLL_ERRORS,
        })
      }
      return podcast
    } finally {
      endLoading()
    }
  }

  const removePodcast = async (podcastId: string) => {
    await studioApi.deletePodcast(podcastId)
    podcasts.value = podcasts.value.filter((p) => p.id !== podcastId)
  }

  return {
    mindMaps,
    slideDecks,
    infographics,
    loading,
    setShareToken,
    fetchMindMaps,
    generateMindMap,
    removeMindMap,
    fetchSlideDecks,
    generateSlides,
    updateSlideDeck,
    regenerateSlideDeck,
    fetchInfographics,
    generateInfographic,
    updateInfographic,
    regenerateInfographic,
    removeInfographic,
    reports,
    fetchReports,
    generateReport,
    updateReport,
    regenerateReport,
    removeReport,
    podcasts,
    fetchPodcasts,
    generatePodcast,
    removePodcast,
  }
})
