import client from './client'
import type { GraphData } from '@/components/studio/MindMapViewer.vue'

export interface MindMapData {
  id: string
  notebook_id: string
  title: string
  suggested_filename?: string | null
  graph_data: GraphData | null
  status?: string
  error_message?: string | null
  source_count?: number | null
  created_at: string
}

export interface SlideDeckData {
  id: string
  notebook_id: string
  title: string
  suggested_filename?: string | null
  theme: string
  slides_data: Record<string, unknown> | null
  status: string
  error_message?: string | null
  file_path: string | null
  slide_style?: string
  slide_audience?: string
  slide_language?: string
  slide_duration?: string
  slide_custom_prompt?: string | null
  source_count?: number | null
  created_at: string
}

export interface SlideDeckImageVariantData {
  filename?: string | null
  content_type?: string | null
  width?: number | null
  height?: number | null
  object_key?: string | null
  url?: string | null
  proxy_url: string
  preferred_url: string
}

export interface SlideDeckImageData {
  index: number
  slide_number: number
  title: string
  filename?: string | null
  variants: {
    thumb: SlideDeckImageVariantData
    preview: SlideDeckImageVariantData
    export: SlideDeckImageVariantData
  }
}

export interface SlideDeckImagesManifest {
  slide_id: string
  image_count: number
  images: SlideDeckImageData[]
  cache_ttl_seconds: number
}

export interface SlideDeckCreateOptions {
  title?: string
  theme?: string
  source_ids?: string[]
  focus_topic?: string | null
  slide_style?: string
  slide_audience?: string
  slide_language?: string
  slide_duration?: string
  slide_custom_prompt?: string | null
}

export interface SlideDeckUpdateOptions {
  title?: string
  theme?: string
  slide_style?: string
  slide_audience?: string
  slide_language?: string
  slide_duration?: string
  slide_custom_prompt?: string | null
}

export interface SlideDeckPdfUrlOptions {
  download?: boolean
  filename?: string
}

export interface InfographicData {
  id: string
  notebook_id: string
  title: string
  suggested_filename?: string | null
  layout_data: Record<string, unknown> | null
  file_path: string | null
  status: string
  error_message?: string | null
  infographic_style?: string
  infographic_language?: string
  infographic_direction?: string
  infographic_visual_style?: string
  infographic_custom_prompt?: string | null
  source_count?: number | null
  created_at: string
}

export interface InfographicCreateOptions {
  title?: string
  source_ids?: string[]
  infographic_style?: string
  infographic_language?: string
  infographic_direction?: string
  infographic_visual_style?: string
  infographic_custom_prompt?: string | null
}

export interface InfographicUpdateOptions {
  title?: string
  infographic_style?: string
  infographic_language?: string
  infographic_direction?: string
  infographic_visual_style?: string
  infographic_custom_prompt?: string | null
}

export interface ReportData {
  id: string
  notebook_id: string
  title: string
  suggested_filename?: string | null
  report_format: string
  report_language: string
  report_custom_prompt?: string | null
  content?: string | null
  status: string
  error_message?: string | null
  source_count?: number | null
  created_at: string
}

export interface ReportCreateOptions {
  title?: string
  source_ids?: string[]
  report_format?: string
  report_language?: string
  report_custom_prompt?: string | null
}

export interface ReportUpdateOptions {
  title?: string
  report_format?: string
  report_language?: string
  report_custom_prompt?: string | null
}

export interface PodcastData {
  id: string
  notebook_id: string
  title: string
  suggested_filename?: string | null
  audio_format: string
  audio_language: string
  audio_length: string
  audio_focus_prompt?: string | null
  file_path: string | null
  transcript?: string | null
  status: string
  error_message?: string | null
  source_count?: number | null
  created_at: string
}

export interface PodcastCreateOptions {
  title?: string
  source_ids?: string[]
  audio_format?: string
  audio_language?: string
  audio_length?: string
  audio_focus_prompt?: string | null
}

