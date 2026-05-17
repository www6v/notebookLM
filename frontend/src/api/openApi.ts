import client from '@/api/client'

export interface OpenApiCredentialStatus {
  has_credential: boolean
  client_id?: string | null
  status?: string | null
  status_label?: string | null
  expires_at?: string | null
}

export interface OpenApiCredentialReveal {
  client_id: string
  api_key: string
  status: string
  status_label: string
  expires_at: string
  reveal_once: boolean
}

export interface OpenApiCredentialDelete {
  has_credential: boolean
}

export async function fetchOpenApiCredentialStatus(): Promise<OpenApiCredentialStatus> {
  const res = await client.get<OpenApiCredentialStatus>('/open-api/credential')
  return res.data
}

export async function createOpenApiCredential(): Promise<OpenApiCredentialReveal> {
  const res = await client.post<OpenApiCredentialReveal>('/open-api/credential')
  return res.data
}

export async function regenerateOpenApiCredential(): Promise<OpenApiCredentialReveal> {
  const res = await client.post<OpenApiCredentialReveal>(
    '/open-api/credential/regenerate',
  )
  return res.data
}

export async function deleteOpenApiCredential(): Promise<OpenApiCredentialDelete> {
  const res = await client.delete<OpenApiCredentialDelete>('/open-api/credential')
  return res.data
}
