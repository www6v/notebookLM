import shareClient from './shareClient'
import type {
  DeepResearchReportDto,
} from '@/api/deepResearch'
import type {
  InfographicData,
  MindMapData,
  PodcastData,
  ReportData,
  SlideDeckData,
  SlideDeckImagesManifest,
  SlideDeckImageVariantData,
  SlideDeckPdfUrlOptions,
} from '@/api/studio'
import type { Note } from '@/api/note'
import type { ChunkContext, Source } from '@/api/source'

export interface SharedNotebookDto {
  id: string
  title: string
  description: string
  created_at: string
  updated_at: string
  source_count: number
}

function shareRoot(token: string): string {
  return `/share/${encodeURIComponent(token)}`
}

export interface SourceContentDto {
  id: string
  title: string
  raw_content: string | null
  chunk_count: number
  file_url: string | null
}

export const shareReadApi = {
  getNotebook: async (token: string): Promise<SharedNotebookDto> => {
    const res = await shareClient.get(`${shareRoot(token)}/notebook`)
    return res.data
  },

  listSources: async (token: string): Promise<Source[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/sources`)
    return res.data
  },

  getSource: async (token: string, sourceId: string): Promise<Source> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/sources/${sourceId}`,
    )
    return res.data
  },

  getSourceContent: async (
    token: string,
    sourceId: string,
  ): Promise<SourceContentDto> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/sources/${sourceId}/content`,
    )
    return res.data
  },

  getFileUrl: async (
    token: string,
    sourceId: string,
  ): Promise<{ url: string }> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/sources/${sourceId}/file`,
    )
    return res.data
  },

  getFileStream: async (token: string, sourceId: string): Promise<Blob> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/sources/${sourceId}/file/stream`,
      { responseType: 'blob' },
    )
    return res.data as Blob
  },

  getChunkContext: async (
    token: string,
    sourceId: string,
    chunkId: string,
  ): Promise<ChunkContext> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/sources/${sourceId}/chunks/${chunkId}`,
    )
    return res.data
  },

  listMindMaps: async (token: string): Promise<MindMapData[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/mindmaps`)
    return res.data
  },

  getMindMap: async (
    token: string,
    mindmapId: string,
  ): Promise<MindMapData> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/mindmaps/${mindmapId}`,
    )
    return res.data
  },

  listSlides: async (token: string): Promise<SlideDeckData[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/slides`)
    return res.data
  },

  getSlide: async (token: string, slideId: string): Promise<SlideDeckData> => {
    const res = await shareClient.get(`${shareRoot(token)}/slides/${slideId}`)
    return res.data
  },

  getSlidePdfUrl: async (
    token: string,
    slideId: string,
    options: SlideDeckPdfUrlOptions = {},
  ): Promise<{ url: string }> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/slides/${slideId}/pdf-url`,
      { params: options },
    )
    return res.data
  },

  getSlidePdfArrayBuffer: async (
    token: string,
    slideId: string,
  ): Promise<ArrayBuffer> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/slides/${slideId}/pdf`,
      { responseType: 'arraybuffer', timeout: 120000 },
    )
    return res.data as ArrayBuffer
  },

  getSlideImagesManifest: async (
    token: string,
    slideId: string,
  ): Promise<SlideDeckImagesManifest> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/slides/${slideId}/images-manifest`,
    )
    return res.data
  },

  getSlideImageUrl: async (
    token: string,
    slideId: string,
    imageIndex: number,
    variant: 'thumb' | 'preview' | 'export' = 'preview',
  ): Promise<SlideDeckImageVariantData> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/slides/${slideId}/images/${imageIndex}/url`,
      { params: { variant } },
    )
    return res.data
  },

  getSlideImageArrayBuffer: async (
    token: string,
    slideId: string,
    imageIndex: number,
    variant: 'thumb' | 'preview' | 'export' | 'full' = 'preview',
  ): Promise<ArrayBuffer> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/slides/${slideId}/images/${imageIndex}`,
      { params: { variant }, responseType: 'arraybuffer', timeout: 120000 },
    )
    return res.data as ArrayBuffer
  },

  getSlidePptxArrayBuffer: async (
    token: string,
    slideId: string,
  ): Promise<ArrayBuffer> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/slides/${slideId}/pptx`,
      { responseType: 'arraybuffer', timeout: 120000 },
    )
    return res.data as ArrayBuffer
  },

  listInfographics: async (token: string): Promise<InfographicData[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/infographics`)
    return res.data
  },

  getInfographic: async (
    token: string,
    infographicId: string,
  ): Promise<InfographicData> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/infographics/${infographicId}`,
    )
    return res.data
  },

  getInfographicImageUrl: async (
    token: string,
    infographicId: string,
  ): Promise<{ url: string }> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/infographics/${infographicId}/image-url`,
    )
    return res.data
  },

  getInfographicImageArrayBuffer: async (
    token: string,
    infographicId: string,
  ): Promise<ArrayBuffer> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/infographics/${infographicId}/image`,
      { responseType: 'arraybuffer', timeout: 120000 },
    )
    return res.data as ArrayBuffer
  },

  listReports: async (token: string): Promise<ReportData[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/reports`)
    return res.data
  },

  getReport: async (token: string, reportId: string): Promise<ReportData> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/reports/${reportId}`,
    )
    return res.data
  },

  listPodcasts: async (token: string): Promise<PodcastData[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/podcasts`)
    return res.data
  },

  getPodcast: async (
    token: string,
    podcastId: string,
  ): Promise<PodcastData> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/podcasts/${podcastId}`,
    )
    return res.data
  },

  getPodcastAudioUrl: async (
    token: string,
    podcastId: string,
  ): Promise<{ url: string }> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/podcasts/${podcastId}/audio-url`,
    )
    return res.data
  },

  getPodcastAudioArrayBuffer: async (
    token: string,
    podcastId: string,
  ): Promise<ArrayBuffer> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/podcasts/${podcastId}/audio`,
      { responseType: 'arraybuffer', timeout: 120000 },
    )
    return res.data as ArrayBuffer
  },

  listNotes: async (token: string): Promise<Note[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/notes`)
    return res.data
  },

  listDeepResearch: async (token: string): Promise<DeepResearchReportDto[]> => {
    const res = await shareClient.get(`${shareRoot(token)}/deep-research`)
    return res.data
  },

  getDeepResearch: async (
    token: string,
    reportId: string,
  ): Promise<DeepResearchReportDto> => {
    const res = await shareClient.get(
      `${shareRoot(token)}/deep-research/${reportId}`,
    )
    return res.data
  },
}
