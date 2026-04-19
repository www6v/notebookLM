import client from './client'
import type { UserResponse } from './auth'
import type { PublicClientConfig } from '@/api/publicClient'

export interface UploadedFileTypeStat {
  source_type: string
  count: number
  size_bytes: number
}

export interface NotebookStatsItem {
  id: string
  title: string
  source_count: number
  mind_map_success_count: number
  mind_map_failed_count: number
  slide_deck_success_count: number
  slide_deck_failed_count: number
  infographic_success_count: number
  infographic_failed_count: number
  report_success_count: number
  report_failed_count: number
  podcast_overview_success_count: number
  podcast_overview_failed_count: number
  created_at: string
  uploaded_file_stats: UploadedFileTypeStat[]
  uploaded_file_total_count: number
  uploaded_file_total_bytes: number
}

export interface AdminUserDetailResponse {
  id: string
  email: string
  username: string
  role: string
  is_active: boolean
  created_at: string
  notebook_count: number
  notebooks: NotebookStatsItem[]
}

export interface AdminUserListResponse {
  users: UserResponse[]
  total: number
  page: number
  page_size: number
}

export interface AdminUserUpdateRequest {
  role?: string
  is_active?: boolean
}

export const adminApi = {
  listUsers: async (params: {
    page?: number
    page_size?: number
    search?: string
    role?: string
  } = {}): Promise<AdminUserListResponse> => {
    const res = await client.get('/admin/users', { params })
    return res.data
  },

  getUserDetail: async (userId: string): Promise<AdminUserDetailResponse> => {
    const res = await client.get(`/admin/users/${userId}`)
    return res.data
  },

  updateUser: async (
    userId: string,
    data: AdminUserUpdateRequest,
  ): Promise<UserResponse> => {
    const res = await client.patch(`/admin/users/${userId}`, data)
    return res.data
  },

  putClientConfig: async (body: {
    desktop_backend_url: string
  }): Promise<PublicClientConfig> => {
    const res = await client.put<PublicClientConfig>('/admin/client-config', body)
    return res.data
  },
}
