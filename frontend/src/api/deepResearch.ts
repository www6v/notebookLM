import client from './client'
import type { Source } from './source'
import { streamTaskUntilTerminal } from './taskEvents'

export interface DeepResearchReportDto {
  id: string
  query: string
  sourceCount: number
  popularCount: number
  content: string | null
  status: string
  error_message: string | null
  created_at: string
}

export interface DeepResearchCreateBody {
  query: string
}

const POLL_INTERVAL_MS = 2500
/** Wall-clock cap aligned with server 30m + buffer (31m). */
const POLL_MAX_WAIT_MS = 31 * 60 * 1000
const STREAM_MAX_WAIT_MS = 31 * 60 * 1000

/**
 * Create a deep research task. Returns the initial report (status pending);
 * caller should poll getDeepResearch(reportId) until status is ready or error.
 */
export async function createDeepResearch(
  notebookId: string,
  body: DeepResearchCreateBody
): Promise<DeepResearchReportDto> {
  const { data } = await client.post<DeepResearchReportDto>(
    `/notebooks/${notebookId}/deep-research`,
    body
  )
  return data
}

export async function getDeepResearch(
  reportId: string
): Promise<DeepResearchReportDto> {
  const { data } = await client.get<DeepResearchReportDto>(
    `/deep-research/${reportId}`
  )
  return data
}

export async function listDeepResearch(
  notebookId: string
): Promise<DeepResearchReportDto[]> {
  const { data } = await client.get<DeepResearchReportDto[]>(
    `/notebooks/${notebookId}/deep-research`
  )
  return data
}

export async function deleteDeepResearch(reportId: string): Promise<void> {
  await client.delete(`/deep-research/${reportId}`)
}

export async function cancelDeepResearch(
  reportId: string
): Promise<DeepResearchReportDto> {
  const { data } = await client.post<DeepResearchReportDto>(
    `/deep-research/${reportId}/cancel`
  )
  return data
}

export async function importDeepResearchAsSource(
  notebookId: string,
  reportId: string
): Promise<Source> {
  const { data } = await client.post<Source>(
    `/notebooks/${notebookId}/deep-research/${reportId}/import-source`
  )
  return data
}

/**
 * Poll until report status is ready or error; returns final report.
 * Throws if max wait time is exceeded.
 */
export function pollDeepResearchUntilDone(
  reportId: string,
  onProgress?: (report: DeepResearchReportDto) => void
): Promise<DeepResearchReportDto> {
  const start = Date.now()
  return new Promise((resolve, reject) => {
    const poll = async () => {
      if (Date.now() - start > POLL_MAX_WAIT_MS) {
        reject(new Error('Deep research 等待超时'))
        return
      }
      try {
        const report = await getDeepResearch(reportId)
        onProgress?.(report)
        if (report.status === 'ready') {
          resolve(report)
          return
        }
        if (report.status === 'error') {
          resolve(report)
          return
        }
        setTimeout(poll, POLL_INTERVAL_MS)
      } catch (e) {
        reject(e)
      }
    }
    poll()
  })
}

export async function streamDeepResearchUntilDone(
  reportId: string,
  onProgress?: (report: DeepResearchReportDto) => void
): Promise<DeepResearchReportDto> {
  const finalReport = await streamTaskUntilTerminal<DeepResearchReportDto>({
    resourceType: 'deep-research',
    resourceId: reportId,
    fetchCurrent: () => getDeepResearch(reportId),
    timeoutMs: STREAM_MAX_WAIT_MS,
  })
  onProgress?.(finalReport)
  return finalReport
}
