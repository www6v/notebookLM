export interface TaskEventPayload {
  resource_type: string
  resource_id: string
  status: string | null
  error_message?: string | null
}

const TERMINAL_TASK_STATUSES = new Set(['ready', 'error'])

const parseSseMessages = (chunk: string) => {
  return chunk
    .split('\n\n')
    .map((entry) => entry.trim())
    .filter((entry) => entry && !entry.startsWith(':'))
    .map((entry) => entry
      .split('\n')
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trim())
      .join('\n'))
    .filter(Boolean)
}

export async function streamTaskUntilTerminal<T>(options: {
  resourceType: string
  resourceId: string
  fetchCurrent: () => Promise<T>
  timeoutMs?: number
  onEvent?: (payload: TaskEventPayload) => void
}): Promise<T> {
  const {
    resourceType,
    resourceId,
    fetchCurrent,
    timeoutMs = 600000,
    onEvent,
  } = options

  const token = localStorage.getItem('token')
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(
      `/api/task-events/${resourceType}/${resourceId}/stream`,
      {
        method: 'GET',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      }
    )

    if (!response.ok || !response.body) {
      throw new Error(`Task event stream failed with status ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const entries = buffer.split('\n\n')
      buffer = entries.pop() || ''

      for (const entry of entries) {
        for (const message of parseSseMessages(entry)) {
          const payload = JSON.parse(message) as TaskEventPayload
          onEvent?.(payload)
          if (TERMINAL_TASK_STATUSES.has(payload.status || '')) {
            return await fetchCurrent()
          }
        }
      }
    }

    throw new Error('Task event stream closed before completion')
  } finally {
    window.clearTimeout(timeoutId)
    controller.abort()
  }
}
