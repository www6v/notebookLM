import client from './client'

export interface Source {
  id: string
  notebook_id: string
  title: string
  type: string
  original_url: string | null
  summary?: string | null
  tags?: string[] | null
  is_active: boolean
  status: string
  created_at: string
}

export interface SourceContent {
  id: string
  title: string
  type: string
  summary: string | null
  tags: string[] | null
  raw_content: string | null
  chunk_count: number
  file_url: string | null
}

export interface ChunkContext {
  chunk_id: string
  source_id: string
  source_title: string
  content: string
  chunk_index: number
  page_number: number | null
  paragraph_index: number | null
  prev_content: string | null
  next_content: string | null
}

export const sourceApi = {
  list: async (notebookId: string): Promise<Source[]> => {
    const res = await client.get(`/notebooks/${notebookId}/sources`)
    return res.data
  },

  get: async (sourceId: string): Promise<Source> => {
    const res = await client.get(`/sources/${sourceId}`)
    return res.data
  },

  add: async (notebookId: string, data: { title?: string; type: string; url?: string }): Promise<Source> => {
    const res = await client.post(`/notebooks/${notebookId}/sources`, data)
    return res.data
  },

  upload: async (notebookId: string, file: File, title?: string): Promise<Source> => {
    const formData = new FormData()
    formData.append('file', file)
    if (title) {
      formData.append('title', title)
    }
    const res = await client.post(`/notebooks/${notebookId}/sources/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },

  update: async (sourceId: string, data: { title?: string; is_active?: boolean }): Promise<Source> => {
    const res = await client.patch(`/sources/${sourceId}`, data)
    return res.data
  },

  remove: async (sourceId: string): Promise<void> => {
    await client.delete(`/sources/${sourceId}`)
  },

  getContent: async (sourceId: string): Promise<SourceContent> => {
    const res = await client.get<SourceContent>(`/sources/${sourceId}/content`)
    return res.data
  },

  /** 获取图片源在对象存储中的展示链接，前端直接用该 URL 展示图片 */
  getFileUrl: async (sourceId: string): Promise<{ url: string }> => {
    const res = await client.get<{ url: string }>(`/sources/${sourceId}/file`)
    return res.data
  },

  /** 直链加载失败时，通过后端流式接口拉取图片（带鉴权） */
  getFileStream: async (sourceId: string): Promise<Blob> => {
    const res = await client.get(`/sources/${sourceId}/file/stream`, {
      responseType: 'blob',
    })
    return res.data
  },

  getChunkContext: async (sourceId: string, chunkId: string): Promise<ChunkContext> => {
    const res = await client.get(`/sources/${sourceId}/chunks/${chunkId}`)
    return res.data
  },
}