export const studioApi = {
  // Mind Map
  generateMindMap: async (notebookId: string, data: { title?: string; source_ids?: string[]; output_language?: string }): Promise<MindMapData> => {
    const res = await client.post(`/notebooks/${notebookId}/mindmap`, data)
    return res.data
  },

  listMindMaps: async (notebookId: string): Promise<MindMapData[]> => {
    const res = await client.get(`/notebooks/${notebookId}/mindmaps`)
    return res.data
  },

  getMindMap: async (mindmapId: string): Promise<MindMapData> => {
    const res = await client.get(`/mindmaps/${mindmapId}`)
    return res.data
  },

  deleteMindMap: async (mindmapId: string): Promise<void> => {
    await client.delete(`/mindmaps/${mindmapId}`)
  },

  // Slides
  generateSlides: async (notebookId: string, data: SlideDeckCreateOptions): Promise<SlideDeckData> => {
    const res = await client.post(`/notebooks/${notebookId}/slides`, data)
    return res.data
  },

  regenerateSlide: async (slideId: string, data: SlideDeckUpdateOptions): Promise<SlideDeckData> => {
    const res = await client.post(`/slides/${slideId}/regenerate`, data)
    return res.data
  },

  listSlides: async (notebookId: string): Promise<SlideDeckData[]> => {
    const res = await client.get(`/notebooks/${notebookId}/slides`)
    return res.data
  },

  getSlide: async (slideId: string): Promise<SlideDeckData> => {
    const res = await client.get(`/slides/${slideId}`)
    return res.data
  },

  getSlidePdfUrl: async (
    slideId: string,
    options: SlideDeckPdfUrlOptions = {}
  ): Promise<{ url: string }> => {
    const res = await client.get(`/slides/${slideId}/pdf-url`, {
      params: options,
    })
    return res.data
  },

  getSlidePdfArrayBuffer: async (slideId: string): Promise<ArrayBuffer> => {
    const res = await client.get(`/slides/${slideId}/pdf`, {
      responseType: 'arraybuffer',
      timeout: 120000,
    })
    return res.data as ArrayBuffer
  },

  getSlideImagesManifest: async (
    slideId: string
  ): Promise<SlideDeckImagesManifest> => {
    const res = await client.get(`/slides/${slideId}/images-manifest`)
    return res.data
  },

  getSlideImageUrl: async (
    slideId: string,
    imageIndex: number,
    variant: 'thumb' | 'preview' | 'export' = 'preview'
  ): Promise<SlideDeckImageVariantData> => {
    const res = await client.get(`/slides/${slideId}/images/${imageIndex}/url`, {
      params: { variant },
    })
    return res.data
  },

  getSlideImageArrayBuffer: async (
    slideId: string,
    imageIndex: number,
    variant: 'thumb' | 'preview' | 'export' | 'full' = 'preview'
  ): Promise<ArrayBuffer> => {
    const res = await client.get(`/slides/${slideId}/images/${imageIndex}`, {
      params: { variant },
      responseType: 'arraybuffer',
      timeout: 120000,
    })
    return res.data as ArrayBuffer
  },

  getSlidePptxArrayBuffer: async (slideId: string): Promise<ArrayBuffer> => {
    const res = await client.get(`/slides/${slideId}/pptx`, {
      responseType: 'arraybuffer',
      timeout: 120000,
    })
    return res.data as ArrayBuffer
  },

  updateSlide: async (slideId: string, data: SlideDeckUpdateOptions): Promise<SlideDeckData> => {
    const res = await client.put(`/slides/${slideId}`, data)
    return res.data
  },

  deleteSlide: async (slideId: string): Promise<void> => {
    await client.delete(`/slides/${slideId}`)
  },

  // Infographic
  generateInfographic: async (notebookId: string, data: InfographicCreateOptions): Promise<InfographicData> => {
    const res = await client.post(`/notebooks/${notebookId}/infographics`, data)
    return res.data
  },

  listInfographics: async (notebookId: string): Promise<InfographicData[]> => {
    const res = await client.get(`/notebooks/${notebookId}/infographics`)
    return res.data
  },

  getInfographic: async (infographicId: string): Promise<InfographicData> => {
    const res = await client.get(`/infographics/${infographicId}`)
    return res.data
  },

  getInfographicImageUrl: async (infographicId: string): Promise<{ url: string }> => {
    const res = await client.get(`/infographics/${infographicId}/image-url`)
    return res.data
  },

  getInfographicImageArrayBuffer: async (
    infographicId: string
  ): Promise<ArrayBuffer> => {
    const res = await client.get(`/infographics/${infographicId}/image`, {
      responseType: 'arraybuffer',
      timeout: 120000,
    })
    return res.data as ArrayBuffer
  },

  updateInfographic: async (infographicId: string, data: InfographicUpdateOptions): Promise<InfographicData> => {
    const res = await client.put(`/infographics/${infographicId}`, data)
    return res.data
  },

  regenerateInfographic: async (infographicId: string, data: InfographicUpdateOptions): Promise<InfographicData> => {
    const res = await client.post(`/infographics/${infographicId}/regenerate`, data)
    return res.data
  },

  deleteInfographic: async (infographicId: string): Promise<void> => {
    await client.delete(`/infographics/${infographicId}`)
  },

  // Reports
  generateReport: async (notebookId: string, data: ReportCreateOptions): Promise<ReportData> => {
    const res = await client.post(`/notebooks/${notebookId}/reports`, data)
    return res.data
  },

  listReports: async (notebookId: string): Promise<ReportData[]> => {
    const res = await client.get(`/notebooks/${notebookId}/reports`)
    return res.data
  },

  getReport: async (reportId: string): Promise<ReportData> => {
    const res = await client.get(`/reports/${reportId}`)
    return res.data
  },

  updateReport: async (reportId: string, data: ReportUpdateOptions): Promise<ReportData> => {
    const res = await client.put(`/reports/${reportId}`, data)
    return res.data
  },

  regenerateReport: async (reportId: string, data: ReportUpdateOptions): Promise<ReportData> => {
    const res = await client.post(`/reports/${reportId}/regenerate`, data)
    return res.data
  },

  deleteReport: async (reportId: string): Promise<void> => {
    await client.delete(`/reports/${reportId}`)
  },

  // Podcasts (audio overview)
  generatePodcast: async (notebookId: string, data: PodcastCreateOptions): Promise<PodcastData> => {
    const res = await client.post(`/notebooks/${notebookId}/podcasts`, data)
    return res.data
  },

  listPodcasts: async (notebookId: string): Promise<PodcastData[]> => {
    const res = await client.get(`/notebooks/${notebookId}/podcasts`)
    return res.data
  },

  getPodcast: async (podcastId: string): Promise<PodcastData> => {
    const res = await client.get(`/podcasts/${podcastId}`)
    return res.data
  },

  getPodcastAudioUrl: async (podcastId: string): Promise<{ url: string }> => {
    const res = await client.get(`/podcasts/${podcastId}/audio-url`)
    return res.data
  },

  getPodcastAudioArrayBuffer: async (podcastId: string): Promise<ArrayBuffer> => {
    const res = await client.get(`/podcasts/${podcastId}/audio`, {
      responseType: 'arraybuffer',
      timeout: 120000,
    })
    return res.data as ArrayBuffer
  },

  deletePodcast: async (podcastId: string): Promise<void> => {
    await client.delete(`/podcasts/${podcastId}`)
  },
}
