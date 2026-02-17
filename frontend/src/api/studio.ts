import client from './client'

export interface MindMapData {
  id: string
  notebook_id: string
  title: string
  graph_data: Record<string, unknown> | null
  created_at: string
}

export interface SlideDeckData {
  id: string
  notebook_id: string
  title: string
  theme: string
  slides_data: Record<string, unknown> | null
  status: string
  file_path: string | null
  created_at: string
}

export interface InfographicData {
  id: string
  notebook_id: string
  title: string
  template_type: string
  layout_data: Record<string, unknown> | null
  file_path: string | null
  status: string
  created_at: string
}

export const studioApi = {
  // Mind Map
  generateMindMap: async (notebookId: string, data: { title?: string; source_ids?: string[] }): Promise<MindMapData> => {
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
  generateSlides: async (notebookId: string, data: { title?: string; theme?: string }): Promise<SlideDeckData> => {
    const res = await client.post(`/notebooks/${notebookId}/slides`, data)
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

  getSlidePdfUrl: async (slideId: string): Promise<{ url: string }> => {
    const res = await client.get(`/slides/${slideId}/pdf-url`)
    return res.data
  },

  updateSlide: async (slideId: string, data: Record<string, unknown>): Promise<SlideDeckData> => {
    const res = await client.put(`/slides/${slideId}`, data)
    return res.data
  },

  deleteSlide: async (slideId: string): Promise<void> => {
    await client.delete(`/slides/${slideId}`)
  },

  // Infographic
  generateInfographic: async (notebookId: string, data: { title?: string; template_type?: string }): Promise<InfographicData> => {
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

  updateInfographic: async (infographicId: string, data: Record<string, unknown>): Promise<InfographicData> => {
    const res = await client.put(`/infographics/${infographicId}`, data)
    return res.data
  },

  deleteInfographic: async (infographicId: string): Promise<void> => {
    await client.delete(`/infographics/${infographicId}`)
  },

  // Reports
  generateReport: async (notebookId: string) => {
    const res = await client.post(`/notebooks/${notebookId}/reports`)
    return res.data
  },
}
