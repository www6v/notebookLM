import client from './client'

export interface UserSettingsResponse {
  output_language: string
  llm_provider: string
  llm_model: string
}

export interface UserSettingsUpdate {
  output_language?: string
  llm_provider?: string
  llm_model?: string
}

export const settingsApi = {
  get: async (): Promise<UserSettingsResponse> => {
    const res = await client.get('/settings')
    return res.data
  },

  patch: async (data: UserSettingsUpdate): Promise<UserSettingsResponse> => {
    const res = await client.patch('/settings', data)
    return res.data
  },
}
